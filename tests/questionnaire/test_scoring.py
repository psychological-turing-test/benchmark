from __future__ import annotations

import pytest

from rationale_benchmark.questionnaire import (
  AnswerValidationError,
  Question,
  QuestionDistribution,
  QuestionScore,
  QuestionType,
  ScoringRule,
  build_distribution,
  score_question,
  validate_answer,
)


def _rating_question() -> Question:
  return Question(
    id="q1",
    type=QuestionType.RATING_5,
    prompt="Prompt",
    options=None,
    scoring=ScoringRule(
      total=5,
      weights={
        "1": 0,
        "2": 1,
        "3": 3,
        "4": 4,
        "5": 5,
      },
    ),
  )


def _choice_question() -> Question:
  return Question(
    id="q2",
    type=QuestionType.CHOICE,
    prompt="Prompt",
    options={
      "low": "Low",
      "high": "High",
    },
    scoring=ScoringRule(
      total=3,
      weights={
        "low": 0,
        "high": 3,
      },
    ),
  )


def _distribution_choice_question() -> Question:
  return Question(
    id="q3",
    type=QuestionType.CHOICE,
    prompt="Prompt",
    options={
      "low": "Low",
      "medium": "Medium",
      "high": "High",
    },
    scoring=ScoringRule(
      total=None,
      distribution={"low": 0.33, "medium": 0.34, "high": 0.33},
    ),
  )


def _distribution_rating_question() -> Question:
  return Question(
    id="q4",
    type=QuestionType.RATING_5,
    prompt="Prompt",
    options=None,
    scoring=ScoringRule(
      total=None,
      distribution={
        "1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2,
      },
    ),
  )


def test_validate_answer_rating_returns_token() -> None:
  question = _rating_question()
  token = validate_answer(question, 3)
  assert token == "3"


def test_validate_answer_choice_returns_key() -> None:
  question = _choice_question()
  token = validate_answer(question, "high")
  assert token == "high"


def test_validate_answer_rating_out_of_range_raises() -> None:
  question = _rating_question()
  with pytest.raises(AnswerValidationError):
    validate_answer(question, 10)


def test_validate_answer_choice_unknown_key_raises() -> None:
  question = _choice_question()
  with pytest.raises(AnswerValidationError):
    validate_answer(question, "medium")


def test_validate_answer_distribution_choice_returns_key() -> None:
  question = _distribution_choice_question()
  token = validate_answer(question, "medium")
  assert token == "medium"


def test_validate_answer_distribution_rating_returns_token() -> None:
  question = _distribution_rating_question()
  token = validate_answer(question, 2)
  assert token == "2"


def test_score_question_returns_expected_points() -> None:
  question = _choice_question()
  score = score_question(question, "high")
  assert isinstance(score, QuestionScore)
  assert score.question_id == "q2"
  assert score.awarded == 3
  assert score.total == 3


def test_score_question_on_distribution_mode_raises() -> None:
  question = _distribution_choice_question()
  with pytest.raises(Exception, match="distribution question"):
    score_question(question, "low")


def test_build_distribution_computes_fractions() -> None:
  question = _distribution_choice_question()
  counts = {"low": 40, "medium": 35, "high": 25}
  result = build_distribution(question, counts)
  assert isinstance(result, QuestionDistribution)
  assert result.question_id == "q3"
  assert result.counts == counts
  assert result.fractions["low"] == pytest.approx(0.40)
  assert result.fractions["medium"] == pytest.approx(0.35)
  assert result.fractions["high"] == pytest.approx(0.25)


def test_build_distribution_zero_total_yields_zero_fractions() -> None:
  question = _distribution_choice_question()
  counts = {"low": 0, "medium": 0, "high": 0}
  result = build_distribution(question, counts)
  assert result.fractions == {"low": 0.0, "medium": 0.0, "high": 0.0}


def test_build_distribution_on_weighted_mode_raises() -> None:
  question = _choice_question()
  with pytest.raises(Exception, match="weighted question"):
    build_distribution(question, {"low": 1, "high": 2})
