from pathlib import Path

from eureka_recall.core import activate
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
    source.write_text("# Rules\n\nContext cards must include source paths.", encoding="utf-8")

    before = source.read_text(encoding="utf-8")
    result = activate(
        ActivationRequest(
            message="context cards source paths",
            cwd=workspace,
            localwiki_root=localwiki,
            max_cards=3,
        )
    )
    after = source.read_text(encoding="utf-8")

    assert before == after
    assert any(card.authority == "canon" for card in result.cards)

