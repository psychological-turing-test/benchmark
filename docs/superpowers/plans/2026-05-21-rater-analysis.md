# Rater Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rater module and script that convert flat evaluator result
directories into `analysis.json` plus a static comparison HTML page.

**Architecture:** Add a dedicated `rationale_benchmark.rater` package. Keep
loading, scoring, output orchestration, and HTML rendering in focused modules,
with `bin/rate_results.py` as a thin wrapper. The rater consumes current
evaluator `*-results.json` files and supports `risky-choice-framing` plus
`decision-premise`.

**Tech Stack:** Python standard library, dataclasses, JSON, argparse, pytest,
HTML/CSS/vanilla JavaScript.

---

## File Structure

- Create `rationale_benchmark/rater/__init__.py`: public rater API exports.
- Create `rationale_benchmark/rater/models.py`: dataclasses, constants,
  display-name formatting, and `RaterError`.
- Create `rationale_benchmark/rater/loader.py`: flat-directory discovery and
  evaluator JSON validation.
- Create `rationale_benchmark/rater/scoring.py`: BAS/VAS/SRS calculations for
  `risky-choice-framing` and `decision-premise`.
- Create `rationale_benchmark/rater/analysis.py`: orchestration, top-level
  model averaging, and `analysis.json` writing.
- Create `rationale_benchmark/rater/visualization.py`: static HTML writer.
- Create `bin/rate_results.py`: command-line script wrapper.
- Create `tests/rater/test_models.py`: display-name and model utility tests.
- Create `tests/rater/test_loader.py`: file discovery and JSON validation
  tests.
- Create `tests/rater/test_scoring.py`: questionnaire scoring tests.
- Create `tests/rater/test_analysis.py`: end-to-end artifact writing tests.
- Create `docs/05-rater/design.md`: user-facing rater command and output
  contract.

Before implementation, create a feature branch or isolated worktree using the
project prefix, for example `feat/rater-analysis`. The current workspace has an
already staged `docs/05-rater/rating.md`; every commit command below stages
explicit paths so that file remains controlled by the user.

---

### Task 1: Add Public Models And Display Names

**Files:**
- Create: `rationale_benchmark/rater/__init__.py`
- Create: `rationale_benchmark/rater/models.py`
- Create: `tests/rater/test_models.py`

- [ ] **Step 1: Write failing display-name tests**

Create `tests/rater/test_models.py`:

```python
from __future__ import annotations

from rationale_benchmark.rater.models import format_model_display_name


def test_format_aliyun_no_thinking_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (0)")
    == "aliyun/qwen3.6-plus (no thinking)"
  )


def test_format_aliyun_max_thinking_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (-1)")
    == "aliyun/qwen3.6-plus (max thinking)"
  )


def test_format_aliyun_positive_thinking_budget_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (10)")
    == "aliyun/qwen3.6-plus (thinking budget 10)"
  )


def test_format_aliyun_without_suffix_is_unchanged() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus")
    == "aliyun/qwen3.6-plus"
  )


def test_format_non_aliyun_suffix_is_unchanged() -> None:
  assert (
    format_model_display_name("openai/gpt-4.1 (0)")
    == "openai/gpt-4.1 (0)"
  )
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named
'rationale_benchmark.rater'`.

- [ ] **Step 3: Add rater models and exports**

Create `rationale_benchmark/rater/models.py`:

```python
"""Shared rater data models and naming helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ANALYSIS_VERSION = 1
SUPPORTED_QUESTIONNAIRES = {"risky-choice-framing", "decision-premise"}


class RaterError(RuntimeError):
  """Raised when rater input or processing fails."""


@dataclass(frozen=True)
class EvaluatorQuestionResult:
  """One question entry loaded from an evaluator result file."""

  source_file: str
  questionnaire_id: str
  section_name: str
  question_id: str
  human: dict[str, float]
  llms: dict[str, dict[str, float]]


@dataclass(frozen=True)
class QuestionnaireRating:
  """BAS, VAS, SRS, and trace details for one questionnaire/model pair."""

  bas: float
  vas: float
  srs: float
  details: dict[str, Any]


@dataclass(frozen=True)
class RatingRunResult:
  """Paths and payload produced by rating an evaluator result directory."""

  input_dir: Path
  analysis_json: Path
  visualization_html: Path
  payload: dict[str, Any]


_ALIYUN_SUFFIX_RE = re.compile(r"^(?P<prefix>.+?)\s*\((?P<budget>-?\d+)\)$")


def format_model_display_name(llm_id: str) -> str:
  """Return a human-readable model label for visualization."""
  provider = llm_id.split("/", 1)[0]
  if provider != "aliyun" and not provider.endswith("_aliyun"):
    return llm_id

  match = _ALIYUN_SUFFIX_RE.match(llm_id)
  if match is None:
    return llm_id

  budget = int(match.group("budget"))
  prefix = match.group("prefix")
  if budget == 0:
    suffix = "no thinking"
  elif budget == -1:
    suffix = "max thinking"
  else:
    suffix = f"thinking budget {budget}"
  return f"{prefix} ({suffix})"
```

Create `rationale_benchmark/rater/__init__.py`:

```python
"""Rater APIs for evaluator result analysis."""

from .models import (
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
  RatingRunResult,
  format_model_display_name,
)

__all__ = [
  "EvaluatorQuestionResult",
  "QuestionnaireRating",
  "RaterError",
  "RatingRunResult",
  "format_model_display_name",
]
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```bash
uv run pytest tests/rater/test_models.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/models.py \
  tests/rater/test_models.py
git commit -m "feat: add rater model helpers" -- \
  rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/models.py \
  tests/rater/test_models.py
```

Expected: commit succeeds and does not include `docs/05-rater/rating.md`.

---

### Task 2: Load Flat Evaluator Result Directories

**Files:**
- Create: `rationale_benchmark/rater/loader.py`
- Modify: `rationale_benchmark/rater/__init__.py`
- Create: `tests/rater/test_loader.py`

- [ ] **Step 1: Write failing loader tests**

Create `tests/rater/test_loader.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rationale_benchmark.rater.loader import discover_result_files, load_results
from rationale_benchmark.rater.models import RaterError


def write_result(path: Path, questionnaire_id: str = "decision-premise") -> None:
  path.write_text(
    json.dumps(
      [
        {
          "questionnaire_id": questionnaire_id,
          "section_name": "Scenario-P-1",
          "question_id": "q1",
          "question_prompt": "Choose.",
          "human": {
            "population": 10,
            "responses": [
              {"option": "A", "count": 6, "percentage": 0.6},
              {"option": "B", "count": 4, "percentage": 0.4},
            ],
          },
          "llms": [
            {
              "llm_id": "aliyun/qwen3.6-plus (0)",
              "population": 10,
              "responses": [
                {"option": "A", "count": 3, "percentage": 0.3},
                {"option": "B", "count": 7, "percentage": 0.7},
              ],
            }
          ],
        }
      ]
    )
    + "\n",
    encoding="utf-8",
  )


def test_discover_result_files_uses_flat_directory_only(tmp_path: Path) -> None:
  direct = tmp_path / "decision-premise-thinking-results.json"
  nested = tmp_path / "nested"
  nested.mkdir()
  write_result(direct)
  write_result(nested / "risky-choice-framing-thinking-results.json")

  assert discover_result_files(tmp_path) == [direct]


def test_discover_result_files_fails_when_directory_missing(tmp_path: Path) -> None:
  with pytest.raises(RaterError, match="cannot be read"):
    discover_result_files(tmp_path / "missing")


def test_discover_result_files_fails_when_no_results(tmp_path: Path) -> None:
  with pytest.raises(RaterError, match="No direct \\*-results\\.json"):
    discover_result_files(tmp_path)


def test_load_results_validates_and_normalizes_question_entries(
  tmp_path: Path,
) -> None:
  path = tmp_path / "decision-premise-thinking-results.json"
  write_result(path)

  results = load_results(tmp_path)

  assert len(results) == 1
  assert results[0].source_file == path.name
  assert results[0].questionnaire_id == "decision-premise"
  assert results[0].human == {"A": 0.6, "B": 0.4}
  assert results[0].llms == {"aliyun/qwen3.6-plus (0)": {"A": 0.3, "B": 0.7}}


def test_load_results_rejects_malformed_json(tmp_path: Path) -> None:
  (tmp_path / "decision-premise-thinking-results.json").write_text(
    "{not-json",
    encoding="utf-8",
  )

  with pytest.raises(RaterError, match="Malformed JSON"):
    load_results(tmp_path)


def test_load_results_rejects_missing_human_distribution(tmp_path: Path) -> None:
  path = tmp_path / "decision-premise-thinking-results.json"
  write_result(path)
  payload = json.loads(path.read_text(encoding="utf-8"))
  payload[0]["human"] = None
  path.write_text(json.dumps(payload), encoding="utf-8")

  with pytest.raises(RaterError, match="missing human distribution"):
    load_results(tmp_path)
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError` or import errors for
`rationale_benchmark.rater.loader`.

- [ ] **Step 3: Implement loader discovery and validation**

Create `rationale_benchmark/rater/loader.py`:

```python
"""Load evaluator result JSON files for rater analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import EvaluatorQuestionResult, RaterError


def discover_result_files(input_dir: Path | str) -> list[Path]:
  """Return direct evaluator result JSON files under ``input_dir``."""
  directory = Path(input_dir)
  if not directory.is_dir():
    raise RaterError(f"Input directory '{directory}' cannot be read")

  files = sorted(path for path in directory.glob("*-results.json") if path.is_file())
  if not files:
    raise RaterError(f"No direct *-results.json files found in '{directory}'")
  return files


def load_results(input_dir: Path | str) -> list[EvaluatorQuestionResult]:
  """Load and validate all direct evaluator result JSON files."""
  results: list[EvaluatorQuestionResult] = []
  for path in discover_result_files(input_dir):
    payload = _load_json_array(path)
    for index, item in enumerate(payload, start=1):
      results.append(_parse_question_result(path.name, index, item))
  return results


def _load_json_array(path: Path) -> list[Any]:
  try:
    value = json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError as exc:
    raise RaterError(f"Malformed JSON in '{path.name}': {exc}") from exc
  except OSError as exc:
    raise RaterError(f"Result file '{path}' cannot be read") from exc

  if not isinstance(value, list):
    raise RaterError(f"Result file '{path.name}' must contain a JSON array")
  return value


def _parse_question_result(
  source_file: str,
  index: int,
  item: Any,
) -> EvaluatorQuestionResult:
  if not isinstance(item, dict):
    raise RaterError(f"{source_file} entry {index} must be an object")

  questionnaire_id = _required_str(item, "questionnaire_id", source_file, index)
  section_name = _required_str(item, "section_name", source_file, index)
  question_id = _required_str(item, "question_id", source_file, index)
  human = _parse_human_distribution(item.get("human"), source_file, index)
  llms = _parse_llm_distributions(item.get("llms"), source_file, index)

  return EvaluatorQuestionResult(
    source_file=source_file,
    questionnaire_id=questionnaire_id,
    section_name=section_name,
    question_id=question_id,
    human=human,
    llms=llms,
  )


def _required_str(
  item: dict[str, Any],
  key: str,
  source_file: str,
  index: int,
) -> str:
  value = item.get(key)
  if not isinstance(value, str) or not value:
    raise RaterError(f"{source_file} entry {index} is missing {key}")
  return value


def _parse_human_distribution(
  value: Any,
  source_file: str,
  index: int,
) -> dict[str, float]:
  if not isinstance(value, dict):
    raise RaterError(f"{source_file} entry {index} is missing human distribution")
  return _responses_to_distribution(value.get("responses"), source_file, index)


def _parse_llm_distributions(
  value: Any,
  source_file: str,
  index: int,
) -> dict[str, dict[str, float]]:
  if not isinstance(value, list) or not value:
    raise RaterError(f"{source_file} entry {index} is missing model responses")

  llms: dict[str, dict[str, float]] = {}
  for llm_index, llm in enumerate(value, start=1):
    if not isinstance(llm, dict):
      raise RaterError(f"{source_file} entry {index} has malformed model response")
    llm_id = llm.get("llm_id")
    if not isinstance(llm_id, str) or not llm_id:
      raise RaterError(
        f"{source_file} entry {index} model {llm_index} is missing llm_id"
      )
    llms[llm_id] = _responses_to_distribution(
      llm.get("responses"),
      source_file,
      index,
    )
  return llms


def _responses_to_distribution(
  responses: Any,
  source_file: str,
  index: int,
) -> dict[str, float]:
  if not isinstance(responses, list) or not responses:
    raise RaterError(f"{source_file} entry {index} is missing response distribution")

  distribution: dict[str, float] = {}
  for response in responses:
    if not isinstance(response, dict):
      raise RaterError(f"{source_file} entry {index} has malformed response")
    option = response.get("option")
    percentage = response.get("percentage")
    if not isinstance(option, str) or not isinstance(percentage, (int, float)):
      raise RaterError(f"{source_file} entry {index} has malformed response")
    distribution[option] = float(percentage)
  return distribution
```

Modify `rationale_benchmark/rater/__init__.py`:

```python
"""Rater APIs for evaluator result analysis."""

from .loader import discover_result_files, load_results
from .models import (
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
  RatingRunResult,
  format_model_display_name,
)

__all__ = [
  "EvaluatorQuestionResult",
  "QuestionnaireRating",
  "RaterError",
  "RatingRunResult",
  "discover_result_files",
  "format_model_display_name",
  "load_results",
]
```

- [ ] **Step 4: Run loader tests to verify they pass**

Run:

```bash
uv run pytest tests/rater/test_loader.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all current rater tests**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/loader.py \
  tests/rater/test_loader.py
git commit -m "feat: load rater evaluator results" -- \
  rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/loader.py \
  tests/rater/test_loader.py
```

Expected: commit succeeds and does not include unrelated staged files.

---

### Task 3: Implement Questionnaire Scoring

**Files:**
- Create: `rationale_benchmark/rater/scoring.py`
- Modify: `rationale_benchmark/rater/__init__.py`
- Create: `tests/rater/test_scoring.py`

- [ ] **Step 1: Write failing scoring tests**

Create `tests/rater/test_scoring.py`:

```python
from __future__ import annotations

import pytest

from rationale_benchmark.rater.models import EvaluatorQuestionResult, RaterError
from rationale_benchmark.rater.scoring import score_questionnaire


def result(
  *,
  questionnaire_id: str,
  section_name: str,
  question_id: str,
  human_b: float,
  llm_b: float,
  llm_id: str = "aliyun/qwen3.6-plus (0)",
) -> EvaluatorQuestionResult:
  return EvaluatorQuestionResult(
    source_file=f"{questionnaire_id}-results.json",
    questionnaire_id=questionnaire_id,
    section_name=section_name,
    question_id=question_id,
    human={"A": 1.0 - human_b, "B": human_b},
    llms={llm_id: {"A": 1.0 - llm_b, "B": llm_b}},
  )


def test_score_decision_premise() -> None:
  rating = score_questionnaire(
    "decision-premise",
    "aliyun/qwen3.6-plus (0)",
    [
      result(
        questionnaire_id="decision-premise",
        section_name="Scenario-P-1",
        question_id="q1",
        human_b=0.4,
        llm_b=0.7,
      ),
      result(
        questionnaire_id="decision-premise",
        section_name="Scenario-P-2",
        question_id="q2",
        human_b=0.8,
        llm_b=0.6,
      ),
    ],
  )

  assert rating.bas == pytest.approx(75.0)
  assert rating.vas == pytest.approx(74.504871)
  assert rating.srs == pytest.approx(74.752436)
  assert [item["label"] for item in rating.details["bas_items"]] == ["q1", "q2"]
  assert rating.details["vas"]["labels"] == ["q1", "q2"]


def test_score_risky_choice_framing() -> None:
  rating = score_questionnaire(
    "risky-choice-framing",
    "aliyun/qwen3.6-plus (0)",
    [
      result(
        questionnaire_id="risky-choice-framing",
        section_name="Group size-P-6life",
        question_id="1-P-6life",
        human_b=0.4,
        llm_b=0.5,
      ),
      result(
        questionnaire_id="risky-choice-framing",
        section_name="Group size-N-6life",
        question_id="2-N-6life",
        human_b=0.7,
        llm_b=0.6,
      ),
    ],
  )

  assert rating.bas == pytest.approx(90.0)
  assert rating.vas == pytest.approx(80.0)
  assert rating.srs == pytest.approx(85.0)
  assert rating.details["bas_items"][0]["label"] == "6life"
  assert rating.details["vas"]["labels"] == ["6life"]


def test_score_rejects_unsupported_questionnaire() -> None:
  with pytest.raises(RaterError, match="Unsupported questionnaire"):
    score_questionnaire("decision-mode", "model", [])


def test_score_risky_choice_rejects_unmatched_frame_pair() -> None:
  with pytest.raises(RaterError, match="unmatched positive or negative"):
    score_questionnaire(
      "risky-choice-framing",
      "aliyun/qwen3.6-plus (0)",
      [
        result(
          questionnaire_id="risky-choice-framing",
          section_name="Group size-P-6life",
          question_id="1-P-6life",
          human_b=0.4,
          llm_b=0.5,
        )
      ],
    )
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_scoring.py -v
```

Expected: FAIL with import errors for `rationale_benchmark.rater.scoring`.

- [ ] **Step 3: Implement scoring functions**

Create `rationale_benchmark/rater/scoring.py`:

```python
"""BAS, VAS, and SRS scoring for evaluator result data."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

from .models import (
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
  SUPPORTED_QUESTIONNAIRES,
)

RISK_OPTION = "B"
CONSERVATIVE_OPTION = "A"
_FRAME_RE = re.compile(r"-(?P<frame>[PN])-(?P<key>.+)$")


def score_questionnaire(
  questionnaire_id: str,
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  """Score one questionnaire for one LLM."""
  if questionnaire_id not in SUPPORTED_QUESTIONNAIRES:
    raise RaterError(f"Unsupported questionnaire '{questionnaire_id}'")
  if questionnaire_id == "risky-choice-framing":
    return _score_risky_choice_framing(llm_id, results)
  return _score_decision_premise(llm_id, results)


def _score_decision_premise(
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  bas_items = []
  labels = []
  human_trajectory = []
  llm_trajectory = []

  for item in sorted(results, key=lambda result: result.question_id):
    human_risk = _option_percentage(item.human, RISK_OPTION, item.question_id)
    human_conservative = _option_percentage(
      item.human,
      CONSERVATIVE_OPTION,
      item.question_id,
    )
    llm_distribution = _llm_distribution(item, llm_id)
    llm_risk = _option_percentage(llm_distribution, RISK_OPTION, item.question_id)
    llm_conservative = _option_percentage(
      llm_distribution,
      CONSERVATIVE_OPTION,
      item.question_id,
    )
    distance = _euclidean(
      [llm_risk, llm_conservative],
      [human_risk, human_conservative],
    )
    contribution = _clamp_score(100 * (1 - distance / math.sqrt(2)))
    bas_items.append(
      {
        "label": item.question_id,
        "human": {"risk": human_risk, "conservative": human_conservative},
        "llm": {"risk": llm_risk, "conservative": llm_conservative},
        "distance": distance,
        "bas": contribution,
      }
    )
    labels.append(item.question_id)
    human_trajectory.append(human_risk)
    llm_trajectory.append(llm_risk)

  if not bas_items:
    raise RaterError("No decision-premise scenarios available to rate")
  vas_detail = _trajectory_vas(labels, human_trajectory, llm_trajectory)
  bas = sum(item["bas"] for item in bas_items) / len(bas_items)
  return _rating(bas=bas, vas_detail=vas_detail, bas_items=bas_items)


def _score_risky_choice_framing(
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  pairs: dict[str, dict[str, EvaluatorQuestionResult]] = defaultdict(dict)
  for item in results:
    frame, key = _frame_and_key(item)
    pairs[key][frame] = item

  incomplete = sorted(key for key, pair in pairs.items() if set(pair) != {"P", "N"})
  if incomplete:
    joined = ", ".join(incomplete)
    raise RaterError(
      "Risky-choice framing result has unmatched positive or negative "
      f"frame pairs: {joined}"
    )

  bas_items = []
  labels = []
  human_trajectory = []
  llm_trajectory = []
  for key in sorted(pairs):
    positive = pairs[key]["P"]
    negative = pairs[key]["N"]
    human_positive = _option_percentage(positive.human, RISK_OPTION, key)
    human_negative = _option_percentage(negative.human, RISK_OPTION, key)
    llm_positive = _option_percentage(
      _llm_distribution(positive, llm_id),
      RISK_OPTION,
      key,
    )
    llm_negative = _option_percentage(
      _llm_distribution(negative, llm_id),
      RISK_OPTION,
      key,
    )
    distance = _euclidean(
      [llm_positive, llm_negative],
      [human_positive, human_negative],
    )
    contribution = _clamp_score(100 * (1 - distance / math.sqrt(2)))
    human_rd = human_negative - human_positive
    llm_rd = llm_negative - llm_positive
    bas_items.append(
      {
        "label": key,
        "human": {"positive_risk": human_positive, "negative_risk": human_negative},
        "llm": {"positive_risk": llm_positive, "negative_risk": llm_negative},
        "distance": distance,
        "bas": contribution,
      }
    )
    labels.append(key)
    human_trajectory.append(human_rd)
    llm_trajectory.append(llm_rd)

  if not bas_items:
    raise RaterError("No risky-choice framing pairs available to rate")
  vas_detail = _trajectory_vas(labels, human_trajectory, llm_trajectory)
  bas = sum(item["bas"] for item in bas_items) / len(bas_items)
  return _rating(bas=bas, vas_detail=vas_detail, bas_items=bas_items)


def _frame_and_key(item: EvaluatorQuestionResult) -> tuple[str, str]:
  for value in (item.question_id, item.section_name):
    match = _FRAME_RE.search(value)
    if match is not None:
      return match.group("frame"), match.group("key")
  raise RaterError(
    "Risky-choice framing result cannot identify P/N frame from "
    f"question '{item.question_id}'"
  )


def _llm_distribution(
  item: EvaluatorQuestionResult,
  llm_id: str,
) -> dict[str, float]:
  distribution = item.llms.get(llm_id)
  if distribution is None:
    raise RaterError(
      f"Question '{item.question_id}' is missing model response distribution "
      f"for '{llm_id}'"
    )
  return distribution


def _option_percentage(
  distribution: dict[str, float],
  option: str,
  label: str,
) -> float:
  if option not in distribution:
    raise RaterError(f"Distribution for '{label}' is missing option '{option}'")
  return distribution[option]


def _trajectory_vas(
  labels: list[str],
  human: list[float],
  llm: list[float],
) -> dict[str, Any]:
  distance = _euclidean(llm, human)
  max_distance = math.sqrt(len(labels))
  vas = _clamp_score(100 * (1 - distance / max_distance))
  return {
    "labels": labels,
    "human": human,
    "llm": llm,
    "distance": distance,
    "max_distance": max_distance,
    "vas": vas,
  }


def _rating(
  *,
  bas: float,
  vas_detail: dict[str, Any],
  bas_items: list[dict[str, Any]],
) -> QuestionnaireRating:
  clamped_bas = _clamp_score(bas)
  clamped_vas = _clamp_score(vas_detail["vas"])
  return QuestionnaireRating(
    bas=clamped_bas,
    vas=clamped_vas,
    srs=(clamped_bas + clamped_vas) / 2,
    details={"bas_items": bas_items, "vas": vas_detail},
  )


def _euclidean(left: list[float], right: list[float]) -> float:
  return math.sqrt(
    sum(
      (left_value - right_value) ** 2
      for left_value, right_value in zip(left, right)
    )
  )


def _clamp_score(value: float) -> float:
  return max(0.0, min(100.0, value))
```

Modify `rationale_benchmark/rater/__init__.py`:

```python
"""Rater APIs for evaluator result analysis."""

from .loader import discover_result_files, load_results
from .models import (
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
  RatingRunResult,
  format_model_display_name,
)
from .scoring import score_questionnaire

__all__ = [
  "EvaluatorQuestionResult",
  "QuestionnaireRating",
  "RaterError",
  "RatingRunResult",
  "discover_result_files",
  "format_model_display_name",
  "load_results",
  "score_questionnaire",
]
```

- [ ] **Step 4: Run scoring tests to verify they pass**

Run:

```bash
uv run pytest tests/rater/test_scoring.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all current rater tests**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/scoring.py \
  tests/rater/test_scoring.py
git commit -m "feat: score rater questionnaires" -- \
  rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/scoring.py \
  tests/rater/test_scoring.py
```

Expected: commit succeeds.

---

### Task 4: Orchestrate Analysis JSON Output

**Files:**
- Create: `rationale_benchmark/rater/analysis.py`
- Modify: `rationale_benchmark/rater/__init__.py`
- Create: `tests/rater/test_analysis.py`

- [ ] **Step 1: Write failing analysis-output test**

Create `tests/rater/test_analysis.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rationale_benchmark.rater.analysis import rate_results
from rationale_benchmark.rater.models import RaterError


def question(
  questionnaire_id: str,
  question_id: str,
  human_b: float,
  llm_b: float,
  *,
  section_name: str | None = None,
) -> dict:
  return {
    "questionnaire_id": questionnaire_id,
    "section_name": section_name or question_id,
    "question_id": question_id,
    "question_prompt": "Choose.",
    "human": {
      "population": 10,
      "responses": [
        {"option": "A", "count": 0, "percentage": 1.0 - human_b},
        {"option": "B", "count": 0, "percentage": human_b},
      ],
    },
    "llms": [
      {
        "llm_id": "aliyun/qwen3.6-plus (0)",
        "population": 10,
        "responses": [
          {"option": "A", "count": 0, "percentage": 1.0 - llm_b},
          {"option": "B", "count": 0, "percentage": llm_b},
        ],
      }
    ],
  }


def write_json(path: Path, payload: list[dict]) -> None:
  path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_rate_results_writes_analysis_json(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-premise-thinking-results.json",
    [
      question("decision-premise", "q1", 0.4, 0.7),
      question("decision-premise", "q2", 0.8, 0.6),
    ],
  )

  result = rate_results(tmp_path)
  payload = json.loads(result.analysis_json.read_text(encoding="utf-8"))

  assert result.analysis_json == tmp_path / "analysis.json"
  assert payload["version"] == 1
  assert payload["source_files"] == ["decision-premise-thinking-results.json"]
  assert payload["models"][0]["llm_id"] == "aliyun/qwen3.6-plus (0)"
  assert payload["models"][0]["display_name"] == (
    "aliyun/qwen3.6-plus (no thinking)"
  )
  assert payload["models"][0]["bas"] == pytest.approx(75.0)
  assert payload["models"][0]["vas"] == pytest.approx(74.504871)
  assert payload["models"][0]["srs"] == pytest.approx(74.752436)
  assert "decision-premise" in payload["models"][0]["questionnaires"]


def test_rate_results_rejects_unsupported_questionnaire(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-mode-thinking-results.json",
    [question("decision-mode", "q1", 0.4, 0.7)],
  )

  with pytest.raises(RaterError, match="Unsupported questionnaire"):
    rate_results(tmp_path)
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_analysis.py -v
```

Expected: FAIL with import errors for `rationale_benchmark.rater.analysis`.

- [ ] **Step 3: Implement analysis orchestration**

Create `rationale_benchmark/rater/analysis.py`:

```python
"""Top-level rater analysis orchestration."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .loader import discover_result_files, load_results
from .models import (
  ANALYSIS_VERSION,
  EvaluatorQuestionResult,
  RaterError,
  RatingRunResult,
  format_model_display_name,
)
from .scoring import score_questionnaire


def rate_results(input_dir: Path | str) -> RatingRunResult:
  """Rate evaluator result files and write analysis artifacts."""
  directory = Path(input_dir)
  source_files = [path.name for path in discover_result_files(directory)]
  results = load_results(directory)
  payload = build_analysis_payload(source_files, results)

  analysis_json = directory / "analysis.json"
  visualization_html = directory / "analysis-visualize.html"
  analysis_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
  return RatingRunResult(
    input_dir=directory,
    analysis_json=analysis_json,
    visualization_html=visualization_html,
    payload=payload,
  )


def build_analysis_payload(
  source_files: list[str],
  results: list[EvaluatorQuestionResult],
) -> dict[str, Any]:
  """Build the deterministic JSON payload for ``analysis.json``."""
  grouped: dict[str, list[EvaluatorQuestionResult]] = defaultdict(list)
  for result in results:
    grouped[result.questionnaire_id].append(result)

  llm_ids = sorted(
    {
      llm_id
      for questionnaire_results in grouped.values()
      for result in questionnaire_results
      for llm_id in result.llms
    }
  )
  if not llm_ids:
    raise RaterError("No overlapping supported model/questionnaire data to rate")

  models = []
  for llm_id in llm_ids:
    questionnaires: dict[str, dict[str, Any]] = {}
    for questionnaire_id in sorted(grouped):
      questionnaire_results = [
        result for result in grouped[questionnaire_id] if llm_id in result.llms
      ]
      if not questionnaire_results:
        continue
      rating = score_questionnaire(questionnaire_id, llm_id, questionnaire_results)
      questionnaires[questionnaire_id] = asdict(rating)

    if not questionnaires:
      continue

    bas = _mean([rating["bas"] for rating in questionnaires.values()])
    vas = _mean([rating["vas"] for rating in questionnaires.values()])
    srs = _mean([rating["srs"] for rating in questionnaires.values()])
    models.append(
      {
        "llm_id": llm_id,
        "display_name": format_model_display_name(llm_id),
        "bas": bas,
        "vas": vas,
        "srs": srs,
        "questionnaires": questionnaires,
      }
    )

  if not models:
    raise RaterError("No overlapping supported model/questionnaire data to rate")

  return {
    "version": ANALYSIS_VERSION,
    "source_files": sorted(source_files),
    "models": models,
  }


def _mean(values: list[float]) -> float:
  return sum(values) / len(values)
```

Modify `rationale_benchmark/rater/__init__.py`:

```python
"""Rater APIs for evaluator result analysis."""

from .analysis import build_analysis_payload, rate_results
from .loader import discover_result_files, load_results
from .models import (
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
  RatingRunResult,
  format_model_display_name,
)
from .scoring import score_questionnaire

__all__ = [
  "EvaluatorQuestionResult",
  "QuestionnaireRating",
  "RaterError",
  "RatingRunResult",
  "build_analysis_payload",
  "discover_result_files",
  "format_model_display_name",
  "load_results",
  "rate_results",
  "score_questionnaire",
]
```

- [ ] **Step 4: Run analysis tests to verify they pass**

Run:

```bash
uv run pytest tests/rater/test_analysis.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all current rater tests**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/analysis.py \
  tests/rater/test_analysis.py
git commit -m "feat: write rater analysis json" -- \
  rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/analysis.py \
  tests/rater/test_analysis.py
```

Expected: commit succeeds.

---

### Task 5: Render Static Visualization HTML

**Files:**
- Create: `rationale_benchmark/rater/visualization.py`
- Modify: `rationale_benchmark/rater/analysis.py`
- Modify: `rationale_benchmark/rater/__init__.py`
- Modify: `tests/rater/test_analysis.py`

- [ ] **Step 1: Add failing visualization assertions**

Append this assertion block to `test_rate_results_writes_analysis_json` in
`tests/rater/test_analysis.py`:

```python
  html = result.visualization_html.read_text(encoding="utf-8")
  assert result.visualization_html == tmp_path / "analysis-visualize.html"
  assert "fetch(\"analysis.json\")" in html
  assert 'input.type = "checkbox"' in html
  assert "Overall ratings" in html
  assert "Individual scores" in html
  assert "Comparison table" in html
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_analysis.py::test_rate_results_writes_analysis_json -v
```

Expected: FAIL because `analysis-visualize.html` is not written.

- [ ] **Step 3: Implement the HTML renderer**

Create `rationale_benchmark/rater/visualization.py`:

```python
"""Static HTML visualization for rater analysis output."""

from __future__ import annotations

from pathlib import Path


def write_visualization_html(path: Path) -> None:
  """Write the dependency-free analysis visualization page."""
  path.write_text(_HTML, encoding="utf-8")


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rater Analysis</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      background: #f6f8fb;
      color: #1f2937;
    }
    body {
      margin: 0;
      padding: 24px;
    }
    main {
      max-width: 1200px;
      margin: 0 auto;
    }
    h1, h2 {
      margin: 0;
      letter-spacing: 0;
    }
    header, section {
      margin-bottom: 20px;
    }
    .selector {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px 16px;
      margin-top: 12px;
    }
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
    }
    .charts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
    }
    .panel {
      background: #ffffff;
      border: 1px solid #dbe3ef;
      border-radius: 8px;
      padding: 16px;
    }
    svg {
      width: 100%;
      min-height: 280px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
    }
    th, td {
      border-bottom: 1px solid #e5eaf2;
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      font-weight: 700;
      background: #eef3f9;
    }
    .empty {
      color: #667085;
      padding: 24px 0;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Rater Analysis</h1>
      <div id="model-selector" class="selector"></div>
    </header>
    <section class="charts">
      <div class="panel">
        <h2>Overall ratings</h2>
        <svg id="bar-chart" role="img" aria-label="Overall ratings bar chart"></svg>
      </div>
      <div class="panel">
        <h2>Individual scores</h2>
        <svg id="radar-chart" role="img" aria-label="Individual scores radar chart"></svg>
      </div>
    </section>
    <section class="panel">
      <h2>Comparison table</h2>
      <div id="comparison-table"></div>
    </section>
  </main>
  <script>
    const state = { data: null, selected: new Set() };
    const colors = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c"];

    fetch("analysis.json")
      .then((response) => response.json())
      .then((data) => {
        state.data = data;
        data.models.forEach((model) => state.selected.add(model.llm_id));
        render();
      })
      .catch((error) => {
        document.body.innerHTML = `<main><p class="empty">Unable to load analysis.json: ${error}</p></main>`;
      });

    function render() {
      renderSelector();
      const models = selectedModels();
      renderBarChart(models);
      renderRadarChart(models);
      renderTable(models);
    }

    function selectedModels() {
      return state.data.models.filter((model) => state.selected.has(model.llm_id));
    }

    function renderSelector() {
      const root = document.getElementById("model-selector");
      root.innerHTML = "";
      state.data.models.forEach((model) => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = state.selected.has(model.llm_id);
        input.addEventListener("change", () => {
          if (input.checked) {
            state.selected.add(model.llm_id);
          } else {
            state.selected.delete(model.llm_id);
          }
          render();
        });
        label.append(input, model.display_name);
        root.append(label);
      });
    }

    function renderBarChart(models) {
      const svg = document.getElementById("bar-chart");
      svg.innerHTML = "";
      if (models.length === 0) {
        svg.innerHTML = `<text x="10" y="32" class="empty">Select at least one model.</text>`;
        return;
      }
      const metrics = ["srs", "bas", "vas"];
      const width = 520;
      const rowHeight = 28;
      const height = 40 + models.length * metrics.length * rowHeight;
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      let y = 28;
      models.forEach((model, modelIndex) => {
        metrics.forEach((metric) => {
          const value = model[metric];
          const barWidth = Math.max(1, value * 3.2);
          svg.insertAdjacentHTML("beforeend", `
            <text x="0" y="${y + 12}" font-size="11">${model.display_name} ${metric.toUpperCase()}</text>
            <rect x="180" y="${y}" width="${barWidth}" height="16" fill="${colors[modelIndex % colors.length]}"></rect>
            <text x="${185 + barWidth}" y="${y + 12}" font-size="11">${value.toFixed(2)}</text>
          `);
          y += rowHeight;
        });
      });
    }

    function renderRadarChart(models) {
      const svg = document.getElementById("radar-chart");
      svg.innerHTML = "";
      if (models.length === 0) {
        svg.innerHTML = `<text x="10" y="32" class="empty">Select at least one model.</text>`;
        return;
      }
      const axes = Array.from(new Set(models.flatMap((model) =>
        Object.keys(model.questionnaires).flatMap((name) => [`${name} BAS`, `${name} VAS`])
      )));
      const center = 160;
      const radius = 110;
      svg.setAttribute("viewBox", "0 0 340 320");
      axes.forEach((axis, index) => {
        const angle = (Math.PI * 2 * index / axes.length) - Math.PI / 2;
        const x = center + Math.cos(angle) * radius;
        const y = center + Math.sin(angle) * radius;
        svg.insertAdjacentHTML("beforeend", `
          <line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="#d0d7e2"></line>
          <text x="${x}" y="${y}" font-size="10">${axis}</text>
        `);
      });
      models.forEach((model, modelIndex) => {
        const points = axes.map((axis, index) => {
          const [name, metric] = axis.split(" ");
          const value = model.questionnaires[name][metric.toLowerCase()];
          const angle = (Math.PI * 2 * index / axes.length) - Math.PI / 2;
          const scaled = radius * value / 100;
          return `${center + Math.cos(angle) * scaled},${center + Math.sin(angle) * scaled}`;
        }).join(" ");
        svg.insertAdjacentHTML("beforeend", `
          <polygon points="${points}" fill="${colors[modelIndex % colors.length]}33" stroke="${colors[modelIndex % colors.length]}" stroke-width="2"></polygon>
        `);
      });
    }

    function renderTable(models) {
      const root = document.getElementById("comparison-table");
      if (models.length === 0) {
        root.innerHTML = `<p class="empty">Select at least one model.</p>`;
        return;
      }
      const rows = models.map((model) => `
        <tr>
          <td>${model.display_name}<br><small>${model.llm_id}</small></td>
          <td>${model.srs.toFixed(2)}</td>
          <td>${model.bas.toFixed(2)}</td>
          <td>${model.vas.toFixed(2)}</td>
          <td>${Object.entries(model.questionnaires).map(([name, rating]) =>
            `${name}: SRS ${rating.srs.toFixed(2)}, BAS ${rating.bas.toFixed(2)}, VAS ${rating.vas.toFixed(2)}`
          ).join("<br>")}</td>
        </tr>
      `).join("");
      root.innerHTML = `
        <table>
          <thead><tr><th>Model</th><th>SRS</th><th>BAS</th><th>VAS</th><th>Questionnaires</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }
  </script>
</body>
</html>
"""
```

Modify `rationale_benchmark/rater/analysis.py` to import and call the writer:

```python
from .visualization import write_visualization_html
```

After writing `analysis_json`, add:

```python
  write_visualization_html(visualization_html)
```

Modify `rationale_benchmark/rater/__init__.py` to export the writer:

```python
from .visualization import write_visualization_html
```

and add `"write_visualization_html"` to `__all__`.

- [ ] **Step 4: Run analysis tests to verify they pass**

Run:

```bash
uv run pytest tests/rater/test_analysis.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all rater tests**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 5**

Run:

```bash
git add rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/analysis.py \
  rationale_benchmark/rater/visualization.py \
  tests/rater/test_analysis.py
git commit -m "feat: render rater visualization" -- \
  rationale_benchmark/rater/__init__.py \
  rationale_benchmark/rater/analysis.py \
  rationale_benchmark/rater/visualization.py \
  tests/rater/test_analysis.py
```

Expected: commit succeeds.

---

### Task 6: Add Script Wrapper And Documentation

**Files:**
- Create: `bin/rate_results.py`
- Create: `docs/05-rater/design.md`
- Modify: `tests/rater/test_analysis.py`

- [ ] **Step 1: Add a script invocation test**

Append this test to `tests/rater/test_analysis.py`:

```python
def test_rate_results_script_reports_outputs(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-premise-thinking-results.json",
    [
      question("decision-premise", "q1", 0.4, 0.7),
      question("decision-premise", "q2", 0.8, 0.6),
    ],
  )

  import subprocess

  completed = subprocess.run(
    ["uv", "run", "python", "bin/rate_results.py", str(tmp_path)],
    check=False,
    text=True,
    capture_output=True,
  )

  assert completed.returncode == 0
  assert f"Wrote {tmp_path / 'analysis.json'}" in completed.stdout
  assert f"Wrote {tmp_path / 'analysis-visualize.html'}" in completed.stdout
```

- [ ] **Step 2: Run the script test to verify it fails**

Run:

```bash
uv run pytest tests/rater/test_analysis.py::test_rate_results_script_reports_outputs -v
```

Expected: FAIL because `bin/rate_results.py` does not exist.

- [ ] **Step 3: Add the script wrapper**

Create `bin/rate_results.py`:

```python
#!/usr/bin/env python
"""Rate evaluator result JSON files in one flat directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rationale_benchmark.rater import RaterError, rate_results


def main() -> int:
  """Rate evaluator results and report artifact paths."""
  parser = argparse.ArgumentParser(
    description="Rate evaluator result JSON files in one flat directory.",
  )
  parser.add_argument("input_dir", help="Directory containing *-results.json files")
  args = parser.parse_args()

  try:
    result = rate_results(Path(args.input_dir))
  except RaterError as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1

  print(f"Wrote {result.analysis_json}")
  print(f"Wrote {result.visualization_html}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
```

- [ ] **Step 4: Add rater usage documentation**

Create `docs/05-rater/design.md`:

```markdown
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
```

- [ ] **Step 5: Run the script test to verify it passes**

Run:

```bash
uv run pytest tests/rater/test_analysis.py::test_rate_results_script_reports_outputs -v
```

Expected: PASS.

- [ ] **Step 6: Run all rater tests**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 6**

Run:

```bash
git add bin/rate_results.py docs/05-rater/design.md tests/rater/test_analysis.py
git commit -m "feat: add rater script" -- \
  bin/rate_results.py \
  docs/05-rater/design.md \
  tests/rater/test_analysis.py
```

Expected: commit succeeds.

---

### Task 7: Verify Against Existing Sample Results

**Files:**
- No source changes expected.
- Generated files under `results/` are ignored by git.

- [ ] **Step 1: Prepare a flat temporary analysis directory**

Run:

```bash
mkdir -p /tmp/rater-analysis-sample
cp results/risky-choice-framing-thinking-2026-05-08T11-15-30-637484Z/risky-choice-framing-thinking-results.json \
  /tmp/rater-analysis-sample/
```

Expected: `/tmp/rater-analysis-sample/risky-choice-framing-thinking-results.json`
exists.

- [ ] **Step 2: Run the rater script on the sample**

Run:

```bash
uv run python bin/rate_results.py /tmp/rater-analysis-sample
```

Expected:

```text
Wrote /tmp/rater-analysis-sample/analysis.json
Wrote /tmp/rater-analysis-sample/analysis-visualize.html
```

- [ ] **Step 3: Inspect generated JSON shape**

Run:

```bash
python -m json.tool /tmp/rater-analysis-sample/analysis.json >/tmp/rater-analysis-sample/analysis.pretty.json
rg '"display_name"|"risky-choice-framing"|"srs"' /tmp/rater-analysis-sample/analysis.pretty.json
```

Expected: output includes display names, `risky-choice-framing`, and `srs`
fields.

- [ ] **Step 4: Run targeted test suite**

Run:

```bash
uv run pytest tests/rater/ -v
```

Expected: PASS.

- [ ] **Step 5: Run evaluator tests for regression coverage**

Run:

```bash
uv run pytest tests/evaluator/test_basic.py -v
```

Expected: PASS.

- [ ] **Step 6: Run full test suite**

Run:

```bash
uv run pytest
```

Expected: PASS.

- [ ] **Step 7: Confirm working tree state**

Run:

```bash
git status --short
```

Expected: only intentional user-owned changes remain, such as
`docs/05-rater/rating.md` if the user has not committed it separately. No
generated `/tmp` files appear in git status.
