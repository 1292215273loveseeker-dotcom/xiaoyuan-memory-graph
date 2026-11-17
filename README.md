# Xiaoyuan Memory Graph

A new, standalone project for the **Relate by Neo4j Hackathon 2026**.

Xiaoyuan 14B is a local-first 14B agent architecture. This project makes its memory auditable: every session, turn, scenario, hard constraint, post-check, repair, and issue is a node in **Relate by Neo4j**. The graph is built from a real local regression transcript: **10 sessions / 31 turns / 31 checks / 5 repairs / 5 issues**.

## Why Relate

- One embedded database, no server to deploy, one `.rl` file to share.
- Cypher follows the connections that matter: `Session -> Turn -> Check -> Issue`.
- The agent's memory keeps provenance, not just text: which gate fired, on which turn, and what was repaired.

## What is real

- Input: `data/ten_question_regression_full.json`, produced by the local Xiaoyuan 14B regression run on **2026-11-17**.
- Model: `qwen2.5:14b-instruct-q4_K_M` served by Ollama; local, about 9 GB, 4k context.
- Checks: the transcript's `post_valid`, `post_repaired`, and `post_issues` fields.
- Counts: 10 sessions, 31 turns, 31 post-checks, 5 repaired checks, 5 issue occurrences, 20 extracted constraint links, 13 scenario nodes.
- **Not** an official score, ranking, leaderboard entry, or third-party safety label. All results are local.

## Quick start

Requires Python 3.9+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e .

xiaoyuan-memory seed --reset
xiaoyuan-memory stats
xiaoyuan-memory ask "what did the agent remember from Q1?"
xiaoyuan-memory ask "which gates repaired Q8?"
xiaoyuan-memory ask "what constraints were in Q1?"
xiaoyuan-memory trace Q8-T1
xiaoyuan-memory demo
```

The seeded store is included at `data/xiaoyuan_memory.rl`; `seed --reset` reproduces it from the JSON fixture.

## Graph schema

```text
(:Session {id, title, model, created_at, note, turn_count})
   |-[:USED_MODEL]-> (:Model {name})
   |-[:HAS_TURN]-> (:Turn {id, index, user, scenario, task,
                           post_valid, post_repaired, chars,
                           first_token_s, total_s, eval_count, tokens_per_s,
                           answer_preview})
        |-[:NEXT]-> (:Turn)
        |-[:IN_SCENARIO]-> (:Scenario {name})
        |-[:CHECKED_BY]-> (:Check {id, valid, repaired})
        |      |-[:FOUND]-> (:Issue {id, text})
        |-[:INCLUDES]-> (:Constraint {text})
```

## Example Cypher

```cypher
// What happened in Q8, and which checks were repaired?
MATCH (s:Session {id: 'Q8'})-[:HAS_TURN]->(t:Turn)-[:CHECKED_BY]->(c:Check)
OPTIONAL MATCH (c)-[:FOUND]->(i:Issue)
RETURN t.id, t.scenario, c.valid, c.repaired, collect(i.text) AS issues
ORDER BY t.index;
```

```cypher
// Which constraint was attached to the repaired routing turn?
MATCH (t:Turn {id: 'Q8-T1'})-[:INCLUDES]->(co:Constraint)
RETURN co.text;
```

## Repository layout

```text
src/xiaoyuan_memory_graph/   ingest, queries, CLI, store
tests/                       unittest suite (5 tests)
data/                        real fixture + seeded .rl store
docs/                        plan, schema, evidence, demo script
```

## Boundaries

- The public repository does **not** include private production source or model weights.
- The demo does not claim a live hosted 14B inference endpoint.
- The graph is a memory/provenance demo, not a new model checkpoint.
- Relate is Apache-2.0; see `NOTICE.md`.

## 中文摘要

小袁记忆图谱：把“小袁 14B”真实本地回归中的 10 个会话、31 轮对话、31 次后验检查、5 次修复和 5 个问题，建成一个可用 Cypher 查询的 Relate 图数据库。每个会话、轮次、场景、硬约束、检查、修复和问题都是节点；关系保留“哪一轮、哪个门、修了什么”的证据链。全部结果为本地自评，不是官方分数或名次。

## License

MIT for the original code and docs. See `LICENSE`.
