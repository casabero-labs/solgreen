from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

import httpx

from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.llm_output import LLMInterpretation
from solgreen.diagnostics.llm_validator import validate_interpretation
from solgreen.diagnostics.prompt_builder import build_prompt


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
        """Send prompt to LLM, return raw response text."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...


class DeepSeekProvider(LLMProvider):
    API_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or self.default_model

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def default_model(self) -> str:
        return "deepseek-chat"

    def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)
            response.raise_for_status()
        data: dict[str, object] = response.json()
        choices = data["choices"]
        assert isinstance(choices, list)
        assert len(choices) > 0
        message = choices[0]
        assert isinstance(message, dict)
        content = message["message"]
        assert isinstance(content, dict)
        result = content["content"]
        assert isinstance(result, str)
        return result


def interpret_episode(
    provider: LLMProvider,
    input_data: LLMEpisodeInput,
    *,
    prompt_version: str = "1.0.0",
) -> LLMInterpretation:
    prompt = build_prompt(input_data)
    raw_response = provider.complete(prompt, max_tokens=input_data.max_tokens)

    input_hash = hashlib.sha256(prompt.encode()).hexdigest()
    parsed = _parse_response(raw_response, provider, prompt_version, input_hash)

    errors = validate_interpretation(parsed, input_data)
    if errors:
        raise ValueError(f"LLM interpretation validation failed: {errors}")

    return parsed


def _parse_response(
    raw: str,
    provider: LLMProvider,
    prompt_version: str,
    input_hash: str,
) -> LLMInterpretation:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)

    hypotheses = tuple(
        {
            "description": h["description"],
            "support_level": h["support_level"],
            "evidence_refs": tuple(h.get("evidence_refs", ())),
        }
        for h in data.get("hypotheses", [])
    )

    return LLMInterpretation(
        summary=data.get("summary", ""),
        hypotheses=hypotheses,
        alternatives=tuple(data.get("alternatives", ())),
        missing_info=tuple(data.get("missing_info", ())),
        suggested_actions=tuple(data.get("suggested_actions", ())),
        warnings=tuple(data.get("warnings", ())),
        prohibited_claims=(),
        provider=provider.provider_name,
        model=provider.default_model,
        prompt_version=prompt_version,
        input_hash=input_hash,
    )
