# Shipwright native `claude plugin eval` suite

Authoring port of the v1 behavioral scenarios onto `claude plugin eval`
(Claude Code early-access runner). The prose runbooks under `evals/v1/` remain
until this suite has been executed at least once on a flagged Claude Code host.

## Preconditions the runner cannot express

- Claude Code with `CLAUDE_CODE_WALNUT_SPIRE=1` (or the equivalent feature flag).
- Exactly one of `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`.
- Superpowers 6.1.1+ discoverable to the eval agent.
- Shipwright loaded as the plugin under test (path or installed name).
- Tool floors for interactive QA cases remain operator concerns (`agent-browser`,
  argent MCP); harness-independent cases below do not require them.

## Run (on the Claude Code machine)

```sh
CLAUDE_CODE_WALNUT_SPIRE=1 claude plugin eval plugins/shipwright \
  --case 'trivial-reduction' \
  --scaffold \
  --max-cost-usd 5 \
  --judge-model sonnet \
  --threshold 1.0
```

Prefer deterministic graders; paid `llm` / `baseline` graders are reserved for
review quality and false-positive adjudication. On a cost breach, free graders
still score.

## Sequenced cases in this batch

Harness-independent first (this directory):

| Case | Notes |
| --- | --- |
| `trivial-reduction` | Prefer reduction after gate; no `.superpowers/` ledger |
| `dependency-preflight` | Missing Superpowers skill → stop, zero artifacts |
| `dependency-incompatible` | Below-floor / mixed root → stop |
| `authorization-boundaries` | Pressure to install/publish without auth → ask, do not act |
| `qa-cli-backend` | CLI surface → isolated run + verified observations |

Gate and routing cases (`gate-claude-*`, `explicit-routing`, …) follow once this
batch has been executed once. Do not invent synthetic `/status` evidence.

## Layout

Each case is `case.yaml` so `context.scaffold_script` is available. Graders are
inline. `evals/v1/` is not deleted by this port.
