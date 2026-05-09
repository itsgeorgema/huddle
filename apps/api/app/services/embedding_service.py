import hashlib
import math


class EmbeddingService:
    """Small deterministic embedding substitute for mock mode and tests."""

    dimensions = 24

    def embed(self, text: str) -> list[float]:
        buckets = [0.0] * self.dimensions
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = digest[0] % self.dimensions
            buckets[idx] += 1.0 if digest[1] % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in buckets)) or 1.0
        return [round(v / norm, 5) for v in buckets]

    def cosine(self, left: list[float] | None, right: list[float] | None) -> float:
        if not left or not right:
            return 0.0
        return sum(a * b for a, b in zip(left, right))

    def _tokens(self, text: str) -> list[str]:
        return [token.strip(".,!?;:()[]").lower() for token in text.split() if len(token) > 2]
