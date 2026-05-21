# Rater Module Design

## Purpose

The rater consumes evaluator result JSON files and produces model-level
psychological Turing-test ratings. It is separate from the basic evaluator:
the evaluator summarizes one runner output directory, while the rater compares
already-evaluated questionnaire results across models.

## Command

```bash
uv run python bin/rate_results.py results/analysis-batch
```

The input directory must contain evaluator `*-results.json` files directly
inside it. The rater does not scan recursively.

## Outputs

- `analysis.json`: BAS, VAS, and SRS for each LLM, plus questionnaire-level
  details.
- `analysis-visualize.html`: a static page that loads `analysis.json` from the
  same directory.

## Supported Questionnaires

The first version supports:

- `risky-choice-framing`
- `decision-premise`

Other questionnaire IDs fail with a clear unsupported-questionnaire error.

## Model Labels

Raw `llm_id` values remain unchanged in `analysis.json`. The rater also emits
`display_name` for visualization. Aliyun model IDs with trailing thinking
suffixes are rendered as:

- `(0)` -> `(no thinking)`
- `(-1)` -> `(max thinking)`
- `(X)` -> `(thinking budget X)`

Aliyun model IDs without a trailing integer suffix are not changed.
