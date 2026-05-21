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
  html = result.visualization_html.read_text(encoding="utf-8")
  assert result.visualization_html == tmp_path / "analysis-visualize.html"
  assert "fetch(\"analysis.json\")" in html
  assert 'input.type = "checkbox"' in html
  assert "model.questionnaires[name]?.[metric] ?? 0" in html
  assert "Overall ratings" in html
  assert "Individual scores" in html
  assert "Comparison table" in html


def test_rate_results_rejects_unsupported_questionnaire(tmp_path: Path) -> None:
  write_json(
    tmp_path / "decision-mode-thinking-results.json",
    [question("decision-mode", "q1", 0.4, 0.7)],
  )

  with pytest.raises(RaterError, match="Unsupported questionnaire"):
    rate_results(tmp_path)
