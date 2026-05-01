from __future__ import annotations

from eureka_recall.connectors import FilesystemConnector, LocalWikiConnector, MemoryConnector
from eureka_recall.policy import rank_hits
from eureka_recall.schemas import ActivationRequest, ActivationResult, ActivationTrace, MemoryCard
from eureka_recall.text import extract_terms


def activate(
    request: ActivationRequest,
    connectors: list[MemoryConnector] | None = None,
) -> ActivationResult:
    connectors = connectors or [FilesystemConnector(), LocalWikiConnector()]
    queries = plan_queries(request.message)
    hits = []
    queried = []
    for connector in connectors:
        connector_hits = connector.search(request, queries)
        queried.append(connector.name)
        hits.extend(connector_hits)

    ranked = rank_hits(hits)
    selected = ranked[: request.max_cards]
    cards = [
        MemoryCard(
            id=hit.id,
            connector=hit.connector,
            source=str(hit.source_path),
            title=hit.title,
            content=hit.snippet,
            authority=hit.authority,
            relevance=round(hit.score, 3),
            freshness=hit.freshness,
            activation_reason=f"Matched request terms for {hit.authority} context.",
        )
        for hit in selected
    ]
    trace = ActivationTrace(
        request={
            "message": request.message,
            "cwd": str(request.cwd),
            "localwiki_root": str(request.localwiki_root) if request.localwiki_root else None,
            "max_cards": request.max_cards,
        },
        queries=queries,
        connectors=queried,
        selected_ids=[card.id for card in cards],
        rejected_count=max(len(hits) - len(cards), 0),
    )
    return ActivationResult(cards=cards, bundle_markdown=render_bundle(cards), trace=trace)


def plan_queries(message: str) -> list[str]:
    terms = extract_terms(message)
    return [" ".join(terms[:6])] if terms else [message.strip()]


def render_bundle(cards: list[MemoryCard]) -> str:
    if not cards:
        return "# Eureka Context Bundle\n\nNo context cards selected.\n"

    lines = ["# Eureka Context Bundle", ""]
    for index, card in enumerate(cards, start=1):
        lines.extend(
            [
                f"## {index}. {card.title}",
                "",
                f"- Source: `{card.source}`",
                f"- Connector: `{card.connector}`",
                f"- Authority: `{card.authority}`",
                f"- Relevance: `{card.relevance}`",
                f"- Activation reason: {card.activation_reason}",
                "",
                card.content,
                "",
            ]
        )
    return "\n".join(lines)

