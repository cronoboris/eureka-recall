from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ActivationRequest:
    message: str
    cwd: Path
    localwiki_root: Path | None = None
    max_cards: int = 8
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    max_file_bytes: int = 262_144
    workspace_enabled: bool = True


@dataclass(frozen=True)
class MemoryHit:
    id: str
    connector: str
    source_path: Path
    title: str
    snippet: str
    authority: str
    freshness: str | None = None
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryCard:
    id: str
    connector: str
    source: str
    title: str
    content: str
    authority: str
    relevance: float
    freshness: str | None
    activation_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActivationTrace:
    request: dict[str, Any]
    queries: list[str]
    connectors: list[str]
    selected_ids: list[str]
    rejected_count: int
    connector_counts: dict[str, int] = field(default_factory=dict)
    authority_counts: dict[str, int] = field(default_factory=dict)
    top_rejected: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActivationResult:
    cards: list[MemoryCard]
    bundle_markdown: str
    harness_prompt: str
    trace: ActivationTrace
