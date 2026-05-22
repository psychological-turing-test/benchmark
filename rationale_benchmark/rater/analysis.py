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
  write_visualization_html(visualization_html, payload)
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
      questionnaire_results = grouped[questionnaire_id]
      model_results = _model_questionnaire_results(questionnaire_results, llm_id)
      if not model_results:
        continue
      rating = score_questionnaire(questionnaire_id, llm_id, model_results)
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


def _model_questionnaire_results(
  results: list[EvaluatorQuestionResult],
  llm_id: str,
) -> list[EvaluatorQuestionResult]:
  selected: list[EvaluatorQuestionResult] = []
  by_source: dict[str, list[EvaluatorQuestionResult]] = defaultdict(list)
  for result in results:
    by_source[result.source_file].append(result)

  for source_results in by_source.values():
    has_model = [llm_id in result.llms for result in source_results]
    if not any(has_model):
      continue
    if not all(has_model):
      missing = next(
        result for result in source_results if llm_id not in result.llms
      )
      raise RaterError(
        f"Result {missing.question_id} is missing model distribution for {llm_id}"
      )
    selected.extend(source_results)

  return _collapse_repeated_results(selected, llm_id)


def _collapse_repeated_results(
  results: list[EvaluatorQuestionResult],
  llm_id: str,
) -> list[EvaluatorQuestionResult]:
  by_question: dict[str, list[EvaluatorQuestionResult]] = defaultdict(list)
  for result in results:
    by_question[result.question_id].append(result)

  collapsed = []
  for question_id in sorted(by_question):
    question_results = by_question[question_id]
    first = question_results[0]
    collapsed.append(
      EvaluatorQuestionResult(
        source_file=",".join(
          sorted({result.source_file for result in question_results})
        ),
        questionnaire_id=first.questionnaire_id,
        section_name=first.section_name,
        question_id=question_id,
        human=_mean_distributions([result.human for result in question_results]),
        llms={
          llm_id: _mean_distributions(
            [result.llms[llm_id] for result in question_results]
          )
        },
      )
    )
  return collapsed


def _mean_distributions(
  distributions: list[dict[str, float]],
) -> dict[str, float]:
  options = sorted(distributions[0])
  if any(sorted(distribution) != options for distribution in distributions):
    raise RaterError("Repeated result distributions have mismatched options")
  return {
    option: _mean([distribution[option] for distribution in distributions])
    for option in options
  }
