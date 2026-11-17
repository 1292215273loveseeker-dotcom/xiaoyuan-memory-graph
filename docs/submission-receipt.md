# Relate by Neo4j Hackathon 2026 — Submission Receipt

- Submitted: 2026-11-18 03:06 CST (UTC+8)
- Status: **SUBMITTED** (confirmed on the Devpost "My projects" page)
- Public project page: https://devpost.com/software/xiaoyuan-memory-graph
- Devpost submission ID: `1309805`
- Public GitHub repo: https://github.com/1292215273loveseeker-dotcom/xiaoyuan-memory-graph
- Demo video (1:20): https://youtu.be/NaN-DBnEqt8
- Relate mode: single file
- Persistent store: `data/xiaoyuan_memory.rl`
- GitHub topics: `relate`, `relate-neo4j-hackathon`

## Submitted fields

- Project name: **Xiaoyuan Memory Graph**
- Elevator pitch: An auditable memory graph for a local 14B agent: sessions, turns, checks, repairs and issues connected in Relate by Neo4j.
- Built with tags: python, neo4j, cypher, relate, graph, ai, ollama, qwen, memory, audit
- "Try it out": GitHub repo
- Image gallery: 4 frames from the captioned demo (title, schema, scenario stats, Q8-T1 trace)
- Demo video: embedded YouTube walkthrough

## Verified facts in the submission

- Real local regression transcript: 10 sessions / 31 turns / 31 post-checks / 5 repaired checks / 5 issue occurrences.
- Model: `qwen2.5:14b-instruct-q4_K_M` served by Ollama, local run dated 2026-11-17.
- 13 scenario nodes and 20 extracted constraint links.
- Tests: `python -m unittest discover -s tests -v` → 5/5 passing.
- Fresh `seed --reset`: `{'sessions': 10, 'turns': 31, 'checks': 31, 'issues': 5, 'repairs': 5, 'scenarios': 13, 'constraints': 20}`.
- Clean clone of the public repo passed the same test suite and fresh seed.

## Boundary

All results are local self-evaluation. This is not an official score, ranking, leaderboard entry, or third-party safety certification. The demo is a captioned screen walkthrough with no synthetic voice.
