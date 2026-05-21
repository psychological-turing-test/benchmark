"""Load evaluator result JSON files for rater analysis."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import EvaluatorQuestionResult, RaterError


def discover_result_files(input_dir: Path | str) -> list[Path]:
  """Return direct evaluator result JSON files under ``input_dir``."""
  directory = Path(input_dir)
  if not directory.is_dir() or not os.access(directory, os.R_OK | os.X_OK):
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
