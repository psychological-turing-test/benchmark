"""Behavioral tendency metrics for risky-choice framing results."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any

from .models import EvaluatorQuestionResult, RaterError

RISK_OPTION = "B"
CONSERVATIVE_OPTION = "A"
FRAMES = ("P", "N")
MAGNITUDE_DOMAINS = ("life", "painting", "dollar")
MAGNITUDES = (6, 60, 600, 6000)
KIN_VALUES = (1, 2, 3, 6)
CDC_DOMAINS = ("life", "kin", "painting", "dollar")

FramePairs = dict[str, dict[str, EvaluatorQuestionResult]]
DistributionSelector = Callable[[EvaluatorQuestionResult], dict[str, float]]
RiskRates = dict[str, dict[str, float]]


def compute_risky_choice_behavioral_metrics(
  pairs: FramePairs,
  llm_id: str,
) -> dict[str, Any]:
  """Compute risky-choice behavioral tendency metrics for human and LLM."""
  return {
    "human": _agent_metrics(pairs, lambda result: result.human),
    "llm": _agent_metrics(
      pairs,
      lambda result: _llm_distribution(result, llm_id),
    ),
  }


def _agent_metrics(
  pairs: FramePairs,
  distribution_for: DistributionSelector,
) -> dict[str, Any]:
  rates = _risk_rates(pairs, distribution_for)
  framing_effects = _framing_effects(rates)
  reflection_consistency = _reflection_consistency(rates)
  ms = {
    domain: _magnitude_sensitivity(rates, domain)
    for domain in MAGNITUDE_DOMAINS
  }
  kg = _kinship_gradient(rates)
  igb = _ingroup_bias(rates)
  domain_means = _domain_means(rates)

  return {
    "profile": {
      "fes": _mean_or_none(framing_effects.values()),
      "rc": _mean_or_none(
        1.0 if value else 0.0
        for value in reflection_consistency.values()
      ),
      "ms_life": ms["life"]["mean"],
      "kg": kg["mean"],
      "igb": igb["mean"],
      "cdc": _cross_domain_coherence(domain_means),
      "rd": _response_determinism(rates),
    },
    "ms": ms,
    "kg": kg,
    "igb": igb,
    "components": {
      "framing_effects": framing_effects,
      "reflection_consistency": reflection_consistency,
      "domain_means": domain_means,
    },
  }


def _risk_rates(
  pairs: FramePairs,
  distribution_for: DistributionSelector,
) -> RiskRates:
  rates: RiskRates = {}
  for key in sorted(pairs):
    frame_rates: dict[str, float] = {}
    for frame in FRAMES:
      if frame in pairs[key]:
        frame_rates[frame] = _risk(distribution_for(pairs[key][frame]))
    if frame_rates:
      rates[key] = frame_rates
  return rates


def _framing_effects(rates: RiskRates) -> dict[str, float]:
  return {
    key: rates[key]["N"] - rates[key]["P"]
    for key in sorted(rates)
    if _has_frames(rates, key)
  }


def _reflection_consistency(rates: RiskRates) -> dict[str, bool]:
  return {
    key: rates[key]["P"] < 0.5 and rates[key]["N"] > 0.5
    for key in sorted(rates)
    if _has_frames(rates, key)
  }


def _magnitude_sensitivity(
  rates: RiskRates,
  domain: str,
) -> dict[str, float | None]:
  p = _magnitude_slope(rates, domain, "P")
  n = _magnitude_slope(rates, domain, "N")
  return {"p": p, "n": n, "mean": _pair_mean(p, n)}


def _magnitude_slope(
  rates: RiskRates,
  domain: str,
  frame: str,
) -> float | None:
  points = []
  for magnitude in MAGNITUDES:
    key = f"{magnitude}{domain}"
    if key not in rates or frame not in rates[key]:
      return None
    points.append((math.log10(magnitude), rates[key][frame]))
  return _slope(points)


def _kinship_gradient(rates: RiskRates) -> dict[str, float | None]:
  p = _kinship_slope(rates, "P")
  n = _kinship_slope(rates, "N")
  return {"p": p, "n": n, "mean": _pair_mean(p, n)}


def _kinship_slope(rates: RiskRates, frame: str) -> float | None:
  points = []
  for kin_count in KIN_VALUES:
    key = f"{kin_count}kin"
    if key not in rates or frame not in rates[key]:
      return None
    points.append((float(kin_count), rates[key][frame]))
  return _slope(points)


def _ingroup_bias(rates: RiskRates) -> dict[str, float | None]:
  p = _identity_bias(rates, "P")
  n = _identity_bias(rates, "N")
  return {"p": p, "n": n, "mean": _pair_mean(p, n)}


def _identity_bias(rates: RiskRates, frame: str) -> float | None:
  if (
    "Human" not in rates
    or "Alien" not in rates
    or frame not in rates["Human"]
    or frame not in rates["Alien"]
  ):
    return None
  return rates["Human"][frame] - rates["Alien"][frame]


def _domain_means(rates: RiskRates) -> dict[str, float | None]:
  return {domain: _domain_mean(rates, domain) for domain in CDC_DOMAINS}


def _domain_mean(rates: RiskRates, domain: str) -> float | None:
  values: list[float] = []
  keys = _domain_keys(domain)
  for key in keys:
    if key not in rates:
      return None
    for frame in FRAMES:
      if frame not in rates[key]:
        return None
      values.append(rates[key][frame])
  return _mean(values)


def _domain_keys(domain: str) -> tuple[str, ...]:
  if domain == "kin":
    return tuple(f"{value}kin" for value in KIN_VALUES)
  return tuple(f"{value}{domain}" for value in MAGNITUDES)


def _cross_domain_coherence(
  domain_means: dict[str, float | None],
) -> float | None:
  if any(value is None for value in domain_means.values()):
    return None

  values = [value for value in domain_means.values() if value is not None]
  mean = _mean(values)
  std = math.sqrt(_mean((value - mean) ** 2 for value in values))
  return _clamp01(1.0 - std / 0.5)


def _response_determinism(rates: RiskRates) -> float | None:
  item_rates = [
    rates[key][frame]
    for key in sorted(rates)
    for frame in FRAMES
    if frame in rates[key]
  ]
  if not item_rates:
    return None
  return _clamp01(1.0 - _mean(_bernoulli_entropy(rate) for rate in item_rates))


def _bernoulli_entropy(rate: float) -> float:
  if rate <= 0.0 or rate >= 1.0:
    return 0.0
  return -rate * math.log2(rate) - (1.0 - rate) * math.log2(1.0 - rate)


def _slope(points: list[tuple[float, float]]) -> float | None:
  if len(points) < 2:
    return None

  x_mean = _mean(x for x, _ in points)
  y_mean = _mean(y for _, y in points)
  denominator = sum((x - x_mean) ** 2 for x, _ in points)
  if denominator == 0.0:
    return None
  numerator = sum((x - x_mean) * (y - y_mean) for x, y in points)
  return numerator / denominator


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
  _option(distribution, CONSERVATIVE_OPTION)
  return _option(distribution, RISK_OPTION)


def _option(distribution: dict[str, float], option: str) -> float:
  if option not in distribution:
    raise RaterError(f"Distribution is missing {option} option")
  return distribution[option]


def _has_frames(rates: RiskRates, key: str) -> bool:
  return all(frame in rates[key] for frame in FRAMES)


def _pair_mean(left: float | None, right: float | None) -> float | None:
  if left is None or right is None:
    return None
  return (left + right) / 2.0


def _mean_or_none(values: Iterable[float]) -> float | None:
  items = list(values)
  if not items:
    return None
  return _mean(items)


def _mean(values: Iterable[float]) -> float:
  items = list(values)
  return sum(items) / len(items)


def _clamp01(value: float) -> float:
  return max(0.0, min(1.0, value))
