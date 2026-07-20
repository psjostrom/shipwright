# Claude Code Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Claude Code. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Claude Code 2.1.117 or newer with plugin skill discovery, Task/Agent subagents, and current-turn model/effort evidence. Probe the active version and tool schemas. A compatible newer release proceeds with a warning retained in controller preflight state and later reported or ingested according to the shared workflow. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

Accept either:

- active alias `opus` only when current runtime evidence resolves it to Claude Opus 4.7; or
- exact active model ID `claude-opus-4-7`.

Require effort rank `xhigh` or stronger.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

Unknown effort labels are not automatically stronger. An unresolved alias, future model, renamed model, or generic family label is not accepted until this reference explicitly allowlists it from first-party compatibility evidence.

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing resolved active model ID and effort.
2. A current-session `/status` or model-picker view containing the resolved model and effort; a user screenshot or verbatim status readout is acceptable because the user is authoritative for their active UI state.

Reject launch arguments, settings files, environment variables, requested overrides, task/agent names, and the unresolved word `opus`. Conflicting accepted sources are unverified.

On failure, stop before all Shipwright artifacts and say: select **Opus 4.7 / xhigh or stronger**, then provide new current-session evidence so the complete preflight can restart.

## Worker routing

| Shared task class | Claude Code normalized tier |
| --- | --- |
| Mechanical | Haiku |
| Ordinary | Sonnet / Medium |
| Integration | Sonnet / High |
| Critical | Opus / xhigh |

Resolve aliases to active model IDs before recording actual execution. Do not infer effort where the platform does not expose it.

Normalize resolved, allowlisted worker families in this order:

```text
Haiku < Sonnet < Opus
```

A child meets a requested tier only when **both** specified dimensions meet their floors: its normalized model-family rank is at least the requested family rank and, when the route specifies an effort floor, its normalized effort rank is at least that floor. Dimensions do not compensate for each other. For example, Opus/Medium fails a Sonnet/High request, while Sonnet/xhigh fails an Opus/xhigh request. The Haiku mechanical route intentionally has no effort floor; absent effort is accepted only for that route, while a reported unknown nonempty effort label remains unverified. For every other route, absent or unknown effort is unverified. An unresolved alias or unknown, generic, future, or unallowlisted family is always unverified. Apply the shared missing/conflicting-evidence transition rather than guessing a rank.

## Native dispatch and fallback

Use Claude Code's Task/Agent subagent operation when exposed. Inspect the live schema and pass explicit `model` and effort/reasoning fields only when those fields exist. Conceptually:

```text
Task/Agent({ subagent_type, prompt, model, effort })
```

The exact operation and field names come from the live tool schema; never fabricate unsupported arguments. Record requested model and effort before dispatch.

If Task/Agent does not expose both required selectors:

1. Verify the controller passed the Opus 4.7/xhigh gate.
2. Dispatch one fresh inherited child with task-local context.
3. Require child current-turn evidence.
4. Record `inherited correctness-first fallback` and the actual evidence.

An inherited Opus child is correctness-first over-provisioning, not Haiku/Sonnet execution and not adaptive cost routing. Never claim the requested cheaper tier ran.

## Child evidence

Require the child report to include:

```text
session/run ID:
resolved model ID:
effort:
evidence class: harness metadata | current-session status/model-picker
```

The controller independently reads the child session record when exposed and checks attribution. Requested selectors, aliases without resolution, and agent names remain non-evidence. Apply the shared child-evidence transition table and its one-fallback budget exactly.
