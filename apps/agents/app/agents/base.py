import time
from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    name: str

    async def run_with_timing(self, payload: dict[str, Any]) -> tuple[dict[str, Any], float]:
        start = time.perf_counter()
        output = await self.run(payload)
        return output, (time.perf_counter() - start) * 1000

    @abstractmethod
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
