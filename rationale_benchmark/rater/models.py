"""Shared rater data models and naming helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ANALYSIS_VERSION = 2
SUPPORTED_QUESTIONNAIRES = {"risky-choice-framing", "decision-premise"}


class RaterError(RuntimeError):
  """Raised when rater input or processing fails."""


@dataclass(frozen=True)
class EvaluatorQuestionResult:
  """One question entry loaded from an evaluator result file."""

  source_file: str
  questionnaire_id: str
  section_name: str
  question_id: str
  human: dict[str, float]
  llms: dict[str, dict[str, float]]


@dataclass(frozen=True)
class QuestionnaireRating:
  """BAS, VAS, SRS, and trace details for one questionnaire/model pair."""

  bas: float
  vas: float
  srs: float
  details: dict[str, Any]


@dataclass(frozen=True)
class RatingRunResult:
  """Paths and payload produced by rating an evaluator result directory."""

  input_dir: Path
  analysis_json: Path
  visualization_html: Path
  payload: dict[str, Any]


_ALIYUN_SUFFIX_RE = re.compile(r"^(?P<prefix>.+?)\s*\((?P<budget>-?\d+)\)$")


def format_model_display_name(llm_id: str) -> str:
  """Return a human-readable model label for visualization."""
  provider = llm_id.split("/", 1)[0]
  if provider != "aliyun":
    return llm_id

  match = _ALIYUN_SUFFIX_RE.match(llm_id)
  if match is None:
    return llm_id

  budget = int(match.group("budget"))
  prefix = match.group("prefix")
  if budget == 0:
    suffix = "no thinking"
  elif budget == -1:
    suffix = "max thinking"
  else:
    suffix = f"thinking budget {budget}"
  return f"{prefix} ({suffix})"
