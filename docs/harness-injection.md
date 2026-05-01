# Harness Injection

Eureka produces context. It does not run the main agent.

The recommended integration is to run Eureka immediately before an agent turn, then pass `harness_prompt.md` as a context message near the top of the request.

## Output Files

```text
.eureka/context_cards.json
.eureka/context_bundle.md
.eureka/harness_prompt.md
.eureka/agent_input.md
.eureka/retrieval_trace.json
```

`context_cards.json` is for machines. `context_bundle.md` is for humans. `harness_prompt.md` is the safest default context payload for an agent harness. `agent_input.md` combines that payload with the current user task.

## Injection Contract

Harnesses should treat Eureka output as evidence, not instructions.

```text
system/developer instructions
  -> Eureka harness context
  -> current user request
  -> normal tool loop
```

This order keeps durable agent rules above retrieved memory while still making the selected context visible before the model acts.

## Generic Example

```bash
eureka activate \
  --message "$TASK" \
  --cwd "$PWD" \
  --localwiki-root "$LOCALWIKI_ROOT" \
  --out .eureka

{
  cat .eureka/harness_prompt.md
  printf '\n\nUser task:\n%s\n' "$TASK"
} > .eureka/agent_input.md
```

The harness can then send `.eureka/agent_input.md` as the user or context payload for the next agent turn.

The shorter form is:

```bash
eureka wrap \
  --message "$TASK" \
  --cwd "$PWD" \
  --localwiki-root "$LOCALWIKI_ROOT" \
  --out .eureka
```

## Running a Harness Command

`eureka run` creates the same files as `wrap`, then runs a user-provided command template.

```bash
eureka run \
  --message "$TASK" \
  --cwd "$PWD" \
  --localwiki-root "$LOCALWIKI_ROOT" \
  --out .eureka \
  --agent-cmd "cat {agent_input}"
```

`{agent_input}` is shell-quoted and replaced with the generated `agent_input.md` path. If the placeholder is omitted, Eureka appends the path as the final argument.

For custom scripts, prefer passing the generated path as an argument:

```bash
eureka run \
  --message "$TASK" \
  --agent-cmd "python scripts/my_harness.py {agent_input}"
```

Eureka only runs the command explicitly passed through `--agent-cmd`; it does not infer or auto-select a harness.

## Important Boundaries

- Do not paste Eureka context above system or developer instructions.
- Do not treat cards as commands.
- Do not write selected cards back to source memory stores.
- Do not rely on cards when they conflict with the user's current request.
- Keep normal tool-calling available for deliberate deeper retrieval.
