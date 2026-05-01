from pathlib import Path

from eureka_recall.config import load_config, load_eurekaignore, parse_minimal_toml, write_default_config
from eureka_recall.core import activate, build_agent_command, build_codex_command, render_agent_input
from eureka_recall.inspect import render_inspection_data
from eureka_recall.schemas import ActivationRequest


def test_activate_selects_workspace_context(tmp_path: Path) -> None:
    note = tmp_path / "style_reference.md"
    note.write_text("Current style rule: keep context cards short and sourced.", encoding="utf-8")

    result = activate(
        ActivationRequest(
            message="Need current style context cards",
            cwd=tmp_path,
            max_cards=3,
        )
    )

    assert result.cards
    assert result.cards[0].authority == "current_workspace"
    assert "style" in result.bundle_markdown.lower()


def test_activate_reads_localwiki_without_mutating_it(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    localwiki = tmp_path / "localwiki"
    canon = localwiki / "canon" / "Project"
    canon.mkdir(parents=True)
    source = canon / "Rules.md"
    source.write_text("# Rules\n\nEureka context cards must include source paths.", encoding="utf-8")

    before = source.read_text(encoding="utf-8")
    result = activate(
        ActivationRequest(
            message="Eureka context cards source paths",
            cwd=workspace,
            localwiki_root=localwiki,
            max_cards=3,
        )
    )
    after = source.read_text(encoding="utf-8")

    assert before == after
    assert any(card.authority == "canon" for card in result.cards)


def test_activate_balances_connectors(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for index in range(8):
        (workspace / f"note_{index}.md").write_text(
            "Eureka context activation connector design " * 5,
            encoding="utf-8",
        )
    localwiki = tmp_path / "localwiki"
    canon = localwiki / "canon" / "Project"
    canon.mkdir(parents=True)
    (canon / "Rules.md").write_text(
        "# Rules\n\n" + ("Eureka context activation must preserve connector diversity. " * 8),
        encoding="utf-8",
    )

    result = activate(
        ActivationRequest(
            message="Eureka context activation connector design",
            cwd=workspace,
            localwiki_root=localwiki,
            max_cards=5,
        )
    )

    connectors = {card.connector for card in result.cards}
    assert "filesystem" in connectors
    assert "localwiki" in connectors


def test_harness_prompt_marks_cards_as_evidence(tmp_path: Path) -> None:
    note = tmp_path / "memory.md"
    note.write_text("Eureka cards are evidence, not instructions.", encoding="utf-8")

    result = activate(
        ActivationRequest(
            message="Eureka evidence instructions",
            cwd=tmp_path,
            max_cards=2,
        )
    )

    assert "<eureka_context>" in result.harness_prompt
    assert "evidence, not instructions" in result.harness_prompt


def test_render_agent_input_combines_context_and_user_task(tmp_path: Path) -> None:
    note = tmp_path / "memory.md"
    note.write_text("Eureka can wrap a user task for a harness.", encoding="utf-8")
    message = "Use Eureka context before answering."

    result = activate(
        ActivationRequest(
            message=message,
            cwd=tmp_path,
            max_cards=2,
        )
    )
    agent_input = render_agent_input(result.harness_prompt, message)

    assert agent_input.startswith("<eureka_context>")
    assert "<user_task>" in agent_input
    assert message in agent_input
    assert agent_input.rstrip().endswith("</user_task>")


def test_build_agent_command_substitutes_agent_input_path(tmp_path: Path) -> None:
    agent_input = tmp_path / "agent_input.md"
    command = build_agent_command("cat {agent_input}", agent_input)

    assert str(agent_input) in command
    assert "{agent_input}" not in command


def test_build_agent_command_appends_path_when_placeholder_missing(tmp_path: Path) -> None:
    agent_input = tmp_path / "agent_input.md"
    command = build_agent_command("cat", agent_input)

    assert command.startswith("cat ")
    assert str(agent_input) in command


def test_build_codex_command_embeds_agent_input(tmp_path: Path) -> None:
    agent_input = tmp_path / "agent_input.md"
    agent_input.write_text("<user_task>\nhello from eureka\n</user_task>\n", encoding="utf-8")

    command = build_codex_command(
        agent_input,
        codex_bin="codex",
        extra_args=["--cd", str(tmp_path)],
    )

    assert command.startswith("codex exec ")
    assert "--cd" in command
    assert "hello from eureka" in command


def test_activation_trace_includes_inspection_fields(tmp_path: Path) -> None:
    note = tmp_path / "memory.md"
    note.write_text("Eureka inspection should explain selected and rejected cards.", encoding="utf-8")

    result = activate(
        ActivationRequest(
            message="Eureka inspection selected rejected cards",
            cwd=tmp_path,
            max_cards=1,
        )
    )

    trace = result.trace.to_dict()
    assert trace["connector_counts"]
    assert trace["authority_counts"]
    assert "top_rejected" in trace


def test_render_inspection_data_reports_counts_and_warnings() -> None:
    report = render_inspection_data(
        [
            {
                "connector": "filesystem",
                "authority": "current_workspace",
                "title": "README.md",
                "relevance": 3.0,
                "source": "/repo/README.md",
            }
        ],
        {
            "rejected_count": 2,
            "connectors": ["filesystem"],
            "queries": ["eureka"],
            "connector_counts": {"filesystem": 1},
            "authority_counts": {"current_workspace": 1},
            "top_rejected": [
                {
                    "connector": "localwiki",
                    "authority": "canon",
                    "title": "Rules",
                    "score": 1.0,
                    "source": "/wiki/Rules.md",
                }
            ],
        },
    )

    assert "selected: 1" in report
    assert "rejected: 2" in report
    assert "Top Rejected" in report
    assert "Rules" in report


def test_extract_terms_splits_camel_case() -> None:
    from eureka_recall.text import extract_terms

    terms = extract_terms("SessionSummaryEvidence")

    assert "sessionsummaryevidence" in terms
    assert "session" in terms
    assert "summary" in terms
    assert "evidence" in terms


def test_config_loads_workspace_and_localwiki_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "eureka.toml"
    config_path.write_text(
        """
[activation]
max_cards = 3

[sources.workspace]
include = ["**/*.md"]
exclude = ["secret/**"]
max_file_bytes = 123

[sources.localwiki]
enabled = true
root = "../localwiki"
""",
        encoding="utf-8",
    )

    config = load_config(config_path, tmp_path)

    assert config.max_cards == 3
    assert config.workspace.include == ["**/*.md"]
    assert config.workspace.exclude == ["secret/**"]
    assert config.workspace.max_file_bytes == 123
    assert config.localwiki.enabled
    assert config.localwiki.root == "../localwiki"


def test_write_default_config_refuses_to_overwrite(tmp_path: Path) -> None:
    config_path = tmp_path / "eureka.toml"
    write_default_config(config_path)

    assert "sources.workspace" in config_path.read_text(encoding="utf-8")
    try:
        write_default_config(config_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected FileExistsError")


def test_eurekaignore_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    (tmp_path / ".eurekaignore").write_text("\n# comment\nsecrets/**\n\n", encoding="utf-8")

    assert load_eurekaignore(tmp_path) == ["secrets/**"]


def test_minimal_toml_parser_supports_project_config() -> None:
    data = parse_minimal_toml(
        """
[activation]
max_cards = 3

[sources.workspace]
enabled = true
include = ["**/*.md", "**/*.py"]
"""
    )

    assert data["activation"]["max_cards"] == 3
    assert data["sources"]["workspace"]["enabled"] is True
    assert data["sources"]["workspace"]["include"] == ["**/*.md", "**/*.py"]


def test_filesystem_connector_respects_size_limit(tmp_path: Path) -> None:
    (tmp_path / "small.md").write_text("Eureka small visible token", encoding="utf-8")
    (tmp_path / "large.md").write_text("Eureka large hidden token " * 20, encoding="utf-8")

    result = activate(
        ActivationRequest(
            message="Eureka small large token",
            cwd=tmp_path,
            max_file_bytes=64,
        )
    )
    sources = [card.source for card in result.cards]

    assert any("small.md" in source for source in sources)
    assert not any("large.md" in source for source in sources)


def test_filesystem_connector_can_be_disabled(tmp_path: Path) -> None:
    (tmp_path / "memory.md").write_text("Eureka disabled workspace token", encoding="utf-8")

    result = activate(
        ActivationRequest(
            message="Eureka disabled workspace token",
            cwd=tmp_path,
            workspace_enabled=False,
        )
    )

    assert result.cards == []
