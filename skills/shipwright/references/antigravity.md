# Antigravity Runtime and Dispatch Reference

Read this file completely only when Shipwright is running in Google Antigravity (`agy`). The shared `SKILL.md` owns workflow, review, remediation, verification, QA, and authorization.

## Minimum runtime and capability probe

Require Antigravity with plugin skill discovery, subagents (`invoke_subagent`), and current-turn model/effort evidence. Probe the active version and tool schemas; do not infer capabilities from documentation or configuration alone.

Superpowers 6.1.1 or newer must be installed and discoverable as a separate Antigravity plugin (`agy plugin install https://github.com/obra/superpowers`). Shipwright does not vendor Superpowers. Accept an installed-plugin inventory or resolved paths proving one versioned Superpowers package root.

## Controller gate

### Model floor (hard gate)

Require a resolved Gemini model at version `3.7` (Flash or Pro) or newer.

Accept an active model only when current runtime evidence resolves it to the Gemini family at or above the `3.7` floor.

Examples of acceptable evidence forms: harness/display labels such as `Gemini 3.7 Flash`, and IDs/slugs such as `gemini-3.7-flash` or `flash`.

Reject older model generations or unresolved generic labels.

### Recommended effort (disclosed assumption, not a precondition)

Recommended controller effort is `high` (`--effort high`). Recommended controller effort is not a precondition and is never a hard gate.

When effort is available from session/CLI configuration (`--effort high` or UI setting), record resolved effort; otherwise record `unverifiable`. Known effort below `high` still proceeds — record the shortfall as `below recommended`. Never stop solely because controller effort is missing, weak, or unverifiable.

On model-floor failure, stop before all Shipwright artifacts and say: select **Gemini 3.7 Flash or newer**, then provide new current-session evidence so the complete preflight can restart.

## Worker routing

When the controller dispatches implementation tasks or review passes, map subagent model capabilities to Antigravity options:

| Shared task class | Antigravity subagent model |
| --- | --- |
| Mechanical | `flash_lite` or `flash` |
| Ordinary | `flash` (or `inherit`) |
| Integration | `flash` |
| Critical | `pro` |

Dispatch subagents via the `invoke_subagent` tool. Use isolated workspaces (`Workspace: "branch"`) when work requires isolated execution from the controller's main branch.
