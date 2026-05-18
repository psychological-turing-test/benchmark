"""Aliyun provider client."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..config.connector_models import LLMConnectorConfig
from ..exceptions import ProviderError
from ..provider_client import ProviderResponse
from .openai_compatible import OpenAICompatibleClient

DEFAULT_JSON_FORMATTING_MODEL = "qwen3.6-flash"
JSON_FORMATTING_SYSTEM_PROMPT = (
  "You are a JSON formatting expert. Repair the user's model output into a "
  "standard JSON object that satisfies the provided JSON Schema. Return only "
  "the JSON object."
)


class AliyunClient(OpenAICompatibleClient):
  """Client for Aliyun's OpenAI-compatible chat endpoint."""

  def __init__(self, config: LLMConnectorConfig):
    super().__init__(config)

  def _generate(
    self,
    messages: List[dict[str, str]],
    *,
    output_schema: dict[str, Any],
  ) -> ProviderResponse:
    response = super()._generate(messages, output_schema=output_schema)
    if self._uses_native_structured_output():
      return response
    if self._content_conforms_to_schema(response.content, output_schema):
      return response
    return self._repair_json_response(response, output_schema)

  def _uses_native_structured_output(self) -> bool:
    return self.config.default_params.get("enable_thinking") is False

  def _build_payload(
    self,
    messages: List[dict[str, str]],
    output_schema: dict[str, Any],
  ) -> Dict[str, Any]:
    payload = super()._build_payload(messages, output_schema)
    if self._uses_native_structured_output():
      payload["response_format"] = {"type": "json_object"}
    return payload

  def _repair_json_response(
    self,
    response: ProviderResponse,
    output_schema: dict[str, Any],
  ) -> ProviderResponse:
    payload = self._build_json_formatting_payload(
      response.content,
      output_schema,
    )
    url = f"{self.base_url}/chat/completions"
    data, headers = self._post_json(url, self.headers, payload)

    try:
      choice = data["choices"][0]
    except (KeyError, IndexError, TypeError) as exc:
      raise ProviderError(
        self.config.provider.value,
        "Invalid response payload received from Aliyun JSON formatter",
        cause=exc,
      ) from exc

    content = self._extract_content(choice)
    metadata = dict(response.metadata)
    metadata["aliyun_json_formatting"] = {
      "model": payload["model"],
      "id": data.get("id"),
      "headers": headers,
    }

    return ProviderResponse(
      content=content,
      raw={
        "original": response.raw,
        "json_formatting": data,
      },
      finish_reason=choice.get("finish_reason"),
      metadata=metadata,
    )

  def _build_json_formatting_payload(
    self,
    content: str,
    output_schema: dict[str, Any],
  ) -> Dict[str, Any]:
    schema_text = json.dumps(output_schema, ensure_ascii=False, sort_keys=True)
    return {
      "model": self._json_formatting_model(),
      "messages": [
        {
          "role": "system",
          "content": JSON_FORMATTING_SYSTEM_PROMPT,
        },
        {
          "role": "user",
          "content": (
            "JSON Schema:\n"
            f"{schema_text}\n\n"
            "Model output:\n"
            f"{content}"
          ),
        },
      ],
      "response_format": {"type": "json_object"},
      "extra_body": {"enable_thinking": False},
    }

  def _json_formatting_model(self) -> str:
    value = self.config.provider_specific.get("json_formatting_model")
    if isinstance(value, str) and value.strip():
      return value.strip()
    return DEFAULT_JSON_FORMATTING_MODEL

  def _content_conforms_to_schema(
    self,
    content: str,
    output_schema: dict[str, Any],
  ) -> bool:
    try:
      value = json.loads(content)
    except json.JSONDecodeError:
      return False
    return self._matches_schema(value, output_schema)

  def _matches_schema(self, value: Any, schema: dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
      return True

    expected_type = schema.get("type")
    if expected_type is not None and not self._matches_type(
      value,
      expected_type,
    ):
      return False

    if "enum" in schema and value not in schema["enum"]:
      return False

    if not self._matches_numeric_bounds(value, schema):
      return False

    properties = schema.get("properties")
    if isinstance(properties, dict):
      if not isinstance(value, dict):
        return False
      required = schema.get("required", [])
      if isinstance(required, list):
        for key in required:
          if key not in value:
            return False
      if schema.get("additionalProperties") is False:
        allowed = {str(key) for key in properties}
        if any(key not in allowed for key in value):
          return False
      for key, property_schema in properties.items():
        if key in value and not self._matches_schema(
          value[key],
          property_schema,
        ):
          return False

    items = schema.get("items")
    if isinstance(items, dict) and isinstance(value, list):
      return all(self._matches_schema(item, items) for item in value)

    return True

  def _matches_type(self, value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
      return any(self._matches_type(value, item) for item in expected_type)
    if expected_type == "object":
      return isinstance(value, dict)
    if expected_type == "array":
      return isinstance(value, list)
    if expected_type == "string":
      return isinstance(value, str)
    if expected_type == "integer":
      return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
      return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
      )
    if expected_type == "boolean":
      return isinstance(value, bool)
    if expected_type == "null":
      return value is None
    return True

  def _matches_numeric_bounds(
    self,
    value: Any,
    schema: dict[str, Any],
  ) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
      return True
    minimum = schema.get("minimum")
    if isinstance(minimum, (int, float)) and value < minimum:
      return False
    maximum = schema.get("maximum")
    if isinstance(maximum, (int, float)) and value > maximum:
      return False
    return True
