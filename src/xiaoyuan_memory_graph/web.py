import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .queries import all_repairs, list_sessions, recall_session, repair_trace, scenario_stats
from .store import connect, default_db_path, project_root

WEB_DIR = project_root() / "web"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _count(self, conn, query):
        return conn.execute(query).single()["n"]

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            if parsed.path in ("", "/"):
                self.path = "/index.html"
            return super().do_GET()

        try:
            conn = connect(default_db_path(), read_only=True)
            try:
                if parsed.path == "/api/stats":
                    sessions = list_sessions(conn)
                    checks = self._count(conn, "MATCH (c:Check) RETURN count(c) AS n")
                    repairs = self._count(conn, "MATCH (c:Check {repaired: true}) RETURN count(c) AS n")
                    issues = self._count(conn, "MATCH (i:Issue) RETURN count(i) AS n")
                    return self._json(
                        {
                            "sessions": sessions,
                            "checks": checks,
                            "repairs": repairs,
                            "issues": issues,
                            "scenario_stats": scenario_stats(conn),
                            "repair_turns": all_repairs(conn),
                        }
                    )

                if parsed.path == "/api/session":
                    session_id = (parse_qs(parsed.query).get("q") or ["Q1"])[0]
                    result = recall_session(conn, session_id)
                    if not result:
                        return self._json({"error": f"unknown session {session_id}"}, 404)
                    return self._json(result)

                if parsed.path == "/api/trace":
                    turn_id = (parse_qs(parsed.query).get("turn") or [""])[0]
                    result = repair_trace(conn, turn_id)
                    if not result:
                        return self._json({"error": f"unknown turn {turn_id}"}, 404)
                    return self._json(result)

                if parsed.path == "/api/repairs":
                    return self._json({"repairs": all_repairs(conn)})

                return self._json({"error": "not found"}, 404)
            finally:
                conn.close()
        except Exception as exc:
            return self._json({"error": str(exc)}, 500)

    def log_message(self, fmt, *args):
        print(f"[web] {self.address_string()} {fmt % args}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local dashboard for Xiaoyuan Memory Graph")
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    if not default_db_path().exists():
        print(f"Missing graph store: {default_db_path()}")
        print("Run: xiaoyuan-memory seed --reset")
        return 1
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Xiaoyuan Memory Graph dashboard: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
