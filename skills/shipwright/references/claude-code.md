# Claude Code Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Claude Code. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Claude Code 2.1.117 or newer with plugin skill discovery, Task/Agent subagents, and current-turn model/effort evidence. Probe the active version and tool schemas. A compatible newer release proceeds with a warning retained in controller preflight state and later reported or ingested according to the shared workflow. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

### Model floor (hard gate)

Require a resolved Opus model at version `4.6` or newer.

Accept an active model only when current runtime evidence resolves it to a concrete Opus model ID carrying a version, then compare that version numerically against the `4.6` floor. The version passes when its major version is greater than `4`, or when its major version equals `4` and its minor version is at least `6`. So `claude-opus-4-6` and `claude-opus-4-7` pass via the minor comparison, while `claude-opus-5` passes via the higher-major comparison. A context-size suffix such as `[1m]` describes the context window, not capability, and does not affect the comparison.

An Opus version at or above the floor is accepted without editing this reference; record it as newer than the last behaviorally tested version. Reject a non-Opus family, an Opus version below the floor, and any evidence that does not resolve to a concrete versioned model ID — including the unresolved word `opus`, a bare family label, and a generic capability label.

### Recommended effort (disclosed assumption, not a precondition)

Recommended controller effort rank is `xhigh` or stronger. Recommended controller effort is not a precondition and is never a hard gate.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

Unknown effort labels are not automatically stronger. Record resolved effort when an accepted evidence class provides it; otherwise record `unverifiable`. Known effort below `xhigh` still proceeds — record the shortfall as `below recommended`. Never stop solely because controller effort is missing, weak, or unverifiable. Disclose the controller effort evidence state per the shared `SKILL.md` rule (completion report and ledger always; authorized PR body unless repository instructions forbid AI-attribution or tooling references in user-facing text).

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing resolved active model ID and, when present, effort.
2. A current-session `/status` or model-picker view containing the resolved model and, when present, effort; a user screenshot or verbatim status readout is acceptable because the user is authoritative for their active UI state.

Model and effort may come from the same source or be composed across accepted sources for the same controller turn. Harness metadata commonly resolves the model without effort; that proves the model floor only and does not invent effort.

Reject launch arguments, settings files, environment variables, requested overrides, task/agent names, and the unresolved word `opus`. Conflicting accepted sources are unverified.

On model-floor failure, stop before all Shipwright artifacts and say: select **Opus 4.6 or newer**, then provide new current-session evidence so the complete preflight can restart.

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

A child meets a requested tier only when its normalized model-family rank is at least the requested family rank and, when the route specifies an effort floor that this harness can request or attribute, its normalized effort rank is at least that floor. Dimensions do not compensate for each other. For example, when both dimensions are required, Opus/Medium fails a Sonnet/High request, while Sonnet/xhigh fails an Opus/xhigh request. Family alone governs worker routing; version comparison applies only at the controller gate. The Haiku mechanical route intentionally has no effort floor. Accept attributable model-family evidence without effort only when the selected route has no effort floor, or when this reference explicitly waives the effort dimension for that route — see Native dispatch. When an effort selector exists or child effort is attributable, absent or unknown effort is unverified for every route that defines an effort floor. A reported unknown nonempty effort label remains unverified in every schema shape. An unresolved alias or unknown, generic, or unallowlisted family is always unverified — do not treat a newer allowlisted Haiku, Sonnet, or Opus worker as unverified merely for being newer than the last tested version. Apply the shared missing/conflicting-evidence transition rather than guessing a rank.

## Native dispatch and fallback

Use Claude Code's Task/Agent subagent operation when exposed. Inspect the live schema and pass the route's explicit `model` whenever a usable model selector exists. Pass an effort/reasoning request only when that selector exists and the route specifies an effort floor. Conceptually:

```text
Task/Agent({ subagent_type, prompt, model, effort })
```

The exact operation and field names come from the live tool schema; never fabricate unsupported arguments. Record the requested model and any requested effort before dispatch, then validate the child's actual current-turn model and effort evidence.

When a usable model selector exists but no effort selector exists:

1. Dispatch the explicitly selected route model without an effort field.
2. Record the platform limitation: adaptive effort routing is unavailable until the live schema exposes an effort selector or child effort becomes attributable through an accepted evidence class.
3. Validate attributable model-family evidence against the route floor. Accept attributable model-family evidence without effort only when the selected route has no effort floor, or when this reference explicitly waives the effort dimension for that route because child effort cannot be requested or observed. This reference waives child effort for Ordinary, Integration, and Critical routes only when the schema has no effort selector and accepted child records do not attribute effort; Haiku mechanical already has no effort floor. If effort is attributable, validate it against the route floor even when the selector is absent. A nonempty unknown effort label remains unverified. Child effort is waived here because the Agent tool has no effort selector and child effort is not attributable — requiring proof of a dimension the controller could never set or observe is incoherent. Controller recommended effort is a different rule: it is settable by the user but often unobservable from harness metadata, so the shared product rule records and discloses it rather than hard-stopping. Do not treat the child waiver and the controller disclosure rule as the same mechanism.
4. Do not enter the inherited-controller fallback solely because effort is absent. Use that fallback only for weaker, conflicting, missing, or unattributable model-family evidence, per the shared child-evidence transition.
5. If a later probe finds a usable effort selector or attributable child effort evidence, restore the route effort floors and validate both dimensions.

Use selector-absence fallback only when Task/Agent exposes no usable model selector, whether or not it exposes an effort selector:

1. Verify the controller passed the Opus 4.6-or-newer model floor.
2. Dispatch one fresh inherited child with task-local context.
3. Require child current-turn evidence.
4. Record `inherited correctness-first fallback` and the actual evidence.

The same inherited-controller fallback is available once when an explicit dispatch is rejected by the shared child-evidence transition. An inherited Opus child is correctness-first over-provisioning, not Haiku/Sonnet execution and not adaptive cost routing. Never claim the requested cheaper tier ran.

## Child evidence

Claude Code's subagent tooling prevents children from writing report files. Require the report as the child's final message text and have the controller persist it to the dispatch's artifact directory. Do not instruct a child to write its own report file — the instruction will fail and the child will improvise.

Require the child report to include:

```text
session/run ID:
resolved model ID:
effort: <rank | absent>
evidence class: harness metadata | current-session status/model-picker
```

When the live schema has no effort selector and child effort is not attributable, record `effort: absent` and the platform limitation; do not invent an effort rank. Children will keep offering environment-variable-sourced effort; expect it, reject it, and do not treat the offer as a red flag about the child's competence. The controller independently reads the child session record when exposed and checks attribution. Requested selectors, aliases without resolution, and agent names remain non-evidence. Apply the shared child-evidence transition table and its one-fallback budget exactly.
