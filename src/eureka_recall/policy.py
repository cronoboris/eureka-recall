from __future__ import annotations

from math import ceil

from eureka_recall.schemas import MemoryHit


AUTHORITY_WEIGHT = {
    "current_workspace": 5.0,
    "canon": 4.0,
    "decision": 3.0,
    "failure_pattern": 2.5,
    "candidate": 1.5,
    "run_log": 1.0,
}

DIVERSITY_MIN_RATIO = 0.25


def rank_hits(hits: list[MemoryHit]) -> list[MemoryHit]:
    return sorted(hits, key=_weighted_score, reverse=True)


def select_hits(hits: list[MemoryHit], max_cards: int) -> list[MemoryHit]:
    """Pick high-scoring hits while avoiding one connector dominating the bundle."""
    ranked = rank_hits(hits)
    if max_cards <= 0 or not ranked:
        return []

    connectors = {hit.connector for hit in ranked}
    if len(connectors) <= 1:
        return ranked[:max_cards]

    per_connector_cap = max(1, ceil(max_cards * 0.7))
    top_score = _weighted_score(ranked[0])
    diversity_floor = top_score * DIVERSITY_MIN_RATIO
    selected: list[MemoryHit] = []
    selected_ids: set[str] = set()
    connector_counts: dict[str, int] = {}

    for hit in ranked:
        if len(selected) >= max_cards:
            break
        count = connector_counts.get(hit.connector, 0)
        if count >= per_connector_cap:
            continue
        if selected and _weighted_score(hit) < diversity_floor:
            continue
        selected.append(hit)
        selected_ids.add(hit.id)
        connector_counts[hit.connector] = count + 1

    for hit in ranked:
        if len(selected) >= max_cards:
            break
        if hit.id in selected_ids:
            continue
        selected.append(hit)
        selected_ids.add(hit.id)

    return selected


def _weighted_score(hit: MemoryHit) -> float:
    return hit.score * AUTHORITY_WEIGHT.get(hit.authority, 1.0)
