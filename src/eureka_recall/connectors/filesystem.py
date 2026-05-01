from __future__ import annotations

from pathlib import Path

from eureka_recall.connectors.base import MemoryConnector
from eureka_recall.schemas import ActivationRequest, MemoryHit
from eureka_recall.text import extract_terms, score_text, snippet_for


class FilesystemConnector(MemoryConnector):
    name = "filesystem"

    def __init__(self, max_files: int = 200) -> None:
        self.max_files = max_files

    def search(self, request: ActivationRequest, queries: list[str]) -> list[MemoryHit]:
        if not request.cwd.exists():
            return []

        terms = extract_terms(" ".join([request.message, *queries]))
        hits: list[MemoryHit] = []
        for path in self._iter_text_files(request.cwd):
            text = _safe_read(path)
            if not text:
                continue
            score = score_text(path.name + "\n" + text, terms)
            if score <= 0:
                continue
            hits.append(
                MemoryHit(
                    id=f"filesystem:{path}",
                    connector=self.name,
                    source_path=path,
                    title=path.name,
                    snippet=snippet_for(text, terms),
                    authority="current_workspace",
                    score=score,
                )
            )
        return hits

    def _iter_text_files(self, root: Path):
        ignored = {".git", ".venv", "__pycache__", ".pytest_cache"}
        seen = 0
        for path in root.rglob("*"):
            if seen >= self.max_files:
                break
            if any(part in ignored or part.startswith(".eureka") for part in path.parts):
                continue
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".txt", ".py", ".toml", ".json", ".yaml", ".yml"}:
                continue
            seen += 1
            yield path


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
