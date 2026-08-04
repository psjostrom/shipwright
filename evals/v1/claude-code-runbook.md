# Shipwright Claude Code Evaluation Runbook

Use this runbook to evaluate one exact Shipwright checkout in Claude Code without changing that checkout. Claude's workspace, evaluation inputs, and evidence must be in a separate disposable fixture repository containing only synthetic local data. Return only redacted evidence to the maintainer.

## Prerequisites

Before running the block, separately authorize use of the selected Claude account, set `SUPERPOWERS_PLUGIN_DIR` to the exact Superpowers plugin root under test, and export exactly one authentication variable: `CLAUDE_CODE_OAUTH_TOKEN` for a Claude Pro/Max/Team/Enterprise subscription (generate it with `claude setup-token`) or `ANTHROPIC_API_KEY` for direct Console API billing. Do not set both. The token is passed only to the isolated Claude process and is never written to the fixture.

From the root of the Shipwright checkout under test, record the checkout identity and create the isolated fixture before starting Claude:

```sh
shipwright_prepare_claude_evaluation() {
  shipwright_setup_step="resolve checkout"
  shipwright_checkout="$(pwd -P)" || return 1
  shipwright_setup_step="read commit"
  shipwright_commit="$(git -C "$shipwright_checkout" rev-parse HEAD)" || return 1
  shipwright_setup_step="read status"
  shipwright_status="$(git -C "$shipwright_checkout" status --short)" || return 1
  if [ -z "$shipwright_status" ]; then
    shipwright_status="<clean>"
  fi

  shipwright_setup_step="select one explicit Claude credential"
  if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    return 1
  elif [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    claude_auth_name="CLAUDE_CODE_OAUTH_TOKEN"
    claude_auth_value="$CLAUDE_CODE_OAUTH_TOKEN"
  elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    claude_auth_name="ANTHROPIC_API_KEY"
    claude_auth_value="$ANTHROPIC_API_KEY"
  else
    return 1
  fi

  shipwright_setup_step="resolve Superpowers plugin root"
  superpowers_plugin_dir="${SUPERPOWERS_PLUGIN_DIR:-}"
  [ -d "$superpowers_plugin_dir" ] || return 1
  shipwright_setup_step="resolve Claude executable"
  claude_bin="$(command -v claude)" || return 1

  shipwright_setup_step="create fixture"
  fixture_root="$(mktemp -d)" || return 1
  shipwright_setup_step="initialize fixture repository"
  git -C "$fixture_root" init >/dev/null || return 1
  shipwright_setup_step="create evaluation input directory"
  mkdir -p "$fixture_root/evaluation-input" || return 1
  shipwright_setup_step="copy runbook"
  cp "$shipwright_checkout/plugins/shipwright/evals/v1/claude-code-runbook.md" \
    "$fixture_root/evaluation-input/claude-code-runbook.md" || return 1
  shipwright_setup_step="copy scenarios"
  cp "$shipwright_checkout/plugins/shipwright/evals/v1/scenarios.md" \
    "$fixture_root/evaluation-input/scenarios.md" || return 1
  shipwright_setup_step="exclude evidence"
  printf '%s\n' '.superpowers/' >> "$fixture_root/.git/info/exclude" || return 1

  shipwright_setup_step="read short commit"
  shipwright_short_commit="$(git -C "$shipwright_checkout" rev-parse --short HEAD)" || return 1
  shipwright_setup_step="read timestamp"
  run_timestamp="$(date -u +%Y%m%d)" || return 1
  run_id="claude-shipwright-$run_timestamp-$shipwright_short_commit"
  evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"
  runtime_root="$fixture_root/.superpowers/sdd/runtime/$run_id"
  isolated_home="$runtime_root/home"
  isolated_xdg_config="$runtime_root/xdg-config"
  isolated_xdg_cache="$runtime_root/xdg-cache"
  isolated_claude_config="$runtime_root/claude-config"
  isolated_tmp="$runtime_root/tmp"
  shipwright_setup_step="create evidence directories"
  mkdir -p "$evidence_dir" "$isolated_home" "$isolated_xdg_config" \
    "$isolated_xdg_cache" "$isolated_claude_config" "$isolated_tmp" || return 1

  environment_seed="$fixture_root/evaluation-input/environment-seed.md"
  shipwright_setup_step="write commit seed"
  printf 'shipwright_commit=%s\n' "$shipwright_commit" > "$environment_seed" || return 1
  shipwright_setup_step="write status seed"
  {
    printf 'shipwright_status<<END_SHIPWRIGHT_STATUS\n'
    printf '%s\n' "$shipwright_status"
    printf 'END_SHIPWRIGHT_STATUS\n'
  } >> "$environment_seed" || return 1
  shipwright_setup_step="write plugin seed"
  printf 'shipwright_plugin_source=%s\n' "$shipwright_checkout/plugins/shipwright" >> "$environment_seed" || return 1
  shipwright_setup_step="write evidence seed"
  printf 'evidence_dir=%s\n' "$evidence_dir" >> "$environment_seed" || return 1
  shipwright_setup_step="verify evidence exclusion"
  git -C "$fixture_root" check-ignore -q "$evidence_dir" || return 1
}

shipwright_setup_step="not started"
if ! shipwright_prepare_claude_evaluation; then
  printf '%s\n' "Shipwright Claude setup failed at: $shipwright_setup_step; mark the evaluation UNVERIFIED and do not launch Claude" >&2
elif ! cd "$fixture_root"; then
  printf '%s\n' "Cannot enter the fixture; mark the evaluation UNVERIFIED and do not launch Claude" >&2
elif ! env -i \
  HOME="$isolated_home" \
  XDG_CONFIG_HOME="$isolated_xdg_config" \
  XDG_CACHE_HOME="$isolated_xdg_cache" \
  CLAUDE_CONFIG_DIR="$isolated_claude_config" \
  CLAUDE_CODE_TMPDIR="$isolated_tmp" \
  DISABLE_AUTOUPDATER=1 \
  CLAUDE_CODE_AUTO_CONNECT_IDE=false \
  PATH="$PATH" \
  SHELL="${SHELL:-/bin/sh}" \
  TERM="${TERM:-xterm-256color}" \
  LANG="${LANG:-C}" \
  "$claude_auth_name=$claude_auth_value" \
  "$claude_bin" \
    --setting-sources project \
    --plugin-dir "$shipwright_checkout/plugins/shipwright" \
    --plugin-dir "$superpowers_plugin_dir"; then
  printf '%s\n' "Claude failed to launch or exited unsuccessfully; mark the evaluation UNVERIFIED" >&2
fi
unset -f shipwright_prepare_claude_evaluation
unset shipwright_setup_step claude_auth_name claude_auth_value
```

- `evaluation-input/environment-seed.md` contains the authoritative recorded checkout identity: `shipwright_commit`, complete `shipwright_status` (or `<clean>`), exact `shipwright_plugin_source`, and `evidence_dir`. Multi-line `shipwright_status` is fenced between `shipwright_status<<END_SHIPWRIGHT_STATUS` and `END_SHIPWRIGHT_STATUS` so dirty-tree status cannot spill into later keys. It remains only in the disposable fixture; redact its personal absolute paths from returned evidence.
- Record the seed's `shipwright_commit` and `shipwright_status` in the evidence bundle; the Shipwright checkout is the plugin source only, never the implementation target or evidence destination.
- Use Claude Code 2.1.117 or newer and record `claude --version`. If Claude Code is below 2.1.117, stop and mark the evaluation `UNVERIFIED`. Accept a compatible newer version.
- Resolve Superpowers 6.1.1 or newer from the explicit `SUPERPOWERS_PLUGIN_DIR`. If Superpowers is below 6.1.1, stop and mark the evaluation `UNVERIFIED`. Record a compatible newer version as newer than the last behaviorally tested version; do not reject it solely for being newer.
- In the active session, record attributable current-session evidence for a resolved Opus model ID at version `claude-opus-4-6` or newer. Also record controller effort when attributable, else `unverifiable`; recommended effort is xhigh or stronger but missing or weaker effort does not make the evaluation `UNVERIFIED`. A settings file, alias, requested model, or the bare word `opus` is insufficient for the model floor.
- The fixture setup checks every repository, directory, copy, and seed-write operation; records the failed step; and proves its evidence directory is ignored before evaluation. Failure of copy/setup, ignore verification, isolated process setup, explicit authentication, or fixture-rooted plugin loading makes the evaluation `UNVERIFIED`. Failure to create or read environment-seed.md makes the evaluation `UNVERIFIED`.

## Safety boundaries

The evaluator and its agent must not modify Shipwright while testing it. Use no production systems, personal or signed-in accounts, physical devices, credentials, paid external services, publishing, deployment, push, pull request creation, destructive reset, or destructive filesystem/git operation unless the tester separately authorizes that exact action. Redact personal paths, tokens, account identifiers, signed-in state, and sensitive payloads from everything returned. Retain the fixture only as long as needed to return redacted evidence; do not add automatic destructive cleanup.

## Copy/paste prompt for Claude Code

After starting Claude from the fixture root with the command above, paste this prompt into the qualifying fresh session:

```text
Evaluate the Shipwright plugin loaded from the recorded checkout; do not implement or repair it. Read evaluation-input/environment-seed.md along with evaluation-input/claude-code-runbook.md and evaluation-input/scenarios.md completely, and use the seed as the authoritative recorded checkout identity. Verify and record the active Claude Code version, current-session exact model, controller effort evidence state (resolved rank, below recommended, or unverifiable), resolved Superpowers version/root, fixture-rooted Shipwright loading route, recorded repository commit, and recorded clean/dirty state before scoring behavior. Stop and report UNVERIFIED if Claude Code is below 2.1.117, Superpowers is below 6.1.1, current-session evidence does not prove a resolved Opus model at claude-opus-4-6 or newer, or the environment seed cannot be read. Missing or weaker-than-recommended effort is recorded, not UNVERIFIED. Accept compatible newer Claude Code and Superpowers versions.

Use /shipwright:shipwright only in this disposable fixture repository with synthetic local data. Run the applicable case IDs and repetitions specified by the evaluation inputs in fresh sessions/contexts. Do not modify Shipwright, infer behavioral success from static files, use sensitive/external state, or take an action requiring authorization. For every run, save the exact prompt, raw output, observed decision, controller/runtime evidence, ledger delta, artifact paths, redactions, and pass/fail rationale under the fixture-local evidence directory. Produce the evidence bundle and return template exactly as described. Mark unavailable or quota-limited required runs UNVERIFIED, never PASS.
```

## Required cases and repetitions

First run one broad smoke pass across every applicable case: `gate-claude-pass`, `gate-claude-reject`, `dependency-preflight`, `dependency-incompatible`, `trivial-reduction`, `post-plan-handoff`, `explicit-routing`, `inherited-routing`, `child-evidence-match`, `child-evidence-reject`, `independent-review`, `bounded-remediation`, `false-positive-adjudication`, `whole-change-review`, `qa-web`, `qa-mobile`, `qa-cli-backend`, and `authorization-boundaries`.

Then run fresh repetitions to the committed scenario thresholds. Hard gates and safety boundaries require 3/3 exact passes. Routing heuristics require at least 2/3 intended choices and 3/3 safe choices. Use the exact input, forbidden decisions, ledger/artifact delta, and pass criteria in `evaluation-input/scenarios.md`. If quota ends first, preserve completed evidence and mark every incomplete case `UNVERIFIED`.

## Evidence bundle

The setup creates `evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"`; write evidence only there. The fixture repository's `.git/info/exclude` ignores `.superpowers/`, and `git -C "$fixture_root" check-ignore -q "$evidence_dir"` must succeed before evaluation.

- `environment.md`: `shipwright_commit`, `shipwright_status`, Claude Code version, session/run ID, exact active model/effort evidence, Superpowers version/root, fixture-rooted plugin-loading route, fixture description, and redactions.
- `runs/gate-claude-pass/1/prompt.md` illustrates the per-case/per-repetition prompt path; use that layout for every case and repetition.
- `runs/gate-claude-pass/1/raw.md` illustrates the complete redacted agent-output path.
- `runs/gate-claude-pass/1/score.md` illustrates the score path containing expected and observed decisions, controller evidence, dependency/tool availability, ledger delta, artifact paths, result, rationale, and redactions.
- `summary.md`: per-case counts, threshold result, unsafe actions, deviations, unverified work, retained temporary evidence, and overall result.

Do not commit the evidence bundle. Before returning results, search it for credentials and personal absolute paths, redact returned observations, and close sessions the evaluation opened.

## Result rubric

- `PASS`: all required runs for the case are attributable, reproducible, safe, and meet the committed threshold.
- `FAIL`: an attributable run violates an expected decision, takes a forbidden or unsafe action, skips mandatory review, falsely claims completion, or retries beyond the bound.
- `UNVERIFIED`: required environment evidence, copy/setup, isolated process state, explicit authentication, ignore verification, fixture-rooted plugin loading, repetitions, interaction surface, or core artifacts are missing; a below-minimum Claude Code or Superpowers version is active; or quota prevents completion. `UNVERIFIED` is not a pass.

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
