# Codex Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Codex. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Codex CLI 0.139.0 or newer, or a Codex desktop runtime with equivalent plugin discovery, Agent Skills, multi-agent dispatch, and current-turn metadata. Probe the actual harness/version and tool schemas; do not infer capabilities from documentation or configuration alone. A compatible newer release proceeds with a warning in the ledger. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

Accept only exact active model ID `gpt-5.6-sol` with effort rank `high` or stronger.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

Unknown effort labels are not automatically stronger. A future model, renamed model, or generic family label is not accepted until this reference explicitly allowlists it from first-party compatibility evidence.

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing exact model ID and effort.
2. A current-session status/model-picker view containing both values; a user screenshot or verbatim status readout is acceptable because the user is authoritative for their active UI state.
3. A local `turn_context` record whose thread ID matches the active Codex thread and whose current turn contains both values.

Reject launch arguments, config files, environment variables, requested overrides, task/agent/profile names, unmatched thread records, and generic labels such as `GPT-5`. Conflicting accepted sources are unverified.

On failure, stop before all Shipwright artifacts and say: select **GPT-5.6 Sol / High or stronger**, then provide new current-session evidence so the complete preflight can restart.

## Worker routing

| Shared task class | Codex normalized tier |
| --- | --- |
| Mechanical | Luna / Medium |
| Ordinary | Terra / Medium |
| Integration | Terra / High |
| Critical | Sol / High |

Treat the exact observed model IDs for Luna, Terra, and Sol as the platform's current IDs only after the harness exposes them. Compare observed family and effort to the table; do not invent an ID from a display label.

## Native dispatch and fallback

When available, dispatch with the Codex collaboration `spawn_agent` operation. The commonly exposed generic shape is:

```text
spawn_agent({ task_name, message, fork_turns })
```

Inspect the live tool schema. Supply explicit model/profile and effort fields only when that schema actually exposes them. If it does, request the mapped tier and record the exact request before dispatch.

The current generic `spawn_agent` interface may omit model and effort selection. In that case:

1. Verify the controller passed the Sol/High gate.
2. Dispatch one fresh child with `fork_turns: "none"` when sufficient task-local files exist; otherwise pass only the minimum recent context.
3. Require child current-turn evidence.
4. Record `inherited correctness-first fallback` and the actual evidence.

An inherited Sol child is correctness-first over-provisioning, not Luna/Terra execution and not adaptive cost routing. Never describe it as a successful cheaper-model choice.

## Child evidence

Require the child report to include:

```text
thread ID:
model ID:
effort:
evidence class: harness metadata | current-session view | matching-thread turn_context
```

The controller independently reads the child turn/session record when exposed and checks thread attribution. Requested selectors and agent names remain non-evidence. Apply the shared child-evidence transition table and its one-fallback budget exactly.
