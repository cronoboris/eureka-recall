from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


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

DEFAULT_INCLUDES = ["**/*.md", "**/*.txt", "**/*.py", "**/*.toml", "**/*.json", "**/*.yaml", "**/*.yml"]

DEFAULT_CONFIG = """[project]
name = "eureka-project"

[activation]
max_cards = 8

[sources.workspace]
enabled = true
root = "."
include = ["**/*.md", "**/*.txt", "**/*.py", "**/*.toml", "**/*.json", "**/*.yaml", "**/*.yml"]
exclude = [".git/**", ".venv/**", "__pycache__/**", ".pytest_cache/**", ".mypy_cache/**", ".ruff_cache/**", ".eureka*/**", "node_modules/**", "dist/**", "build/**", "*.egg-info/**"]
max_file_bytes = 262144

[sources.localwiki]
enabled = false
root = ""
"""


@dataclass(frozen=True)
class WorkspaceSourceConfig:
    enabled: bool = True
    root: str = "."
    include: list[str] = field(default_factory=lambda: list(DEFAULT_INCLUDES))
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    max_file_bytes: int = 262_144


@dataclass(frozen=True)
class LocalWikiSourceConfig:
    enabled: bool = False
    root: str | None = None


@dataclass(frozen=True)
class EurekaConfig:
    project_name: str = "eureka-project"
    max_cards: int = 8
    workspace: WorkspaceSourceConfig = field(default_factory=WorkspaceSourceConfig)
    localwiki: LocalWikiSourceConfig = field(default_factory=LocalWikiSourceConfig)


def default_config_path(cwd: Path) -> Path:
    return cwd / "eureka.toml"


def load_config(path: Path | None, cwd: Path) -> EurekaConfig:
    config_path = path or default_config_path(cwd)
    if not config_path.exists():
        return EurekaConfig()
    text = config_path.read_text(encoding="utf-8")
    data = tomllib.loads(text) if tomllib else parse_minimal_toml(text)
    return parse_config(data)


def parse_config(data: dict[str, Any]) -> EurekaConfig:
    project = data.get("project", {})
    activation = data.get("activation", {})
    sources = data.get("sources", {})
    workspace_data = sources.get("workspace", {})
    localwiki_data = sources.get("localwiki", {})
    workspace = WorkspaceSourceConfig(
        enabled=bool(workspace_data.get("enabled", True)),
        root=str(workspace_data.get("root", ".")),
        include=_list_or_default(workspace_data.get("include"), DEFAULT_INCLUDES),
        exclude=_list_or_default(workspace_data.get("exclude"), DEFAULT_EXCLUDES),
        max_file_bytes=int(workspace_data.get("max_file_bytes", 262_144)),
    )
    localwiki_root = localwiki_data.get("root") or None
    localwiki = LocalWikiSourceConfig(
        enabled=bool(localwiki_data.get("enabled", False)),
        root=str(localwiki_root) if localwiki_root else None,
    )
    return EurekaConfig(
        project_name=str(project.get("name", "eureka-project")),
        max_cards=int(activation.get("max_cards", 8)),
        workspace=workspace,
        localwiki=localwiki,
    )


def write_default_config(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    path.write_text(DEFAULT_CONFIG, encoding="utf-8")


def load_eurekaignore(cwd: Path) -> list[str]:
    path = cwd / ".eurekaignore"
    if not path.exists():
        return []
    patterns: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def parse_minimal_toml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] = data
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = data
            for part in line[1:-1].split("."):
                current = current.setdefault(part, {})
            continue
        if "=" not in line:
            continue
        key, raw_value = [part.strip() for part in line.split("=", 1)]
        current[key] = _parse_value(raw_value)
    return data


def _parse_value(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_value(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        return value


def _list_or_default(value: Any, default: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return list(default)
