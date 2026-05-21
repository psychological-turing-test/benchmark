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


def test_discover_result_files_fails_when_directory_unreadable(
  tmp_path: Path,
) -> None:
  unreadable = tmp_path / "unreadable"
  unreadable.mkdir()
  unreadable.chmod(0)
  try:
    with pytest.raises(RaterError, match="cannot be read"):
      discover_result_files(unreadable)
  finally:
    unreadable.chmod(0o700)


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
