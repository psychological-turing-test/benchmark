from __future__ import annotations

import math

import pytest

from rationale_benchmark.rater.models import EvaluatorQuestionResult
from rationale_benchmark.rater.risky_choice_metrics import (
  compute_risky_choice_behavioral_metrics,
)

LLM_ID = "aliyun/qwen3.6-plus (0)"
FRAMES = ("P", "N")
LLM_RATES = {
  "6life": {"P": 0.2, "N": 0.6},
  "60life": {"P": 0.3, "N": 0.7},
  "600life": {"P": 0.4, "N": 0.8},
  "6000life": {"P": 0.5, "N": 0.9},
  "1kin": {"P": 0.1, "N": 0.2},
  "2kin": {"P": 0.2, "N": 0.3},
  "3kin": {"P": 0.3, "N": 0.4},
  "6kin": {"P": 0.6, "N": 0.7},
  "Human": {"P": 0.4, "N": 0.7},
  "Alien": {"P": 0.2, "N": 0.5},
  "6painting": {"P": 0.4, "N": 0.8},
  "60painting": {"P": 0.3, "N": 0.7},
  "600painting": {"P": 0.2, "N": 0.6},
  "6000painting": {"P": 0.1, "N": 0.5},
  "6dollar": {"P": 0.3, "N": 0.3},
  "60dollar": {"P": 0.3, "N": 0.3},
  "600dollar": {"P": 0.3, "N": 0.3},
  "6000dollar": {"P": 0.3, "N": 0.3},
}


def result(key: str, frame: str, llm_b: float) -> EvaluatorQuestionResult:
  return EvaluatorQuestionResult(
    source_file="risky-choice-framing-results.json",
    questionnaire_id="risky-choice-framing",
    section_name=f"Scenario-{frame}-{key}",
    question_id=f"1-{frame}-{key}",
    human={"A": 0.5, "B": 0.5},
    llms={LLM_ID: {"A": 1.0 - llm_b, "B": llm_b}},
  )


def frame_pairs() -> dict[str, dict[str, EvaluatorQuestionResult]]:
  return {
    key: {
      frame: result(key, frame, rates[frame])
      for frame in FRAMES
    }
    for key, rates in LLM_RATES.items()
  }


def entropy(rate: float) -> float:
  if rate <= 0.0 or rate >= 1.0:
    return 0.0
  return -rate * math.log2(rate) - (1.0 - rate) * math.log2(1.0 - rate)


def test_compute_risky_choice_behavioral_metrics_for_llm_and_human() -> None:
  metrics = compute_risky_choice_behavioral_metrics(frame_pairs(), LLM_ID)

  llm = metrics["llm"]
  human = metrics["human"]
  llm_profile = llm["profile"]
  human_profile = human["profile"]
  expected_fes = sum(
    rates["N"] - rates["P"] for rates in LLM_RATES.values()
  ) / len(LLM_RATES)
  expected_rc = sum(
    1.0 if rates["P"] < 0.5 and rates["N"] > 0.5 else 0.0
    for rates in LLM_RATES.values()
  ) / len(LLM_RATES)
  llm_values = [
    rates[frame]
    for key, rates in sorted(LLM_RATES.items())
    for frame in FRAMES
  ]
  expected_rd = 1.0 - sum(entropy(value) for value in llm_values) / len(
    llm_values
  )

  assert llm_profile["fes"] == pytest.approx(expected_fes)
  assert llm_profile["rc"] == pytest.approx(expected_rc)
  assert llm_profile["ms_life"] == pytest.approx(0.1)
  assert llm_profile["kg"] == pytest.approx(0.1)
  assert llm_profile["igb"] == pytest.approx(0.2)
  assert llm_profile["cdc"] == pytest.approx(0.8079713563)
  assert llm_profile["rd"] == pytest.approx(expected_rd)
  assert llm["ms"]["life"] == pytest.approx(
    {"p": 0.1, "n": 0.1, "mean": 0.1}
  )
  assert llm["ms"]["painting"] == pytest.approx(
    {"p": -0.1, "n": -0.1, "mean": -0.1}
  )
  assert llm["ms"]["dollar"] == pytest.approx(
    {"p": 0.0, "n": 0.0, "mean": 0.0}
  )
  assert llm["kg"] == pytest.approx({"p": 0.1, "n": 0.1, "mean": 0.1})
  assert llm["igb"] == pytest.approx({"p": 0.2, "n": 0.2, "mean": 0.2})
  assert llm["components"]["domain_means"]["life"] == pytest.approx(0.55)
  assert llm["components"]["domain_means"]["kin"] == pytest.approx(0.35)
  assert llm["components"]["domain_means"]["painting"] == pytest.approx(0.45)
  assert llm["components"]["domain_means"]["dollar"] == pytest.approx(0.3)

  assert human_profile["fes"] == pytest.approx(0.0)
  assert human_profile["rc"] == pytest.approx(0.0)
  assert human_profile["ms_life"] == pytest.approx(0.0)
  assert human_profile["kg"] == pytest.approx(0.0)
  assert human_profile["igb"] == pytest.approx(0.0)
  assert human_profile["cdc"] == pytest.approx(1.0)
  assert human_profile["rd"] == pytest.approx(0.0)
