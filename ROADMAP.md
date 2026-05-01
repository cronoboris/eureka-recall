# Eureka Roadmap

Eureka should become a stable read-only recall router for LLM agents. It should not become a memory database, a wiki, or a memory mutation product.

## Product North Star

Eureka can be safely placed before an agent turn.

That means it can select relevant context from existing stores, explain why it selected that context, avoid mutating source memory, and produce harness-ready output with predictable schemas.

## Non-negotiable Boundaries

- Read-only connectors by default and by design.
- No memory creation, update, deletion, or promotion in core.
- Retrieved cards are evidence, not instructions.
- Current user intent and current workspace state outrank stored memory.
- Traceability is a core feature, not debug garnish.

## v0.1: Safe MVP

- `activate`, `wrap`, `run`, `codex`, and `inspect` commands.
- Filesystem and LocalWiki connectors.
- Context cards, harness prompt, agent input, and retrieval trace outputs.
- Basic connector diversity, authority weights, and rejected-candidate inspection.
- CI on Python 3.10, 3.11, and 3.12.

## v0.2: Project Configuration And Safety

- `eureka init` to create `eureka.toml`.
- `.eurekaignore` support.
- Default ignores for dependency, build, cache, VCS, and Eureka output folders.
- File size limits and safer binary detection.
- Card content escaping for harness payloads.
- Secret redaction for common token, key, and password patterns.
- `eureka doctor` for connector, path, ignore, and permission checks.

## v0.3: Retrieval Quality

- BM25 or equivalent lexical ranking.
- Filename, path, title, and heading boosts.
- Markdown frontmatter parsing for project, tags, status, created, and updated metadata.
- Freshness scoring that is reflected in ranking, not only output.
- Duplicate suppression across connectors and authority levels.
- Token budget estimation for cards and bundles.
- Better Korean and mixed-case tokenization for developer docs.

## v0.4: Connector SDK

- Stable read-only connector interface.
- Connector health checks.
- Filesystem and LocalWiki as reference implementations.
- Markdown frontmatter connector behavior.
- SQLite FTS connector.
- Git history or Git notes connector.
- Connector authoring guide and fixture suite.

## v0.5: MCP Surface

- `eureka serve-mcp`.
- `eureka_activate` tool.
- `eureka_explain` tool.
- `eureka_preview` tool.
- Resources for latest cards, bundle, trace, and config.
- Security checks for resource access and source path validation.

## v0.6: Evaluation

- Golden fixtures for coding-agent scenarios.
- Precision@K, Recall@K, MRR, NDCG, token efficiency, latency, and safety pass rate.
- Mutation tests proving source stores are not modified.
- Regression tests for ranking and trace explanations.

## v1.0: Stable Developer Product

- Stable context card schema.
- Stable retrieval trace schema.
- Stable connector API.
- Stable CLI for installable use.
- Documented safety model.
- Published coding-agent demos.
- `pipx install eureka-recall` path documented and tested.

## Avoided Scope

- Built-in memory mutation or curation.
- A proprietary memory database.
- An agent platform.
- Default LLM summarization in the retrieval hot path.
- Broad product claims beyond context activation for existing stores.
