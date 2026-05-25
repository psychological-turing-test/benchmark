"""Behavioral tendency metrics for decision-premise results."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import EvaluatorQuestionResult, RaterError

RISK_OPTION = "B"

PROFILE_KEYS = ("frp", "sam", "kp", "sc", "gpr", "sbs")
CANONICAL_KEYS = (
  "Pf-6life",
  "Pf-600life",
  "Py-old",
  "Py-young",
  "Pm-old",
  "Pm-young",
  "Pu-6kin",
  "Pu-6life",
  "Pu-600life",
  "Pe-6kin",
  "Pe-6life",
  "Pe-600life",
  "P-6kin",
  "P-6life",
  "P-600life",
)

_KEYS_BY_LENGTH = tuple(sorted(CANONICAL_KEYS, key=len, reverse=True))


def decision_premise_behavioral_tendency_metrics(
  results: list[EvaluatorQuestionResult],
  llm_id: str,
) -> dict[str, Any] | None:
  """Return DecisionPremise behavioral metrics for complete canonical results."""
  human_rates: dict[str, float] = {}
  llm_rates: dict[str, float] = {}

  for result in results:
    key = _canonical_key(result)
    if key is None:
      continue
    if key in human_rates:
      raise RaterError(f"Duplicate decision-premise scenario key: {key}")

    human_rates[key] = _risk(result.human)
    llm_rates[key] = _risk(_llm_distribution(result, llm_id))

  if not human_rates:
    return None

  missing = [key for key in CANONICAL_KEYS if key not in human_rates]
  if missing:
    joined = ", ".join(missing)
    raise RaterError(
      "Decision-premise behavioral metrics require complete canonical "
      f"scenarios; missing: {joined}"
    )

  human = _agent_metrics(human_rates)
  llm = _agent_metrics(llm_rates)
  return {
    "profile": {
      "human": human["profile"],
      "llm": llm["profile"],
      "delta": _profile_delta(llm["profile"], human["profile"]),
    },
    "components": {
      "human": human["components"],
      "llm": llm["components"],
    },
  }


def _canonical_key(result: EvaluatorQuestionResult) -> str | None:
  for value in (result.question_id, result.section_name):
    for key in _KEYS_BY_LENGTH:
      if value == key or value.endswith(f"-{key}"):
        return key
  return None


def _llm_distribution(
  result: EvaluatorQuestionResult,
  llm_id: str,
) -> dict[str, float]:
  if llm_id not in result.llms:
    raise RaterError(
      f"Result {result.question_id} is missing model distribution for {llm_id}"
    )
  return result.llms[llm_id]


def _risk(distribution: dict[str, float]) -> float:
  if RISK_OPTION not in distribution:
    raise RaterError(f"Distribution is missing {RISK_OPTION} option")
  return distribution[RISK_OPTION]


def _agent_metrics(rates: dict[str, float]) -> dict[str, dict[str, Any]]:
  age_gaps = {
    "young_prompt": rates["Py-old"] - rates["Py-young"],
    "middle_aged_prompt": rates["Pm-old"] - rates["Pm-young"],
  }
  kinship_premiums = {
    "pu": rates["Pu-6kin"] - rates["Pu-6life"],
    "pe": rates["Pe-6kin"] - rates["Pe-6life"],
    "p": rates["P-6kin"] - rates["P-6life"],
  }
  scale_conservatism = {
    "pu": rates["Pu-6life"] - rates["Pu-600life"],
    "pe": rates["Pe-6life"] - rates["Pe-600life"],
    "p": rates["P-6life"] - rates["P-600life"],
  }
  gamble_payoff_responsiveness = {
    "6kin": rates["Pe-6kin"] - rates["Pu-6kin"],
    "6life": rates["Pe-6life"] - rates["Pu-6life"],
    "600life": rates["Pe-600life"] - rates["Pu-600life"],
  }
  sure_benefit_sensitivity = {
    "6kin": rates["P-6kin"] - rates["Pu-6kin"],
    "6life": rates["P-6life"] - rates["Pu-6life"],
    "600life": rates["P-600life"] - rates["Pu-600life"],
  }

  profile = {
    "frp": _mean([rates["Pf-6life"], rates["Pf-600life"]]),
    "sam": age_gaps["middle_aged_prompt"] - age_gaps["young_prompt"],
    "kp": _mean(kinship_premiums.values()),
    "sc": _mean(scale_conservatism.values()),
    "gpr": _mean(gamble_payoff_responsiveness.values()),
    "sbs": _mean(sure_benefit_sensitivity.values()),
  }
  return {
    "profile": profile,
    "components": {
      "age_premise_gaps": age_gaps,
      "kinship_premiums": kinship_premiums,
      "scale_conservatism": scale_conservatism,
      "gamble_payoff_responsiveness": gamble_payoff_responsiveness,
      "sure_benefit_sensitivity": sure_benefit_sensitivity,
    },
  }


def _profile_delta(
  llm_profile: dict[str, float],
  human_profile: dict[str, float],
) -> dict[str, float]:
  return {
    key: llm_profile[key] - human_profile[key]
    for key in PROFILE_KEYS
  }


def _mean(values: Iterable[float]) -> float:
  items = list(values)
  return sum(items) / len(items)
