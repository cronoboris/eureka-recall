# Eureka Project Summary

## One-line Definition

Eureka is a read-only memory activation layer for LLM agents.

It selects the right context from existing memory stores and delivers it to an agent before the agent acts.

## Core Position

Eureka is not a RAG framework in the usual sense. It is not a memory database, not a wiki, and not an agent state platform.

It is a recall router:

```text
existing memory stores -> Eureka -> compact context cards -> LLM agent
```

## Problem

Tool-calling RAG depends on the main model realizing that context is missing. In long-running work, that is often too late. The model may not know that a project has canon rules, recent user decisions, rejected plot branches, coding conventions, or known failure patterns.

Static system prompts are also a poor fit. They are always present, grow stale, and easily become bloated.

Eureka sits between those extremes. It activates a small amount of relevant context before the main model begins, while leaving deeper retrieval to normal tools.

## Non-goals

- Do not write to source memory stores.
- Do not manage canon.
- Do not summarize sessions into permanent memory.
- Do not replace LocalWiki, Obsidian, Zep, mem0, Signet, or vector databases.
- Do not become a full agent harness.

## Target Users

- Local-first AI agent users.
- Coding agents that need project rules and prior decisions.
- Writers using structured project memory.
- Teams with existing knowledge stores that want better context selection without migrating storage.
- Agent framework builders who need a recall layer rather than another memory store.

## Main Abstractions

### MemoryConnector

A read-only adapter for one memory source. It can search, fetch, and report health. It cannot create, update, delete, or promote memory.

### MemoryCard

A normalized context unit selected from a connector. Cards carry source metadata, authority, relevance, freshness, and an activation reason.

### ActivationPolicy

The ranking and safety rules that decide which cards should be delivered.

### ActivationTrace

A debug artifact explaining which connectors were queried, what was selected, and why.

## Initial Connectors

- Filesystem connector: reads current workspace files.
- LocalWiki connector: reads `canon/`, `wiki/decisions/`, `wiki/failure-patterns/`, and `wiki/runs/`.

## Future Connectors

- Obsidian vault
- SQLite FTS
- vector databases
- Git history or notes
- MCP memory servers
- Signet
- mem0
- Zep / Graphiti

## MVP Success Criteria

- Given a user request and workspace path, Eureka emits useful context cards.
- The source memory stores remain untouched.
- Output includes a human-readable context bundle and machine-readable trace.
- Connector boundaries are clean enough to add a third connector without changing the core.

