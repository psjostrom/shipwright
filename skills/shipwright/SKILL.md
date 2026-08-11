---
name: shipwright
description: Use when the user explicitly requests Shipwright, full end-to-end development, autonomous implementation with subagents, or implementation plus independent iterative review and real verification; do not use for factual questions, read-only review, diagnosis without a requested fix, or tiny mechanical edits.
disable-model-invocation: true
---

# Shipwright

Orchestrate approved development through bounded implementation, independent review, fresh verification, and applicable real-world QA. The controller owns decisions and evidence; children receive file-based, task-local context.

Invoke as `$shipwright:shipwright` in Codex, `/shipwright:shipwright` in Claude Code, or `/shipwright` in Cursor.

## 1. Select the platform and run preflight

Identify the active harness, then read exactly one complete reference:

- Codex: [references/codex.md](references/codex.md)
- Claude Code: [references/claude-code.md](references/claude-code.md)
- Cursor: [references/cursor.md](references/cursor.md)

Stop if the harness cannot be identified. Stop if the selected platform reference cannot be read. Apply its controller gate before writing specifications, plans, branches, ledgers, or implementation artifacts — including before any §3 reduction. An unreadable platform reference is a stop condition, not a downgrade or a reason to skip the gate. Configuration, aliases, task labels, filenames, and requested profiles are not current-turn evidence. Conflicting accepted evidence is unverified. After the user changes the model or supplies evidence, restart the complete preflight in the same task.

As a preflight output, record this skill's loaded base-directory path and commit (or equivalent package identity) and compare it to the plugin install record. Stop on mismatch — a stale cached copy is not the installed skill.

Shared controller-gate product rule for every harness: the platform model/family floor is a hard gate. Recommended controller effort is not a precondition. Record resolved effort when an accepted evidence class provides it; otherwise record `unverifiable` in the ledger. Known effort below the platform's recommended floor still proceeds — record the shortfall. Never stop solely because controller effort is missing, weak, or unverifiable. Disclose resolved or `below recommended` effort in the completion report and the ledger; suppress `unverifiable` from the user-facing completion report and from any authorized PR body. When disclosing to a PR and repository instructions forbid AI-attribution or tooling references in user-facing text, record the omission and its reason in the ledger rather than breaching the repository's rules. Platform references own how evidence is read; they must not invent a harder effort precondition than this shared rule.

Resolve the subject repository as an explicit preflight output. Stop when a requested target path lies outside the current repository root, and direct the user to re-invoke Shipwright from that repository.

Inspect repository instructions, fresh upstream baseline when relevant, branch/worktree, tracked and untracked changes, test commands, authorization boundaries, and applicable QA surfaces. Also read the commit gate — pre-commit hooks, `lint-staged` or equivalent — and determine whether any file the task must modify carries pre-existing findings that the gate will reject. A repository whose gate lints every staged file makes "do not fix pre-existing debt" and "never `--no-verify`" mutually unsatisfiable for that file. Resolve it before dispatch, not at commit time. Preserve unrelated work. Do not implement on `main` or `master` without explicit authorization.

The workspace must live somewhere the project's own tooling will actually operate on. Do not accept a workspace inside a tool-owned directory such as `.claude/`, `.cursor/`, or `.agents/` — these are conventionally excluded from test runners, typecheckers, and linters, so a workspace inside one is invisible to the very tools §11 depends on. If it was created there by default, relocate it before dispatching anyone. A fresh worktree is also the wrong workspace when the project requires generated, gitignored files to be present — env config, version stamps, native artifacts — because a new worktree does not have them and §12 may require running the real app. Check for this before creating one. When it applies, work on a branch in the main checkout instead, and record the reason in the ledger. Do not treat the worktree step as satisfied by a workspace that cannot build.

Prove the test runner actually discovers tests in the chosen workspace before dispatching anyone. Run an explicit discovery or collection command such as `--listTests` or `--collect-only`, keep stdout path lists (discard stderr and banners), and compare filtered path *sets* — not line counts — to expectations and to later re-measurements. Do not treat a single targeted known-good test as sufficient discovery proof; if the project has no discovery/collection flag, run the unfiltered project test command and record its discovered path set instead. Separately, run at least one real known-good test to green so setup files and dependencies actually load — discovery alone does not prove that. A workspace the project's tooling silently ignores produces green runs that verify nothing, and the failure is invisible in exit codes. Confirm too that the workspace can actually build and test at all: freshly created worktrees routinely lack installed dependencies and generated-but-gitignored files that no commit contains. Restore declared state per §14 when needed; do not report `BLOCKED` for a missing install the project's own manifests already declare.

When a visual QA surface (web/mobile) applies or is expected, capture baseline screens at the merge base before implementation — the *before* for §12. On JS/Metro, swapping to the base ref and reloading is enough when the native binary is unchanged. Skip baseline only when no visual surface applies.

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

Also verify the harness minimum and capabilities in its platform reference. A compatible newer release proceeds with a warning that it is newer than the last behaviorally tested version. The controller retains that warning in preflight state: a reduced trivial workflow reports it without creating Shipwright artifacts, while a nontrivial workflow ingests it when the ledger is initialized. Stop and report the complete problem set when a version is below minimum, explicitly incompatible, unverified, mixed across package roots, or missing any dependency or required capability. Do not copy a missing workflow into Shipwright. After install, upgrade/downgrade, reload, or restart, rerun the full preflight — including the loaded-skill vs install-record check in §1.

## 3. Reduce trivial work

Only after §1 identifies the harness and the controller gate passes: if the work is tiny, mechanical, locally obvious, does not justify independent subagents, **and the verification surface it can affect is narrow**, route it to a smaller workflow and explain the reduction. Shipwright wording does not justify costly fan-out for a one-line or otherwise trivial change. A small diff with a wide verification or QA surface — for example a dependency bump that can break an app, device flow, or shared runtime — is not trivial; keep the full workflow. The reduction path does not waive the controller gate, the requirement to read the platform reference, §11 fresh verification, or §12 QA routing. The reduced path may change only files required by the requested task; do not create or modify project-level configuration (for example `package.json`, lockfiles, build config, or CI config) unless the user asked for that change or explicitly approved it.

## 4. Approve the design and plan

Use `superpowers:brainstorming` unless the user already approved a written design. Clarify value, definition of done, constraints, maintenance burden, security, performance, and user friction. Challenge unnecessary complexity. Produce a concise specification, independently review substantial or high-risk designs, resolve Critical and Important findings, and obtain approval unless the prompt explicitly approves that design.

After approval, use `superpowers:using-git-worktrees` and `superpowers:writing-plans`. When §1's generated-gitignored-file exception applies, skip the fresh worktree and use a branch in the main checkout instead; otherwise keep the worktree flow. Split work into bounded, independently testable tasks with exact files, interfaces, tests, and completion contracts. Record the original merge base for final review. Exact-code plan steps carry correctness risk proportional to how little of the target source the author has actually read and run; prefer precise interface contracts plus "read this first" over fabricated implementations for unread files. This applies with extra force to literal expected values — version strings, counts, fixture contents, boundary cases in tables. A wrong expectation is worse than wrong code: the implementer writes the assertion to the plan, it passes, and the wrong value becomes load-bearing. Any literal expected value must either be measured before the plan is written, or written as UNVERIFIED with an instruction for the implementer to determine and report it.

After the plan is saved, do not present Superpowers `writing-plans` execution options, ask which approach to use, or offer `superpowers:executing-plans` / Inline Execution. Shipwright overrides that handoff: proceed immediately to §5 ledger initialization, then §6–§8 with `superpowers:subagent-driven-development` and independent review gates. Announce the override briefly if useful; do not wait for the user to choose an execution mode.

## 5. Exclude artifacts and initialize the ledger

Before writing any `.superpowers/` path, run `git check-ignore` on that exact path. If needed, add the exact `.superpowers/` pattern to the repository-local exclude file returned by `git rev-parse --git-path info/exclude`; never edit a global ignore. Re-check exclusion. If local exclusion cannot be established, stop and ask before using an external temporary location. Apply the same exclusion check to `docs/superpowers/`, which `superpowers:writing-plans` uses as its default save location, or direct the plan to a path under `.superpowers/`.

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

Children produce their own reports and any unique artifacts; the controller owns persistence where the platform prevents children from writing files. A read-only reviewer may write its report but must not mutate tracked product code. Run at most one write-capable implementer or fixer at a time. Independent read-only review and QA may run in parallel only with unique artifact paths and no shared mutable state.

## 6. Dispatch task-local work adaptively

Classify each dispatch independently from scope, ambiguity, systems touched, integration, risk, judgment, brief quality, and prior attempts. Escalate the class when the work is hard to reverse or the domain is unforgiving — financial, medical, safety-critical, destructive, or shipped where rollback is impossible. A small diff in code that cannot be rolled back deserves a higher tier than its size implies:

| Task class | Examples | Route |
| --- | --- | --- |
| Mechanical | Complete, objective, local edit or check | Platform mechanical tier |
| Ordinary | Bounded implementation with clear interfaces | Platform ordinary tier |
| Integration | Multi-file contracts, debugging, meaningful review | Platform integration tier |
| Critical | Architecture, security, concurrency, subtle state, escalation, final review | Platform critical tier |

Use the selected platform reference to map and dispatch the tier. Use explicit model/effort selection only if the active tool schema exposes it. Otherwise use one fresh inherited child of the verified controller and record `inherited correctness-first fallback`; this is not adaptive cost routing. Never infer actual runtime from the request, agent name, profile, task label, or output quality. Do not recursively delegate unless the approved task explicitly requires nested, non-overlapping work.

Each child receives the task brief, applicable repository instructions, base revision, allowed paths, test expectations, artifact/report paths, and completion contract—not accumulated conversation history. Workers must use `superpowers:test-driven-development` where applicable and report `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`. Never pass `--no-verify` or `-n` to `git commit`; if hooks fail, fix the code or report `BLOCKED`.

## 7. Validate child evidence

Take the child thread/run ID from the harness spawn result; do not require the child to self-report it. Require current-turn model from an accepted platform evidence class. Require current-turn effort when the selected route defines an effort floor; absent effort is allowed only when that route defines none, or when the selected platform reference waives the effort dimension because the harness cannot request or attribute child effort. Independently validate each reported dimension when the harness exposes the child turn/session record. Any unknown nonempty model or effort label is unverified.

Use the selected platform reference's route order and sufficiency rules. A result is sufficient only when its complete observed route matches the requested route or an explicitly defined stronger route. When a platform defines separate family and effort floors, every required dimension must independently meet its floor; never assemble a passing route from mismatched dimensions. An unknown dimension is never stronger.

| Observed evidence | Transition |
| --- | --- |
| Requested tier or stronger allowlisted tier | Accept; record requested and actual. Record stronger execution as a cost deviation. |
| Proven weaker than the role minimum | Reject for the gated role; redispatch once through the inherited-controller fallback. |
| Missing, conflicting, or not attributable to that child | Reject for the gated role; redispatch once through the inherited-controller fallback. |
| Fallback proves the verified controller tier and meets the role minimum | Accept; record `inherited correctness-first fallback`. |
| Fallback is weaker, conflicting, missing, or unverifiable | Set `BLOCKED_RUNTIME`; retain the report as untrusted evidence and stop. |

**Orphaned work.** A dispatch that dies on a terminal platform or API error is distinct from one rejected for weak evidence. If it left uncommitted changes in the tree, nothing from it is accepted — there is no report and no attributable runtime. Do not resume it as itself and do not discard the changes reflexively. When the orphaned tree measures green under controller verification and auditing is cheaper than redoing the work, dispatch a fresh child to audit, correct, and take ownership of the orphaned diff, instructed explicitly to scrutinise rather than rubber-stamp it, and subject the result to the normal independent review. With a red or unverified orphaned tree, first perform a non-destructive ownership and diff-scope check: preserve unrelated user edits, and require authorization before any destructive Git or filesystem cleanup. Discard and redispatch from a clean base only after confirming the tree contains solely the failed dispatch's changes. Record the dead dispatch's status, that nothing was accepted from it, and that the adoption consumed the role's runtime fallback.

The runtime budget is one fallback per gated role. It is separate from remediation and cannot reset when the task is renamed. Never credit untrusted work toward implementation, review, remediation, or QA gates.

## 8. Implement, review, and remediate each task

Use `superpowers:subagent-driven-development` and `superpowers:requesting-code-review`:

1. Dispatch a fresh implementer. Require TDD where applicable, self-review, narrow and broader checks, diff inspection, and a report.
2. Inspect the actual artifacts, diff, commands, and evidence. Worker statements are not verification. Controller statements are not verification either — the completion report and any authorized PR must carry the same evidence standard (see Reading evidence below).
3. Generate a review package from the task's recorded base and dispatch a fresh independent reviewer.
4. Require separate **specification compliance** and **code quality** verdicts with severity, evidence, and stable finding IDs.
5. Send the complete Critical/Important finding set to one fixer selected for current complexity; require covering checks and a report.
6. Dispatch a fresh independent re-review. Complete the task only when both verdicts pass and no Critical/Important finding remains.

**Reading evidence.** Gate results come from the narrowest output that can only mean one thing. Read exit status from a value written to a file — never from a harness background/async completion code for a compound command (that code is usually the last element, e.g. `tee`). Prefer probes that cannot be misread (`lsof -nP -iTCP:<port> -sTCP:LISTEN` for listeners, not `lsof -ti`). Use filtered path *sets* and set diffs for discovery and similar metrics, not line counts.

When remediation overrides an approved plan constraint, either amend the plan and record the supersession, or declare the plan frozen with the ledger authoritative; record which path was chosen. Do not leave both documents live with conflicting constraints.

`NEEDS_CONTEXT` before an implementation attempt improves the brief and consumes no remediation cycle. Allow at most two context-repair redispatches for a task; each must record the missing context and use a materially revised brief. If the second redispatch still returns `NEEDS_CONTEXT`, set `BLOCKED`, keep the verdict incomplete, mark the ledger entry `resumable: awaiting user context`, record the unresolved context, and ask the user. Do not dispatch again automatically. Only after the user supplies the missing context and explicitly asks to continue, reopen the same ledger task, record the authorization, and reset the two-redispatch context-repair budget for the materially revised brief. Resume with a new child dispatch ID and unique artifact directory. Renaming or splitting the task cannot reset the budget before that user-authorized reopen. Broad scope may be split, but inherited findings retain their stable IDs and consumed cycles.

## 9. Enforce stable findings and terminal states

One remediation cycle is one fixer attempt followed by one fresh re-review. Maintain cumulative finding status so rewording, splitting, merging, or renaming cannot reset history.

1. Allow at most two ordinary remediation cycles for a task or whole-change review.
2. After two failed cycles, reassess scope, brief, and capability. Split only genuinely broad work while retaining inherited history.
3. When direct evidence supports a capability problem, allow one final escalated attempt and one fresh re-review.
4. If any Critical or Important finding remains, set `BLOCKED`, record unresolved evidence, and hand the decision to the user. Do not make a fourth attempt or claim completion.

Reject a reviewer finding only with direct source, test, or platform-documentation evidence. Record its stable ID, evidence, and rejected adjudication; never dismiss it silently.

## 10. Review the whole change

After every task passes, generate a whole-branch package from the original merge base. Dispatch a fresh critical-tier reviewer who did not implement the change. Require specification, cross-task, regression, authorization, and code-quality verdicts. Remediate the complete finding set under the same stable-ID and bounded-cycle rules, then re-review the whole remediation. A single fresh critical-tier reviewer may serve both the final task's §8 gate and this whole-change gate, provided it is asked for a separate per-task verdict alongside the whole-change verdicts and the consolidation is recorded. With exactly one task, that consolidation is allowed under the same conditions. Do not consolidate any earlier task's gate this way — those reviews inform the work that follows them.

## 11. Run fresh verification

Use `superpowers:verification-before-completion`. Independently inspect repository state and the complete diff; confirm unrelated work is untouched; then freshly run applicable formatting, lint/static analysis, builds, focused tests, full relevant suites, documentation/package validators, and the requested user flow. Read output and exit status. Old reports or worker summaries do not prove completion. Apply §8 Reading evidence: a harness-reported completion code for a compound command is not the tool's exit status.

Before treating any gate as pass/fail, measure it at the merge base. A repository with pre-existing lint, type, or test debt makes "the gate passes" the wrong bar — the bar is "no new failures versus base." Record both numbers in the ledger. Conversely, do not conclude a gate is unavailable because no packaged script wraps it; probe the underlying tool directly. A repository with no `typecheck` script may still have a clean typechecker, and a clean gate you skipped is the one most likely to be hiding a regression.

Piping a command to `tail` or `head` replaces its exit status with the pipe's. Redirect to a file and read `$?`.

Run deterministic verification before interactive QA. Record commands, results, versions, and redacted artifact paths.

## 12. Route applicable real-world QA

Store redacted QA evidence under the already excluded `.superpowers/sdd/qa/<run-id>/`. That path is storage, not publication. Close only sessions Shipwright opened. Remove raw credential-bearing captures after extracting safe observations.

Screenshots are mandatory for applicable visual surfaces — there is no exemption for “no UI change.” For a no-observable-change refactor, exercise the *unchanged* flow; identical before/after screens are the required artifact. Capture after-images under matched conditions with the §1 baseline (same device/binary class, settled UI; JS swap by reload only when claiming pixel equivalence). Prefer quantitative screenshot-diff (or equivalent); eyeball alone is insufficient for a “behaves identically” definition of done. Exercise a path that depends on the changed behavior — boot or a consent dialog alone is not enough.

Prefer provisioning a fresh simulator/emulator (or copy-bundle + reinstall) over interrupting a device already in use. Ask only when no alternative exists — a physical device, or a build obtainable nowhere else. Preserve app/device data on devices you do use: do not erase or reset app, simulator, emulator, or device state. Data mutations that are inherent to the flow under test are expected — perform them against test accounts, restore the prior state afterwards, and record both in the QA evidence.

| Surface | Required route and core observations |
| --- | --- |
| Web | Probe `agent-browser --version`; require 0.32.3 or compatible newer and an isolated real browser. Exercise the changed or equivalence flow and affected loading/error/empty states at relevant affected desktop and mobile viewports; inspect semantic DOM/UI, console and failed network requests when networked; capture before/after screenshots and viewport evidence; prefer quantitative screenshot-diff when claiming equivalence. Existing Playwright tests remain regression evidence. Add Playwright for persistent or Chromium/Firefox/WebKit coverage. |
| Android/iOS | Probe the loaded argent MCP toolset for interaction capability (device listing/control, screenshots, and gestures); require those tools to be present in the current session. CLI presence alone does not establish the capability. After the tools are present, optionally probe `argent --version` and require 0.16.0 or compatible newer as a secondary compatibility check. Android also needs `adb` and an emulator; iOS needs macOS, Xcode command-line tools, and a Simulator. Exercise the changed or equivalence flow; inspect accessibility/component state, crashes/errors and failed requests when networked; capture before/after screenshots and performance evidence when performance is in scope; prefer quantitative screenshot-diff when claiming equivalence. |
| CLI | Build the distributable; run with isolated HOME, XDG config/cache/state, and task-specific data. Verify stdout, stderr, exit status, effects, malformed input, expected failures, and idempotence when promised. |
| Backend | Run isolated local dependencies and a real request/job through persistence and intended side effects. Mock only external boundaries. Verify response/status, stored state, logs, expected failures, and retries/idempotence when promised. |

An alternative browser/mobile tool is equivalent only when it supplies every core capability: a real rendered target, semantic inspection, user interaction, crash/log or console inspection, failed-network visibility when applicable, material screenshots, and isolated session control. Missing a core capability is `unverified`, not equivalent.

**Publish evidence.** For visual QA, the session completion report must include the absolute QA evidence directory path and quantitative diff/observation numbers. When the OS allows, open that folder. Do not require or claim harness-inline image display — CLI shells cannot reliably show images to the user. When authorized to open or update a PR: you cannot upload the images yourself. GitHub's `user-attachments` endpoint is browser-upload only — it requires a session cookie, not a token — and private-repo raw or relative links do not render. Do not attempt CLI upload tooling or cookie-extraction extensions. Give the redacted copies a distinct prefix (e.g. `pr-*`) so unredacted captures cannot be published by mistake, open the evidence folder, and ask the human to drag those files into the PR comment box; then fill the body from the returned URLs. If the human declines, put paths and numbers in the PR and state explicitly that images are not on the PR. Never use public image hosts for app UI. Never imply screenshots are on the PR when only local paths exist.

## 13. Record QA outcomes

- `verified`: every mandatory observation and artifact exists and the flow passed; for visual surfaces this includes the published session evidence (absolute QA path plus diff/observation numbers in the completion report).
- `partially verified`: every core observation passed, but a named non-core planned observation was unavailable.
- `unverified`: the flow could not run, the interaction surface was unavailable, or core evidence is missing.

When a named observation is impossible in this environment rather than merely unavailable — a live external system overwrites the seeded state, the surface cannot be isolated — record it as impossible, state why in one line, and record the substitute evidence and its strength. This does not upgrade the outcome: it remains non-passing and still sets `BLOCKED_QA`. It exists so the user sees an honest account of what was proven by other means, rather than a bare `unverified` that undersells it or a `verified` that overstates it.

Only `verified` passes an applicable QA gate. `partially verified` or `unverified` sets `BLOCKED_QA`, records missing evidence, and prevents unqualified completion or branch finishing. Retry only after the user authorizes installation/access or explicitly revises the approved specification so the observation is no longer required; acknowledgement alone is not a pass. If no surface applies, record why.

Missing *capability* tools (browser/mobile MCP, agent-browser, and similar) never authorize installation or configuration by themselves. Use an already-approved capability-equivalent project tool, ask for authorization, or record the blocked outcome. Restoring the project's declared build/test state remains §14 and does not require a stop. Use isolated accounts and local test data. Signed-in sessions, physical devices, production, paid services, and destructive resets require explicit authorization.

## 14. Authorization matrix

**Self-unblocking is an obligation, not a permission.** §§1 and §11 require a workspace that can build and test. When it cannot, restore the project's declared state without asking — install from the committed manifest (`npm install` / `npm ci`, `pod install`, `bundle install`), generate gitignored build artifacts the project expects, rebuild a native dev client, clear project-local tool caches (not shared machine-wide caches). Afterwards, prove declared state is unchanged (manifests and lockfiles byte-identical) and record both the action and the proof in the ledger. If that proof fails, stop and surface the drift. Reporting `BLOCKED` for a condition standard project setup would repair is a failure of the run.

| Action | Default |
| --- | --- |
| Read scoped repository state and public documentation/package metadata | Allowed when relevant and sandbox/network policy permits |
| Modify scoped repository files and make local commits | Allowed by an explicit Shipwright implementation request |
| Restore declared project state (install from lockfile/manifest, generate expected gitignored artifacts, rebuild dev client, clear project-local caches) | Allowed; then prove manifests/lockfiles unchanged |
| Add/upgrade dependencies, mutate lockfile contents intentionally, edit CI/build/`package.json`, install global tools, or configure plugins/MCP | Ask first |
| Write outside the repository or task-specific temporary directories | Ask first |
| Use credentials, signed-in state, external accounts/services, or paid quota | Ask first unless the exact safe system/account is explicitly in scope |
| Contact production; push; open a PR; deploy; publish; message another person/system | Ask first |
| Use physical devices or erase/reset app, simulator, emulator, or device data | Ask first (prefer a fresh simulator/emulator first per §12) |
| Destructive filesystem or git action | Ask first after resolving exact targets read-only |

Never pass `--no-verify` or `-n` to `git commit`. Never put credentials, tokens, personal data, unredacted network payloads, or signed-in state in tracked files, reports, screenshots, or the ledger.

## 15. Finish the branch

Finish only after the approved specification, every task review, whole-change review, fresh verification, and every applicable QA gate passes. Use `superpowers:finishing-a-development-branch`. Report scope, commits, verification, QA state (including absolute QA evidence path and diff/observation numbers when visual QA applied), remaining risks, temporary evidence, and integration options. Include controller effort in the completion report only when resolved or `below recommended`; always record the effort evidence state in the ledger (including `unverifiable`). When authorized to open a PR and effort is disclosable, put that disclosure in the PR body unless repository instructions forbid AI-attribution or tooling references in user-facing text — in which case record the omission and its reason in the ledger rather than breaching the repository's rules. Apply §12 publish rules for screenshots. Never push, open a PR, deploy, or publish without explicit authorization.

## Red flags

| Rationalization | Required response |
| --- | --- |
| “The worker says it passed.” | Inspect artifacts and run fresh controller verification. |
| “The requested profile proves the model.” | Require attributable current-turn evidence. |
| “One more retry might work.” | Enforce the runtime and remediation budgets. |
| “Partial QA is close enough.” | Set `BLOCKED_QA`; only `verified` passes. |
| “Autonomous means external actions are allowed.” | Apply the authorization matrix. |
| “Which approach—Subagent-Driven or Inline?” | Only after an approved plan is saved: override the `writing-plans` handoff, initialize the ledger, and dispatch SDD. Otherwise finish §§1–4 first. |
| “Inline Execution is fine for this plan.” | Only after an approved plan is saved: require `subagent-driven-development`; do not use `executing-plans`. Otherwise finish §§1–4 first. |
| “No UI change, so no screenshots.” | Capture before/after of the unchanged flow; publish path + numbers. |
| “Ask before npm install.” | Restore declared state, prove lockfiles unchanged, record proof. |
