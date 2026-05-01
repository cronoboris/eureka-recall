from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_inspection(out: Path) -> str:
    cards_path = out / "context_cards.json"
    trace_path = out / "retrieval_trace.json"
    if not cards_path.exists() or not trace_path.exists():
        raise FileNotFoundError(f"Expected context_cards.json and retrieval_trace.json in {out}")

    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    return render_inspection_data(cards, trace)


def render_inspection_data(cards: list[dict[str, Any]], trace: dict[str, Any]) -> str:
    lines = [
        "# Eureka Inspection",
        "",
        f"selected: {len(cards)}",
        f"rejected: {trace.get('rejected_count', 0)}",
        f"connectors queried: {', '.join(trace.get('connectors', [])) or '(none)'}",
        f"queries: {', '.join(trace.get('queries', [])) or '(none)'}",
        "",
        "## Selected By Connector",
        "",
    ]
    lines.extend(_count_lines(trace.get("connector_counts", {})))
    lines.extend(["", "## Selected By Authority", ""])
    lines.extend(_count_lines(trace.get("authority_counts", {})))
    lines.extend(["", "## Selected Cards", ""])
    for index, card in enumerate(cards, start=1):
        lines.append(
            f"{index}. [{card.get('connector')}/{card.get('authority')}] "
            f"{card.get('title')} ({card.get('relevance')})"
        )
        lines.append(f"   {card.get('source')}")

    top_rejected = trace.get("top_rejected", [])
    lines.extend(["", "## Top Rejected", ""])
    if not top_rejected:
        lines.append("(none)")
    for index, hit in enumerate(top_rejected, start=1):
        lines.append(
            f"{index}. [{hit.get('connector')}/{hit.get('authority')}] "
            f"{hit.get('title')} ({hit.get('score')})"
        )
        lines.append(f"   {hit.get('source')}")

    warnings = _warnings(cards, trace)
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("(none)")
    return "\n".join(lines) + "\n"


def _count_lines(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["(none)"]
    return [f"- {key}: {value}" for key, value in sorted(counts.items())]


def _warnings(cards: list[dict[str, Any]], trace: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not cards:
        warnings.append("no context cards selected")
    authorities = {card.get("authority") for card in cards}
    if "run_log" in authorities and "canon" not in authorities:
        warnings.append("run_log selected without canon; check for stale context risk")
    connector_counts = trace.get("connector_counts", {})
    if len(connector_counts) == 1 and len(cards) >= 4:
        only = next(iter(connector_counts))
        warnings.append(f"all selected cards came from one connector: {only}")
    return warnings
