def _rows(conn, query: str, params: dict | None = None) -> list[dict]:
    return list(conn.execute(query, params or {}))


def list_sessions(conn) -> list[dict]:
    return _rows(
        conn,
        """
        MATCH (s:Session)
        RETURN s.id AS id, s.title AS title, s.turn_count AS turn_count,
               s.model AS model, s.created_at AS created_at
        ORDER BY s.id
        """,
    )


def recall_session(conn, session_id: str) -> dict | None:
    summary = conn.execute(
        """
        MATCH (s:Session {id: $id})
        RETURN s.id AS id, s.title AS title, s.model AS model,
               s.created_at AS created_at, s.note AS note,
               s.turn_count AS turn_count
        """,
        {"id": session_id},
    ).single()
    if not summary:
        return None

    turns = _rows(
        conn,
        """
        MATCH (s:Session {id: $id})-[:HAS_TURN]->(t:Turn)
        MATCH (t)-[:CHECKED_BY]->(c:Check)
        RETURN t.id AS id, t.index AS index, t.user AS user,
               t.scenario AS scenario, t.answer_preview AS answer_preview,
               c.valid AS valid, c.repaired AS repaired
        ORDER BY t.index
        """,
        {"id": session_id},
    )
    for turn in turns:
        turn["issues"] = _rows(
            conn,
            """
            MATCH (t:Turn {id: $id})-[:CHECKED_BY]->(:Check)-[:FOUND]->(i:Issue)
            RETURN i.text AS text
            ORDER BY i.id
            """,
            {"id": turn["id"]},
        )
        turn["issues"] = [row["text"] for row in turn["issues"]]

    summary["turns"] = turns
    summary["turn_count"] = len(turns)
    summary["last_turn"] = turns[-1] if turns else None
    return summary


def gate_trace(conn, session_id: str) -> list[dict]:
    turns = _rows(
        conn,
        """
        MATCH (s:Session {id: $id})-[:HAS_TURN]->(t:Turn)
        MATCH (t)-[:CHECKED_BY]->(c:Check)
        RETURN t.id AS id, t.index AS index, t.user AS user,
               t.scenario AS scenario, t.answer_preview AS answer_preview,
               c.valid AS valid, c.repaired AS repaired
        ORDER BY t.index
        """,
        {"id": session_id},
    )
    for turn in turns:
        issues = _rows(
            conn,
            """
            MATCH (t:Turn {id: $id})-[:CHECKED_BY]->(:Check)-[:FOUND]->(i:Issue)
            RETURN i.text AS text
            ORDER BY i.id
            """,
            {"id": turn["id"]},
        )
        turn["issues"] = [row["text"] for row in issues]
    return turns


def scenario_stats(conn) -> list[dict]:
    rows = _rows(
        conn,
        """
        MATCH (t:Turn)-[:IN_SCENARIO]->(s:Scenario)
        MATCH (t)-[:CHECKED_BY]->(c:Check)
        RETURN s.name AS scenario, t.total_s AS latency_s, c.repaired AS repaired
        """,
    )
    grouped: dict[str, dict] = {}
    for row in rows:
        item = grouped.setdefault(
            row["scenario"],
            {"scenario": row["scenario"], "turns": 0, "repairs": 0, "total_latency_s": 0.0},
        )
        item["turns"] += 1
        item["repairs"] += 1 if row["repaired"] else 0
        item["total_latency_s"] += float(row.get("latency_s") or 0.0)
    result = []
    for item in grouped.values():
        item["avg_latency_s"] = round(item["total_latency_s"] / item["turns"], 2) if item["turns"] else 0.0
        del item["total_latency_s"]
        result.append(item)
    return sorted(result, key=lambda item: (-item["turns"], item["scenario"]))


def constraints_for_turn(conn, turn_id: str) -> list[dict]:
    return _rows(
        conn,
        """
        MATCH (t:Turn {id: $id})-[:INCLUDES]->(co:Constraint)
        RETURN co.text AS text
        ORDER BY co.text
        """,
        {"id": turn_id},
    )


def repair_trace(conn, turn_id: str) -> dict | None:
    base = conn.execute(
        """
        MATCH (t:Turn {id: $id})-[:CHECKED_BY]->(c:Check)
        RETURN t.id AS id, t.index AS index, t.scenario AS scenario,
               t.user AS user, t.answer_preview AS answer_preview,
               c.valid AS valid, c.repaired AS repaired
        """,
        {"id": turn_id},
    ).single()
    if not base:
        return None
    issues = _rows(
        conn,
        """
        MATCH (t:Turn {id: $id})-[:CHECKED_BY]->(:Check)-[:FOUND]->(i:Issue)
        RETURN i.text AS text
        ORDER BY i.id
        """,
        {"id": turn_id},
    )
    base["issues"] = [row["text"] for row in issues]
    base["constraints"] = constraints_for_turn(conn, turn_id)
    return base


def all_repairs(conn) -> list[dict]:
    return _rows(
        conn,
        """
        MATCH (t:Turn)-[:CHECKED_BY]->(c:Check)-[:FOUND]->(i:Issue)
        RETURN t.id AS id, t.index AS index, t.scenario AS scenario,
               t.answer_preview AS answer_preview, i.text AS issue
        ORDER BY t.id
        """,
    )
