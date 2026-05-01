from __future__ import annotations

from eureka_recall.schemas import MemoryHit


AUTHORITY_WEIGHT = {
    "current_workspace": 5.0,
    "canon": 4.0,
    "decision": 3.0,
    "failure_pattern": 2.5,
    "candidate": 1.5,
    "run_log": 1.0,
}


def rank_hits(hits: list[MemoryHit]) -> list[MemoryHit]:
    return sorted(hits, key=_weighted_score, reverse=True)


def _weighted_score(hit: MemoryHit) -> float:
    return hit.score * AUTHORITY_WEIGHT.get(hit.authority, 1.0)

