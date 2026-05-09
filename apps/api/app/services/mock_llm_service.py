import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings


class LLMProvider:
    async def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    async def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"mode": "mock", "prompt_preview": prompt[:120], "schema": schema}


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Return only valid JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


def get_llm_provider(mode: str | None = None) -> LLMProvider:
    settings = get_settings()
    selected = mode or settings.llm_mode
    if selected == "real":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_MODE=real")
        return OpenAIProvider()
    return MockLLMProvider()
