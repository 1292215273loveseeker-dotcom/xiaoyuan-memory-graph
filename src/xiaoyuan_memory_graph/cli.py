import argparse
import json
import re
import sys

from . import __version__
from .ingest import seed_fixture
from .queries import (
    all_repairs,
    constraints_for_turn,
    gate_trace,
    list_sessions,
    recall_session,
    repair_trace,
    scenario_stats,
)
from .store import connect, default_db_path, project_root


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _print_session(result):
    print(f"{result['id']} — {result['title']}")
    print(f"model: {result.get('model', '')} | turns: {result.get('turn_count', 0)}")
    for turn in result.get("turns", []):
        status = "REPAIRED" if turn.get("repaired") else ("valid" if turn.get("valid") else "invalid")
        print(f"  {turn['id']} [{turn.get('scenario', '')}] {status}")
        print(f"    user: {turn.get('user', '')[:160]}")
        if turn.get("issues"):
            for issue in turn["issues"]:
                print(f"    issue: {issue}")


def _print_stats(conn):
    sessions = list_sessions(conn)
    total_turns = sum(int(item.get("turn_count") or 0) for item in sessions)
    checks = conn.execute("MATCH (c:Check) RETURN count(c) AS n").single()["n"]
    issues = conn.execute("MATCH (i:Issue) RETURN count(i) AS n").single()["n"]
    repairs = conn.execute("MATCH (c:Check {repaired: true}) RETURN count(c) AS n").single()["n"]
    print(f"Graph: {len(sessions)} sessions / {total_turns} turns / {checks} checks / {repairs} repairs / {issues} issues")
    print("")
    print("Scenario stats:")
    for row in scenario_stats(conn):
        print(
            f"  {row['scenario']:<14} turns={row['turns']:<2} repairs={row['repairs']:<2} avg_latency={row['avg_latency_s']}s"
        )


def _resolve_question(conn, question: str):
    lower = question.lower()
    match = re.search(r"\bq(\d+)\b", lower)
    session_id = f"Q{match.group(1)}" if match else None
    if "constraint" in lower:
        turn_id = f"{session_id}-T1" if session_id else "Q1-T1"
        rows = constraints_for_turn(conn, turn_id)
        print(f"Constraints for {turn_id}:")
        for row in rows:
            print(f"  - {row['text']}")
        return
    if "repair" in lower or "gate" in lower or "safety" in lower or "blocked" in lower:
        if session_id:
            rows = gate_trace(conn, session_id)
            for row in rows:
                status = "REPAIRED" if row.get("repaired") else ("valid" if row.get("valid") else "invalid")
                print(f"{row['id']} [{row.get('scenario', '')}] {status}")
                for issue in row.get("issues", []):
                    print(f"  issue: {issue}")
            return
        rows = all_repairs(conn)
        for row in rows:
            print(f"{row['id']} [{row.get('scenario', '')}] {row['issue']}")
        return
    if "stats" in lower or "scenario" in lower:
        _print_stats(conn)
        return
    if "remember" in lower or "recall" in lower or "last session" in lower or session_id:
        target = session_id or "Q10"
        result = recall_session(conn, target)
        if not result:
            print(f"No session {target!r} in the graph.")
            return
        _print_session(result)
        return
    print("Try one of these:")
    print('  xiaoyuan-memory ask "what did the agent remember from Q1?"')
    print('  xiaoyuan-memory ask "which gates repaired Q8?"')
    print('  xiaoyuan-memory ask "what constraints were in Q1?"')
    print('  xiaoyuan-memory ask "show scenario stats"')


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="xiaoyuan-memory",
        description="A local-first memory graph for Xiaoyuan 14B, built on Relate by Neo4j.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--db", default=str(default_db_path()), help="Path to a .rl store")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Build the graph from the real regression fixture")
    seed.add_argument(
        "--fixture",
        default=str(project_root() / "data" / "ten_question_regression_full.json"),
        help="Path to ten_question_regression_full.json",
    )
    seed_group = seed.add_mutually_exclusive_group()
    seed_group.add_argument("--reset", action="store_true", help="Clear the existing graph first (default)")
    seed_group.add_argument("--no-reset", action="store_true", help="Merge into an existing store instead of clearing it")

    ask = sub.add_parser("ask", help="Ask one of the supported deterministic questions")
    ask.add_argument("question")

    trace = sub.add_parser("trace", help="Show a turn's gate trace")
    trace.add_argument("turn_id")

    sub.add_parser("stats", help="Show graph and scenario statistics")
    sub.add_parser("sessions", help="List sessions")
    sub.add_parser("demo", help="Print a short, reproducible demo sequence")
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "seed":
            conn = connect(args.db, read_only=False)
            stats = seed_fixture(conn, args.fixture, reset=not args.no_reset)
            conn.close()
            print(json.dumps(stats, ensure_ascii=False, indent=2) if args.json else f"Seeded {args.db}: {stats}")
            return 0

        conn = connect(args.db, read_only=True)
        try:
            if args.command == "ask":
                if args.json:
                    lower = args.question.lower()
                    match = re.search(r"\bq(\d+)\b", lower)
                    session_id = f"Q{match.group(1)}" if match else None
                    if "repair" in lower or "gate" in lower:
                        _print_json(gate_trace(conn, session_id) if session_id else all_repairs(conn))
                    elif "constraint" in lower:
                        _print_json(constraints_for_turn(conn, f"{session_id}-T1" if session_id else "Q1-T1"))
                    elif "stats" in lower or "scenario" in lower:
                        _print_json(scenario_stats(conn))
                    else:
                        _print_json(recall_session(conn, session_id or "Q10"))
                else:
                    _resolve_question(conn, args.question)
                return 0

            if args.command == "trace":
                result = repair_trace(conn, args.turn_id)
                if not result:
                    print(f"No turn {args.turn_id!r} in the graph.")
                    return 1
                if args.json:
                    _print_json(result)
                else:
                    status = "REPAIRED" if result.get("repaired") else ("valid" if result.get("valid") else "invalid")
                    print(f"{result['id']} [{result.get('scenario', '')}] {status}")
                    print(f"user: {result.get('user', '')}")
                    print(f"answer preview: {result.get('answer_preview', '')}")
                    if result.get("issues"):
                        print("issues:")
                        for issue in result["issues"]:
                            print(f"  - {issue}")
                    if result.get("constraints"):
                        print("constraints:")
                        for item in result["constraints"]:
                            print(f"  - {item['text']}")
                return 0

            if args.command == "stats":
                if args.json:
                    sessions = list_sessions(conn)
                    _print_json(
                        {
                            "sessions": sessions,
                            "scenario_stats": scenario_stats(conn),
                            "repairs": all_repairs(conn),
                        }
                    )
                else:
                    _print_stats(conn)
                return 0

            if args.command == "sessions":
                sessions = list_sessions(conn)
                if args.json:
                    _print_json(sessions)
                else:
                    for item in sessions:
                        print(f"{item['id']} — {item['title']} ({item['turn_count']} turns)")
                return 0

            if args.command == "demo":
                print("Xiaoyuan Memory Graph — reproducible demo")
                print("=" * 44)
                print("\n1. Recall the last turn of Q1")
                _print_session(recall_session(conn, "Q1"))
                print("\n2. Show the post-check gate trace for Q8")
                for row in gate_trace(conn, "Q8"):
                    status = "REPAIRED" if row.get("repaired") else ("valid" if row.get("valid") else "invalid")
                    print(f"  {row['id']} [{row.get('scenario', '')}] {status}")
                    for issue in row.get("issues", []):
                        print(f"    issue: {issue}")
                print("\n3. Show scenario-level evidence")
                _print_stats(conn)
                return 0
        finally:
            conn.close()
    except Exception as exc:
        print(f"xiaoyuan-memory: {exc}", file=sys.stderr)
        return 1
