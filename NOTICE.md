# NOTICE

## Original work

This repository is a new, standalone project created for the Relate by Neo4j
Hackathon 2026. It is not a re-upload of the `xiaoyuan-14b-agent` repository.

## Third-party components

- **Relate by Neo4j** — Apache License 2.0. The Python client is installed as
  `relate-db`. See https://relatedb.ai and the Relate project license.
- **Qwen2.5 14B Instruct** — the local base model used to generate the
  transcript. Model weights are not included. Qwen2.5 is distributed under
  its own license; see the Qwen project for terms.
- **Ollama** — local model runner used for the regression run. Not bundled.

## Data

The transcript in `data/ten_question_regression_full.json` is a local
self-evaluation of Xiaoyuan 14B. It contains no private production source,
model weights, or personal data. Counts and latencies are local results, not
official scores or rankings.

## Demo media

The demo is a captioned screen walkthrough. It contains no synthetic voice and
does not claim to be a recording of a human speaker. Any future human-narrated
version must be recorded by the entrant.
