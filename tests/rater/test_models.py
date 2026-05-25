from __future__ import annotations

from rationale_benchmark.rater import ANALYSIS_VERSION, SUPPORTED_QUESTIONNAIRES
from rationale_benchmark.rater.models import format_model_display_name


def test_public_constants_are_exported() -> None:
  assert ANALYSIS_VERSION == 2
  assert SUPPORTED_QUESTIONNAIRES == {
    "decision-premise",
    "risky-choice-framing",
  }


def test_format_aliyun_no_thinking_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (0)")
    == "aliyun/qwen3.6-plus (no thinking)"
  )


def test_format_aliyun_max_thinking_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (-1)")
    == "aliyun/qwen3.6-plus (max thinking)"
  )


def test_format_aliyun_positive_thinking_budget_suffix() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus (10)")
    == "aliyun/qwen3.6-plus (thinking budget 10)"
  )


def test_format_aliyun_without_suffix_is_unchanged() -> None:
  assert (
    format_model_display_name("aliyun/qwen3.6-plus")
    == "aliyun/qwen3.6-plus"
  )


def test_format_non_aliyun_suffix_is_unchanged() -> None:
  assert (
    format_model_display_name("openai/gpt-4.1 (0)")
    == "openai/gpt-4.1 (0)"
  )


def test_format_provider_ending_in_aliyun_suffix_is_unchanged() -> None:
  assert (
    format_model_display_name("foo_aliyun/model (0)")
    == "foo_aliyun/model (0)"
  )
