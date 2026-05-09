from app.services.llm_client import LLMClient


class EmbeddingService:
    dimensions = 512

    def __init__(self) -> None:
        self._client: LLMClient | None = None

    def _get_client(self) -> LLMClient:
        if self._client is None:
            self._client = LLMClient()
        return self._client

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._get_client().embed_batch(texts)

    async def embed_async(self, text: str) -> list[float]:
        return await self._get_client().embed(text)

    def embed(self, text: str) -> list[float]:
        # Sync stub — use embed_async or embed_batch in async contexts.
        return [0.0] * self.dimensions

    def cosine(self, left: list[float] | None, right: list[float] | None) -> float:
        return LLMClient.cosine(left, right)
