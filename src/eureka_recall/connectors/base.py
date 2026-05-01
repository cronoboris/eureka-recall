from __future__ import annotations

from abc import ABC, abstractmethod

from eureka_recall.schemas import ActivationRequest, MemoryHit


class MemoryConnector(ABC):
    """Read-only adapter for an existing memory source."""

    name: str

    @abstractmethod
    def search(self, request: ActivationRequest, queries: list[str]) -> list[MemoryHit]:
        """Return matching memory hits without modifying the source store."""

