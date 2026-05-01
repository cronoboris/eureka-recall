from pathlib import Path

from eureka_recall.core import activate, render_agent_input
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


def test_activate_reads_localwiki_without_writing_to_it(tmp_path: Path) -> None:
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
