#!/usr/bin/env python3
"""Deterministically validate the Shipwright cross-platform plugin bundle."""

from __future__ import annotations

import json
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
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
README = Path("README.md")

DESCRIPTION = (
    "Strict end-to-end development with adaptive subagents, independent review, "
    "and real verification."
)
KEYWORDS = ["development", "subagents", "code-review", "verification", "qa"]
CODEX_INVOCATION = "$shipwright:shipwright"
CLAUDE_INVOCATION = "/shipwright:shipwright"
DEFAULT_PROMPT = (
    "Use $shipwright:shipwright to build this feature end to end with independent "
    "review and real verification."
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
    errors: list[str],
) -> None:
    actual = _value_at(data, *keys)
    if actual != expected:
        errors.append(f"{label} must be {expected!r}; found {actual!r}")


def _valid_version(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"1\.0\.0(?:[-+][0-9A-Za-z.-]+)?", value) is not None


def _validate_manifests(codex: Any, claude: Any, errors: list[str]) -> None:
    if isinstance(codex, dict):
        _require_equal(codex, ("name",), "shipwright", "Codex manifest name", errors)
        if not _valid_version(codex.get("version")):
            errors.append("Codex manifest version must start at 1.0.0")
        _require_equal(codex, ("description",), DESCRIPTION, "Codex manifest description", errors)
        _require_equal(codex, ("author", "name"), "psjostrom", "Codex manifest author.name", errors)
        _require_equal(
            codex,
            ("author", "url"),
            "https://github.com/psjostrom",
            "Codex manifest author.url",
            errors,
        )
        _require_equal(
            codex,
            ("repository",),
            "https://github.com/psjostrom/agent-plugins",
            "Codex manifest repository",
            errors,
        )
        _require_equal(codex, ("keywords",), KEYWORDS, "Codex manifest keywords", errors)
        _require_equal(codex, ("skills",), "./skills/", "Codex manifest skills path", errors)

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
                errors,
            )
    elif codex is not None:
        errors.append("Codex manifest root must be a JSON object")

    if isinstance(claude, dict):
        _require_equal(claude, ("name",), "shipwright", "Claude manifest name", errors)
        if not _valid_version(claude.get("version")):
            errors.append("Claude manifest version must start at 1.0.0")
        _require_equal(claude, ("description",), DESCRIPTION, "Claude manifest description", errors)
        _require_equal(claude, ("author", "name"), "psjostrom", "Claude manifest author.name", errors)
        _require_equal(claude, ("keywords",), KEYWORDS, "Claude manifest keywords", errors)
    elif claude is not None:
        errors.append("Claude manifest root must be a JSON object")


def _marketplace_entry(catalog: Any, label: str, errors: list[str]) -> Optional[dict[str, Any]]:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("plugins"), list):
        if catalog is not None:
            errors.append(f"{label} marketplace must contain a plugins list")
        return None
    matches = [
        item
        for item in catalog["plugins"]
        if isinstance(item, dict) and item.get("name") == "shipwright"
    ]
    if len(matches) != 1:
        errors.append(f"{label} marketplace must contain exactly one shipwright entry")
        return None
    return matches[0]


def _validate_marketplaces(
    codex_catalog: Any, claude_catalog: Any, errors: list[str]
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
    codex = _marketplace_entry(codex_catalog, "Codex", errors)
    claude = _marketplace_entry(claude_catalog, "Claude", errors)
    if codex is not None:
        _require_equal(codex, ("name",), "shipwright", "Codex marketplace name", errors)
        _require_equal(codex, ("source", "source"), "local", "Codex marketplace source.source", errors)
        _require_equal(
            codex,
            ("source", "path"),
            "./plugins/shipwright",
            "Codex marketplace source.path",
            errors,
        )
        _require_equal(
            codex,
            ("policy", "installation"),
            "AVAILABLE",
            "Codex marketplace policy.installation",
            errors,
        )
        _require_equal(
            codex,
            ("policy", "authentication"),
            "ON_INSTALL",
            "Codex marketplace policy.authentication",
            errors,
        )
        _require_equal(codex, ("category",), "Developer Tools", "Codex marketplace category", errors)
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
            _require_equal(claude, (key,), expected, f"Claude marketplace {key}", errors)
        _require_equal(
            claude,
            ("author", "name"),
            "psjostrom",
            "Claude marketplace author.name",
            errors,
        )
    return codex, claude


def _parse_frontmatter(skill_text: str, errors: list[str]) -> Optional[dict[str, str]]:
    lines = skill_text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{_display(SKILL)} must start with YAML frontmatter")
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        errors.append(f"{_display(SKILL)} has unterminated YAML frontmatter")
        return None

    frontmatter: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", line)
        if match is None:
            errors.append(f"{_display(SKILL)} has unsupported frontmatter line: {line!r}")
            continue
        frontmatter[match.group(1)] = match.group(2).strip().strip("'\"")
    return frontmatter


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
            if frontmatter.get("name") != "shipwright":
                errors.append("Shipwright SKILL.md frontmatter name must be 'shipwright'")
            if not frontmatter.get("description"):
                errors.append("Shipwright SKILL.md frontmatter description must be nonempty")
        if len(skill_text.splitlines()) >= 500:
            errors.append("Shipwright shared SKILL.md must be fewer than 500 lines")

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
            ("one fallback per gated role", "runtime retry contract"),
            ("BLOCKED_RUNTIME", "BLOCKED_RUNTIME terminal state"),
            ("fresh independent reviewer", "independent review contract"),
            ("at most two ordinary remediation cycles", "two remediation cycle cap"),
            ("one final escalated attempt", "escalated remediation contract"),
            ("agent-browser", "agent-browser web QA route"),
            ("Playwright", "Playwright web regression route"),
            ("argent", "Argent mobile QA route"),
            ("verified", "verified QA outcome"),
            ("partially verified", "partially verified QA outcome"),
            ("unverified", "unverified QA outcome"),
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


def _validate_openai_metadata(metadata_text: Optional[str], errors: list[str]) -> None:
    _require_markers(
        metadata_text,
        (
            ('display_name: "Shipwright"', "openai display_name"),
            (
                'short_description: "Strict end-to-end development workflow"',
                "openai short_description",
            ),
            (f'default_prompt: "{DEFAULT_PROMPT}"', "openai default_prompt"),
            ("allow_implicit_invocation: false", "openai allow_implicit_invocation policy"),
        ),
        OPENAI_METADATA,
        errors,
    )


def _validate_readme(readme_text: Optional[str], errors: list[str]) -> list[str]:
    if readme_text is None:
        return []
    bullets = [line for line in readme_text.splitlines() if line.startswith("- `shipwright`")]
    if len(bullets) != 1:
        errors.append("README.md must contain exactly one Shipwright plugin bullet")
    elif CODEX_INVOCATION not in bullets[0] or CLAUDE_INVOCATION not in bullets[0]:
        errors.append("Shipwright README bullet must document Codex invocation and Claude invocation")
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
        for path in sorted(plugin_root.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if _contains_stale_name(content):
                relative_path = path.relative_to(repo_root)
                errors.append(
                    "stale public name/profile dependency in " f"{_display(relative_path)}"
                )

    for label, entry in (("Codex marketplace entry", codex_entry), ("Claude marketplace entry", claude_entry)):
        if entry is not None and _contains_stale_name(json.dumps(entry, sort_keys=True)):
            errors.append(f"stale public name/profile dependency in {label}")
    if any(_contains_stale_name(line) for line in readme_bullets):
        errors.append("stale public name/profile dependency in Shipwright README bullet")


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
    _validate_openai_metadata(openai_text, errors)
    readme_bullets = _validate_readme(readme_text, errors)
    _validate_stale_names(repo_root, codex_entry, claude_entry, readme_bullets, errors)

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    errors = validate_bundle(repo_root)
    if errors:
        print("Shipwright validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Shipwright validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
