import json
import math
import os

from openai import AsyncOpenAI


class LLMClient:
    def __init__(self) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.environ.get("LLM_MODEL", "gpt-5.4-mini")
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 512

    async def complete_json(self, system: str, user: str, temperature: float = 0.2) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
            dimensions=self.embedding_dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
            dimensions=self.embedding_dimensions,
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    @staticmethod
    def cosine(left: list[float] | None, right: list[float] | None) -> float:
        if not left or not right:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        norm_l = math.sqrt(sum(a * a for a in left))
        norm_r = math.sqrt(sum(b * b for b in right))
        if norm_l == 0 or norm_r == 0:
            return 0.0
        return dot / (norm_l * norm_r)
