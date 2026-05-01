from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from eureka_recall.connectors.base import MemoryConnector
from eureka_recall.schemas import ActivationRequest, MemoryHit
from eureka_recall.text import extract_terms, score_text, snippet_for


DEFAULT_INCLUDES = ["**/*.md", "**/*.txt", "**/*.py", "**/*.toml", "**/*.json", "**/*.yaml", "**/*.yml"]
DEFAULT_EXCLUDES = [
    ".git/**",
    ".venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    ".eureka*/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    "*.egg-info/**",
]


class FilesystemConnector(MemoryConnector):
    name = "filesystem"

    def __init__(self, max_files: int = 200) -> None:
        self.max_files = max_files

    def search(self, request: ActivationRequest, queries: list[str]) -> list[MemoryHit]:
        if not request.workspace_enabled:
            return []
        if not request.cwd.exists():
            return []

        terms = extract_terms(" ".join([request.message, *queries]))
        hits: list[MemoryHit] = []
        include_globs = request.include_globs or DEFAULT_INCLUDES
        exclude_globs = request.exclude_globs or DEFAULT_EXCLUDES
        for path in self._iter_text_files(
            request.cwd,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            max_file_bytes=request.max_file_bytes,
        ):
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

    def _iter_text_files(
        self,
        root: Path,
        *,
        include_globs: list[str],
        exclude_globs: list[str],
        max_file_bytes: int,
    ):
        seen = 0
        for path in root.rglob("*"):
            if seen >= self.max_files:
                break
            if _matches_any(path, root, exclude_globs):
                continue
            if not path.is_file():
                continue
            if path.stat().st_size > max_file_bytes:
                continue
            if not _matches_any(path, root, include_globs):
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


def _matches_any(path: Path, root: Path, patterns: list[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(_matches_pattern(rel, path.name, pattern) for pattern in patterns)


def _matches_pattern(rel: str, name: str, pattern: str) -> bool:
    if fnmatch(rel, pattern) or fnmatch(name, pattern):
        return True
    if pattern.startswith("**/") and fnmatch(rel, pattern[3:]):
        return True
    return False
