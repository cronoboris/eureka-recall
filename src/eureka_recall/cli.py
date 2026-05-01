from __future__ import annotations

import argparse
import json
from pathlib import Path

from eureka_recall.config import load_config, load_eurekaignore, write_default_config
from eureka_recall.core import (
    activate,
    build_agent_command,
    build_codex_command,
    render_agent_input,
    run_agent_command,
)
from eureka_recall.inspect import render_inspection
from eureka_recall.schemas import ActivationRequest, ActivationResult


def main() -> None:
    parser = argparse.ArgumentParser(prog="eureka")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a starter eureka.toml")
    init_parser.add_argument("--cwd", default=".")
    init_parser.add_argument("--config", default="eureka.toml")

    activate_parser = subparsers.add_parser("activate", help="select read-only context cards")
    activate_parser.add_argument("--message", required=True)
    activate_parser.add_argument("--cwd")
    activate_parser.add_argument("--localwiki-root")
    activate_parser.add_argument("--max-cards", type=int)
    activate_parser.add_argument("--out", default=".eureka")
    activate_parser.add_argument("--config")

    wrap_parser = subparsers.add_parser("wrap", help="build a harness-ready agent input file")
    wrap_parser.add_argument("--message", required=True)
    wrap_parser.add_argument("--cwd")
    wrap_parser.add_argument("--localwiki-root")
    wrap_parser.add_argument("--max-cards", type=int)
    wrap_parser.add_argument("--out", default=".eureka")
    wrap_parser.add_argument("--config")

    run_parser = subparsers.add_parser("run", help="build context and run an agent command")
    run_parser.add_argument("--message", required=True)
    run_parser.add_argument("--cwd")
    run_parser.add_argument("--localwiki-root")
    run_parser.add_argument("--max-cards", type=int)
    run_parser.add_argument("--out", default=".eureka")
    run_parser.add_argument("--config")
    run_parser.add_argument(
        "--agent-cmd",
        required=True,
        help="Command template. Use {agent_input} for the generated input path.",
    )

    codex_parser = subparsers.add_parser("codex", help="build context and run Codex CLI")
    codex_parser.add_argument("--message", required=True)
    codex_parser.add_argument("--cwd")
    codex_parser.add_argument("--localwiki-root")
    codex_parser.add_argument("--max-cards", type=int)
    codex_parser.add_argument("--out", default=".eureka")
    codex_parser.add_argument("--config")
    codex_parser.add_argument("--codex-bin", default="codex")
    codex_parser.add_argument("--mode", choices=["exec"], default="exec")
    codex_parser.add_argument("--codex-arg", action="append", default=[])
    codex_parser.add_argument("--dry-run", action="store_true")

    inspect_parser = subparsers.add_parser("inspect", help="inspect a previous Eureka output folder")
    inspect_parser.add_argument("--out", default=".eureka")

    args = parser.parse_args()
    if args.command == "init":
        cwd = Path(args.cwd).expanduser().resolve()
        path = Path(args.config).expanduser()
        if not path.is_absolute():
            path = cwd / path
        write_default_config(path)
        print(f"Wrote {path}")
        return

    if args.command == "inspect":
        print(render_inspection(Path(args.out).expanduser().resolve()), end="")
        return

    if args.command in {"activate", "wrap", "run", "codex"}:
        request = build_request(args)
        result = activate(request)
        out = Path(args.out).expanduser().resolve()
        write_activation_outputs(result, out)
        if args.command == "activate":
            print(f"Wrote {len(result.cards)} context cards to {out}")
            return

        agent_input_path = write_agent_input(result, args.message, out)
        if args.command == "wrap":
            print(f"Wrote harness input with {len(result.cards)} context cards to {out}")
            return

        if args.command == "codex":
            command = build_codex_command(
                agent_input_path,
                mode=args.mode,
                codex_bin=args.codex_bin,
                extra_args=args.codex_arg,
            )
            if args.dry_run:
                print(command)
                return
        else:
            command = build_agent_command(args.agent_cmd, agent_input_path)
        print(f"Running: {command}", flush=True)
        raise SystemExit(run_agent_command(command))


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


def write_agent_input(result: ActivationResult, message: str, out: Path) -> Path:
    agent_input = render_agent_input(result.harness_prompt, message)
    path = out / "agent_input.md"
    path.write_text(agent_input, encoding="utf-8")
    return path


def build_request(args: argparse.Namespace) -> ActivationRequest:
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    if args.cwd:
        base_cwd = Path(args.cwd).expanduser().resolve()
    elif config_path:
        base_cwd = config_path.parent
    else:
        base_cwd = Path(".").resolve()
    config = load_config(config_path, base_cwd)
    cwd = base_cwd
    if args.cwd is None and config.workspace.root:
        cwd = _resolve_optional_path(config.workspace.root, base_cwd) or base_cwd
    localwiki_root = _resolve_optional_path(args.localwiki_root, cwd)
    if localwiki_root is None and config.localwiki.enabled and config.localwiki.root:
        localwiki_root = _resolve_optional_path(config.localwiki.root, cwd)
    exclude_globs = [*config.workspace.exclude, *load_eurekaignore(cwd)]
    return ActivationRequest(
        message=args.message,
        cwd=cwd,
        localwiki_root=localwiki_root,
        max_cards=args.max_cards if args.max_cards is not None else config.max_cards,
        include_globs=config.workspace.include,
        exclude_globs=exclude_globs,
        max_file_bytes=config.workspace.max_file_bytes,
        workspace_enabled=config.workspace.enabled,
    )


def _resolve_optional_path(value: str | None, cwd: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


if __name__ == "__main__":
    main()
