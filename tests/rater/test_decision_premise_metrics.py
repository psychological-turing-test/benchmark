from __future__ import annotations

import pytest

from rationale_benchmark.rater.decision_premise_metrics import (
  decision_premise_behavioral_tendency_metrics,
)
from rationale_benchmark.rater.models import EvaluatorQuestionResult, RaterError

LLM_ID = "aliyun/qwen3.6-plus (0)"

HUMAN_RATES = {
  "Pf-6life": 0.2,
  "Pf-600life": 0.4,
  "Py-old": 0.775,
  "Py-young": 0.761904761905,
  "Pm-old": 0.966666666667,
  "Pm-young": 0.527777777778,
  "Pu-6kin": 0.55,
  "Pu-6life": 0.25,
  "Pu-600life": 0.1,
  "Pe-6kin": 0.677419354839,
  "Pe-6life": 0.40625,
  "Pe-600life": 0.294117647059,
  "P-6kin": 0.7,
  "P-6life": 0.64,
  "P-600life": 0.4,
}

LLM_RATES = {
  "Pf-6life": 0.4,
  "Pf-600life": 0.6,
  "Py-old": 0.5,
  "Py-young": 0.2,
  "Pm-old": 0.9,
  "Pm-young": 0.4,
  "Pu-6kin": 0.6,
  "Pu-6life": 0.3,
  "Pu-600life": 0.1,
  "Pe-6kin": 0.8,
  "Pe-6life": 0.5,
  "Pe-600life": 0.2,
  "P-6kin": 0.7,
  "P-6life": 0.4,
  "P-600life": 0.25,
}


def canonical_results(
  human_rates: dict[str, float] | None = None,
  llm_rates: dict[str, float] | None = None,
) -> list[EvaluatorQuestionResult]:
  human_values = human_rates or HUMAN_RATES
  llm_values = llm_rates or LLM_RATES
  return [
    EvaluatorQuestionResult(
      source_file="decision-premise-results.json",
      questionnaire_id="decision-premise",
      section_name=f"Scenario {key}",
      question_id=f"{index}-{key}",
      human={"A": 1.0 - human_values[key], "B": human_values[key]},
      llms={LLM_ID: {"A": 1.0 - llm_values[key], "B": llm_values[key]}},
    )
    for index, key in enumerate(human_values, start=1)
  ]


def test_decision_premise_behavioral_metrics() -> None:
  metrics = decision_premise_behavioral_tendency_metrics(
    canonical_results(),
    LLM_ID,
  )

  assert metrics is not None
  profile = metrics["profile"]
  assert list(profile["human"]) == ["frp", "sam", "kp", "sc", "gpr", "sbs"]
  assert profile["human"]["frp"] == pytest.approx(0.3)
  assert profile["human"]["sam"] == pytest.approx(0.425793650794)
  assert profile["human"]["kp"] == pytest.approx(0.210389784946)
  assert profile["human"]["sc"] == pytest.approx(0.16737745098)
  assert profile["human"]["gpr"] == pytest.approx(0.159262333966)
  assert profile["human"]["sbs"] == pytest.approx(0.28)

  assert profile["llm"]["frp"] == pytest.approx(0.5)
  assert profile["llm"]["sam"] == pytest.approx(0.2)
  assert profile["llm"]["kp"] == pytest.approx(0.3)
  assert profile["llm"]["sc"] == pytest.approx(0.216666666667)
  assert profile["llm"]["gpr"] == pytest.approx(0.166666666667)
  assert profile["llm"]["sbs"] == pytest.approx(0.116666666667)
  assert profile["delta"]["frp"] == pytest.approx(0.2)
  assert profile["delta"]["sbs"] == pytest.approx(-0.163333333333)

  components = metrics["components"]["human"]
  assert components["age_premise_gaps"]["middle_aged_prompt"] == pytest.approx(
    0.438888888889
  )
  assert components["kinship_premiums"]["pe"] == pytest.approx(0.271169354839)
  assert components["scale_conservatism"]["p"] == pytest.approx(0.24)
  assert components["gamble_payoff_responsiveness"]["600life"] == pytest.approx(
    0.194117647059
  )
  assert components["sure_benefit_sensitivity"]["6life"] == pytest.approx(0.39)


def test_decision_premise_behavioral_metrics_ignore_noncanonical_data() -> None:
  result = EvaluatorQuestionResult(
    source_file="decision-premise-results.json",
    questionnaire_id="decision-premise",
    section_name="Scenario-P-1",
    question_id="q1",
    human={"A": 0.6, "B": 0.4},
    llms={LLM_ID: {"A": 0.3, "B": 0.7}},
  )

  assert decision_premise_behavioral_tendency_metrics([result], LLM_ID) is None


def test_decision_premise_behavioral_metrics_reject_incomplete_canonical_data() -> None:
  results = canonical_results()[:-1]

  with pytest.raises(RaterError, match="missing: P-600life"):
    decision_premise_behavioral_tendency_metrics(results, LLM_ID)
