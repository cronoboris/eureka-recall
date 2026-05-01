from __future__ import annotations

from pathlib import Path

from eureka_recall.connectors.base import MemoryConnector
from eureka_recall.schemas import ActivationRequest, MemoryHit
from eureka_recall.text import extract_terms, has_specific_match, score_text, snippet_for


class LocalWikiConnector(MemoryConnector):
    name = "localwiki"

    authority_by_dir = {
        "canon": "canon",
        "decisions": "decision",
        "failure-patterns": "failure_pattern",
        "runs": "run_log",
    }

    def search(self, request: ActivationRequest, queries: list[str]) -> list[MemoryHit]:
        if request.localwiki_root is None or not request.localwiki_root.exists():
            return []

        roots = [
            request.localwiki_root / "canon",
            request.localwiki_root / "wiki" / "decisions",
            request.localwiki_root / "wiki" / "failure-patterns",
            request.localwiki_root / "wiki" / "runs",
        ]
        terms = extract_terms(" ".join([request.message, *queries]))
        hits: list[MemoryHit] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*.md"):
                text = _safe_read(path)
                haystack = path.name + "\n" + text
                if not has_specific_match(haystack, terms):
                    continue
                score = score_text(haystack, terms)
                if score <= 0:
                    continue
                authority = self._authority_for(path)
                hits.append(
                    MemoryHit(
                        id=f"localwiki:{path.relative_to(request.localwiki_root)}",
                        connector=self.name,
                        source_path=path,
                        title=_title_for(path, text),
                        snippet=snippet_for(text, terms),
                        authority=authority,
                        freshness=_freshness_for(path, text),
                        score=score,
                    )
                )
        return hits

    def _authority_for(self, path: Path) -> str:
        parts = set(path.parts)
        for marker, authority in self.authority_by_dir.items():
            if marker in parts:
                return authority
        return "candidate"


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _title_for(path: Path, text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _freshness_for(path: Path, text: str) -> str | None:
    for line in text.splitlines()[:20]:
        if line.startswith("updated:") or line.startswith("created:"):
            return line.split(":", 1)[1].strip()
    return None
