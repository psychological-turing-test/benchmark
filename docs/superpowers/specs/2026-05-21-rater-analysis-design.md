# Rater Analysis Design

## Goal

Add a dedicated rater module and script that consume evaluator result JSON files
from one flat directory and produce:

- `analysis.json`: machine-readable BAS, FAS, and PAS ratings for each LLM.
- `analysis-visualize.html`: a static comparison page that loads
  `analysis.json` from the same directory.

The first version supports `risky-choice-framing` and `decision-premise`.
`DecisionMode` is intentionally out of scope until the repository has matching
questionnaire configuration and evaluator result fixtures.

## Assumptions

- The input path is a directory containing evaluator result JSON files directly
  inside it, such as `risky-choice-framing-thinking-results.json`.
- The rater does not scan recursively.
- Evaluator result files use the current per-question JSON shape produced by
  `rationale_benchmark.evaluator.basic`.
- For the supported questionnaires, option `B` is the risk-seeking choice and
  option `A` is the conservative choice.
- Human distributions in evaluator result files are the human reference for
  scoring.
- Top-level model ratings are simple averages across supported questionnaires
  present for that model.

## Architecture

Add `rationale_benchmark/rater/` as a new package with focused modules for:

- Loading and validating evaluator result JSON files.
- Computing questionnaire-level BAS, FAS, and PAS.
- Combining questionnaire-level scores into model-level scores.
- Rendering `analysis.json`.
- Rendering the static HTML visualization.

Add `bin/rate_results.py` as a thin script wrapper, following the existing
`bin/evaluate_basic.py` pattern. The script accepts one argument, the analysis
directory, and writes both output files into that same directory.

Keep the rater separate from the basic evaluator. The evaluator operates on one
runner output directory and emits per-question results. The rater operates on a
batch of evaluator result files and compares models across questionnaires.

## Data Flow

1. List `*-results.json` files directly under the input directory.
2. Load each file as a JSON array and validate required fields:
   `questionnaire_id`, `section_name`, `question_id`, `human`, and `llms`.
3. Group entries by questionnaire ID and LLM ID.
4. Reject unsupported questionnaire IDs with a clear rater error.
5. Compute questionnaire-level BAS, FAS, and PAS for each LLM.
6. Average each model's questionnaire-level BAS, FAS, and PAS into top-level
   metrics.
7. Write deterministic `analysis.json`.
8. Write `analysis-visualize.html`, which fetches `analysis.json` from the same
   directory.

## Model Display Names

Preserve raw model IDs in `analysis.json` as `llm_id`. Also include a
`display_name` for UI rendering.

For Aliyun model IDs only, rewrite a trailing integer suffix in parentheses:

- `(0)` becomes `(no thinking)`.
- `(-1)` becomes `(max thinking)`.
- `(X)` becomes `(thinking budget X)` for any other integer `X`.

If an Aliyun model ID has no trailing integer suffix, leave the display label
unchanged. Non-Aliyun model IDs are also left unchanged.

## Scoring

Clamp final normalized scores to the `0..100` range.

### Risky Choice Framing

Pair positive and negative frame entries by the suffix after `P-` or `N-`.
Examples include `6life`, `60life`, `1kin`, and `Human`.

For each pair, build a behavior vector:

```text
(P_risk, N_risk)
```

where each value is the proportion choosing option `B`.

BAS:

- Compute Euclidean distance between each LLM pair vector and its human pair
  vector.
- Normalize each distance by `sqrt(2)`.
- Convert to a `0..100` score with `100 * (1 - distance / sqrt(2))`.
- Average pair-level BAS values.

FAS:

- For each pair, compute `RD = N_risk - P_risk`.
- Build human and LLM RD trajectories across all pairs.
- Compute Euclidean distance between trajectories.
- Normalize by `sqrt(n)`, where `n` is the number of complete pairs.
- Convert to `0..100` with `100 * (1 - distance / sqrt(n))`.

### Decision Premise

Each question is treated as one scenario.

BAS:

- Build `(risk, conservative) = (B_percentage, A_percentage)` for human and
  LLM.
- Compute scenario-level Euclidean distance.
- Normalize by `sqrt(2)`.
- Convert to `0..100`.
- Average scenario-level BAS values.

FAS:

- Build human and LLM trajectories of `B_percentage` across all scenarios.
- Compute Euclidean distance between trajectories.
- Normalize by `sqrt(n)`, where `n` is the number of scenarios.
- Convert to `0..100`.

For both questionnaires, `PAS = (BAS + FAS) / 2`.

## Output Schema

`analysis.json` is a deterministic object:

```json
{
  "version": 1,
  "source_files": ["decision-premise-thinking-results.json"],
  "models": [
    {
      "llm_id": "aliyun/qwen3.6-plus (0)",
      "display_name": "aliyun/qwen3.6-plus (no thinking)",
      "bas": 72.1,
      "fas": 68.4,
      "pas": 70.25,
      "questionnaires": {
        "decision-premise": {
          "bas": 70.0,
          "fas": 66.0,
          "pas": 68.0,
          "details": {}
        }
      }
    }
  ]
}
```

`details` contains deterministic intermediate values for auditability:

- `bas_items`: ordered per-pair or per-scenario records with human proportions,
  LLM proportions, Euclidean distance, and BAS contribution.
- `fas`: trajectory labels, human trajectory, LLM trajectory, Euclidean
  distance, normalization maximum, and FAS contribution.

## Visualization

`analysis-visualize.html` is dependency-free and self-contained. It loads
`analysis.json` from the same directory using browser `fetch`.

The page contains:

- Top: checkbox-based multi-select for models, using `display_name`.
- Middle-left: bar chart for selected models' overall BAS, FAS, and PAS.
- Middle-right: radar chart for selected models' questionnaire-level BAS and
  FAS axes.
- Bottom: side-by-side comparison table with raw model ID, display name,
  overall metrics, and questionnaire breakdowns.

The page should degrade gracefully when no models are selected by showing empty
chart/table states rather than throwing JavaScript errors.

## Error Handling

Raise a specific rater error when:

- The input directory cannot be read.
- No direct `*-results.json` files exist.
- A result file contains malformed JSON.
- A result file does not contain the expected evaluator result shape.
- A questionnaire ID is unsupported.
- A required human distribution is missing.
- A required model response distribution is missing.
- A risky-choice framing result has unmatched positive or negative frame pairs.
- No overlapping supported model/questionnaire data remains to rate.

## Testing

Add `tests/rater/` with focused pytest coverage for:

- Flat-directory input discovery.
- Evaluator JSON parsing and validation.
- Aliyun display-name rewriting, including the no-suffix no-op case.
- Risky-choice framing BAS, FAS, and PAS.
- Decision-premise BAS, FAS, and PAS.
- Top-level averaging across questionnaires.
- Writing `analysis.json` and `analysis-visualize.html`.
- Unsupported questionnaire errors.
- Missing human/model distribution errors.

Run targeted tests with:

```bash
uv run pytest tests/rater/
```

Run the full suite before completion:

```bash
uv run pytest
```
