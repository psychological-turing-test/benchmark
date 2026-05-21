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
from .visualization import write_visualization_html


def rate_results(input_dir: Path | str) -> RatingRunResult:
  """Rate evaluator result files and write analysis artifacts."""
  directory = Path(input_dir)
  source_files = [path.name for path in discover_result_files(directory)]
  results = load_results(directory)
  payload = build_analysis_payload(source_files, results)

  analysis_json = directory / "analysis.json"
  visualization_html = directory / "analysis-visualize.html"
  analysis_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
  write_visualization_html(visualization_html)
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
