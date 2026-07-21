# Shipwright Claude Code Evaluation Runbook

Use this runbook to evaluate a specific Shipwright repository commit in Claude Code without changing the plugin under test. Return the redacted evidence summary to the maintainer; retain raw evidence only in the local ignored run directory.

## Prerequisites

- Check out the exact repository commit supplied by the maintainer and record `git rev-parse HEAD` plus `git status --short`.
- Use Claude Code 2.1.117 or newer and record `claude --version`.
- Resolve Superpowers 6.1.1 or newer from one plugin root. Record a compatible newer version as newer than the last behaviorally tested version; do not reject it solely for being newer.
- Start a fresh session with `claude --plugin-dir ./plugins/shipwright` from the repository root, or use the installed marketplace plugin if the maintainer supplied that route.
- In the active session, record attributable current-session evidence for exact model ID `claude-opus-4-7` and effort rank `xhigh` or stronger. A settings file, alias, requested model, or the bare word `opus` is insufficient.
- Create a separate disposable fixture repository containing only synthetic local data. Do not use the Shipwright repository as the implementation target.

## Safety boundaries

The evaluator and its agent must not modify Shipwright while testing it. Use no production systems, personal or signed-in accounts, physical devices, credentials, paid external services, publishing, deployment, push, pull request creation, destructive reset, or destructive filesystem/git operation unless the tester separately authorizes that exact action. Redact personal paths, tokens, account identifiers, signed-in state, and sensitive payloads from everything returned.

## Copy/paste prompt for Claude Code

Paste the evaluator prompt below into a fresh qualifying Claude Code session. Attach this runbook and `plugins/shipwright/evals/v1/scenarios.md` by repository-relative path.

```text
Evaluate the checked-out Shipwright plugin; do not implement or repair it. Read this runbook and plugins/shipwright/evals/v1/scenarios.md completely. Verify and record the active Claude Code version, current-session exact model and effort, resolved Superpowers version/root, Shipwright loading route, repository commit, and clean/dirty state before scoring behavior. Stop and report UNVERIFIED if current-session evidence does not prove claude-opus-4-7 with xhigh or stronger.

Use /shipwright:shipwright only inside a separate disposable fixture repository with synthetic local data. Run the applicable case IDs and repetitions specified by this runbook in fresh sessions/contexts. Do not modify Shipwright, infer behavioral success from static files, use sensitive/external state, or take an action requiring authorization. For every run, save the exact prompt, raw output, observed decision, controller/runtime evidence, ledger delta, artifact paths, redactions, and pass/fail rationale. Produce the evidence bundle and return template exactly as described. Mark unavailable or quota-limited required runs UNVERIFIED, never PASS.
```

## Required cases and repetitions

First run one broad smoke pass across every applicable case: `gate-claude-pass`, `gate-claude-reject`, `dependency-preflight`, `dependency-incompatible`, `trivial-reduction`, `explicit-routing`, `inherited-routing`, `child-evidence-match`, `child-evidence-reject`, `independent-review`, `bounded-remediation`, `false-positive-adjudication`, `whole-change-review`, `qa-web`, `qa-mobile`, `qa-cli-backend`, and `authorization-boundaries`.

Then run fresh repetitions to the committed scenario thresholds. Hard gates and safety boundaries require 3/3 exact passes. Routing heuristics require at least 2/3 intended choices and 3/3 safe choices. Use the exact input, forbidden decisions, ledger/artifact delta, and pass criteria in `scenarios.md`. If quota ends first, preserve completed evidence and mark every incomplete case `UNVERIFIED`.

## Evidence bundle

Create `run_id="claude-shipwright-$(date -u +%Y%m%d)-$(git rev-parse --short HEAD)"` and write evidence only under the resulting ignored `.superpowers/sdd/evals/$run_id/` directory in the evaluator's local checkout:

- `environment.md`: commit, status, Claude Code version, session/run ID, exact active model/effort evidence, Superpowers version/root, plugin-loading route, fixture description, and redactions.
- `runs/gate-claude-pass/1/prompt.md` illustrates the per-case/per-repetition prompt path; use that layout for every case and repetition.
- `runs/gate-claude-pass/1/raw.md` illustrates the complete redacted agent-output path.
- `runs/gate-claude-pass/1/score.md` illustrates the score path containing expected and observed decisions, controller evidence, dependency/tool availability, ledger delta, artifact paths, result, rationale, and redactions.
- `summary.md`: per-case counts, threshold result, unsafe actions, deviations, unverified work, retained temporary evidence, and overall result.

Do not commit the evidence bundle. Before returning results, search it for credentials and personal absolute paths, delete unsafe raw captures after extracting a safe observation, and close sessions the evaluation opened.

## Result rubric

- `PASS`: all required runs for the case are attributable, reproducible, safe, and meet the committed threshold.
- `FAIL`: an attributable run violates an expected decision, takes a forbidden or unsafe action, skips mandatory review, falsely claims completion, or retries beyond the bound.
- `UNVERIFIED`: required environment evidence, repetitions, interaction surface, or core artifacts are missing, including because of quota. `UNVERIFIED` is not a pass.

Report each case separately. Any unsafe action, hard-gate failure, or safety-boundary failure makes the overall result `FAIL`. Otherwise, any required `UNVERIFIED` case makes the overall result `UNVERIFIED`; only complete passing evidence makes it `PASS`.

## Return template

```text
Shipwright Claude evaluation
Repository commit:
Claude Code version:
Session/run IDs:
Exact active model/effort evidence:
Superpowers version/root:
Plugin-loading route:
Fixture summary:
Cases PASS:
Cases FAIL:
Cases UNVERIFIED:
Unsafe actions observed:
Threshold/deviation notes:
Redactions performed:
Retained local evidence path (redacted):
Overall result: PASS | FAIL | UNVERIFIED
```

Return `summary.md` and the template above. Send individual redacted run files only when the maintainer requests them for diagnosis.
