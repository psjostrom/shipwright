# Codex Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Codex. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Codex CLI 0.139.0 or newer, or a Codex desktop runtime with equivalent plugin discovery, Agent Skills, multi-agent dispatch, and current-turn metadata. Probe the actual harness/version and tool schemas; do not infer capabilities from documentation or configuration alone. A compatible newer release proceeds with a warning retained in controller preflight state and later reported or ingested according to the shared workflow. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

### Model floor (hard gate)

Require a resolved Sol model at version `5.6` or newer.

Accept an active model only when current runtime evidence resolves it to a concrete Sol model ID carrying a version, then compare that version numerically against the `5.6` floor. The version passes when its major version is greater than `5`, or when its major version equals `5` and its minor version is at least `6`. So `gpt-5.6-sol` and `gpt-5.7-sol` pass via the minor comparison, while `gpt-6-sol` or `gpt-6.0-sol` passes via the higher-major comparison. Capability or effort suffixes on the model ID do not affect the version comparison.

A Sol version at or above the floor is accepted without editing this reference; record it as newer than the last behaviorally tested version. Reject a non-Sol family, a Sol version below the floor, and any evidence that does not resolve to a concrete versioned Sol model ID — including generic labels such as `GPT-5`, bare family labels, and unresolved display names.

### Recommended effort (disclosed assumption, not a precondition)

Recommended controller effort rank is `high` or stronger. Recommended controller effort is not a precondition and is never a hard gate.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

Unknown effort labels are not automatically stronger. Record resolved effort when an accepted evidence class provides it; otherwise record `unverifiable`. Known effort below `high` still proceeds — record the shortfall as `below recommended`. Never stop solely because controller effort is missing, weak, or unverifiable. Disclose the controller effort evidence state per the shared `SKILL.md` rule: ledger always; completion report and authorized PR body only when resolved or `below recommended` (suppress `unverifiable` from user-facing text); PR disclosure still yields to repository rules that forbid AI-attribution or tooling references.

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing resolved active model ID and, when present, effort.
2. A current-session status/model-picker view containing the model and, when present, effort; a user screenshot or verbatim status readout is acceptable because the user is authoritative for their active UI state.
3. A local `turn_context` record whose thread ID matches the active Codex thread and whose current turn contains the model and, when present, effort.

Model and effort may come from the same source or be composed across accepted sources for the same controller turn. Resolved model ID without effort proves the model floor only and does not invent effort.

Reject launch arguments, config files, environment variables, requested overrides, task/agent/profile names, unmatched thread records, and generic labels such as `GPT-5`. Conflicting accepted sources are unverified.

On model-floor failure, stop before all Shipwright artifacts and say: select **GPT-5.6 Sol or newer**, then provide new current-session evidence so the complete preflight can restart.

## Worker routing

| Shared task class | Codex normalized tier |
| --- | --- |
| Mechanical | Luna / Medium |
| Ordinary | Terra / Medium |
| Integration | Terra / High |
| Critical | Sol / High |

Treat the exact observed model IDs for Luna, Terra, and Sol as the platform's current IDs only after the harness exposes them. Compare observed family and effort to the table; do not invent an ID from a display label.

Normalize the allowlisted worker families in this order:

```text
Luna < Terra < Sol
```

A child meets a requested tier only when **both** dimensions meet their floors: its normalized model-family rank is at least the requested family rank and its normalized effort rank is at least the requested effort rank. Dimensions do not compensate for each other. For example, Sol/Medium fails a Terra/High request, while Terra/xhigh passes it and records the stronger-effort cost deviation. An unknown, generic, future, or unallowlisted model family and an unknown or absent effort label are unverified, not stronger. Apply the shared missing/conflicting-evidence transition rather than guessing a rank.

## Native dispatch and fallback

When available, dispatch with the Codex collaboration `spawn_agent` operation. The commonly exposed generic shape is:

```text
spawn_agent({ task_name, message, fork_turns })
```

Inspect the live tool schema. Supply explicit model/profile and effort fields only when that schema actually exposes them. If it does, request the mapped tier and record the exact request before dispatch.

The current generic `spawn_agent` interface may omit model and effort selection. In that case:

1. Verify the controller passed the Sol `5.6` or newer model floor.
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
