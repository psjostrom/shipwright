#!/usr/bin/env python3
"""Deterministically validate the Shipwright cross-platform plugin bundle."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional


PLUGIN_ROOT = Path("plugins/shipwright")
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin/plugin.json"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin/plugin.json"
SKILL = PLUGIN_ROOT / "skills/shipwright/SKILL.md"
OPENAI_METADATA = PLUGIN_ROOT / "skills/shipwright/agents/openai.yaml"
CODEX_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/codex.md"
CLAUDE_REFERENCE = PLUGIN_ROOT / "skills/shipwright/references/claude-code.md"
SCENARIOS = PLUGIN_ROOT / "evals/v1/scenarios.md"
CLAUDE_RUNBOOK = PLUGIN_ROOT / "evals/v1/claude-code-runbook.md"
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
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
DEFAULT_PROMPT = (
    "Use $shipwright:shipwright to build this feature end to end with independent "
    "review and real verification."
)
CLAUDE_GUARDED_LAUNCH = (
    'if ! git -C "$fixture_root" check-ignore -q "$evidence_dir"; then\n'
    "  printf '%s\\n' \"evidence_dir is not ignored; mark the evaluation "
    "UNVERIFIED and stop\" >&2\n"
    "else\n"
    '  cd "$fixture_root" &&\n'
    '    claude --plugin-dir "$shipwright_checkout/plugins/shipwright"\n'
    "fi"
)

SCENARIO_CASES = (
    "gate-codex-pass",
    "gate-codex-reject",
    "gate-claude-pass",
    "gate-claude-reject",
    "dependency-preflight",
    "dependency-incompatible",
    "trivial-reduction",
    "explicit-routing",
    "inherited-routing",
    "child-evidence-match",
    "child-evidence-reject",
    "independent-review",
    "bounded-remediation",
    "false-positive-adjudication",
    "whole-change-review",
    "qa-web",
    "qa-mobile",
    "qa-cli-backend",
    "authorization-boundaries",
)

CLAUDE_RUNBOOK_CASES = tuple(
    case
    for case in SCENARIO_CASES
    if case not in {"gate-codex-pass", "gate-codex-reject"}
)


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


def _read_text(repo_root: Path, relative_path: Path, errors: list[str]) -> Optional[str]:
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


def _validate_manifests(codex: Any, claude: Any, errors: list[str]) -> None:
    if isinstance(codex, dict):
        _require_equal(codex, ("name",), "shipwright", "Codex manifest name", CODEX_MANIFEST, errors)
        if not _valid_codex_version(codex.get("version")):
            errors.append(
                f"{_display(CODEX_MANIFEST)}: Codex manifest version must be '1.0.0' "
                "or '1.0.0+codex.<cachebuster>'"
            )
        _require_equal(codex, ("description",), DESCRIPTION, "Codex manifest description", CODEX_MANIFEST, errors)
        _require_equal(codex, ("author", "name"), "psjostrom", "Codex manifest author.name", CODEX_MANIFEST, errors)
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
            "https://github.com/psjostrom/agent-plugins",
            "Codex manifest repository",
            CODEX_MANIFEST,
            errors,
        )
        _require_equal(codex, ("keywords",), KEYWORDS, "Codex manifest keywords", CODEX_MANIFEST, errors)
        _require_equal(codex, ("skills",), "./skills/", "Codex manifest skills path", CODEX_MANIFEST, errors)

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
        errors.append(f"{_display(CODEX_MANIFEST)}: Codex manifest root must be a JSON object")

    if isinstance(claude, dict):
        _require_equal(claude, ("name",), "shipwright", "Claude manifest name", CLAUDE_MANIFEST, errors)
        if claude.get("version") != "1.0.0":
            errors.append(
                f"{_display(CLAUDE_MANIFEST)}: Claude manifest version must be exactly '1.0.0'; "
                f"found {claude.get('version')!r}"
            )
        _require_equal(claude, ("description",), DESCRIPTION, "Claude manifest description", CLAUDE_MANIFEST, errors)
        _require_equal(claude, ("author", "name"), "psjostrom", "Claude manifest author.name", CLAUDE_MANIFEST, errors)
        _require_equal(claude, ("keywords",), KEYWORDS, "Claude manifest keywords", CLAUDE_MANIFEST, errors)
    elif claude is not None:
        errors.append(f"{_display(CLAUDE_MANIFEST)}: Claude manifest root must be a JSON object")


def _marketplace_entry(
    catalog: Any, label: str, source_path: Path, errors: list[str]
) -> Optional[dict[str, Any]]:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("plugins"), list):
        if catalog is not None:
            errors.append(
                f"{_display(source_path)}: {label} marketplace must contain a plugins list"
            )
        return None
    matches = [
        item
        for item in catalog["plugins"]
        if isinstance(item, dict) and item.get("name") == "shipwright"
    ]
    if len(matches) != 1:
        errors.append(
            f"{_display(source_path)}: {label} marketplace must contain exactly one "
            "shipwright entry"
        )
        return None
    return matches[0]


def _validate_marketplaces(
    codex_catalog: Any, claude_catalog: Any, errors: list[str]
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
    codex = _marketplace_entry(codex_catalog, "Codex", CODEX_MARKETPLACE, errors)
    claude = _marketplace_entry(claude_catalog, "Claude", CLAUDE_MARKETPLACE, errors)
    if codex is not None:
        _require_equal(codex, ("name",), "shipwright", "Codex marketplace name", CODEX_MARKETPLACE, errors)
        _require_equal(codex, ("source", "source"), "local", "Codex marketplace source.source", CODEX_MARKETPLACE, errors)
        _require_equal(
            codex,
            ("source", "path"),
            "./plugins/shipwright",
            "Codex marketplace source.path",
            CODEX_MARKETPLACE,
            errors,
        )
        _require_equal(
            codex,
            ("policy", "installation"),
            "AVAILABLE",
            "Codex marketplace policy.installation",
            CODEX_MARKETPLACE,
            errors,
        )
        _require_equal(
            codex,
            ("policy", "authentication"),
            "ON_INSTALL",
            "Codex marketplace policy.authentication",
            CODEX_MARKETPLACE,
            errors,
        )
        _require_equal(codex, ("category",), "Developer Tools", "Codex marketplace category", CODEX_MARKETPLACE, errors)
    if claude is not None:
        expectations = {
            "name": "shipwright",
            "source": "./plugins/shipwright",
            "description": DESCRIPTION,
            "version": "1.0.0",
            "keywords": KEYWORDS,
            "category": "development",
        }
        for key, expected in expectations.items():
            _require_equal(
                claude,
                (key,),
                expected,
                f"Claude marketplace {key}",
                CLAUDE_MARKETPLACE,
                errors,
            )
        _require_equal(
            claude,
            ("author", "name"),
            "psjostrom",
            "Claude marketplace author.name",
            CLAUDE_MARKETPLACE,
            errors,
        )
    return codex, claude


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
        errors.append(f"{_display(relative_path)}:{line_number}: malformed quoted scalar")
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
            if quote == "'" and index + 1 < len(raw_value) and raw_value[index + 1] == "'":
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
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?:[ ]*(.*))?", line[indentation:])
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
                value = _parse_yaml_scalar(raw_value, relative_path, line_number, errors)
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


def _validate_skill_and_contracts(
    repo_root: Path,
    skill_text: Optional[str],
    codex_text: Optional[str],
    claude_text: Optional[str],
    scenarios_text: Optional[str],
    errors: list[str],
) -> None:
    skill_root = repo_root / PLUGIN_ROOT
    if skill_root.is_dir():
        skill_files = sorted(
            path.relative_to(repo_root).as_posix() for path in skill_root.rglob("SKILL.md")
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
            if set(frontmatter) != {"name", "description"}:
                errors.append(
                    f"{_display(SKILL)}: Shipwright SKILL.md frontmatter keys must be "
                    f"exactly ['description', 'name']; found {sorted(frontmatter)!r}"
                )
        if len(skill_text.splitlines()) >= 500:
            errors.append(
                f"{_display(SKILL)}: Shipwright shared SKILL.md must be fewer than 500 lines"
            )

    _require_markers(
        skill_text,
        (
            (CODEX_INVOCATION, "Codex invocation"),
            (CLAUDE_INVOCATION, "Claude invocation"),
            ("[references/codex.md](references/codex.md)", "reachable Codex reference link"),
            (
                "[references/claude-code.md](references/claude-code.md)",
                "reachable Claude reference link",
            ),
            ("thread/run ID", "child runtime evidence contract"),
            (
                "when the selected route defines an effort floor",
                "conditional effort evidence contract",
            ),
            (
                "absent effort is allowed only when that route defines none",
                "absent effort evidence contract",
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
            ("BLOCKED_QA", "BLOCKED_QA terminal state"),
            ("Install/download tools", "authorization boundary for tool installation"),
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

    _require_markers(
        codex_text,
        (
            ("gpt-5.6-sol", "Codex controller gate exact model"),
            ("effort rank `high` or stronger", "Codex controller gate effort"),
            ("GPT-5.6 Sol / High or stronger", "Codex controller gate guidance"),
            ("generic family label", "Codex controller evidence rejection"),
        ),
        CODEX_REFERENCE,
        errors,
    )
    _require_markers(
        claude_text,
        (
            ("claude-opus-4-7", "Claude controller gate exact model"),
            ("effort rank `xhigh` or stronger", "Claude controller gate effort"),
            ("Opus 4.7 / xhigh or stronger", "Claude controller gate guidance"),
            ("unresolved word `opus`", "Claude controller evidence rejection"),
        ),
        CLAUDE_REFERENCE,
        errors,
    )

    if scenarios_text is not None:
        for case in SCENARIO_CASES:
            heading = re.compile(rf"^### `{re.escape(case)}`\s*$", re.MULTILINE)
            if heading.search(scenarios_text) is None:
                errors.append(f"missing committed scenario case {case} in {_display(SCENARIOS)}")


def _validate_claude_runbook(
    runbook_text: Optional[str], errors: list[str]
) -> None:
    required_markers = (
        ("## Prerequisites", "Claude runbook prerequisites"),
        ("## Safety boundaries", "Claude runbook safety boundaries"),
        (
            "## Copy/paste prompt for Claude Code",
            "Claude runbook copy/paste prompt",
        ),
        (
            "## Required cases and repetitions",
            "Claude runbook repetition contract",
        ),
        ("## Evidence bundle", "Claude runbook evidence bundle"),
        ("## Result rubric", "Claude runbook result rubric"),
        ("## Return template", "Claude runbook return template"),
        (CLAUDE_INVOCATION, "Claude runbook invocation"),
        ("Claude Code 2.1.117 or newer", "Claude runbook version floor"),
        ("Superpowers 6.1.1 or newer", "Claude runbook dependency floor"),
        ("claude-opus-4-7", "Claude runbook exact model evidence"),
        ("xhigh or stronger", "Claude runbook effort evidence"),
        ("one broad smoke pass", "Claude runbook smoke threshold"),
        ("3/3 exact passes", "Claude runbook hard-gate threshold"),
        ("at least 2/3 intended", "Claude runbook routing threshold"),
        ("3/3 safe choices", "Claude runbook routing safety threshold"),
        ("PASS", "Claude runbook PASS result"),
        ("FAIL", "Claude runbook FAIL result"),
        ("UNVERIFIED", "Claude runbook UNVERIFIED result"),
        ("disposable fixture repository", "Claude runbook isolation boundary"),
        ("credentials", "Claude runbook credential boundary"),
        ("paid external services", "Claude runbook paid-service boundary"),
        ("must not modify Shipwright", "Claude runbook evaluator boundary"),
        ('shipwright_checkout="$(pwd -P)"', "Claude runbook checkout capture"),
        (
            'shipwright_status="<clean>"',
            "Claude runbook explicit clean-status representation",
        ),
        ('fixture_root="$(mktemp -d)"', "Claude runbook fixture creation"),
        ('git -C "$fixture_root" init', "Claude runbook fixture repository"),
        (
            "evaluation-input/claude-code-runbook.md",
            "Claude runbook fixture-local runbook input",
        ),
        (
            "evaluation-input/scenarios.md",
            "Claude runbook fixture-local scenario input",
        ),
        (
            'environment_seed="$fixture_root/evaluation-input/environment-seed.md"',
            "Claude runbook fixture-local environment seed",
        ),
        (
            "printf 'shipwright_commit=%s\\n' \"$shipwright_commit\" > \"$environment_seed\"",
            "Claude runbook seeded commit transfer",
        ),
        (
            "printf 'shipwright_status=%s\\n' \"$shipwright_status\" >> \"$environment_seed\"",
            "Claude runbook seeded status transfer",
        ),
        (
            "printf 'shipwright_plugin_source=%s\\n' \"$shipwright_checkout/plugins/shipwright\" >> \"$environment_seed\"",
            "Claude runbook seeded plugin-source transfer",
        ),
        (
            "printf 'evidence_dir=%s\\n' \"$evidence_dir\" >> \"$environment_seed\"",
            "Claude runbook seeded evidence-destination transfer",
        ),
        (
            "Read evaluation-input/environment-seed.md along with",
            "Claude runbook seeded-identity read contract",
        ),
        (
            "Failure to create or read environment-seed.md makes the evaluation `UNVERIFIED`.",
            "Claude runbook unverifiable environment seed",
        ),
        (".git/info/exclude", "Claude runbook fixture ignore contract"),
        (
            'git -C "$fixture_root" check-ignore -q "$evidence_dir"',
            "Claude runbook fixture evidence ignore verification",
        ),
        (
            'if ! git -C "$fixture_root" check-ignore -q "$evidence_dir"; then',
            "Claude runbook guarded ignore verification",
        ),
        (
            "evidence_dir is not ignored; mark the evaluation UNVERIFIED and stop",
            "Claude runbook ignore-verification failure path",
        ),
        (CLAUDE_GUARDED_LAUNCH, "Claude runbook guarded launch"),
        (
            'claude --plugin-dir "$shipwright_checkout/plugins/shipwright"',
            "Claude runbook fixture-rooted plugin loading",
        ),
        ('cd "$fixture_root"', "Claude runbook fixture-rooted workspace"),
        (
            'evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"',
            "Claude runbook fixture-local evidence destination",
        ),
        (
            "copy/setup, ignore verification, or fixture-rooted plugin loading",
            "Claude runbook unverifiable fixture setup",
        ),
    )
    _require_markers(
        runbook_text,
        required_markers,
        CLAUDE_RUNBOOK,
        errors,
    )
    if runbook_text is None:
        return
    for case in CLAUDE_RUNBOOK_CASES:
        if f"`{case}`" not in runbook_text:
            errors.append(
                f"missing delegated Claude case {case} in {_display(CLAUDE_RUNBOOK)}"
            )


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
    bullets = [line for line in readme_text.splitlines() if line.startswith("- `shipwright`")]
    if len(bullets) != 1:
        errors.append(f"{_display(README)}: must contain exactly one Shipwright plugin bullet")
    elif CODEX_INVOCATION not in bullets[0] or CLAUDE_INVOCATION not in bullets[0]:
        errors.append(
            f"{_display(README)}: Shipwright bullet must document Codex and Claude invocations"
        )
    return bullets


def _contains_stale_name(text: str) -> bool:
    legacy = "full" + "-dev"
    return ("$" + legacy) in text or ("/" + legacy) in text or (legacy + "-") in text


def _validate_stale_names(
    repo_root: Path,
    codex_entry: Optional[dict[str, Any]],
    claude_entry: Optional[dict[str, Any]],
    readme_bullets: list[str],
    errors: list[str],
) -> None:
    plugin_root = repo_root / PLUGIN_ROOT
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

    for relative_path, entry in (
        (CODEX_MARKETPLACE, codex_entry),
        (CLAUDE_MARKETPLACE, claude_entry),
    ):
        if entry is not None and _contains_stale_name(json.dumps(entry, sort_keys=True)):
            errors.append(
                f"stale public name/profile dependency in {_display(relative_path)} "
                "Shipwright marketplace entry"
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
    codex_catalog = _load_json(repo_root, CODEX_MARKETPLACE, errors)
    claude_catalog = _load_json(repo_root, CLAUDE_MARKETPLACE, errors)

    skill_text = _read_text(repo_root, SKILL, errors)
    openai_text = _read_text(repo_root, OPENAI_METADATA, errors)
    codex_text = _read_text(repo_root, CODEX_REFERENCE, errors)
    claude_text = _read_text(repo_root, CLAUDE_REFERENCE, errors)
    scenarios_text = _read_text(repo_root, SCENARIOS, errors)
    runbook_text = _read_text(repo_root, CLAUDE_RUNBOOK, errors)
    readme_text = _read_text(repo_root, README, errors)

    _validate_manifests(codex_manifest, claude_manifest, errors)
    codex_entry, claude_entry = _validate_marketplaces(
        codex_catalog, claude_catalog, errors
    )
    _validate_skill_and_contracts(
        repo_root,
        skill_text,
        codex_text,
        claude_text,
        scenarios_text,
        errors,
    )
    _validate_claude_runbook(runbook_text, errors)
    _validate_openai_metadata(openai_text, errors)
    readme_bullets = _validate_readme(readme_text, errors)
    _validate_stale_names(repo_root, codex_entry, claude_entry, readme_bullets, errors)

    return errors


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


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
