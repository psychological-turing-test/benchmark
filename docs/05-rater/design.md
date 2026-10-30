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

- `analysis.json`: BAS, FAS, and PAS for each LLM, plus questionnaire-level
  details. For `risky-choice-framing`, details also include behavioral
  tendency metrics for both the LLM and the human baseline.
- `analysis-visualize.html`: a self-contained static page with the analysis
  JSON embedded inline, so it can be opened directly from the filesystem.

## Supported Questionnaires

The first version supports:

- `risky-choice-framing`
- `decision-premise`

Other questionnaire IDs fail with a clear unsupported-questionnaire error.

## Risky-Choice Behavioral Metrics

For `risky-choice-framing`, the rater emits
`details.behavioral_tendency_metrics` with parallel `llm` and `human`
profiles. Each profile includes FES, RC, MS for life-scale sensitivity, KG,
IGB, CDC, and RD, plus supporting MS/KG/IGB components and audit values.

## Model Labels

Raw `llm_id` values remain unchanged in `analysis.json`. The rater also emits
`display_name` for visualization. Aliyun model IDs with trailing thinking
suffixes are rendered as:

- `(0)` -> `(no thinking)`
- `(-1)` -> `(max thinking)`
- `(X)` -> `(thinking budget X)`

Aliyun model IDs without a trailing integer suffix are not changed.
