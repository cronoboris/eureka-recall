# Configuration

Eureka can run without a config file. If `eureka.toml` exists in the working directory, Eureka reads it automatically. Pass `--config` to use a different file.

Create a starter config:

```bash
eureka init --cwd .
```

## Example

```toml
[project]
name = "my-agent-project"

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
```

CLI arguments override config values where both are provided. If `--cwd` is omitted, `[sources.workspace].root` is used as the workspace root.

## Ignore Rules

Eureka also reads `.eurekaignore` from the workspace root. Each non-empty, non-comment line is appended to the workspace exclude list.

```gitignore
secrets/**
private-notes/**
*.pem
```

Eureka's filesystem connector is read-only. Ignore rules only affect what files Eureka may read and select as context cards.
