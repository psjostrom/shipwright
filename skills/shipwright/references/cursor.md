# Cursor Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Cursor. The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Cursor with plugin skill discovery, Task subagents, and current-turn model/effort evidence. Probe the active version and tool schemas; do not infer capabilities from documentation or configuration alone. A compatible newer release proceeds with a warning retained in controller preflight state and later reported or ingested according to the shared workflow. A below-minimum, explicitly incompatible, unverified, or capability-incomplete runtime fails preflight.

Superpowers 6.1.1 or newer must be installed and discoverable as a separate Cursor plugin. Shipwright does not vendor Superpowers. Accept an installed-plugin inventory or resolved paths proving one versioned Superpowers package root.

No releases newer than the minimum are currently listed as explicitly incompatible. This statement does not override observed missing capabilities.

## Controller gate

Accept only resolved Grok 4.5 family IDs with effort rank `high` or stronger.

Examples of acceptable evidence forms, not an exhaustive invent-list: `cursor-grok-4.5`, `grok-4.5`, and effort-bearing variants such as `cursor-grok-4.5-high` or `cursor-grok-4.5-high-fast` when the effort token is `high` or stronger.

Normalized effort order:

```text
low < medium < high < xhigh < max
```

When effort is encoded only in the model slug, parse the effort token from the slug and treat that as the effort dimension. Unknown nonempty effort tokens are unverified. Unknown effort labels are not automatically stronger. A future model, renamed model, or generic family label is not accepted until this reference explicitly allowlists it from first-party compatibility evidence.

Accepted current-turn evidence, in priority order:

1. Harness-provided metadata for this turn containing resolved model ID and effort.
2. A current-session status/model-picker view containing both values; a user screenshot or verbatim status readout is acceptable because the user is authoritative for their active UI state.
3. Any Cursor-exposed child/parent turn record that attributes both values to this controller turn.

Reject Composer as controller. Reject Auto, Balance, generic labels such as `Grok` or `GPT-5`, display-only names, launch arguments, settings JSON, requested profile names, and task/agent names until resolved to an allowlisted ID. Conflicting accepted sources are unverified.

On failure, stop before all Shipwright artifacts and say: select **Grok 4.5 / High or stronger**, then provide new current-session evidence so the complete preflight can restart.

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

1. Verify the controller passed the Grok 4.5/High gate.
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
