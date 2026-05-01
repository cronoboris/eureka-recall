# Eureka

Eureka is a read-only recall router for LLM agents.

It does not store, edit, or manage memory. It selects relevant context from the memory systems you already use, ranks it by authority and relevance, and delivers compact context cards before an agent acts.

## Why

Most agent harnesses retrieve context only when the main model asks for a tool. That works for deliberate lookup, but it misses the kind of context that should naturally come to mind before work begins: current project rules, canon notes, recent decisions, failure patterns, and nearby files.

Eureka adds a thin memory activation layer in front of an agent harness.

```text
User request
  -> Eureka activation
  -> read-only connectors
  -> context cards
  -> main LLM or agent harness
```

## What Eureka Does

- Reads from existing memory stores through connectors.
- Selects context relevant to the current request and workspace.
- Normalizes results into context cards.
- Ranks cards by authority, relevance, freshness, and source type.
- Writes trace output that explains why context was selected.

## What Eureka Does Not Do

- It does not create memory.
- It does not update memory.
- It does not delete memory.
- It does not promote notes into canon.
- It does not replace a memory store, wiki, vector database, or agent platform.

Memory management belongs to your existing systems and human or agent curators. Eureka only activates what is already there.

## Early CLI

```bash
eureka activate \
  --message "Revise this chapter using the current style rules" \
  --cwd /path/to/project \
  --localwiki-root /path/to/localwiki \
  --out .eureka
```

To build a single harness-ready input file:

```bash
eureka wrap \
  --message "Revise this chapter using the current style rules" \
  --cwd /path/to/project \
  --localwiki-root /path/to/localwiki \
  --out .eureka
```

To build the input and immediately run a harness command:

```bash
eureka run \
  --message "Revise this chapter using the current style rules" \
  --cwd /path/to/project \
  --localwiki-root /path/to/localwiki \
  --out .eureka \
  --agent-cmd "cat {agent_input}"
```

`{agent_input}` is replaced with the generated `.eureka/agent_input.md` path. If the placeholder is omitted, Eureka appends the path as the final argument.

To run Codex CLI directly:

```bash
eureka codex \
  --message "Revise this chapter using the current style rules" \
  --cwd /path/to/project \
  --localwiki-root /path/to/localwiki \
  --codex-arg=--cd \
  --codex-arg=/path/to/project
```

Use `--dry-run` to print the generated Codex command without executing it.

Outputs:

```text
.eureka/context_cards.json
.eureka/context_bundle.md
.eureka/harness_prompt.md
.eureka/agent_input.md
.eureka/retrieval_trace.json
```

`harness_prompt.md` is the default payload to pass into an agent harness before the current user task. It labels selected cards as evidence, not instructions, so the harness can keep system and developer instructions above retrieved context.

`agent_input.md` combines `harness_prompt.md` with the current user task inside a `<user_task>` block.

## Design Principles

1. Read-only by default and by design.
2. Current user intent outranks stored memory.
3. Current workspace files outrank old logs.
4. Canon and approved project rules outrank candidate notes.
5. Small context cards beat large prompt dumps.
6. Every activated memory should carry a source and activation reason.

## Status

This repository is an initial scaffold. The first implementation focuses on:

- connector interface
- filesystem connector
- LocalWiki connector
- rule-based activation
- context card output
- harness-ready prompt output
- traceable CLI
