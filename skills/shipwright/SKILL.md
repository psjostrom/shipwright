---
name: shipwright
description: Use when the user explicitly requests Shipwright, full end-to-end development, autonomous implementation with subagents, or implementation plus independent iterative review and real verification; do not use for factual questions, read-only review, diagnosis without a requested fix, or tiny mechanical edits.
---

# Shipwright

Orchestrate approved development through bounded implementation, independent review, fresh verification, and applicable real-world QA. The controller owns decisions and evidence; children receive file-based, task-local context.

Invoke as `$shipwright:shipwright` in Codex or `/shipwright:shipwright` in Claude Code.

## 1. Select the platform and run preflight

Identify the active harness, then read exactly one complete reference:

- Codex: [references/codex.md](references/codex.md)
- Claude Code: [references/claude-code.md](references/claude-code.md)

Stop if the harness cannot be identified. Apply its controller gate before writing specifications, plans, branches, ledgers, or implementation artifacts. Configuration, aliases, task labels, filenames, and requested profiles are not current-turn evidence. Conflicting accepted evidence is unverified. After the user changes the model or supplies evidence, restart the complete preflight in the same task.

Inspect repository instructions, fresh upstream baseline when relevant, branch/worktree, tracked and untracked changes, test commands, authorization boundaries, and applicable QA surfaces. Preserve unrelated work. Do not implement on `main` or `master` without explicit authorization.

## 2. Verify dependencies and capabilities

Before design, verify Superpowers 6.1.1 or newer and every required namespaced skill below. Accept an installed-plugin inventory or resolved paths proving that all dependencies come from one versioned package root.

- **REQUIRED FOR DESIGN:** `superpowers:brainstorming`
- **REQUIRED BEFORE IMPLEMENTATION:** `superpowers:using-git-worktrees`
- **REQUIRED FOR PLANNING:** `superpowers:writing-plans`
- **REQUIRED FOR EXECUTION:** `superpowers:subagent-driven-development`
- **REQUIRED FOR WORKERS:** `superpowers:test-driven-development`
- **REQUIRED FOR REVIEWS:** `superpowers:requesting-code-review`
- **REQUIRED FOR COMPLETION:** `superpowers:verification-before-completion`
- **REQUIRED FOR HANDOFF:** `superpowers:finishing-a-development-branch`

Also verify the harness minimum and capabilities in its platform reference. A compatible newer release proceeds with a warning that it is newer than the last behaviorally tested version. The controller retains that warning in preflight state: a reduced trivial workflow reports it without creating Shipwright artifacts, while a nontrivial workflow ingests it when the ledger is initialized. Stop and report the complete problem set when a version is below minimum, explicitly incompatible, unverified, mixed across package roots, or missing any dependency or required capability. Do not copy a missing workflow into Shipwright. After install, upgrade/downgrade, reload, or restart, rerun the full preflight.

## 3. Reduce trivial work

If the work is tiny, mechanical, locally obvious, and does not justify independent subagents, route it to a smaller workflow and explain the reduction. Shipwright wording does not justify costly fan-out for a one-line or otherwise trivial change.

## 4. Approve the design and plan

Use `superpowers:brainstorming` unless the user already approved a written design. Clarify value, definition of done, constraints, maintenance burden, security, performance, and user friction. Challenge unnecessary complexity. Produce a concise specification, independently review substantial or high-risk designs, resolve Critical and Important findings, and obtain approval unless the prompt explicitly approves that design.

After approval, use `superpowers:using-git-worktrees` and `superpowers:writing-plans`. Split work into bounded, independently testable tasks with exact files, interfaces, tests, and completion contracts. Record the original merge base for final review.

## 5. Exclude artifacts and initialize the ledger

Before writing any `.superpowers/` path, run `git check-ignore` on that exact path. If needed, add the exact `.superpowers/` pattern to the repository-local exclude file returned by `git rev-parse --git-path info/exclude`; never edit a global ignore. Re-check exclusion. If local exclusion cannot be established, stop and ask before using an external temporary location.

Create or resume `.superpowers/sdd/progress.md`. The controller is its only writer. On initialization, ingest any compatible-newer warnings retained during preflight. Before every dispatch or resume:

- Stop on every reused dispatch ID, even when all recorded fields match; never overwrite its artifact directory.
- Stop every dispatch for a task whose ledger verdict is already complete, even when task ID, base, and verdict match.
- Stop on a stale or conflicting task ID, base commit, head, or verdict.
- Resume only a ledger entry explicitly marked `resumable` and incomplete. A resume keeps the parent task ID and history but creates a new child dispatch ID and a unique artifact directory.

Give every new child dispatch a unique ID and artifact directory under `.superpowers/sdd/runs/<dispatch-id>/`.

Every ledger dispatch entry contains:

```text
Dispatch ID / parent task / role / artifact directory
Recorded base commit and head when reviewed
Task class, risk, requested tier and effort, selection rationale
Actual model and effort, evidence source, child thread/run ID
Evidence disposition and runtime-fallback retry count
Status, commands and exit status, findings and stable IDs
Remediation lineage and cycles, commits, final verdict
```

Children write only their own reports and unique artifacts. A read-only reviewer may write its report but must not mutate tracked product code. Run at most one write-capable implementer or fixer at a time. Independent read-only review and QA may run in parallel only with unique artifact paths and no shared mutable state.

## 6. Dispatch task-local work adaptively

Classify each dispatch independently from scope, ambiguity, systems touched, integration, risk, judgment, brief quality, and prior attempts:

| Task class | Examples | Route |
| --- | --- | --- |
| Mechanical | Complete, objective, local edit or check | Platform mechanical tier |
| Ordinary | Bounded implementation with clear interfaces | Platform ordinary tier |
| Integration | Multi-file contracts, debugging, meaningful review | Platform integration tier |
| Critical | Architecture, security, concurrency, subtle state, escalation, final review | Platform critical tier |

Use the selected platform reference to map and dispatch the tier. Use explicit model/effort selection only if the active tool schema exposes it. Otherwise use one fresh inherited child of the verified controller and record `inherited correctness-first fallback`; this is not adaptive cost routing. Never infer actual runtime from the request, agent name, profile, task label, or output quality. Do not recursively delegate unless the approved task explicitly requires nested, non-overlapping work.

Each child receives the task brief, applicable repository instructions, base revision, allowed paths, test expectations, artifact/report paths, and completion contract—not accumulated conversation history. Workers must use `superpowers:test-driven-development` where applicable and report `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

## 7. Validate child evidence

Require child thread/run ID plus current-turn model from an accepted platform evidence class. Require current-turn effort when the selected route defines an effort floor; absent effort is allowed only when that route defines none. Independently validate each reported dimension when the harness exposes the child turn/session record. Any unknown nonempty model or effort label is unverified.

Use the selected platform reference's model-family and effort orders. A result is sufficient only when every required dimension independently meets its requested floor; a stronger dimension never compensates for a weaker or unknown one.

| Observed evidence | Transition |
| --- | --- |
| Requested tier or stronger allowlisted tier | Accept; record requested and actual. Record stronger execution as a cost deviation. |
| Proven weaker than the role minimum | Reject for the gated role; redispatch once through the inherited-controller fallback. |
| Missing, conflicting, or not attributable to that child | Reject for the gated role; redispatch once through the inherited-controller fallback. |
| Fallback proves the verified controller tier and meets the role minimum | Accept; record `inherited correctness-first fallback`. |
| Fallback is weaker, conflicting, missing, or unverifiable | Set `BLOCKED_RUNTIME`; retain the report as untrusted evidence and stop. |

The runtime budget is one fallback per gated role. It is separate from remediation and cannot reset when the task is renamed. Never credit untrusted work toward implementation, review, remediation, or QA gates.

## 8. Implement, review, and remediate each task

Use `superpowers:subagent-driven-development` and `superpowers:requesting-code-review`:

1. Dispatch a fresh implementer. Require TDD where applicable, self-review, narrow and broader checks, diff inspection, and a report.
2. Inspect the actual artifacts, diff, commands, and evidence. Worker statements are not verification.
3. Generate a review package from the task's recorded base and dispatch a fresh independent reviewer.
4. Require separate **specification compliance** and **code quality** verdicts with severity, evidence, and stable finding IDs.
5. Send the complete Critical/Important finding set to one fixer selected for current complexity; require covering checks and a report.
6. Dispatch a fresh independent re-review. Complete the task only when both verdicts pass and no Critical/Important finding remains.

`NEEDS_CONTEXT` before an implementation attempt improves the brief and consumes no remediation cycle. Allow at most two context-repair redispatches for a task; each must record the missing context and use a materially revised brief. If the second redispatch still returns `NEEDS_CONTEXT`, set `BLOCKED`, keep the verdict incomplete, mark the ledger entry `resumable: awaiting user context`, record the unresolved context, and ask the user. Do not dispatch again automatically. Only after the user supplies the missing context and explicitly asks to continue, reopen the same ledger task, record the authorization, and reset the two-redispatch context-repair budget for the materially revised brief. Resume with a new child dispatch ID and unique artifact directory. Renaming or splitting the task cannot reset the budget before that user-authorized reopen. Broad scope may be split, but inherited findings retain their stable IDs and consumed cycles.

## 9. Enforce stable findings and terminal states

One remediation cycle is one fixer attempt followed by one fresh re-review. Maintain cumulative finding status so rewording, splitting, merging, or renaming cannot reset history.

1. Allow at most two ordinary remediation cycles for a task or whole-change review.
2. After two failed cycles, reassess scope, brief, and capability. Split only genuinely broad work while retaining inherited history.
3. When direct evidence supports a capability problem, allow one final escalated attempt and one fresh re-review.
4. If any Critical or Important finding remains, set `BLOCKED`, record unresolved evidence, and hand the decision to the user. Do not make a fourth attempt or claim completion.

Reject a reviewer finding only with direct source, test, or platform-documentation evidence. Record its stable ID, evidence, and rejected adjudication; never dismiss it silently.

## 10. Review the whole change

After every task passes, generate a whole-branch package from the original merge base. Dispatch a fresh critical-tier reviewer who did not implement the change. Require specification, cross-task, regression, authorization, and code-quality verdicts. Remediate the complete finding set under the same stable-ID and bounded-cycle rules, then re-review the whole remediation.

## 11. Run fresh verification

Use `superpowers:verification-before-completion`. Independently inspect repository state and the complete diff; confirm unrelated work is untouched; then freshly run applicable formatting, lint/static analysis, builds, focused tests, full relevant suites, documentation/package validators, and the requested user flow. Read output and exit status. Old reports or worker summaries do not prove completion.

Run deterministic verification before interactive QA. Record commands, results, versions, and redacted artifact paths.

## 12. Route applicable real-world QA

Store redacted QA evidence under the already excluded `.superpowers/sdd/qa/<run-id>/`. Close only sessions Shipwright opened. Remove raw credential-bearing captures after extracting safe observations.

| Surface | Required route and core observations |
| --- | --- |
| Web | Probe `agent-browser --version`; require 0.32.3 or compatible newer and an isolated real browser. Exercise the changed flow and affected loading/error/empty states at relevant affected desktop and mobile viewports; inspect semantic DOM/UI, console and failed network requests when networked; capture material screenshots and viewport evidence. Existing Playwright tests remain regression evidence. Add Playwright for persistent or Chromium/Firefox/WebKit coverage. |
| Android/iOS | Probe `argent --version`; require 0.16.0 or compatible newer. Android also needs `adb` and an emulator; iOS needs macOS, Xcode command-line tools, and a Simulator. Exercise the changed flow; inspect accessibility/component state, crashes/errors and failed requests when networked; capture material screenshots and performance evidence when performance is in scope. Preserve app/device data. |
| CLI | Build the distributable; run with isolated HOME, XDG config/cache/state, and task-specific data. Verify stdout, stderr, exit status, effects, malformed input, expected failures, and idempotence when promised. |
| Backend | Run isolated local dependencies and a real request/job through persistence and intended side effects. Mock only external boundaries. Verify response/status, stored state, logs, expected failures, and retries/idempotence when promised. |

An alternative browser/mobile tool is equivalent only when it supplies every core capability: a real rendered target, semantic inspection, user interaction, crash/log or console inspection, failed-network visibility when applicable, material screenshots, and isolated session control. Missing a core capability is `unverified`, not equivalent.

## 13. Record QA outcomes

- `verified`: every mandatory observation and artifact exists and the flow passed.
- `partially verified`: every core observation passed, but a named non-core planned observation was unavailable.
- `unverified`: the flow could not run, the interaction surface was unavailable, or core evidence is missing.

Only `verified` passes an applicable QA gate. `partially verified` or `unverified` sets `BLOCKED_QA`, records missing evidence, and prevents unqualified completion or branch finishing. Retry only after the user authorizes installation/access or explicitly revises the approved specification so the observation is no longer required; acknowledgement alone is not a pass. If no surface applies, record why.

Missing tools never authorize installation or configuration. Use an already-approved capability-equivalent project tool, ask for authorization, or record the blocked outcome. Use isolated accounts and local test data. Signed-in sessions, physical devices, production, paid services, and destructive resets require explicit authorization.

## 14. Authorization matrix

| Action | Default |
| --- | --- |
| Read scoped repository state and public documentation/package metadata | Allowed when relevant and sandbox/network policy permits |
| Modify scoped repository files and make local commits | Allowed by an explicit Shipwright implementation request |
| Install/download tools, mutate tooling lockfiles, or configure plugins/MCP | Ask first |
| Write outside the repository or task-specific temporary directories | Ask first |
| Use credentials, signed-in state, external accounts/services, or paid quota | Ask first unless the exact safe system/account is explicitly in scope |
| Contact production; push; open a PR; deploy; publish; message another person/system | Ask first |
| Use physical devices or erase/reset app, simulator, emulator, or device data | Ask first |
| Destructive filesystem or git action | Ask first after resolving exact targets read-only |

Never put credentials, tokens, personal data, unredacted network payloads, or signed-in state in tracked files, reports, screenshots, or the ledger.

## 15. Finish the branch

Finish only after the approved specification, every task review, whole-change review, fresh verification, and every applicable QA gate passes. Use `superpowers:finishing-a-development-branch`. Report scope, commits, verification, QA state, remaining risks, temporary evidence, and integration options. Never push, open a PR, deploy, or publish without explicit authorization.

## Red flags

| Rationalization | Required response |
| --- | --- |
| “The worker says it passed.” | Inspect artifacts and run fresh controller verification. |
| “The requested profile proves the model.” | Require attributable current-turn evidence. |
| “One more retry might work.” | Enforce the runtime and remediation budgets. |
| “Partial QA is close enough.” | Set `BLOCKED_QA`; only `verified` passes. |
| “Autonomous means external actions are allowed.” | Apply the authorization matrix. |
