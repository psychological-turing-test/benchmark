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
