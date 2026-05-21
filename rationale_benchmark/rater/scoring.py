"""BAS, VAS, and SRS scoring for evaluator result data."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .models import (
  SUPPORTED_QUESTIONNAIRES,
  EvaluatorQuestionResult,
  QuestionnaireRating,
  RaterError,
)

RISK_OPTION = "B"
CONSERVATIVE_OPTION = "A"
_FRAME_RE = re.compile(r"-(?P<frame>[PN])-(?P<key>.+)$")


def score_questionnaire(
  questionnaire_id: str,
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  """Score one questionnaire/model pair with BAS, VAS, and SRS."""
  if questionnaire_id not in SUPPORTED_QUESTIONNAIRES:
    raise RaterError(f"Unsupported questionnaire: {questionnaire_id}")

  if questionnaire_id == "decision-premise":
    return _score_decision_premise(llm_id, results)
  if questionnaire_id == "risky-choice-framing":
    return _score_risky_choice_framing(llm_id, results)

  raise RaterError(f"Unsupported questionnaire: {questionnaire_id}")


def _score_decision_premise(
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  scenarios = sorted(results, key=lambda item: item.question_id)
  if not scenarios:
    raise RaterError("No scenarios to score")

  bas_items: list[dict[str, Any]] = []
  human_trajectory: list[float] = []
  llm_trajectory: list[float] = []

  for scenario in scenarios:
    human_risk, human_cons = _risk_and_conservative(scenario.human)
    llm_risk, llm_cons = _risk_and_conservative(_llm_distribution(scenario, llm_id))
    score = _similarity_score(
      [llm_risk, llm_cons],
      [human_risk, human_cons],
      math.sqrt(2),
    )
    bas_items.append(
      {
        "label": scenario.question_id,
        "score": score,
        "human": [human_risk, human_cons],
        "llm": [llm_risk, llm_cons],
      }
    )
    human_trajectory.append(human_risk)
    llm_trajectory.append(llm_risk)

  bas = _mean(item["score"] for item in bas_items)
  vas = _similarity_score(
    llm_trajectory,
    human_trajectory,
    math.sqrt(len(human_trajectory)),
  )
  return _rating(
    bas,
    vas,
    {
      "bas_items": bas_items,
      "vas": {
        "labels": [scenario.question_id for scenario in scenarios],
        "human": human_trajectory,
        "llm": llm_trajectory,
      },
    },
  )


def _score_risky_choice_framing(
  llm_id: str,
  results: list[EvaluatorQuestionResult],
) -> QuestionnaireRating:
  pairs = _frame_pairs(results)
  if not pairs:
    raise RaterError("No frame pairs to score")

  bas_items: list[dict[str, Any]] = []
  labels: list[str] = []
  human_trajectory: list[float] = []
  llm_trajectory: list[float] = []

  for key in sorted(pairs):
    pair = pairs[key]
    if set(pair) != {"P", "N"}:
      raise RaterError(f"Frame pair {key} has unmatched positive or negative frame")

    human_p = _risk(pair["P"].human)
    human_n = _risk(pair["N"].human)
    llm_p = _risk(_llm_distribution(pair["P"], llm_id))
    llm_n = _risk(_llm_distribution(pair["N"], llm_id))
    score = _similarity_score([llm_p, llm_n], [human_p, human_n], math.sqrt(2))
    bas_items.append(
      {
        "label": key,
        "score": score,
        "human": [human_p, human_n],
        "llm": [llm_p, llm_n],
      }
    )

    labels.append(key)
    human_trajectory.append(human_n - human_p)
    llm_trajectory.append(llm_n - llm_p)

  bas = _mean(item["score"] for item in bas_items)
  vas = _similarity_score(
    llm_trajectory,
    human_trajectory,
    math.sqrt(len(human_trajectory)),
  )
  return _rating(
    bas,
    vas,
    {
      "bas_items": bas_items,
      "vas": {
        "labels": labels,
        "human": human_trajectory,
        "llm": llm_trajectory,
      },
    },
  )


def _frame_pairs(
  results: list[EvaluatorQuestionResult],
) -> dict[str, dict[str, EvaluatorQuestionResult]]:
  pairs: dict[str, dict[str, EvaluatorQuestionResult]] = defaultdict(dict)
  for result in results:
    frame, key = _frame_and_key(result)
    pairs[key][frame] = result
  return dict(pairs)


def _frame_and_key(result: EvaluatorQuestionResult) -> tuple[str, str]:
  for value in (result.question_id, result.section_name):
    match = _FRAME_RE.search(value)
    if match is not None:
      return match.group("frame"), match.group("key")
  raise RaterError(
    f"Could not identify positive or negative frame for {result.question_id}"
  )


def _llm_distribution(
  result: EvaluatorQuestionResult,
  llm_id: str,
) -> dict[str, float]:
  if llm_id not in result.llms:
    raise RaterError(
      f"Result {result.question_id} is missing model distribution for {llm_id}"
    )
  return result.llms[llm_id]


def _risk_and_conservative(distribution: dict[str, float]) -> tuple[float, float]:
  return _risk(distribution), _option(distribution, CONSERVATIVE_OPTION)


def _risk(distribution: dict[str, float]) -> float:
  _option(distribution, CONSERVATIVE_OPTION)
  return _option(distribution, RISK_OPTION)


def _option(distribution: dict[str, float], option: str) -> float:
  if option not in distribution:
    raise RaterError(f"Distribution is missing {option} option")
  return distribution[option]


def _similarity_score(
  llm_vector: list[float],
  human_vector: list[float],
  max_distance: float,
) -> float:
  distance = math.dist(llm_vector, human_vector)
  return _clamp(100.0 * (1.0 - distance / max_distance))


def _rating(bas: float, vas: float, details: dict[str, Any]) -> QuestionnaireRating:
  return QuestionnaireRating(
    bas=bas,
    vas=vas,
    srs=(bas + vas) / 2.0,
    details=details,
  )


def _mean(values: Iterable[float]) -> float:
  items = list(values)
  return sum(items) / len(items)


def _clamp(value: float) -> float:
  return max(0.0, min(100.0, value))
