from __future__ import annotations

import math

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


def canonical_decision_premise_results() -> list[EvaluatorQuestionResult]:
  return [
    result(
      questionnaire_id="decision-premise",
      section_name=f"Scenario {key}",
      question_id=f"{index}-{key}",
      human_b=human_b,
      llm_b=llm_b,
    )
    for index, (key, human_b, llm_b) in enumerate(
      CANONICAL_DECISION_PREMISE_RATES,
      start=1,
    )
  ]


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
  assert rating.details["bas_items"][0]["label"] == "q1"
  assert rating.details["bas_items"][0]["distance"] == pytest.approx(
    math.sqrt(0.3**2 + 0.3**2)
  )
  assert rating.details["bas_items"][0]["bas"] == pytest.approx(70.0)
  assert rating.details["vas"]["labels"] == ["q1", "q2"]
  assert rating.details["vas"]["distance"] == pytest.approx(
    math.sqrt(0.3**2 + 0.2**2)
  )
  assert rating.details["vas"]["max_distance"] == pytest.approx(math.sqrt(2))
  assert rating.details["vas"]["vas"] == pytest.approx(74.504871)
  assert "behavioral_tendency_metrics" not in rating.details


def test_score_decision_premise_includes_behavioral_metrics() -> None:
  rating = score_questionnaire(
    "decision-premise",
    "aliyun/qwen3.6-plus (0)",
    canonical_decision_premise_results(),
  )

  assert "bas_items" in rating.details
  assert "vas" in rating.details
  metrics = rating.details["behavioral_tendency_metrics"]
  profile = metrics["profile"]
  assert profile["human"]["frp"] == pytest.approx(0.3)
  assert profile["llm"]["frp"] == pytest.approx(0.5)
  assert profile["delta"]["frp"] == pytest.approx(0.2)
  assert profile["human"]["sbs"] == pytest.approx(0.28)
  assert profile["llm"]["sbs"] == pytest.approx(0.116666666667)


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
  assert rating.details["bas_items"][0]["distance"] == pytest.approx(
    math.sqrt(0.1**2 + 0.1**2)
  )
  assert rating.details["bas_items"][0]["bas"] == pytest.approx(90.0)
  assert rating.details["vas"]["labels"] == ["6life"]
  assert rating.details["vas"]["distance"] == pytest.approx(0.2)
  assert rating.details["vas"]["max_distance"] == pytest.approx(1.0)
  assert rating.details["vas"]["vas"] == pytest.approx(80.0)


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
