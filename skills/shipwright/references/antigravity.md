# Antigravity Shipwright Runtime Reference

This reference adapts the shared Shipwright workflow to Google Antigravity.

## Controller Model Requirements

Shipwright is a controller skill that manages state transitions, gate evaluation, and subagent orchestration.

- **Recommended Controller Model**: Gemini 3.7 Flash with High Reasoning (`reasoningEffort: "high"`).
- **Subagent Routing**: Subagents are dispatched via the `invoke_subagent` tool.

## Subagent Dispatch Mapping

When the controller dispatches tasks or review passes, map subagent model capabilities to Antigravity options:

- **Light/Exploration Tasks**: `Model: "flash_lite"` or `Model: "flash"`.
- **Standard Implementation / Review**: `Model: "flash"` (or `Model: "inherit"`).
- **High-Complexity Architecture / Medical Safety**: `Model: "pro"`.

Use isolated workspaces (`Workspace: "branch"`) when work requires isolated execution from the controller's main branch.
