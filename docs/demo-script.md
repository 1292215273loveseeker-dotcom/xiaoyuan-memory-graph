# Demo Script (captioned walkthrough)

Target length: about 80 seconds. No synthetic voice. Captions and real terminal output.

| Time | Visual | Caption |
|---|---|---|
| 0:00–0:08 | Title card | **Xiaoyuan Memory Graph** — a memory that can be audited. |
| 0:08–0:18 | Problem card | A 14B agent can answer. But can it show **what it remembered, which gate fired, and what was repaired**? |
| 0:18–0:28 | Schema card | 10 sessions, 31 turns, 31 post-checks, 5 repairs, 5 issues. Every fact is a node in **Relate**. |
| 0:28–0:38 | Terminal: `seed --reset` | One command builds a single `.rl` graph from the real local regression transcript. |
| 0:38–0:50 | Terminal: `stats` | Scenario-level evidence: `memory` has 4 turns; `routing` has 3 turns and 2 repairs. |
| 0:50–1:00 | Terminal: `ask "what did the agent remember from Q1?"` | Recall is a graph query: session → turns → checks. No vector store guesswork. |
| 1:00–1:10 | Terminal: `ask "which gates repaired Q8?"` | The gate trace shows exactly which turns were repaired and the issue text. |
| 1:10–1:20 | Terminal: `trace Q8-T1` | Follow the edge: turn → check → issue, plus the hard constraint that framed the turn. |
| 1:20–1:30 | Closing card | **Local evidence, clearly labeled.** GitHub repo + one `.rl` file. |

## Capture notes

- Terminal screenshots should use a dark background and large monospace text.
- Do not claim an official score or a human narrator.
- If a human-narrated version is recorded later, replace this captioned version and update `NOTICE.md`.
