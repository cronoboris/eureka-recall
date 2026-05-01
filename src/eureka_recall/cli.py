from __future__ import annotations

import argparse
import json
from pathlib import Path

from eureka_recall.core import activate, render_agent_input
from eureka_recall.schemas import ActivationRequest, ActivationResult


def main() -> None:
    parser = argparse.ArgumentParser(prog="eureka")
    subparsers = parser.add_subparsers(dest="command", required=True)

    activate_parser = subparsers.add_parser("activate", help="select read-only context cards")
    activate_parser.add_argument("--message", required=True)
    activate_parser.add_argument("--cwd", default=".")
    activate_parser.add_argument("--localwiki-root")
    activate_parser.add_argument("--max-cards", type=int, default=8)
    activate_parser.add_argument("--out", default=".eureka")

    wrap_parser = subparsers.add_parser("wrap", help="build a harness-ready agent input file")
    wrap_parser.add_argument("--message", required=True)
    wrap_parser.add_argument("--cwd", default=".")
    wrap_parser.add_argument("--localwiki-root")
    wrap_parser.add_argument("--max-cards", type=int, default=8)
    wrap_parser.add_argument("--out", default=".eureka")

    args = parser.parse_args()
    if args.command in {"activate", "wrap"}:
        request = ActivationRequest(
            message=args.message,
            cwd=Path(args.cwd).expanduser().resolve(),
            localwiki_root=Path(args.localwiki_root).expanduser().resolve()
            if args.localwiki_root
            else None,
            max_cards=args.max_cards,
        )
        result = activate(request)
        out = Path(args.out).expanduser().resolve()
        write_activation_outputs(result, out)
        if args.command == "wrap":
            agent_input = render_agent_input(result.harness_prompt, args.message)
            (out / "agent_input.md").write_text(agent_input, encoding="utf-8")
            print(f"Wrote harness input with {len(result.cards)} context cards to {out}")
        else:
            print(f"Wrote {len(result.cards)} context cards to {out}")


def write_activation_outputs(result: ActivationResult, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "context_bundle.md").write_text(result.bundle_markdown, encoding="utf-8")
    (out / "harness_prompt.md").write_text(result.harness_prompt, encoding="utf-8")
    (out / "context_cards.json").write_text(
        json.dumps([card.to_dict() for card in result.cards], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "retrieval_trace.json").write_text(
        json.dumps(result.trace.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
