# Cursor Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Cursor. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Cursor with plugin skill discovery, Task subagents, and current-turn model/effort evidence. Probe the active version and tool schemas; do not infer capabilities from documentation or configuration alone. A compatible newer release proceeds with a warning retained in controller preflight state and later reported or ingested according to the shared workflow. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

Superpowers 6.1.1 or newer must be installed and discoverable as a separate Cursor plugin. Shipwright does not vendor Superpowers. Accept an installed-plugin inventory or resolved paths proving one versioned Superpowers package root.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

### Model floor (hard gate)

Require a resolved Grok model at version `4.5` or newer.

Accept an active model only when current runtime evidence resolves it to the Grok family with a concrete version, then compare that version numerically against the `4.5` floor. The version passes when its major version is greater than `4`, or when its major version equals `4` and its minor version is at least `5`. So `Grok 4.5`, `cursor-grok-4.5`, and `grok-4.5` pass via the minor comparison, while `Grok 5` / `cursor-grok-5` pass via the higher-major comparison. Effort tokens encoded in a slug (for example `-high`) are not part of the version comparison.

Examples of acceptable evidence forms at or above the floor, not an exhaustive invent-list: harness/display labels such as `Cursor Grok 4.5` or `powered by Cursor Grok 4.5`, and IDs/slugs such as `cursor-grok-4.5` or `grok-4.5`. A Grok version at or above the floor is accepted without editing this reference; record it as newer than the last behaviorally tested version.

Reject a non-Grok family, a Grok version below the floor, and any evidence that does not resolve to a versioned Grok family ID — including the bare word `Grok`, Composer, Auto, Balance, and generic capability labels.

### Recommended effort (disclosed assumption, not a precondition)

Recommended controller effort rank is `high` or stronger. Recommended controller effort is not a precondition and is never a hard gate.

Examples of acceptable effort evidence forms when present: effort-bearing slug tokens such as `cursor-grok-4.5-high` or `cursor-grok-4.5-high-fast` when the token is `high` or stronger; current-session status/model-picker labels such as `High`, `Extra High`, `xhigh`, or `max`; CLI `model.param_summary` values that normalize to those ranks.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

When effort is encoded only in the model slug, parse the effort token from the slug and treat that as the effort dimension. Cursor harness identity commonly exposes only the Grok family display name and omits effort; that resolves the family dimension only and does not prove, weaken, or invent effort. Unknown nonempty effort tokens are unverified. Unknown effort labels are not automatically stronger. Record resolved effort when an accepted evidence class provides it; otherwise record `unverifiable`. Known effort below `high` still proceeds — record the shortfall as `below recommended`. Never stop solely because controller effort is missing, weak, or unverifiable. Disclose the controller effort evidence state per the shared `SKILL.md` rule (completion report and any authorized PR body, not only the ledger).

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing resolved model ID and/or effort. Dimensions may come from the same source or be composed across accepted sources for the same controller turn.
2. A current-session status/model-picker view containing the missing dimension(s); a user screenshot, verbatim status readout, or authoritative user confirmation of the visible picker/status values is acceptable because the user is authoritative for their active UI state.
3. Any Cursor-exposed child/parent turn record that attributes model or effort values to this controller turn.

Compose dimensions when needed: if harness metadata resolves Grok at or above the `4.5` floor and effort is absent from that metadata, keep the family result and record effort from evidence class 2 or 3 when available, else `unverifiable`. Do not treat family-only harness metadata as a wrong-model failure, and do not instruct the user to change models when only effort evidence is missing.

Reject Composer as controller. Reject Auto, Balance, generic labels such as `Grok` or `GPT-5`, unresolved display-only names, launch arguments, settings JSON, requested profile names, and task/agent names until resolved to a versioned Grok family ID at or above the floor. Floor-meeting family display labels such as `Cursor Grok 4.5` are sufficient model-floor evidence; they are not resolved effort by themselves. Conflicting accepted sources are unverified.

On model-floor failure, stop before all Shipwright artifacts and say: select **Grok 4.5 or newer**, then provide new current-session evidence so the complete preflight can restart.

## Worker routing

| Shared task class | Cursor normalized tier |
| --- | --- |
| Mechanical | Composer |
| Ordinary | Composer / High |
| Integration | Grok / High |
| Critical | Grok / High |

Resolve aliases and slugs to family and effort before ranking. `composer-2.5-fast` is Composer family; do not invent ranks from `fast`. Never claim Luna/Terra/Sol execution on Cursor. Record Cursor family names only. GPT Luna/Terra/Sol may appear in the picker; they are not allowlisted worker families in v1 unless later promoted with first-party compatibility evidence. Unallowlisted families are unverified.

Normalize the allowlisted worker families in this order:

```text
Composer < Grok
```

A child meets a requested tier only when **both** specified dimensions meet their floors: its normalized model-family rank is at least the requested family rank and, when the route specifies an effort floor, its normalized effort rank is at least that floor. Dimensions do not compensate for each other. The Mechanical route intentionally has no effort floor; attributable Composer-or-stronger evidence with absent effort is acceptable, while a reported unknown nonempty effort label remains unverified. For Ordinary, require Composer family and effort `high+` when effort is exposed or parseable. If the live Task schema only exposes `composer-2.5-fast` and no separate effort field or slug token, record the selector limitation and apply the shared child-evidence rules: accept only when attributable evidence still meets the ordinary floor, otherwise one inherited-controller fallback. Integration and Critical both floor at Grok/High. An unresolved alias or unknown, generic, future, or unallowlisted family is always unverified. Apply the shared missing/conflicting-evidence transition rather than guessing a rank.

## Native dispatch and fallback

Use Cursor's Task subagent operation when exposed. Inspect the live schema. Conceptual shape:

```text
Task({ subagent_type, prompt, model, /* effort only if schema exposes it */ })
```

Rules:

1. Pass explicit `model` whenever a usable selector exists for the mapped tier.
2. Pass a separate effort/reasoning field only when the schema exposes it **and** the route has an effort floor.
3. If effort is only available as part of an allowlisted model slug, request that slug and record the requested slug before dispatch.
4. Never fabricate unsupported arguments.
5. Record the requested model and any requested effort before dispatch, then validate the child's actual current-turn model and effort evidence.

When a usable model selector exists but no effort selector exists:

1. Dispatch the explicitly selected route model without an effort field.
2. For the Mechanical route, accept attributable Composer-or-stronger evidence with absent effort because that route has no effort floor; a nonempty unknown effort remains unverified.
3. For Ordinary, Integration, and Critical routes, require the actual current-turn effort evidence to meet the route floor. Weaker, absent, unknown, conflicting, or unattributable effort rejects the gated result through the shared child-evidence transition and permits exactly one fresh inherited-controller fallback.
4. Accept that fallback only when its attributable model and effort meet the task minimum; otherwise enter `BLOCKED_RUNTIME`.

Use selector-absence fallback only when Task exposes no usable model selector, whether or not it exposes an effort selector:

1. Verify the controller passed the Grok `4.5` or newer model floor.
2. Dispatch one fresh inherited child with task-local context.
3. Require child current-turn evidence.
4. Record `inherited correctness-first fallback` and the actual evidence.

The same inherited-controller fallback is available once when an explicit dispatch is rejected by the shared child-evidence transition. An inherited Grok child is correctness-first over-provisioning, not Composer execution and not adaptive cost routing. Never claim the requested cheaper tier ran.

## Child evidence

Require the child report to include:

```text
session/run ID:
resolved model ID:
effort:
evidence class: harness metadata | current-session status/model-picker | matching turn record
```

The controller independently reads the child turn/session record when exposed and checks attribution. Requested selectors and agent names remain non-evidence. Apply the shared child-evidence transition table and its one-fallback budget exactly.
