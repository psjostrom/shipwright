#!/usr/bin/env python3
"""Deterministically validate the Shipwright cross-platform plugin bundle."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

PLUGIN_ROOT = Path(".")
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
CURSOR_MANIFEST = PLUGIN_ROOT / ".cursor-plugin/plugin.json"
ANTIGRAVITY_MANIFEST = PLUGIN_ROOT / "plugin.json"
SKILL = PLUGIN_ROOT / "skills/shipwright/SKILL.md"
OPENAI_METADATA = PLUGIN_ROOT / "skills/shipwright/agents/openai.yaml"
CODEX_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/codex.md"
CLAUDE_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/claude-code.md"
CURSOR_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/cursor.md"
ANTIGRAVITY_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/antigravity.md"
README = Path("README.md")

DESCRIPTION = (
    "Strict end-to-end development with adaptive subagents, independent review, "
    "and real verification."
)
SKILL_DESCRIPTION = (
    "Use when the user explicitly requests Shipwright, full end-to-end development, "
    "autonomous implementation with subagents, or implementation plus independent "
    "iterative review and real verification; do not use for factual questions, "
    "read-only review, diagnosis without a requested fix, or tiny mechanical edits."
)
KEYWORDS = ["development", "subagents", "code-review", "verification", "qa"]
CODEX_INVOCATION = "$shipwright:shipwright"
CLAUDE_INVOCATION = "/shipwright:shipwright"
CURSOR_INVOCATION = "/shipwright"
CURSOR_INVOCATION_DOC = "`/shipwright` in Cursor"
# Accept `/shipwright` or bare /shipwright as a slash-command, not path segments
# like .../plugins/shipwright/... and not Claude's /shipwright:shipwright.
_CURSOR_BARE_INVOCATION_RE = re.compile(
    r"(?:`/shipwright`|(?<![/\w])/shipwright(?![/\w:]))"
)
DEFAULT_PROMPT = (
    "Use $shipwright:shipwright to build this feature end to end with independent "
    "review and real verification."
)
CODEX_INSTALL_ROUTE = (
    "codex plugin marketplace add psjostrom/agent-plugins\n"
    "codex plugin add shipwright@agent-plugins"
)


def _has_cursor_invocation(text: str) -> bool:
    """True when text contains bare /shipwright, not only /shipwright:shipwright."""

    return _CURSOR_BARE_INVOCATION_RE.search(text) is not None


def _display(path: Path) -> str:
    return path.as_posix()


def _load_json(repo_root: Path, relative_path: Path, errors: list[str]) -> Any:
    path = repo_root / relative_path
    if not path.is_file():
        errors.append(f"missing required JSON file: {_display(relative_path)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"malformed JSON in {_display(relative_path)}: {exc}")
        return None


def _read_text(
    repo_root: Path, relative_path: Path, errors: list[str]
) -> Optional[str]:
    path = repo_root / relative_path
    if not path.is_file():
        errors.append(f"missing required file: {_display(relative_path)}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read {_display(relative_path)}: {exc}")
        return None


def _value_at(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _require_equal(
    data: Any,
    keys: tuple[str, ...],
    expected: Any,
    label: str,
    source_path: Path,
    errors: list[str],
) -> None:
    actual = _value_at(data, *keys)
    if actual != expected:
        errors.append(
            f"{_display(source_path)}: {label} must be {expected!r}; found {actual!r}"
        )


def _valid_codex_version(value: Any) -> bool:
    """Match the cachebuster form emitted by update_plugin_cachebuster.py."""

    return (
        isinstance(value, str)
        and re.fullmatch(r"1\.0\.0(?:\+codex\.[a-z0-9]+(?:-[a-z0-9]+)*)?", value)
        is not None
    )


def _validate_manifests(
    codex: Any, claude: Any, cursor: Any, antigravity: Any, errors: list[str]
) -> None:
    if isinstance(codex, dict):
        _require_equal(
            codex,
            ("name",),
            "shipwright",
            "Codex manifest name",
            CODEX_MANIFEST,
            errors,
        )
        if not _valid_codex_version(codex.get("version")):
            errors.append(
                f"{_display(CODEX_MANIFEST)}: Codex manifest version must be '1.0.0' "
                "or '1.0.0+codex.<cachebuster>'"
            )
        _require_equal(
            codex,
            ("description",),
            DESCRIPTION,
            "Codex manifest description",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("author", "name"),
            "psjostrom",
            "Codex manifest author.name",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("author", "url"),
            "https://github.com/psjostrom",
            "Codex manifest author.url",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("repository",),
            "https://github.com/psjostrom/shipwright",
            "Codex manifest repository",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("keywords",),
            KEYWORDS,
            "Codex manifest keywords",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(
            codex,
            ("skills",),
            "./skills/",
            "Codex manifest skills path",
            CODEX_MANIFEST,
            errors,
        )

        interface_expectations = {
            "displayName": "Shipwright",
            "shortDescription": "Strict end-to-end development workflow",
            "longDescription": (
                "Build approved work through adaptive implementation, independent "
                "iterative review, fresh verification, and applicable browser, "
                "mobile, CLI, or backend QA."
            ),
            "developerName": "psjostrom",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Read", "Write"],
            "defaultPrompt": [DEFAULT_PROMPT],
        }
        for key, expected in interface_expectations.items():
            _require_equal(
                codex,
                ("interface", key),
                expected,
                f"Codex interface {key}",
                CODEX_MANIFEST,
                errors,
            )
    elif codex is not None:
        errors.append(
            f"{_display(CODEX_MANIFEST)}: Codex manifest root must be a JSON object"
        )

    if isinstance(claude, dict):
        _require_equal(
            claude,
            ("name",),
            "shipwright",
            "Claude manifest name",
            CLAUDE_MANIFEST,
            errors,
        )
        # Claude omits version so updates track git commit SHA. Cursor/Codex keep
        # an explicit pin; that asymmetry is intentional — do not restore Claude
        # version for cross-platform symmetry.
        if "version" in claude:
            errors.append(
                f"{_display(CLAUDE_MANIFEST)}: Claude manifest must omit version "
                f"(SHA-tracked delivery); found {claude.get('version')!r}"
            )
        _require_equal(
            claude,
            ("description",),
            DESCRIPTION,
            "Claude manifest description",
            CLAUDE_MANIFEST,
            errors,
        )
        _require_equal(
            claude,
            ("author", "name"),
            "psjostrom",
            "Claude manifest author.name",
            CLAUDE_MANIFEST,
            errors,
        )
        _require_equal(
            claude,
            ("keywords",),
            KEYWORDS,
            "Claude manifest keywords",
            CLAUDE_MANIFEST,
            errors,
        )
    elif claude is not None:
        errors.append(
            f"{_display(CLAUDE_MANIFEST)}: Claude manifest root must be a JSON object"
        )

    if isinstance(cursor, dict):
        _require_equal(
            cursor,
            ("name",),
            "shipwright",
            "Cursor manifest name",
            CURSOR_MANIFEST,
            errors,
        )
        if cursor.get("version") != "1.0.0":
            errors.append(
                f"{_display(CURSOR_MANIFEST)}: Cursor manifest version must be exactly '1.0.0'; "
                f"found {cursor.get('version')!r}"
            )
        _require_equal(
            cursor,
            ("displayName",),
            "Shipwright",
            "Cursor manifest displayName",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("description",),
            DESCRIPTION,
            "Cursor manifest description",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("author", "name"),
            "psjostrom",
            "Cursor manifest author.name",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("author", "url"),
            "https://github.com/psjostrom",
            "Cursor manifest author.url",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("repository",),
            "https://github.com/psjostrom/shipwright",
            "Cursor manifest repository",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("keywords",),
            KEYWORDS,
            "Cursor manifest keywords",
            CURSOR_MANIFEST,
            errors,
        )
        _require_equal(
            cursor,
            ("skills",),
            "./skills/",
            "Cursor manifest skills path",
            CURSOR_MANIFEST,
            errors,
        )
    elif cursor is not None:
        errors.append(
            f"{_display(CURSOR_MANIFEST)}: Cursor manifest root must be a JSON object"
        )

    if isinstance(antigravity, dict):
        _require_equal(
            antigravity,
            ("name",),
            "shipwright",
            "Antigravity manifest name",
            ANTIGRAVITY_MANIFEST,
            errors,
        )
        if "version" in antigravity:
            errors.append(
                f"{_display(ANTIGRAVITY_MANIFEST)}: Antigravity manifest must omit version "
                f"(SHA-tracked delivery); found {antigravity.get('version')!r}"
            )
        _require_equal(
            antigravity,
            ("description",),
            DESCRIPTION,
            "Antigravity manifest description",
            ANTIGRAVITY_MANIFEST,
            errors,
        )
    elif antigravity is not None:
        errors.append(
            f"{_display(ANTIGRAVITY_MANIFEST)}: Antigravity manifest root must be a JSON object"
        )


def _parse_yaml_scalar(
    raw_value: str, relative_path: Path, line_number: int, errors: list[str]
) -> Any:
    raw_value = _strip_yaml_inline_comment(raw_value).rstrip()
    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            errors.append(
                f"{_display(relative_path)}:{line_number}: malformed double-quoted scalar: {exc.msg}"
            )
            return None
        if not isinstance(value, str):
            errors.append(
                f"{_display(relative_path)}:{line_number}: quoted scalar must be a string"
            )
            return None
        return value
    if raw_value.startswith("'"):
        if len(raw_value) < 2 or not raw_value.endswith("'"):
            errors.append(
                f"{_display(relative_path)}:{line_number}: malformed single-quoted scalar"
            )
            return None
        interior = raw_value[1:-1]
        decoded: list[str] = []
        index = 0
        while index < len(interior):
            if interior[index] != "'":
                decoded.append(interior[index])
                index += 1
                continue
            if index + 1 < len(interior) and interior[index + 1] == "'":
                decoded.append("'")
                index += 2
                continue
            errors.append(
                f"{_display(relative_path)}:{line_number}: malformed single-quoted scalar"
            )
            return None
        return "".join(decoded)
    if raw_value.endswith(("'", '"')):
        errors.append(
            f"{_display(relative_path)}:{line_number}: malformed quoted scalar"
        )
        return None
    if raw_value.lower() == "true":
        return True
    if raw_value.lower() == "false":
        return False
    return raw_value


def _strip_yaml_inline_comment(raw_value: str) -> str:
    """Remove a YAML separation comment without treating quoted hashes as comments."""

    quote = raw_value[0] if raw_value.startswith(("'", '"')) else None
    index = 1 if quote is not None else 0
    in_quote = quote is not None
    while index < len(raw_value):
        character = raw_value[index]
        if in_quote and quote == '"' and character == "\\":
            index += 2
            continue
        if in_quote and character == quote:
            if (
                quote == "'"
                and index + 1 < len(raw_value)
                and raw_value[index + 1] == "'"
            ):
                index += 2
                continue
            in_quote = False
        elif (
            not in_quote
            and character == "#"
            and (index == 0 or raw_value[index - 1].isspace())
        ):
            return raw_value[:index].rstrip()
        index += 1
    return raw_value.rstrip()


def _parse_constrained_yaml(
    yaml_text: str, relative_path: Path, errors: list[str]
) -> dict[str, Any]:
    """Parse the mapping-only YAML subset used by Shipwright metadata files."""

    entries: list[tuple[int, int, str, str]] = []
    for line_number, line in enumerate(yaml_text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        leading = line[: len(line) - len(line.lstrip(" "))]
        if "\t" in line[: len(line) - len(line.lstrip())]:
            errors.append(
                f"{_display(relative_path)}:{line_number}: tabs are unsupported in YAML indentation"
            )
            continue
        indentation = len(leading)
        if indentation % 2:
            errors.append(
                f"{_display(relative_path)}:{line_number}: YAML indentation must use two-space levels"
            )
            continue
        match = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_-]*):(?:[ ]*(.*))?", line[indentation:]
        )
        if match is None:
            errors.append(
                f"{_display(relative_path)}:{line_number}: unsupported YAML mapping line: {line!r}"
            )
            continue
        entries.append((line_number, indentation, match.group(1), match.group(2) or ""))

    index = 0

    def parse_block(indentation: int) -> dict[str, Any]:
        nonlocal index
        result: dict[str, Any] = {}
        while index < len(entries):
            line_number, current_indent, key, raw_value = entries[index]
            if current_indent < indentation:
                break
            if current_indent > indentation:
                errors.append(
                    f"{_display(relative_path)}:{line_number}: unexpected YAML indentation"
                )
                index += 1
                continue

            index += 1
            duplicate = key in result
            if duplicate:
                errors.append(
                    f"{_display(relative_path)}:{line_number}: duplicate YAML key {key!r}"
                )

            raw_value = _strip_yaml_inline_comment(raw_value).rstrip()
            if raw_value:
                value = _parse_yaml_scalar(
                    raw_value, relative_path, line_number, errors
                )
                if index < len(entries) and entries[index][1] > indentation:
                    nested_line = entries[index][0]
                    errors.append(
                        f"{_display(relative_path)}:{nested_line}: scalar key {key!r} "
                        "cannot contain nested keys"
                    )
                    parse_block(entries[index][1])
            elif index < len(entries) and entries[index][1] > indentation:
                child_indent = entries[index][1]
                if child_indent != indentation + 2:
                    errors.append(
                        f"{_display(relative_path)}:{entries[index][0]}: nested YAML keys "
                        "must indent exactly two spaces"
                    )
                value = parse_block(child_indent)
            else:
                value = {}

            if not duplicate:
                result[key] = value
        return result

    if not entries:
        return {}
    if entries[0][1] != 0:
        errors.append(
            f"{_display(relative_path)}:{entries[0][0]}: top-level YAML key must not be indented"
        )
    return parse_block(entries[0][1])


def _parse_frontmatter(skill_text: str, errors: list[str]) -> Optional[dict[str, Any]]:
    lines = skill_text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{_display(SKILL)} must start with YAML frontmatter")
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line == "---")
    except StopIteration:
        errors.append(f"{_display(SKILL)} has unterminated YAML frontmatter")
        return None

    return _parse_constrained_yaml("\n".join(lines[1:end]), SKILL, errors)


def _require_markers(
    content: Optional[str],
    markers: tuple[tuple[str, str], ...],
    relative_path: Path,
    errors: list[str],
) -> None:
    if content is None:
        return
    for marker, label in markers:
        if marker not in content:
            errors.append(f"{_display(relative_path)} is missing {label}: {marker!r}")


def _forbid_markers(
    content: Optional[str],
    markers: tuple[tuple[str, str], ...],
    relative_path: Path,
    errors: list[str],
) -> None:
    if content is None:
        return
    active = _active_markdown(content)
    for marker, label in markers:
        if marker in active:
            errors.append(
                f"{_display(relative_path)} must not contain {label}: {marker!r}"
            )


def _active_markdown(markdown: str) -> str:
    """Return Markdown text outside fenced code blocks and HTML comments."""

    active_lines: list[str] = []
    in_comment = False
    fence_character: Optional[str] = None
    fence_length = 0

    for original_line in markdown.splitlines():
        if fence_character is not None:
            closing_fence = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                original_line,
            )
            if closing_fence is not None:
                fence_character = None
                fence_length = 0
            continue

        if not in_comment:
            opening_fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", original_line)
            if opening_fence is not None:
                marker = opening_fence.group(1)
                info_string = opening_fence.group(2)
                if marker[0] != "`" or "`" not in info_string:
                    fence_character = marker[0]
                    fence_length = len(marker)
                    continue
            if re.match(r"^(?: {4}| {0,3}\t)", original_line):
                continue

        line_parts: list[str] = []
        cursor = 0
        while cursor < len(original_line):
            if in_comment:
                comment_end = original_line.find("-->", cursor)
                if comment_end < 0:
                    cursor = len(original_line)
                    break
                in_comment = False
                cursor = comment_end + 3
                continue

            if original_line[cursor] == "`":
                run_end = cursor + 1
                while run_end < len(original_line) and original_line[run_end] == "`":
                    run_end += 1
                run_length = run_end - cursor
                closing_start = run_end
                while closing_start < len(original_line):
                    if original_line[closing_start] != "`":
                        closing_start += 1
                        continue
                    closing_end = closing_start + 1
                    while (
                        closing_end < len(original_line)
                        and original_line[closing_end] == "`"
                    ):
                        closing_end += 1
                    if closing_end - closing_start == run_length:
                        line_parts.append(original_line[cursor:closing_end])
                        cursor = closing_end
                        break
                    closing_start = closing_end
                else:
                    line_parts.append(original_line[cursor:run_end])
                    cursor = run_end
                continue

            if original_line.startswith("<!--", cursor):
                in_comment = True
                cursor += 4
                continue

            line_parts.append(original_line[cursor])
            cursor += 1

        line = "".join(line_parts)
        if re.match(r"^(?: {4}| {0,3}\t)", line):
            continue
        active_lines.append(line)

    return "\n".join(active_lines)


def _validate_skill_text(
    repo_root: Path,
    skill_text: Optional[str],
    errors: list[str],
) -> None:
    skill_root = repo_root
    if skill_root.is_dir():
        skill_files = sorted(
            path.relative_to(repo_root).as_posix()
            for path in skill_root.rglob("SKILL.md")
        )
        expected = [_display(SKILL)]
        if skill_files != expected:
            errors.append(
                "Shipwright must expose exactly one SKILL.md workflow surface at "
                f"{_display(SKILL)}; found {skill_files!r}"
            )

    if skill_text is not None:
        frontmatter = _parse_frontmatter(skill_text, errors)
        if frontmatter is not None:
            _require_equal(
                frontmatter,
                ("name",),
                "shipwright",
                "Shipwright SKILL.md frontmatter name",
                SKILL,
                errors,
            )
            _require_equal(
                frontmatter,
                ("description",),
                SKILL_DESCRIPTION,
                "Shipwright SKILL.md frontmatter description",
                SKILL,
                errors,
            )
            if set(frontmatter) != {"name", "description", "disable-model-invocation"}:
                errors.append(
                    f"{_display(SKILL)}: Shipwright SKILL.md frontmatter keys must be "
                    "exactly ['description', 'disable-model-invocation', 'name']; "
                    f"found {sorted(frontmatter)!r}"
                )
            _require_equal(
                frontmatter,
                ("disable-model-invocation",),
                True,
                "Shipwright SKILL.md frontmatter disable-model-invocation",
                SKILL,
                errors,
            )
        if len(skill_text.splitlines()) >= 500:
            errors.append(
                f"{_display(SKILL)}: Shipwright shared SKILL.md must be fewer than 500 lines"
            )

    if skill_text is not None:
        if not _has_cursor_invocation(skill_text):
            errors.append(
                f"{_display(SKILL)} is missing Cursor invocation: bare {CURSOR_INVOCATION!r} "
                f"(not only {CLAUDE_INVOCATION!r})"
            )
        if CURSOR_INVOCATION_DOC not in skill_text:
            errors.append(
                f"{_display(SKILL)} is missing Cursor invocation docs: {CURSOR_INVOCATION_DOC!r}"
            )

    _require_markers(
        skill_text,
        (
            (CODEX_INVOCATION, "Codex invocation"),
            (CLAUDE_INVOCATION, "Claude invocation"),
            (
                "[references/codex.md](references/codex.md)",
                "reachable Codex reference link",
            ),
            (
                "[references/claude-code.md](references/claude-code.md)",
                "reachable Claude reference link",
            ),
            (
                "[references/cursor.md](references/cursor.md)",
                "reachable Cursor reference link",
            ),
            (
                "[references/antigravity.md](references/antigravity.md)",
                "reachable Antigravity reference link",
            ),
            (
                "do not present Superpowers `writing-plans` execution options",
                "post-plan execution handoff override",
            ),
            (
                "offer `superpowers:executing-plans` / Inline Execution",
                "post-plan Inline Execution rejection",
            ),
            (
                "Shipwright overrides that handoff",
                "post-plan handoff ownership",
            ),
            (
                "do not wait for the user to choose an execution mode",
                "post-plan no execution-mode ask",
            ),
            ("thread/run ID", "child runtime evidence contract"),
            (
                "when the selected route defines an effort floor",
                "conditional effort evidence contract",
            ),
            (
                "absent effort is allowed only when that route defines none, or when the selected platform reference waives the effort dimension",
                "absent effort evidence contract",
            ),
            (
                "including before any §3 reduction",
                "controller gate before trivial reduction",
            ),
            (
                "and the verification surface it can affect is narrow",
                "§3 verification-surface reduction criterion",
            ),
            (
                "§11 fresh verification, or §12 QA routing",
                "§3 reduction never waives verification or QA",
            ),
            (
                "do not create or modify project-level configuration",
                "§3 reduced path no unrequested project config",
            ),
            (
                "Recommended controller effort is not a precondition",
                "shared controller effort disclosure rule",
            ),
            (
                "suppress `unverifiable` from the user-facing completion report",
                "controller effort suppress unverifiable from completion report",
            ),
            (
                "and from any authorized PR body",
                "controller effort suppress unverifiable from authorized PR body",
            ),
            (
                "always record the effort evidence state in the ledger",
                "controller effort always recorded in ledger",
            ),
            (
                "forbid AI-attribution or tooling references in user-facing text",
                "controller effort PR disclosure yields to repo rules",
            ),
            (
                "compare it to the plugin install record",
                "§1 loaded skill vs install-record check",
            ),
            (
                "Do not accept a workspace inside a tool-owned directory",
                "§1 refuse tool-owned workspace placement",
            ),
            (
                "Run an explicit discovery or collection command",
                "§1 prove test discovery in workspace",
            ),
            (
                "compare filtered path *sets*",
                "§1 discovery uses path sets not counts",
            ),
            (
                "run at least one real known-good test to green",
                "§1 prove test execution not only discovery",
            ),
            (
                "Do not treat a single targeted known-good test as sufficient",
                "§1 reject targeted-test discovery substitute",
            ),
            (
                "capture baseline screens at the merge base",
                "§1 baseline screens before implementation",
            ),
            (
                "measure it at the merge base",
                "§11 measure gates at merge base",
            ),
            (
                "Piping a command to `tail` or `head` replaces its exit status",
                "§11 piped exit-status warning",
            ),
            (
                "Redirect to a file and read `$?`",
                "§11 file-backed tool exit status",
            ),
            (
                "harness-reported completion code for a compound command is not the tool's exit status",
                "§11 harness completion exit is not tool exit",
            ),
            (
                "docs/superpowers/",
                "§5 writing-plans path exclusion",
            ),
            (
                "the controller owns persistence where the platform prevents children from writing files",
                "§5 controller-owned report persistence",
            ),
            (
                "Take the child thread/run ID from the harness spawn result",
                "§7 child run ID from harness spawn",
            ),
            (
                "**Orphaned work.**",
                "§7 orphaned-work adoption path",
            ),
            (
                "non-destructive ownership and diff-scope check",
                "§7 orphaned-work red-tree ownership check",
            ),
            (
                "Controller statements are not verification either",
                "§8 controller statements are not verification",
            ),
            (
                "**Reading evidence.**",
                "§8 reading evidence section",
            ),
            (
                "Read exit status from a value written to a file",
                "§8 reading evidence file-backed exit status",
            ),
            (
                "declare the plan frozen with the ledger authoritative",
                "§8 plan vs ledger after remediation override",
            ),
            (
                "may serve both the final task's §8 gate and this whole-change gate",
                "§10 final-task review consolidation",
            ),
            (
                "With exactly one task, that consolidation is allowed",
                "§10 single-task consolidation case",
            ),
            (
                "Screenshots are mandatory for applicable visual surfaces",
                "§12 mandatory screenshots",
            ),
            (
                "identical before/after screens are the required artifact",
                "§12 before/after screens required artifact",
            ),
            (
                "absolute QA evidence directory path",
                "§12 absolute QA evidence path in completion report",
            ),
            (
                "quantitative diff/observation numbers",
                "§12 quantitative diff or observation numbers",
            ),
            (
                "Prefer provisioning a fresh simulator/emulator",
                "§12 prefer fresh simulator",
            ),
            (
                "That path is storage, not publication",
                "§12 QA path is storage not publication",
            ),
            (
                "Data mutations that are inherent to the flow under test are expected",
                "§12 flow-inherent QA data mutations",
            ),
            (
                "Escalate the class when the work is hard to reverse",
                "§6 irreversibility escalation",
            ),
            (
                "Exact-code plan steps carry correctness risk",
                "§4 exact-code plan caution",
            ),
            (
                "Any literal expected value must either be measured",
                "§4 literal expected values must be measured",
            ),
            (
                "work on a branch in the main checkout instead",
                "§1 worktree exception for generated gitignored files",
            ),
            (
                "When §1's generated-gitignored-file exception applies, skip the fresh worktree",
                "§4 worktree handoff honors §1 generated-file exception",
            ),
            (
                "Resolve it before dispatch, not at commit time",
                "§1 commit-gate preflight against task files",
            ),
            (
                "you cannot upload the images yourself",
                "§12 PR images require human browser upload",
            ),
            (
                "Give the redacted copies a distinct prefix",
                "§12 redacted PR image naming prefix",
            ),
            (
                "record it as impossible, state why in one line",
                "§13 structurally impossible named observations",
            ),
            (
                "This does not upgrade the outcome: it remains non-passing",
                "§13 impossible observation stays non-passing",
            ),
            (
                "Never stop solely because controller effort is missing, weak, or unverifiable",
                "controller effort never hard-stops",
            ),
            (
                "unreadable platform reference is a stop condition",
                "unreadable platform reference stop",
            ),
            (
                "Independently validate each reported dimension",
                "independent evidence dimensions contract",
            ),
            (
                "Any unknown nonempty model or effort label is unverified.",
                "unknown effort evidence rejection",
            ),
            ("one fallback per gated role", "runtime retry contract"),
            ("BLOCKED_RUNTIME", "BLOCKED_RUNTIME terminal state"),
            ("fresh independent reviewer", "independent review contract"),
            ("at most two ordinary remediation cycles", "two remediation cycle cap"),
            (
                "at most two context-repair redispatches",
                "context-repair retry cap",
            ),
            (
                "If the second redispatch still returns `NEEDS_CONTEXT`, set `BLOCKED`",
                "NEEDS_CONTEXT terminal transition",
            ),
            (
                "`resumable: awaiting user context`",
                "NEEDS_CONTEXT ledger state",
            ),
            (
                "Do not dispatch again automatically.",
                "NEEDS_CONTEXT automatic stop",
            ),
            (
                "the user supplies the missing context and explicitly asks to continue",
                "NEEDS_CONTEXT user-authorized reopen",
            ),
            (
                "reset the two-redispatch context-repair budget",
                "NEEDS_CONTEXT post-intervention budget",
            ),
            ("one final escalated attempt", "escalated remediation contract"),
            ("agent-browser", "agent-browser web QA route"),
            ("Playwright", "Playwright web regression route"),
            ("argent", "Argent mobile QA route"),
            (
                "loaded argent MCP toolset",
                "Argent mobile QA MCP-tool probe",
            ),
            (
                "CLI presence alone does not establish the capability",
                "Argent CLI not sufficient for mobile QA",
            ),
            ("BLOCKED_QA", "BLOCKED_QA terminal state"),
            (
                "Self-unblocking is an obligation, not a permission",
                "§14 self-unblocking obligation",
            ),
            (
                "clear project-local tool caches",
                "§14 project-local cache clearing only",
            ),
            (
                "Restore declared project state",
                "authorization boundary for restoring declared state",
            ),
            (
                "manifests and lockfiles byte-identical",
                "§14 byte-identical restoration proof",
            ),
            (
                "record both the action and the proof in the ledger",
                "§14 restoration proof recorded in ledger",
            ),
            (
                "If that proof fails, stop and surface the drift",
                "§14 restoration drift handling",
            ),
            (
                "Add/upgrade dependencies, mutate lockfile contents intentionally",
                "authorization boundary for changing declared state",
            ),
            (
                "Never pass `--no-verify` or `-n` to `git commit`",
                "forbid git commit --no-verify",
            ),
            ("paid quota", "authorization boundary for paid quota"),
            (
                "push; open a PR; deploy; publish",
                "authorization boundary for publication actions",
            ),
            (
                "Destructive filesystem or git action",
                "authorization boundary for destructive actions",
            ),
        ),
        SKILL,
        errors,
    )
    _forbid_markers(
        skill_text,
        (
            (
                "when obtainable without new credentials or policy breach",
                "§12 soft PR-upload hedge",
            ),
        ),
        SKILL,
        errors,
    )

    if skill_text is not None:
        active_skill_text = _active_markdown(skill_text)
        for outcome in ("verified", "partially verified", "unverified"):
            definition = re.compile(
                rf"^ {{0,3}}-\s+`{re.escape(outcome)}`:\s+\S.*$", re.MULTILINE
            )
            if definition.search(active_skill_text) is None:
                errors.append(
                    f"{_display(SKILL)} is missing standalone QA outcome definition "
                    f"for {outcome!r}"
                )


def _validate_codex_text(
    codex_text: Optional[str],
    errors: list[str],
) -> None:
    _require_markers(
        codex_text,
        (
            ("gpt-5.6-sol", "Codex controller gate minimum model version"),
            (
                "Require a resolved Sol model at version `5.6` or newer",
                "Codex controller gate numeric floor",
            ),
            (
                "Recommended controller effort rank is `high` or stronger",
                "Codex recommended controller effort",
            ),
            (
                "Recommended controller effort is not a precondition",
                "Codex controller effort not a precondition",
            ),
            ("select **GPT-5.6 Sol or newer**", "Codex controller gate guidance"),
            (
                "generic labels such as `GPT-5`",
                "Codex controller evidence rejection",
            ),
            (
                "Never stop solely because controller effort is missing, weak, or unverifiable",
                "Codex controller effort never hard-stops",
            ),
            ("| Mechanical | Luna 5.6+ / Max |", "Codex worker routing mechanical"),
            ("| Ordinary | Luna 5.6+ / Max |", "Codex worker routing ordinary"),
            ("| Integration | Luna 5.6+ / Max |", "Codex worker routing integration"),
            ("| Critical | Sol 5.6+ / High |", "Codex worker routing critical"),
            (
                "Require a resolved Luna or Sol worker model at version `5.6` or newer",
                "Codex worker version floor",
            ),
            ("standard: Luna 5.6+ / Max", "Codex standard complete route"),
            (
                "critical: Sol 5.6+ / High, Sol 5.6+ / xhigh, Sol 5.6+ / max",
                "Codex critical complete routes",
            ),
            (
                "Sol/High or stronger therefore satisfies a standard request",
                "Codex stronger route acceptance",
            ),
            (
                "Terra and Sol/Medium are not allowlisted Shipwright worker routes",
                "Codex worker routing exclusions",
            ),
            (
                "Do not rank family and effort independently across routes",
                "Codex complete-route ordering",
            ),
        ),
        CODEX_REFERENCE,
        errors,
    )
    _forbid_markers(
        codex_text,
        (
            (
                "Accept only exact",
                "Codex exact-version acceptance pin",
            ),
            (
                "until this reference explicitly allowlists",
                "Codex future-model allowlist brittleness",
            ),
        ),
        CODEX_REFERENCE,
        errors,
    )


def _validate_claude_text(
    claude_text: Optional[str],
    errors: list[str],
) -> None:
    _require_markers(
        claude_text,
        (
            (
                "Require a resolved Opus model at version `4.6` or newer",
                "Claude controller gate numeric floor",
            ),
            (
                "compare that version numerically against the `4.6` floor",
                "Claude controller gate numeric comparison",
            ),
            ("claude-opus-4-6", "Claude controller gate minimum model version"),
            (
                "Recommended controller effort rank is `xhigh` or stronger",
                "Claude recommended controller effort",
            ),
            (
                "Recommended controller effort is not a precondition",
                "Claude controller effort not a precondition",
            ),
            ("select **Opus 4.6 or newer**", "Claude controller gate guidance"),
            ("unresolved word `opus`", "Claude controller evidence rejection"),
            (
                "Accept attributable model-family evidence without effort only when",
                "Claude model-only absent effort acceptance",
            ),
            (
                "Child effort is waived here because",
                "Claude child effort waiver justification",
            ),
            (
                "only when the schema has no effort selector and accepted child records do not attribute effort",
                "Claude child effort waiver attribution condition",
            ),
            (
                "If effort is attributable, validate it against the route floor even when the selector is absent",
                "Claude attributable effort without selector",
            ),
            (
                "Do not treat the child waiver and the controller disclosure rule as the same mechanism",
                "Claude child waiver vs controller disclosure",
            ),
            (
                "Claude Code's subagent tooling prevents children from writing report files",
                "Claude child report file precondition",
            ),
            (
                "have the controller persist it to the dispatch's artifact directory",
                "Claude controller-persisted child reports",
            ),
            (
                "Children will keep offering environment-variable-sourced effort",
                "Claude env-sourced effort precondition",
            ),
            (
                "expect it, reject it",
                "Claude expected rejected env effort",
            ),
            (
                "the ledger is a local artifact, not a reply — record it there",
                "Claude child agent ID recorded in ledger",
            ),
            (
                "Do not enter the inherited-controller fallback solely because effort is absent",
                "Claude no fallback on absent effort",
            ),
            (
                "Family alone governs worker routing; version comparison applies only at the controller gate",
                "Claude worker family vs controller version",
            ),
            (
                "Never stop solely because controller effort is missing, weak, or unverifiable",
                "Claude controller effort never hard-stops",
            ),
        ),
        CLAUDE_REFERENCE,
        errors,
    )
    _forbid_markers(
        claude_text,
        (
            (
                "Accept only exact",
                "Claude exact-version acceptance pin",
            ),
            (
                "until this reference explicitly allowlists",
                "Claude future-model allowlist brittleness",
            ),
        ),
        CLAUDE_REFERENCE,
        errors,
    )


def _validate_cursor_text(
    cursor_text: Optional[str],
    errors: list[str],
) -> None:
    _forbid_markers(
        cursor_text,
        (
            (
                "Accept only exact",
                "Cursor exact-version acceptance pin",
            ),
            (
                "until this reference explicitly allowlists",
                "Cursor future-model allowlist brittleness",
            ),
        ),
        CURSOR_REFERENCE,
        errors,
    )
    _require_markers(
        cursor_text,
        (
            ("Grok 4.5", "Cursor controller gate Grok 4.5 floor"),
            (
                "Require a resolved Grok model at version `4.5` or newer",
                "Cursor controller gate numeric floor",
            ),
            (
                "Recommended controller effort rank is `high` or stronger",
                "Cursor recommended controller effort",
            ),
            (
                "Recommended controller effort is not a precondition",
                "Cursor controller effort not a precondition",
            ),
            ("select **Grok 4.5 or newer**", "Cursor controller gate guidance"),
            ("Cursor Grok 4.5", "Cursor controller family display evidence"),
            ("family dimension only", "Cursor harness family-only evidence"),
            ("Compose dimensions", "Cursor composite family/effort evidence"),
            (
                "Never stop solely because controller effort is missing, weak, or unverifiable",
                "Cursor controller effort never hard-stops",
            ),
            ("Composer < Grok", "Cursor worker family order"),
            ("Task({ subagent_type, prompt, model", "Cursor Task dispatch"),
            ("Reject Composer as controller", "Cursor controller Composer rejection"),
        ),
        CURSOR_REFERENCE,
        errors,
    )


def _validate_antigravity_text(
    antigravity_text: Optional[str],
    errors: list[str],
) -> None:
    _require_markers(
        antigravity_text,
        (
            ("Gemini 3.7 Flash", "Antigravity controller gate minimum model version"),
            (
                "Require a resolved Gemini model at version `3.7`",
                "Antigravity controller gate numeric floor",
            ),
            (
                "Recommended controller effort is `high`",
                "Antigravity recommended controller effort",
            ),
            (
                "Recommended controller effort is not a precondition",
                "Antigravity controller effort not a precondition",
            ),
            (
                "select **Gemini 3.7 Flash or newer**",
                "Antigravity controller gate guidance",
            ),
            (
                "Never stop solely because controller effort is missing, weak, or unverifiable",
                "Antigravity controller effort never hard-stops",
            ),
            (
                "| Mechanical | `flash_lite` or `flash` |",
                "Antigravity worker routing mechanical",
            ),
            ("| Critical | `pro` |", "Antigravity worker routing critical"),
            ("invoke_subagent", "Antigravity dispatch tool"),
        ),
        ANTIGRAVITY_REFERENCE,
        errors,
    )


def _validate_skill_and_contracts(
    repo_root: Path,
    skill_text: Optional[str],
    codex_text: Optional[str],
    claude_text: Optional[str],
    cursor_text: Optional[str],
    antigravity_text: Optional[str],
    errors: list[str],
) -> None:
    _validate_skill_text(repo_root, skill_text, errors)
    _validate_codex_text(codex_text, errors)
    _validate_claude_text(claude_text, errors)
    _validate_cursor_text(cursor_text, errors)
    _validate_antigravity_text(antigravity_text, errors)


def _validate_openai_metadata(metadata_text: Optional[str], errors: list[str]) -> None:
    if metadata_text is None:
        return
    metadata = _parse_constrained_yaml(metadata_text, OPENAI_METADATA, errors)
    expected_metadata = {
        "interface": {
            "display_name": "Shipwright",
            "short_description": "Strict end-to-end development workflow",
            "default_prompt": DEFAULT_PROMPT,
        },
        "policy": {"allow_implicit_invocation": False},
    }
    if metadata != expected_metadata:
        errors.append(
            f"{_display(OPENAI_METADATA)}: openai metadata must equal "
            f"{expected_metadata!r}; found {metadata!r}"
        )
    expectations = (
        (("interface", "display_name"), "Shipwright", "openai display_name"),
        (
            ("interface", "short_description"),
            "Strict end-to-end development workflow",
            "openai short_description",
        ),
        (("interface", "default_prompt"), DEFAULT_PROMPT, "openai default_prompt"),
        (
            ("policy", "allow_implicit_invocation"),
            False,
            "openai allow_implicit_invocation policy",
        ),
    )
    for keys, expected, label in expectations:
        _require_equal(metadata, keys, expected, label, OPENAI_METADATA, errors)


def _validate_readme(readme_text: Optional[str], errors: list[str]) -> list[str]:
    if readme_text is None:
        return []
    if CODEX_INSTALL_ROUTE not in readme_text:
        errors.append(
            f"{_display(README)}: Codex install route must use the agent-plugins catalog"
        )
    bullets = [
        line for line in readme_text.splitlines() if line.startswith("- `shipwright`")
    ]
    if len(bullets) != 1:
        errors.append(
            f"{_display(README)}: must contain exactly one Shipwright plugin bullet"
        )
    else:
        bullet = bullets[0]
        if CODEX_INVOCATION not in bullet:
            errors.append(
                f"{_display(README)}: Shipwright bullet must document Codex invocation"
            )
        if CLAUDE_INVOCATION not in bullet:
            errors.append(
                f"{_display(README)}: Shipwright bullet must document Claude invocation"
            )
        if not _has_cursor_invocation(bullet) or CURSOR_INVOCATION_DOC not in bullet:
            errors.append(
                f"{_display(README)}: Shipwright bullet must document Cursor invocation "
                f"({CURSOR_INVOCATION_DOC})"
            )
    return bullets


def _contains_stale_name(text: str) -> bool:
    legacy = "full" + "-dev"
    return ("$" + legacy) in text or ("/" + legacy) in text or (legacy + "-") in text


def _validate_stale_names(
    repo_root: Path, readme_bullets: list[str], errors: list[str]
) -> None:
    plugin_root = repo_root
    if plugin_root.is_dir():

        def report_walk_error(exc: OSError) -> None:
            failed_path = Path(exc.filename) if exc.filename else plugin_root
            try:
                displayed_path = failed_path.relative_to(repo_root)
            except ValueError:
                displayed_path = failed_path
            errors.append(
                f"cannot inspect directory {_display(displayed_path)} for stale names: {exc}"
            )

        for directory, directory_names, file_names in os.walk(
            plugin_root, onerror=report_walk_error
        ):
            directory_names[:] = [name for name in directory_names if name != ".git"]
            directory_names.sort()
            for filename in sorted(file_names):
                path = Path(directory) / filename
                if not path.is_file():
                    continue
                relative_path = path.relative_to(repo_root)
                try:
                    raw_content = path.read_bytes()
                except OSError as exc:
                    errors.append(
                        f"cannot inspect {_display(relative_path)} for stale names: {exc}"
                    )
                    continue
                # A NUL byte is the sole binary exclusion. Every other regular file
                # must be valid UTF-8 so an uninspected text-like asset cannot pass.
                if b"\x00" in raw_content:
                    continue
                try:
                    content = raw_content.decode("utf-8")
                except UnicodeDecodeError as exc:
                    errors.append(
                        f"cannot inspect {_display(relative_path)} for stale names: "
                        f"not valid UTF-8 ({exc})"
                    )
                    continue
                if _contains_stale_name(content):
                    errors.append(
                        "stale public name/profile dependency in "
                        f"{_display(relative_path)}"
                    )

    if any(_contains_stale_name(line) for line in readme_bullets):
        errors.append(
            f"stale public name/profile dependency in {_display(README)} Shipwright bullet"
        )


def validate_bundle(repo_root: Path) -> list[str]:
    """Return every deterministic Shipwright packaging-contract failure."""

    repo_root = Path(repo_root)
    errors: list[str] = []

    codex_manifest = _load_json(repo_root, CODEX_MANIFEST, errors)
    claude_manifest = _load_json(repo_root, CLAUDE_MANIFEST, errors)
    cursor_manifest = _load_json(repo_root, CURSOR_MANIFEST, errors)
    antigravity_manifest = _load_json(repo_root, ANTIGRAVITY_MANIFEST, errors)

    skill_text = _read_text(repo_root, SKILL, errors)
    openai_text = _read_text(repo_root, OPENAI_METADATA, errors)
    codex_text = _read_text(repo_root, CODEX_REFERENCE, errors)
    claude_text = _read_text(repo_root, CLAUDE_REFERENCE, errors)
    cursor_text = _read_text(repo_root, CURSOR_REFERENCE, errors)
    antigravity_text = _read_text(repo_root, ANTIGRAVITY_REFERENCE, errors)
    readme_text = _read_text(repo_root, README, errors)

    _validate_manifests(
        codex_manifest, claude_manifest, cursor_manifest, antigravity_manifest, errors
    )
    _validate_skill_and_contracts(
        repo_root,
        skill_text,
        codex_text,
        claude_text,
        cursor_text,
        antigravity_text,
        errors,
    )
    _validate_openai_metadata(openai_text, errors)
    readme_bullets = _validate_readme(readme_text, errors)
    _validate_stale_names(repo_root, readme_bullets, errors)

    return errors


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    errors = validate_bundle(_repository_root())
    if errors:
        print("Shipwright validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Shipwright validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
