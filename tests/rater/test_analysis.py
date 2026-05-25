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


def question_with_llms(
  questionnaire_id: str,
  question_id: str,
  llm_ids: list[str],
) -> dict:
  payload = question(questionnaire_id, question_id, 0.4, 0.7)
  payload["llms"] = [
    {**payload["llms"][0], "llm_id": llm_id} for llm_id in llm_ids
  ]
  return payload


def write_json(path: Path, payload: list[dict]) -> None:
  path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


CANONICAL_DECISION_PREMISE_RATES = [
  ("Pf-6life", 0.2, 0.4),
  ("Pf-600life", 0.4, 0.6),
  ("Py-old", 0.775, 0.5),
  ("Py-young", 0.761904761905, 0.2),
  ("Pm-old", 0.966666666667, 0.9),
  ("Pm-young", 0.527777777778, 0.4),
  ("Pu-6kin", 0.55, 0.6),
  ("Pu-6life", 0.25, 0.3),
  ("Pu-600life", 0.1, 0.1),
  ("Pe-6kin", 0.677419354839, 0.8),
  ("Pe-6life", 0.40625, 0.5),
  ("Pe-600life", 0.294117647059, 0.2),
  ("P-6kin", 0.7, 0.7),
  ("P-6life", 0.64, 0.4),
  ("P-600life", 0.4, 0.25),
]


def canonical_decision_premise_questions() -> list[dict]:
  return [
    question(
      "decision-premise",
      f"{index}-{key}",
      human_b,
      llm_b,
      section_name=f"Scenario {key}",
    )
    for index, (key, human_b, llm_b) in enumerate(
      CANONICAL_DECISION_PREMISE_RATES,
      start=1,
    )
  ]


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
  assert payload["version"] == 2
  assert payload["source_files"] == ["decision-premise-thinking-results.json"]
  assert payload["models"][0]["llm_id"] == "aliyun/qwen3.6-plus (0)"
  assert payload["models"][0]["display_name"] == (
    "aliyun/qwen3.6-plus (no thinking)"
  )
  assert payload["models"][0]["bas"] == pytest.approx(75.0)
  assert payload["models"][0]["vas"] == pytest.approx(74.504871)
  assert payload["models"][0]["srs"] == pytest.approx(74.752436)
  assert "decision-premise" in payload["models"][0]["questionnaires"]
  details = payload["models"][0]["questionnaires"]["decision-premise"]["details"]
  assert "behavioral_tendency_metrics" not in details
  html = result.visualization_html.read_text(encoding="utf-8")
  assert result.visualization_html == tmp_path / "analysis-visualize.html"
  assert "window.__RATER_ANALYSIS__" in html
  assert "fetch(\"analysis.json\")" not in html
  assert '"display_name": "aliyun/qwen3.6-plus (no thinking)"' in html
  assert "modelsByDisplayName()" in html
  assert "localeCompare(right.display_name)" in html
  assert 'selectorButton("Select all"' in html
  assert 'selectorButton("Deselect all"' in html
  assert 'input.type = "checkbox"' in html
  assert "model.questionnaires[name]?.[metric] ?? 0" in html
  assert "grid-template-columns: minmax(0, 2fr) minmax(280px, 0.9fr)" in html
  assert 'const metrics = ["srs"];' in html
  assert "const width = 760;" in html
  assert "const barStart = 360;" in html
  assert "<th>Raw LLM ID</th>" not in html
  assert '<th class="srs-column">SRS</th>' in html
  assert "formatRatingCell(model.srs, tableExtrema.srs, true)" in html
  assert "Overall ratings" in html
  assert "Individual scores" in html
  assert "Comparison table" in html


def test_rate_results_writes_decision_premise_metrics(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-premise-thinking-results.json",
    canonical_decision_premise_questions(),
  )

  payload = rate_results(tmp_path).payload

  details = payload["models"][0]["questionnaires"]["decision-premise"]["details"]
  metrics = details["behavioral_tendency_metrics"]
  assert metrics["profile"]["human"]["frp"] == pytest.approx(0.3)
  assert metrics["profile"]["llm"]["frp"] == pytest.approx(0.5)
  assert metrics["profile"]["delta"]["frp"] == pytest.approx(0.2)
  assert metrics["profile"]["human"]["sam"] == pytest.approx(0.425793650794)
  assert metrics["profile"]["llm"]["sbs"] == pytest.approx(0.116666666667)


def test_rate_results_rejects_unsupported_questionnaire(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-mode-thinking-results.json",
    [question("decision-mode", "q1", 0.4, 0.7)],
  )

  with pytest.raises(RaterError, match="Unsupported questionnaire"):
    rate_results(tmp_path)


def test_rate_results_rejects_partial_model_coverage_within_questionnaire(
  tmp_path: Path,
) -> None:
  write_json(
    tmp_path / "decision-premise-thinking-results.json",
    [
      question_with_llms("decision-premise", "q1", ["model-a", "model-b"]),
      question_with_llms("decision-premise", "q2", ["model-a"]),
    ],
  )

  with pytest.raises(RaterError, match="missing model distribution"):
    rate_results(tmp_path)


def test_rate_results_allows_separate_model_cohort_files(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-premise-a-results.json",
    [
      question_with_llms("decision-premise", "q1", ["model-a"]),
      question_with_llms("decision-premise", "q2", ["model-a"]),
    ],
  )
  write_json(
    tmp_path / "decision-premise-b-results.json",
    [
      question_with_llms("decision-premise", "q1", ["model-b"]),
      question_with_llms("decision-premise", "q2", ["model-b"]),
    ],
  )

  payload = rate_results(tmp_path).payload

  assert [model["llm_id"] for model in payload["models"]] == ["model-a", "model-b"]


def test_rate_results_averages_repeated_model_runs(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-premise-a-results.json",
    [
      question("decision-premise", "q1", 0.4, 0.2),
      question("decision-premise", "q2", 0.8, 0.6),
    ],
  )
  write_json(
    tmp_path / "decision-premise-b-results.json",
    [
      question("decision-premise", "q1", 0.4, 0.6),
      question("decision-premise", "q2", 0.8, 1.0),
    ],
  )

  payload = rate_results(tmp_path).payload

  assert len(payload["models"]) == 1
  model = payload["models"][0]
  assert model["llm_id"] == "aliyun/qwen3.6-plus (0)"
  assert model["bas"] == pytest.approx(100.0)
  assert model["vas"] == pytest.approx(100.0)
  assert model["srs"] == pytest.approx(100.0)


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
