# Evidence and Boundaries

## Input provenance

- Source file: `ten_question_regression_full.json`
- Produced by the local Xiaoyuan 14B regression run on **2026-11-17 21:26:00**.
- Model: `qwen2.5:14b-instruct-q4_K_M`, served by Ollama at `http://127.0.0.1:11434`.
- The fixture contains 10 cases (`Q1`–`Q10`) and 31 turns.
- The fixture's fields include `post_valid`, `post_repaired`, `post_issues`, `total_s`, `eval_count`, and `tokens_per_s`.

## Graph counts (fresh seed)

| Item | Count |
|---|---|
| Sessions | 10 |
| Turns | 31 |
| Checks | 31 |
| Repaired checks | 5 |
| Issue occurrences | 5 |
| Scenario nodes | 13 |
| Constraint links | 20 |

## The five repaired turns

| Turn | Scenario | Issue |
|---|---|---|
| `Q7-T3` | `health` | 健康回答超过150字或缺羽佳学四步标签（93） |
| `Q8-T1` | `routing` | 路由缺少本地域/云端域/冲突点格式 |
| `Q8-T3` | `routing` | 路由缺少本地域/云端域/冲突点格式 |
| `Q9-T3` | `decision` | 双榜决策未选B或未说明留出集 |
| `Q10-T3` | `self_review` | 观自在自省缺段或未点明最可能错点 |

## What is measured

- The graph stores what the local transcript recorded: turn order, scenario, validity, repair flag, issue text, latency, token counts, and a bounded answer preview.
- Scenario statistics are computed from those stored fields. Average latency is the mean `total_s` of the turns in that scenario, including turns whose `total_s` is `0.0`.
- Constraints are extracted with a deterministic keyword splitter over the user text. It is a provenance aid, not a general natural-language understanding claim.

## What is not measured

- No official leaderboard score, ranking, medal, or third-party safety certification.
- No live model endpoint is hosted by this repository.
- No claim that Relate improves model quality; this project is a memory/provenance layer, not a new checkpoint.
- No claim of full answer fidelity: `answer_preview` is truncated to 240 characters.
- The 5 repairs are the architecture's own post-check outcomes, not human annotations.

## Reproduction

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
xiaoyuan-memory seed --reset
python -m unittest discover -s tests -v
```

Expected: 5 tests pass; seed reports the counts above. The seeded `data/xiaoyuan_memory.rl` store is included for a no-install inspection path.
