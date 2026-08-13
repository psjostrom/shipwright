# Shipwright

`shipwright` orchestrates approved development from design through implementation,
independent review, fresh verification, and applicable real-world QA. The
controller owns decisions and evidence; workers receive bounded, task-local
context.

Shipwright is deliberately stricter than a normal implementation prompt. It
checks the active harness and model floor, preserves unrelated work, requires
independent review, and refuses to call incomplete QA complete.

```text
[Preflight] -> [Design + plan]
                    |
                    v
[Classify + choose agent] -> [Implement] -> [Fresh review]

[Fresh review]
  +-- pass ------> [Task done]
  +-- findings --> [Fix] -> [Fresh re-review]

[Fresh re-review]
  +-- pass ----------------> [Task done]
  +-- findings + retry ----> back to [Fix]
  +-- findings + no retry -> [BLOCKED]

[Task done]
  +-- next planned task --> back to [Classify + choose agent]
  +-- all tasks done -----> [Whole-change review]

[Whole-change review]
  +-- pass ------> [Fresh verification]
  +-- findings --> [Fix] -> [Fresh re-review]

[Fresh re-review]
  +-- pass ----------------> [Fresh verification]
  +-- findings + retry ----> back to [Fix]
  +-- findings + no retry -> [BLOCKED]

[Fresh verification] -> [QA] -> [Finish]

Remediation cap: 2 normal attempts + 1 optional escalation; else [BLOCKED].
```

The shared contract lives in
[`plugins/shipwright/skills/shipwright/SKILL.md`](../../plugins/shipwright/skills/shipwright/SKILL.md). Harness-specific
runtime and dispatch rules live in
[`plugins/shipwright/skills/shipwright/references/`](../../plugins/shipwright/skills/shipwright/references/).

## When to use it

Use Shipwright when the user explicitly asks for Shipwright, full end-to-end
development, autonomous implementation with subagents, or implementation plus
independent iterative review and real verification.

Do not use it for:

- factual questions;
- read-only review of an existing change — use `reviewer`;
- diagnosis without a requested fix;
- tiny mechanical edits where a narrow direct workflow is enough.

Tiny work can be reduced after preflight, but the controller/model gate,
platform reference, fresh verification, and applicable QA still apply.

## Invoke it

| Harness | Invocation |
| --- | --- |
| Codex | `Use $shipwright:shipwright to build this feature end to end ...` |
| Claude Code | `/shipwright:shipwright` |
| Cursor | `/shipwright` |
| opencode | No port |

Examples:

```text
Use $shipwright:shipwright to build the requested feature end to end with
independent review and real verification.
```

```text
/shipwright:shipwright
/shipwright
```

Shipwright does not run from an ambient match: its skill sets
`disable-model-invocation: true`.

## Hard boundaries

Shipwright may read repository state and modify scoped repository files as part
of an explicitly approved implementation task. It does not automatically:

- work on `main` or `master` without explicit authorization;
- add or upgrade dependencies, intentionally mutate lockfiles, edit CI/build
  configuration, install global tools, or configure plugins/MCP;
- use credentials, signed-in external services, production, paid quota, or
  physical devices;
- erase/reset app, simulator, emulator, or device data;
- push, open a PR, deploy, publish, message another system, or merge.

It may restore project-declared state from committed manifests and generate
expected gitignored artifacts, then prove manifests and lockfiles are unchanged.

Never bypass hooks with `--no-verify` or `-n`.

## Preflight

Preflight runs before design, reduction, plans, branches, ledgers, or product
changes.

### Harness and skill identity

The controller:

1. identifies the active harness;
2. reads exactly that harness reference;
3. verifies the harness version and required capabilities;
4. records the loaded skill base path and package commit/identity;
5. compares the loaded skill to the plugin install record and stops on a stale
   or mismatched copy.

Configuration, aliases, task labels, requested profiles, and filenames are not
current-turn evidence. If model or capability evidence changes, preflight
restarts from the beginning.

### Repository and workspace

Preflight inspects:

- repository instructions and the relevant fresh upstream baseline;
- repository root, branch, worktree, `HEAD`, and dirty/untracked state;
- test commands, commit hooks, and `lint-staged` or equivalent gates;
- authorization boundaries and applicable QA surfaces;
- whether the workspace is where the project tooling can discover it.

It rejects a requested target outside the current repository. It does not use a
tool-owned directory such as `.claude/`, `.cursor/`, or `.agents/` as a working
directory. It preserves unrelated user changes.

Before dispatching workers, it proves that the test runner discovers the
expected tests and runs at least one real known-good test. Discovery compares
filtered path sets, not line counts. If a visual surface applies, it captures
the merge-base baseline before implementation.

### Required dependencies

Superpowers `6.1.1+` must be installed and discoverable from one versioned
package root, with these skills available:

- `superpowers:brainstorming` — design;
- `superpowers:using-git-worktrees` — isolation before implementation;
- `superpowers:writing-plans` — plan;
- `superpowers:subagent-driven-development` — execution;
- `superpowers:test-driven-development` — workers where applicable;
- `superpowers:requesting-code-review` — review gates;
- `superpowers:verification-before-completion` — final verification;
- `superpowers:finishing-a-development-branch` — branch finish.

Missing, below-floor, mixed-root, explicitly incompatible, or unverified
dependencies block the run. Shipwright does not copy missing workflows into
itself.

### Harness floors

| Harness | Runtime floor | Controller model floor | Recommended effort |
| --- | --- | --- | --- |
| Codex | Codex CLI `0.139.0+`, or equivalent desktop plugin/Agent Skills/multi-agent/current-turn metadata | Resolved Sol `5.6+` | `high+` |
| Claude Code | `2.1.117+`, with plugin discovery and Task/Agent/current-turn evidence | Resolved Opus `4.6+` | `xhigh+` |
| Cursor | Plugin discovery, Task subagents, current-turn model/effort evidence, and Superpowers `6.1.1+` | Resolved Grok `4.5+` | `high+` |

The controller model family/version is a hard gate. Recommended effort is a
disclosed recommendation, not a gate: known lower effort proceeds as
`below recommended`; missing effort is recorded as `unverifiable` in the local
ledger but is not surfaced as a failure.

## Design and plan

After preflight, Shipwright obtains an approved design unless the user already
approved a written design. The design clarifies value, definition of done,
constraints, maintenance burden, security, performance, and user friction.

After design approval, Shipwright uses an isolated worktree when the repository
does not require generated gitignored state in the main checkout, then writes a
bounded plan. If generated state must remain in the main checkout, it uses a
branch there and records why.

The plan defines task files, interfaces, tests, allowed paths, completion
contracts, and the original merge base. It must not contain guessed literal
expected values; measure them first or mark them unverified for the worker to
determine.

## Task routing

Each task is classified independently:

| Class | Typical work |
| --- | --- |
| Mechanical | Objective local edit or check |
| Ordinary | Bounded implementation with clear interfaces |
| Integration | Multi-file contract, debugging, or meaningful review |
| Critical | Architecture, security, concurrency, subtle state, escalation, or final review |

The active platform maps classes to worker family and effort:

| Class | Codex | Claude Code | Cursor |
| --- | --- | --- | --- |
| Mechanical | Luna / Medium | Haiku | Composer |
| Ordinary | Terra / Medium | Sonnet / Medium | Composer / High |
| Integration | Terra / High | Sonnet / High | Grok / High |
| Critical | Sol / High | Opus / xhigh | Grok / High |

Observed model and effort must satisfy both dimensions. A stronger family does
not compensate for weaker effort, and a stronger effort does not compensate for
an unapproved family. The controller never infers actual runtime from a task
label, profile, alias, or output quality.

If the live child schema cannot select or prove the requested runtime, Shipwright
uses at most one fresh inherited-controller fallback for that gated role and
records it as `inherited correctness-first fallback`. It never claims a cheaper
worker tier ran. A weaker, conflicting, missing, or unverified fallback causes
`BLOCKED_RUNTIME`.

Every worker receives only the task brief, repository instructions, base
revision, allowed paths, tests, artifact/report paths, and completion contract.
Workers report `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

## Ledger and artifacts

Before writing Shipwright artifacts, the controller verifies that `.superpowers/`
and the plan path are git-ignored through the repository-local exclude file.
It never edits a global ignore.

The controller owns:

```text
.superpowers/sdd/progress.md
.superpowers/sdd/runs/<dispatch-id>/
.superpowers/sdd/qa/<run-id>/
```

Each dispatch records its unique ID, parent task, role, artifact directory,
base/head, task class, requested and actual runtime, evidence source,
fallback/retry count, commands and exit status, findings, remediation lineage,
commits, and final verdict. Dispatch IDs and artifact directories are never
reused.

## Implementation and review

For each task, Shipwright:

1. dispatches a fresh implementer with TDD where applicable;
2. inspects the actual diff, artifacts, commands, and evidence;
3. creates a review package from the recorded task base;
4. dispatches a fresh independent reviewer;
5. requires separate specification-compliance and code-quality verdicts;
6. sends all Critical/Important findings to one fixer;
7. dispatches a fresh independent re-review.

A task passes only when both verdicts pass and no Critical or Important finding
remains. Stable finding IDs survive rewording, splitting, merging, and renamed
tasks.

`NEEDS_CONTEXT` is not a remediation failure. Shipwright can repair context at
most twice with materially revised briefs. A second unresolved context failure
marks the task resumable and asks the user; only explicit user continuation
reopens it with a new dispatch ID.

One remediation cycle is one fixer attempt plus one fresh re-review. There are
at most two ordinary cycles. A capability-supported final escalation allows one
additional attempt and re-review. If Critical or Important findings remain,
Shipwright sets `BLOCKED` and stops rather than making a fourth attempt.

After all tasks pass, a fresh critical-tier reviewer reviews the whole change
from the original merge base. It checks specification, cross-task interaction,
regression, authorization, and quality, then follows the same bounded
remediation rules.

Evidence is read from unambiguous exit statuses and artifacts. Do not use a
pipeline's final command status as proof for a compound command; redirect the
status to a file and read it. Compare discovery path sets rather than counts.

## Verification

Final verification independently inspects the complete diff and confirms that
unrelated work is untouched. It runs applicable formatting, lint/static
analysis, builds, focused tests, full relevant suites, package/documentation
validators, and the requested user flow. Base measurements are recorded where
pre-existing failures exist; the bar is no new failure versus base.

Old worker reports do not prove completion.

## Real-world QA

Applicable QA is mandatory. A missing capability is not a reason to install a
tool or silently downgrade the result. Use an approved equivalent, ask for
authorization, or record the gate as blocked.

| Surface | Required evidence |
| --- | --- |
| Web | Isolated real browser; `agent-browser` `0.32.3+` or compatible; changed flow plus affected loading/error/empty states; semantic UI, console, failed requests, viewport evidence, before/after screenshots, quantitative diff when claiming equivalence |
| Android/iOS | Loaded argent interaction/screenshot/gesture tools; Android `adb` and emulator or iOS Simulator/Xcode; changed flow, accessibility/state, crashes/errors, failed requests, screenshots, and performance evidence when in scope |
| CLI | Isolated HOME/XDG/task data; build distributable; verify stdout, stderr, exit status, effects, malformed input, expected failures, and idempotence when promised |
| Backend | Isolated dependencies; real request/job through persistence and side effects; response/status, stored state, logs, failures, retries/idempotence |

For web/mobile, screenshots are required even when the change claims no visual
change: exercise the unchanged affected flow and compare matched baseline and
after conditions. Booting or showing a consent dialog is not enough.

Store redacted evidence under the excluded QA directory. Close only sessions
Shipwright opened. Remove raw credentials and sensitive payloads after extracting
safe observations.

QA outcomes:

- `verified` — every mandatory observation and artifact passed;
- `partially verified` — core observations passed, but a named non-core item was
  unavailable;
- `unverified` — the flow could not run or core evidence is missing.

Only `verified` passes. `partially verified` and `unverified` set
`BLOCKED_QA`; acknowledgement alone does not upgrade them.

When authorized to update a PR, Shipwright cannot upload screenshots through
CLI tooling. It prepares redacted local files with a distinct `pr-` prefix and
asks the user to drag them into the PR comment box. It must not publish private
UI screenshots to public hosts or imply local evidence is already on the PR.

## Finish states

Shipwright finishes only after:

- approved design and plan;
- every task implementation, review, remediation, and re-review;
- whole-change review;
- fresh deterministic verification;
- every applicable QA gate is `verified`.

The completion report includes scope, commits that already exist, verification,
QA state and evidence paths, remaining risks, temporary evidence, and
integration options. It does not push, open a PR, deploy, publish, or merge
without authorization.

## Harness details

### Codex

Install the local marketplace and plugin, then start a new task:

```sh
codex plugin marketplace add .
codex plugin add shipwright@agent-plugins
```

Invoke `$shipwright:shipwright`. Codex dispatches with its collaboration
operation when available. If the schema lacks model/effort selectors, the
inherited Sol fallback is the only permitted fallback after the controller
floor passes.

### Claude Code

Install `shipwright` and invoke `/shipwright:shipwright`. The controller gate
requires a resolved Opus `4.6+`; specialist routing defaults to Haiku for
mechanical work, Sonnet for ordinary/integration work, and Opus for critical
work. Claude child report text is persisted by the controller because its
subagent tooling does not let children write report files.

### Cursor

Install Shipwright from the marketplace and Superpowers `6.1.1+` separately.
Invoke `/shipwright`. The controller gate requires a model resolved to Grok
`4.5` or newer.
Cursor maps mechanical/ordinary work to Composer and integration/critical work
to Grok, with the effort floors shown above. Do not describe GPT Luna/Terra/Sol
as Cursor worker runtimes; they are not allowlisted here.

### opencode

There is no opencode port. Do not invoke Shipwright through opencode.

## Source map

- [`skills/shipwright/SKILL.md`](skills/shipwright/SKILL.md) — complete shared
  workflow and authorization contract.
- [`skills/shipwright/references/codex.md`](skills/shipwright/references/codex.md)
  — Codex runtime floor, model evidence, routing, and fallback.
- [`skills/shipwright/references/claude-code.md`](skills/shipwright/references/claude-code.md)
  — Claude Code runtime floor, model evidence, routing, and fallback.
- [`skills/shipwright/references/cursor.md`](skills/shipwright/references/cursor.md)
  — Cursor runtime floor, model evidence, routing, and fallback.
- [`scripts/validate_shipwright.py`](scripts/validate_shipwright.py) — bundle
  validator.

## Validation

After changing Shipwright platform files, run:

```sh
python3 plugins/shipwright/scripts/validate_shipwright.py
```

After changing validator logic, also run:

```sh
python3 -m unittest plugins/shipwright/scripts/test_validate_shipwright.py
```
