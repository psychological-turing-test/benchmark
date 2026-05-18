"""Tests for provider request payload construction."""

from __future__ import annotations

from rationale_benchmark.llm.config.connector_models import (
  LLMConnectorConfig,
  ProviderType,
)
from rationale_benchmark.llm.providers.aliyun import AliyunClient
from rationale_benchmark.llm.providers.anthropic import AnthropicClient
from rationale_benchmark.llm.providers.gemini import GeminiClient
from rationale_benchmark.llm.providers.openai import OpenAIChatClient
from rationale_benchmark.llm.providers.openai_compatible import (
  OpenAICompatibleClient,
)


OUTPUT_SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "answer": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5,
    }
  },
  "required": ["answer"],
  "title": "rating_01",
}


class CapturingAliyunClient(AliyunClient):
  def __init__(self, config: LLMConnectorConfig, responses):
    super().__init__(config)
    self.requests = []
    self._responses = list(responses)

  def _post_json(self, url, headers, payload):
    self.requests.append(payload)
    return self._responses.pop(0), {}


def test_openai_payload_omits_temperature_when_unset():
  config = LLMConnectorConfig(
    provider=ProviderType.OPENAI,
    model="gpt-4o-mini",
    api_key="token",
  )
  client = OpenAIChatClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert "temperature" not in payload


def test_anthropic_payload_omits_temperature_when_unset():
  config = LLMConnectorConfig(
    provider=ProviderType.ANTHROPIC,
    model="claude-3-5-sonnet",
    api_key="token",
  )
  client = AnthropicClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert "temperature" not in payload


def test_gemini_payload_omits_temperature_when_unset():
  config = LLMConnectorConfig(
    provider=ProviderType.GEMINI,
    model="gemini-2.5-pro",
    api_key="token",
  )
  client = GeminiClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert "generationConfig" not in payload


def test_openai_payload_keeps_explicit_temperature():
  config = LLMConnectorConfig(
    provider=ProviderType.OPENAI,
    model="gpt-4o-mini",
    api_key="token",
    temperature=0.4,
  )
  client = OpenAIChatClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert payload["temperature"] == 0.4


def test_openai_payload_uses_json_schema_response_format():
  config = LLMConnectorConfig(
    provider=ProviderType.OPENAI,
    model="gpt-4o-mini",
    api_key="token",
  )
  client = OpenAIChatClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert payload["response_format"] == {
    "type": "json_schema",
    "json_schema": {
      "name": "rating_01",
      "strict": True,
      "schema": OUTPUT_SCHEMA,
    },
  }


def test_anthropic_payload_uses_output_config_format():
  config = LLMConnectorConfig(
    provider=ProviderType.ANTHROPIC,
    model="claude-sonnet-4-5",
    api_key="token",
  )
  client = AnthropicClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert payload["output_config"] == {
    "format": {
      "type": "json_schema",
      "schema": OUTPUT_SCHEMA,
    }
  }


def test_openai_compatible_payload_uses_json_schema_for_standard_backends():
  config = LLMConnectorConfig(
    provider=ProviderType.OPENAI_COMPATIBLE,
    model="qwen3-max",
    api_key="token",
    base_url="https://openrouter.ai/api/v1",
  )
  client = OpenAICompatibleClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert payload["response_format"]["type"] == "json_schema"


def test_aliyun_payload_omits_native_structured_output_for_reasoning_models():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    default_params={"enable_thinking": True},
  )
  client = AliyunClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert "response_format" not in payload


def test_aliyun_payload_omits_native_structured_output_by_default():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  )
  client = AliyunClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert "response_format" not in payload


def test_aliyun_payload_uses_json_object_mode_when_thinking_disabled():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    default_params={"enable_thinking": False},
  )
  client = AliyunClient(config)

  payload = client._build_payload(
    [{"role": "user", "content": "hello"}],
    OUTPUT_SCHEMA,
  )

  assert payload["response_format"] == {"type": "json_object"}


def test_aliyun_repairs_malformed_reasoning_json_with_formatting_model():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    provider_specific={"json_formatting_model": "qwen-flash"},
  )
  client = CapturingAliyunClient(
    config,
    responses=[
      {
        "choices": [
          {
            "message": {"content": "answer: 4"},
            "finish_reason": "stop",
          }
        ]
      },
      {
        "choices": [
          {
            "message": {"content": "{\"answer\": 4}"},
            "finish_reason": "stop",
          }
        ]
      },
    ],
  )

  response = client._generate(
    [{"role": "user", "content": "hello"}],
    output_schema=OUTPUT_SCHEMA,
  )

  assert response.content == "{\"answer\": 4}"
  assert [request["model"] for request in client.requests] == [
    "qwen3.6-plus",
    "qwen-flash",
  ]
  assert "response_format" not in client.requests[0]
  assert client.requests[1]["response_format"] == {"type": "json_object"}
  assert client.requests[1]["extra_body"] == {"enable_thinking": False}
  formatting_message = client.requests[1]["messages"][-1]
  assert formatting_message["role"] == "user"
  assert "JSON Schema:" in formatting_message["content"]
  assert "Model output:\nanswer: 4" in formatting_message["content"]


def test_aliyun_repairs_schema_invalid_reasoning_json():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  )
  client = CapturingAliyunClient(
    config,
    responses=[
      {
        "choices": [
          {
            "message": {"content": "{\"answer\": 9}"},
            "finish_reason": "stop",
          }
        ]
      },
      {
        "choices": [
          {
            "message": {"content": "{\"answer\": 5}"},
            "finish_reason": "stop",
          }
        ]
      },
    ],
  )

  response = client._generate(
    [{"role": "user", "content": "hello"}],
    output_schema=OUTPUT_SCHEMA,
  )

  assert response.content == "{\"answer\": 5}"
  assert client.requests[1]["model"] == "qwen3.6-flash"


def test_aliyun_does_not_repair_schema_valid_reasoning_json():
  config = LLMConnectorConfig(
    provider=ProviderType.ALIYUN,
    model="qwen3.6-plus",
    api_key="token",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  )
  client = CapturingAliyunClient(
    config,
    responses=[
      {
        "choices": [
          {
            "message": {"content": "{\"answer\": 4}"},
            "finish_reason": "stop",
          }
        ]
      },
    ],
  )

  response = client._generate(
    [{"role": "user", "content": "hello"}],
    output_schema=OUTPUT_SCHEMA,
  )

  assert response.content == "{\"answer\": 4}"
  assert len(client.requests) == 1
