import json
import re
from pathlib import Path

CONSTRAINT_KEYWORDS = (
    "必须",
    "不能",
    "不得",
    "不做",
    "不出",
    "禁止",
    "只",
    "≤",
    "硬约束",
    "上限",
    "以内",
    "无需",
)


def load_fixture(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_constraints(text: str) -> list[str]:
    """Extract short hard-constraint clauses from a user turn.

    This is deliberately deterministic: it keeps clauses with constraint
    markers, trims them, and deduplicates within one turn. It does not claim
    to be a general natural-language constraint extractor.
    """
    if not text:
        return []
    clauses = re.split(r"[；;\n。]", text)
    found: list[str] = []
    for raw in clauses:
        clause = raw.strip(" \t\r-•")
        if len(clause) < 4:
            continue
        if not any(keyword in clause for keyword in CONSTRAINT_KEYWORDS):
            continue
        if len(clause) > 160:
            clause = clause[:160].rstrip()
        if clause not in found:
            found.append(clause)
    return found


def _preview(text: str, limit: int = 240) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def seed_fixture(conn, fixture_path: str | Path, reset: bool = True) -> dict:
    """Write the real 10-case / 31-turn local regression fixture into Relate.

    The function is idempotent when reset=False because all nodes are MERGEd
    by stable ids. reset=True removes the existing graph first.
    """
    data = load_fixture(fixture_path)
    stats = {
        "sessions": 0,
        "turns": 0,
        "checks": 0,
        "issues": 0,
        "repairs": 0,
        "scenarios": 0,
        "constraints": 0,
    }
    scenario_names: set[str] = set()

    if reset:
        conn.execute("MATCH (n) DETACH DELETE n")

    conn.autocommit = False
    try:
        for case in data.get("cases", []):
            session_id = case["id"]
            turns = case.get("turns", [])
            conn.execute(
                """
                MERGE (s:Session {id: $id})
                SET s.title = $title,
                    s.model = $model,
                    s.created_at = $created_at,
                    s.note = $note,
                    s.turn_count = $turn_count
                """,
                {
                    "id": session_id,
                    "title": case.get("title", ""),
                    "model": data.get("model", ""),
                    "created_at": data.get("created_at", ""),
                    "note": data.get("note", ""),
                    "turn_count": len(turns),
                },
            )
            conn.execute(
                "MERGE (m:Model {name: $name})",
                {"name": data.get("model", "")},
            )
            conn.execute(
                """
                MATCH (s:Session {id: $sid}), (m:Model {name: $model})
                MERGE (s)-[:USED_MODEL]->(m)
                """,
                {"sid": session_id, "model": data.get("model", "")},
            )
            stats["sessions"] += 1

            previous_turn_id = None
            for turn in turns:
                turn_id = f"{session_id}-T{turn['index']}"
                check_id = f"{turn_id}-check"
                scenario = turn.get("scenario", "unknown")
                answer = turn.get("answer") or turn.get("raw_answer") or ""
                constraints = extract_constraints(turn.get("user", ""))

                conn.execute(
                    """
                    MERGE (t:Turn {id: $id})
                    SET t.index = $index,
                        t.user = $user,
                        t.scenario = $scenario,
                        t.task = $task,
                        t.post_valid = $valid,
                        t.post_repaired = $repaired,
                        t.chars = $chars,
                        t.first_token_s = $first_token_s,
                        t.total_s = $total_s,
                        t.eval_count = $eval_count,
                        t.tokens_per_s = $tokens_per_s,
                        t.answer_preview = $answer_preview
                    """,
                    {
                        "id": turn_id,
                        "index": int(turn["index"]),
                        "user": turn.get("user", ""),
                        "scenario": scenario,
                        "task": turn.get("task", ""),
                        "valid": bool(turn.get("post_valid", False)),
                        "repaired": bool(turn.get("post_repaired", False)),
                        "chars": int(turn.get("chars") or len(answer)),
                        "first_token_s": float(turn.get("first_token_s") or 0.0),
                        "total_s": float(turn.get("total_s") or 0.0),
                        "eval_count": int(turn.get("eval_count") or 0),
                        "tokens_per_s": float(turn.get("tokens_per_s") or 0.0),
                        "answer_preview": _preview(answer),
                    },
                )
                conn.execute(
                    """
                    MATCH (s:Session {id: $sid}), (t:Turn {id: $tid})
                    MERGE (s)-[:HAS_TURN]->(t)
                    """,
                    {"sid": session_id, "tid": turn_id},
                )
                conn.execute(
                    "MERGE (sc:Scenario {name: $name})",
                    {"name": scenario},
                )
                conn.execute(
                    """
                    MATCH (t:Turn {id: $tid}), (sc:Scenario {name: $name})
                    MERGE (t)-[:IN_SCENARIO]->(sc)
                    """,
                    {"tid": turn_id, "name": scenario},
                )
                scenario_names.add(scenario)

                conn.execute(
                    """
                    MERGE (c:Check {id: $cid})
                    SET c.valid = $valid, c.repaired = $repaired
                    """,
                    {
                        "cid": check_id,
                        "valid": bool(turn.get("post_valid", False)),
                        "repaired": bool(turn.get("post_repaired", False)),
                    },
                )
                conn.execute(
                    """
                    MATCH (t:Turn {id: $tid}), (c:Check {id: $cid})
                    MERGE (t)-[:CHECKED_BY]->(c)
                    """,
                    {"tid": turn_id, "cid": check_id},
                )
                stats["checks"] += 1
                if turn.get("post_repaired"):
                    stats["repairs"] += 1

                for index, issue_text in enumerate(turn.get("post_issues") or [], start=1):
                    issue_id = f"{turn_id}-issue-{index}"
                    conn.execute(
                        "MERGE (i:Issue {id: $iid}) SET i.text = $text",
                        {"iid": issue_id, "text": issue_text},
                    )
                    conn.execute(
                        """
                        MATCH (c:Check {id: $cid}), (i:Issue {id: $iid})
                        MERGE (c)-[:FOUND]->(i)
                        """,
                        {"cid": check_id, "iid": issue_id},
                    )
                    stats["issues"] += 1

                if previous_turn_id:
                    conn.execute(
                        """
                        MATCH (prev:Turn {id: $prev}), (t:Turn {id: $tid})
                        MERGE (prev)-[:NEXT]->(t)
                        """,
                        {"prev": previous_turn_id, "tid": turn_id},
                    )
                previous_turn_id = turn_id
                stats["turns"] += 1

                for constraint in constraints:
                    conn.execute(
                        "MERGE (co:Constraint {text: $text})",
                        {"text": constraint},
                    )
                    conn.execute(
                        """
                        MATCH (t:Turn {id: $tid}), (co:Constraint {text: $text})
                        MERGE (t)-[:INCLUDES]->(co)
                        """,
                        {"tid": turn_id, "text": constraint},
                    )
                    stats["constraints"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True

    stats["scenarios"] = len(scenario_names)
    return stats
