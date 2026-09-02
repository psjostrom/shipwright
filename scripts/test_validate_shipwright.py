#!/usr/bin/env python3
"""Regression tests for the deterministic Shipwright bundle validator."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_shipwright as validator  # noqa: E402


validate_bundle = validator.validate_bundle


class ShipwrightValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temporary_directory.name)

        shutil.copytree(
            REPOSITORY_ROOT,
            self.repo_root,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
            dirs_exist_ok=True,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def path(self, relative_path: str) -> Path:
        return self.repo_root / relative_path

    def read_json(self, relative_path: str) -> object:
        return json.loads(self.path(relative_path).read_text(encoding="utf-8"))

    def write_json(self, relative_path: str, value: object) -> None:
        self.path(relative_path).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def replace(self, relative_path: str, old: str, new: str) -> None:
        path = self.path(relative_path)
        content = path.read_text(encoding="utf-8")
        self.assertIn(old, content, f"fixture marker missing from {relative_path}")
        path.write_text(content.replace(old, new), encoding="utf-8")

    def assert_error(self, fragment: str) -> list[str]:
        errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected error containing {fragment!r}; got {errors!r}",
        )
        return errors

    def test_valid_bundle_has_no_errors(self) -> None:
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_reports_malformed_json(self) -> None:
        path = self.path(".codex-plugin/plugin.json")
        path.write_text("{not-json\n", encoding="utf-8")
        self.assert_error("malformed JSON")

    def test_reports_every_missing_manifest(self) -> None:
        paths = (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
            "plugin.json",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as scratch:
                    moved = Path(scratch) / "missing"
                    self.path(relative_path).rename(moved)
                    self.assert_error(relative_path)
                    moved.rename(self.path(relative_path))

    def test_reports_missing_skill_references_and_openai_metadata(self) -> None:
        paths = (
            "skills/shipwright/SKILL.md",
            "skills/shipwright/references/codex.md",
            "skills/shipwright/references/claude-code.md",
            "skills/shipwright/references/cursor.md",
            "skills/shipwright/references/antigravity.md",
            "skills/shipwright/agents/openai.yaml",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as scratch:
                    moved = Path(scratch) / "missing"
                    self.path(relative_path).rename(moved)
                    self.assert_error(relative_path)
                    moved.rename(self.path(relative_path))

    def test_requires_disable_model_invocation_frontmatter(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(skill, "disable-model-invocation: true", "disable-model-invocation: false")
        self.assert_error("disable-model-invocation")
        self.replace(skill, "disable-model-invocation: false", "disable-model-invocation: true")
        self.replace(skill, "disable-model-invocation: true\n", "")
        self.assert_error("frontmatter keys")

    def test_reports_wrong_manifest_names(self) -> None:
        for relative_path in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
            "plugin.json",
        ):
            with self.subTest(path=relative_path):
                manifest = self.read_json(relative_path)
                manifest["name"] = "wrong-name"
                self.write_json(relative_path, manifest)
                self.assert_error("name")
                manifest["name"] = "shipwright"
                self.write_json(relative_path, manifest)

    def test_manifest_versions_follow_platform_specific_contracts(self) -> None:
        codex_path = ".codex-plugin/plugin.json"
        claude_path = ".claude-plugin/plugin.json"

        codex = self.read_json(codex_path)
        codex["version"] = "1.0.0+codex.local-20260720-120000"
        self.write_json(codex_path, codex)
        self.assertEqual([], validate_bundle(self.repo_root))

        for invalid in (
            "1.0.1",
            "1.0.0-dev",
            "1.0.0+other.token",
            "1.0.0+codex.UPPER",
            "1.0.0+codex.double--dash",
            "1.0.0+codex.-leading",
        ):
            with self.subTest(platform="codex", version=invalid):
                codex["version"] = invalid
                self.write_json(codex_path, codex)
                errors = self.assert_error(codex_path)
                self.assertTrue(any("version" in error for error in errors), errors)

        codex["version"] = "1.0.0"
        self.write_json(codex_path, codex)

        claude = self.read_json(claude_path)
        self.assertNotIn("version", claude)
        self.assertEqual([], validate_bundle(self.repo_root))
        for present in ("1.0.0", "1.0.1", "1.0.0-dev"):
            with self.subTest(platform="claude", version=present):
                claude["version"] = present
                self.write_json(claude_path, claude)
                errors = self.assert_error(claude_path)
                self.assertTrue(
                    any("must omit version" in error for error in errors), errors
                )
        claude.pop("version", None)
        self.write_json(claude_path, claude)

        cursor_path = ".cursor-plugin/plugin.json"
        cursor = self.read_json(cursor_path)
        for invalid in ("1.0.1", "1.0.0-dev", "1.0.0+codex.local-1"):
            with self.subTest(platform="cursor", version=invalid):
                cursor["version"] = invalid
                self.write_json(cursor_path, cursor)
                errors = self.assert_error(cursor_path)
                self.assertTrue(any("version" in error for error in errors), errors)
        cursor["version"] = "1.0.0"
        self.write_json(cursor_path, cursor)

        antigravity_path = "plugin.json"
        antigravity = self.read_json(antigravity_path)
        self.assertNotIn("version", antigravity)
        self.assertEqual([], validate_bundle(self.repo_root))
        for present in ("1.0.0", "1.0.1", "1.0.0-dev"):
            with self.subTest(platform="antigravity", version=present):
                antigravity["version"] = present
                self.write_json(antigravity_path, antigravity)
                errors = self.assert_error(antigravity_path)
                self.assertTrue(
                    any("must omit version" in error for error in errors), errors
                )
        antigravity.pop("version", None)
        self.write_json(antigravity_path, antigravity)

    def test_reports_wrong_skill_frontmatter_name(self) -> None:
        self.replace(
            "skills/shipwright/SKILL.md",
            "name: shipwright",
            "name: wrong-name",
        )
        self.assert_error("frontmatter name")

    def test_skill_frontmatter_accepts_supported_quotes(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(skill, "name: shipwright", 'name: "shipwright"')
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_skill_frontmatter_delimiters_must_start_at_column_zero(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        mutations = {
            "opening": "  " + original,
            "closing": original.replace("\n---\n\n# Shipwright", "\n  ---\n\n# Shipwright", 1),
        }
        for label, content in mutations.items():
            with self.subTest(delimiter=label):
                self.path(skill).write_text(content, encoding="utf-8")
                self.assert_error("frontmatter")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_skill_frontmatter_requires_closing_delimiter(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        unterminated = original.replace("\n---\n\n# Shipwright", "\n\n# Shipwright", 1)
        self.path(skill).write_text(unterminated, encoding="utf-8")
        self.assert_error("unterminated YAML frontmatter")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_yaml_scalars_accept_inline_comments_trailing_space_and_boolean_case(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(skill, "name: shipwright", "name: shipwright   # canonical skill name")
        self.replace(
            skill,
            f"description: {validator.SKILL_DESCRIPTION}",
            f"description: {validator.SKILL_DESCRIPTION}   # activation contract   ",
        )

        metadata = "skills/shipwright/agents/openai.yaml"
        self.replace(
            metadata,
            'display_name: "Shipwright"',
            'display_name: "Shipwright"   # UI label   ',
        )
        self.replace(
            metadata,
            'short_description: "Strict end-to-end development workflow"',
            "short_description: Strict end-to-end development workflow   # UI summary   ",
        )
        self.replace(
            metadata,
            "allow_implicit_invocation: false",
            "allow_implicit_invocation: False   # explicit-only policy   ",
        )
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_yaml_comment_and_boolean_lexing_respects_scalar_boundaries(self) -> None:
        cases = {
            '"Ship # Wright"   # double-quoted label': '"Ship # Wright"',
            "'Ship # Wright'   # single-quoted label": "'Ship # Wright'",
            "Ship#Wright   # unquoted hash": "Ship#Wright",
        }
        for raw_value, expected in cases.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(expected, validator._strip_yaml_inline_comment(raw_value))

        for raw_value, expected in (
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
        ):
            with self.subTest(boolean=raw_value):
                errors: list[str] = []
                actual = validator._parse_yaml_scalar(
                    raw_value + "   # boolean", Path("metadata.yaml"), 1, errors
                )
                self.assertEqual([], errors)
                self.assertIs(expected, actual)

        errors = []
        self.assertIsNone(
            validator._parse_yaml_scalar(
                "'Ship'wright'   # malformed quote",
                Path("metadata.yaml"),
                1,
                errors,
            )
        )
        self.assertTrue(any("malformed single-quoted scalar" in error for error in errors))

    def test_skill_frontmatter_parser_accepts_commented_mapping_keys(self) -> None:
        errors: list[str] = []
        frontmatter = validator._parse_frontmatter(
            "---\nmetadata: # grouped values\n  value: present\n---\n",
            errors,
        )
        self.assertEqual([], errors)
        self.assertEqual({"metadata": {"value": "present"}}, frontmatter)

    def test_openai_metadata_accepts_commented_mapping_keys(self) -> None:
        metadata = "skills/shipwright/agents/openai.yaml"
        self.replace(metadata, "interface:\n", "interface: # UI fields\n")
        self.replace(metadata, "policy:\n", "policy: # invocation policy\n")
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_skill_frontmatter_rejects_inactive_malformed_nested_and_duplicate_fields(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        mutations = {
            "commented": original.replace("name: shipwright", "# name: shipwright", 1),
            "malformed quote": original.replace("name: shipwright", 'name: "shipwright', 1),
            "wrong nesting": original.replace(
                "name: shipwright", "metadata:\n  name: shipwright", 1
            ),
            "duplicate": original.replace(
                "name: shipwright", "name: shipwright\nname: duplicate", 1
            ),
            "extra": original.replace(
                "name: shipwright", "name: shipwright\nextra: metadata", 1
            ),
        }
        for label, content in mutations.items():
            with self.subTest(case=label):
                self.path(skill).write_text(content, encoding="utf-8")
                self.assert_error(skill)
        self.path(skill).write_text(original, encoding="utf-8")

    def test_reports_wrong_codex_skills_path(self) -> None:
        path = ".codex-plugin/plugin.json"
        manifest = self.read_json(path)
        manifest["skills"] = "./other-skills/"
        self.write_json(path, manifest)
        self.assert_error("skills")

    def test_reports_invalid_manifest_and_codex_interface_metadata(self) -> None:
        codex_path = ".codex-plugin/plugin.json"
        claude_path = ".claude-plugin/plugin.json"
        codex = self.read_json(codex_path)
        claude = self.read_json(claude_path)
        del codex["repository"]
        codex["interface"]["capabilities"] = ["Read"]
        codex["interface"]["defaultPrompt"] = "not-a-list"
        claude["keywords"] = []
        self.write_json(codex_path, codex)
        self.write_json(claude_path, claude)
        errors = validate_bundle(self.repo_root)
        for fragment in ("repository", "capabilities", "defaultPrompt", "keywords"):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_invalid_openai_metadata(self) -> None:
        self.replace(
            "skills/shipwright/agents/openai.yaml",
            "allow_implicit_invocation: false",
            "allow_implicit_invocation: true",
        )
        self.assert_error("allow_implicit_invocation")

    def test_openai_metadata_accepts_supported_unquoted_scalars(self) -> None:
        metadata = "skills/shipwright/agents/openai.yaml"
        content = self.path(metadata).read_text(encoding="utf-8")
        content = content.replace('display_name: "Shipwright"', "display_name: Shipwright")
        content = content.replace(
            'short_description: "Strict end-to-end development workflow"',
            "short_description: Strict end-to-end development workflow",
        )
        content = content.replace(
            f'default_prompt: "{validator.DEFAULT_PROMPT}"',
            f"default_prompt: {validator.DEFAULT_PROMPT}",
        )
        self.path(metadata).write_text(content, encoding="utf-8")
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_openai_metadata_rejects_inactive_malformed_nested_and_duplicate_fields(self) -> None:
        metadata = "skills/shipwright/agents/openai.yaml"
        original = self.path(metadata).read_text(encoding="utf-8")
        mutations = {
            "commented": "\n".join(
                f"# {line}" if line.strip() else line for line in original.splitlines()
            )
            + "\n",
            "malformed quote": original.replace(
                'display_name: "Shipwright"', 'display_name: "Shipwright', 1
            ),
            "missing": original.replace('  display_name: "Shipwright"\n', "", 1),
            "wrong nesting": original.replace(
                "policy:\n  allow_implicit_invocation: false",
                "  allow_implicit_invocation: false",
                1,
            ),
            "duplicate": original.replace(
                '  display_name: "Shipwright"',
                '  display_name: "Shipwright"\n  display_name: "Duplicate"',
                1,
            ),
            "quoted boolean": original.replace(
                "allow_implicit_invocation: false",
                'allow_implicit_invocation: "false"',
                1,
            ),
            "extra": original + "extra: metadata\n",
        }
        for label, content in mutations.items():
            with self.subTest(case=label):
                self.path(metadata).write_text(content, encoding="utf-8")
                self.assert_error(metadata)
        self.path(metadata).write_text(original, encoding="utf-8")

    def test_reports_wrong_standalone_manifest_repository(self) -> None:
        for relative_path in (
            ".codex-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
        ):
            with self.subTest(path=relative_path):
                manifest = self.read_json(relative_path)
                manifest["repository"] = "https://github.com/psjostrom/agent-plugins"
                self.write_json(relative_path, manifest)
                self.assert_error(relative_path)

    def test_requires_catalog_based_codex_install_route(self) -> None:
        self.replace(
            "README.md",
            validator.CODEX_INSTALL_ROUTE,
            "codex plugin add shipwright",
        )
        self.assert_error("Codex install route")

    def test_reports_missing_public_invocation_identifiers(self) -> None:
        skill_path = "skills/shipwright/SKILL.md"
        readme_path = "README.md"
        self.replace(skill_path, "$shipwright:shipwright", "$shipwright")
        self.replace(skill_path, "/shipwright:shipwright", "/shipwright")
        self.replace(readme_path, "$shipwright:shipwright", "$shipwright")
        self.replace(readme_path, "/shipwright:shipwright", "/shipwright")
        self.replace(readme_path, " or `/shipwright` in Cursor", "")
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex invocation" in error for error in errors), errors)
        self.assertTrue(any("Claude invocation" in error for error in errors), errors)
        self.assertTrue(any("Cursor invocation" in error for error in errors), errors)

    def test_cursor_invocation_not_satisfied_by_claude_path_alone(self) -> None:
        skill_path = "skills/shipwright/SKILL.md"
        readme_path = "README.md"
        self.replace(skill_path, ", or `/shipwright` in Cursor", "")
        self.replace(readme_path, ", or `/shipwright` in Cursor", "")
        errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any("Cursor invocation" in error for error in errors),
            errors,
        )
        self.assertFalse(
            any("Codex invocation" in error for error in errors),
            errors,
        )
        self.assertFalse(
            any("Claude invocation" in error for error in errors),
            errors,
        )

    def test_reports_duplicate_skill_workflow_surface(self) -> None:
        duplicate = self.path("platform/codex/SKILL.md")
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text("# duplicate workflow\n", encoding="utf-8")
        self.assert_error("exactly one SKILL.md")

    def test_reports_missing_controller_gate_contracts(self) -> None:
        self.replace(
            "skills/shipwright/references/codex.md",
            "gpt-5.6-sol",
            "gpt-other",
        )
        self.replace(
            "skills/shipwright/references/claude-code.md",
            "claude-opus-4-6",
            "claude-other",
        )
        self.replace(
            "skills/shipwright/references/cursor.md",
            "Grok 4.5",
            "Grok-other",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex controller gate" in error for error in errors), errors)
        self.assertTrue(any("Claude controller gate" in error for error in errors), errors)
        self.assertTrue(any("Cursor controller gate" in error for error in errors), errors)

    def test_reports_codex_worker_route_regressions(self) -> None:
        reference = "skills/shipwright/references/codex.md"
        original = self.path(reference).read_text(encoding="utf-8")
        mutations = (
            ("| Mechanical | Luna 5.6+ / Max |", "| Mechanical | Luna 5.6+ / Medium |"),
            ("| Ordinary | Luna 5.6+ / Max |", "| Ordinary | Terra 5.6+ / Medium |"),
            ("| Integration | Luna 5.6+ / Max |", "| Integration | Terra 5.6+ / High |"),
            ("| Critical | Sol 5.6+ / High |", "| Critical | Luna 5.6+ / Max |"),
        )
        for expected, replacement in mutations:
            with self.subTest(route=expected):
                mutated = original.replace(expected, replacement, 1)
                self.path(reference).write_text(mutated, encoding="utf-8")
                self.assert_error("Codex worker routing")
        self.path(reference).write_text(original, encoding="utf-8")

    def test_reports_codex_worker_version_and_complete_route_regressions(self) -> None:
        reference = "skills/shipwright/references/codex.md"
        original = self.path(reference).read_text(encoding="utf-8")
        mutations = (
            (
                "Require a resolved Luna or Sol worker model at version `5.6` or newer",
                "Accept any resolved Luna or Sol worker model version",
                "Codex worker version floor",
            ),
            (
                "Terra and Sol/Medium are not allowlisted Shipwright worker routes",
                "Terra and Sol/Medium may be allowlisted Shipwright worker routes",
                "Codex worker routing exclusions",
            ),
            (
                "Do not rank family and effort independently across routes",
                "Rank family and effort independently across routes",
                "Codex complete-route ordering",
            ),
            (
                "standard: Luna 5.6+ / Max",
                "standard: Luna 5.6+ / High",
                "Codex standard complete route",
            ),
            (
                "critical: Sol 5.6+ / High, Sol 5.6+ / xhigh, Sol 5.6+ / max",
                "critical: Sol 5.6+ / High",
                "Codex critical complete routes",
            ),
            (
                "Sol/High or stronger therefore satisfies a standard request",
                "Only Luna/Max satisfies a standard request",
                "Codex stronger route acceptance",
            ),
        )
        for expected, replacement, error in mutations:
            with self.subTest(contract=error):
                mutated = original.replace(expected, replacement, 1)
                self.path(reference).write_text(mutated, encoding="utf-8")
                self.assert_error(error)
        self.path(reference).write_text(original, encoding="utf-8")

    def test_reports_claude_exact_version_pin_regression(self) -> None:
        claude = "skills/shipwright/references/claude-code.md"
        self.replace(
            claude,
            "Require a resolved Opus model at version `4.6` or newer.",
            "Accept only exact active model ID `claude-opus-4-6`.",
        )
        self.replace(
            claude,
            "An Opus version at or above the floor is accepted without editing this reference; record it as newer than the last behaviorally tested version.",
            "A future model, renamed model, or generic family label is not accepted until this reference explicitly allowlists it from first-party compatibility evidence.",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "Claude controller gate numeric floor",
            "Claude exact-version acceptance pin",
            "Claude future-model allowlist brittleness",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_cursor_family_only_effort_contracts(self) -> None:
        cursor = "skills/shipwright/references/cursor.md"
        self.replace(cursor, "Cursor Grok 4.5", "Cursor Grok-other")
        self.replace(cursor, "family dimension only", "model identity only")
        self.replace(cursor, "Compose dimensions", "Merge evidence")
        self.replace(
            cursor,
            "Never stop solely because controller effort is missing, weak, or unverifiable",
            "Stop when controller effort is missing",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "Cursor controller family display evidence",
            "Cursor harness family-only evidence",
            "Cursor composite family/effort evidence",
            "Cursor controller effort never hard-stops",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_child_evidence_and_retry_contracts(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(skill, "BLOCKED_RUNTIME", "RUNTIME_STOP")
        self.replace(skill, "one fallback per gated role", "fallback when useful")
        self.replace(skill, "thread/run ID", "child identifier")
        self.replace(
            skill,
            "when the selected route defines an effort floor",
            "for every selected route",
        )
        self.replace(
            skill,
            "absent effort is allowed only when that route defines none, or when the selected platform reference waives the effort dimension",
            "absent effort is always allowed",
        )
        self.replace(
            skill,
            "Independently validate each reported dimension",
            "Trust the combined evidence",
        )
        self.replace(
            skill,
            "Any unknown nonempty model or effort label is unverified.",
            "Unknown labels may be accepted.",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "BLOCKED_RUNTIME",
            "runtime retry",
            "child runtime evidence",
            "conditional effort evidence",
            "absent effort evidence",
            "independent evidence dimensions",
            "unknown effort evidence",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_gate_before_reduction_contracts(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(
            skill,
            "including before any §3 reduction",
            "after design artifacts if needed",
        )
        self.replace(
            skill,
            "unreadable platform reference is a stop condition",
            "unreadable platform reference may be ignored",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "controller gate before trivial reduction",
            "unreadable platform reference stop",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_reduction_verification_surface_contracts(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(
            skill,
            "and the verification surface it can affect is narrow",
            "and the change looks cheap to implement",
        )
        self.replace(
            skill,
            "§11 fresh verification, or §12 QA routing",
            "the controller gate, or the requirement to read the platform reference",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "§3 verification-surface reduction criterion",
            "§3 reduction never waives verification or QA",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_reduced_path_project_config_contract(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(
            skill,
            "do not create or modify project-level configuration",
            "project-level configuration may be added as needed",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(
                "§3 reduced path no unrequested project config" in error
                for error in errors
            ),
            errors,
        )

    def test_reports_missing_linked_controller_effort_pr_disclosure(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        cases = (
            (
                "suppress `unverifiable` from the user-facing completion report",
                "always disclose unverifiable effort in the completion report",
                "controller effort suppress unverifiable from completion report",
            ),
            (
                "and from any authorized PR body",
                "but never from any authorized PR body",
                "controller effort suppress unverifiable from authorized PR body",
            ),
            (
                "always record the effort evidence state in the ledger",
                "omit effort evidence from the ledger",
                "controller effort always recorded in ledger",
            ),
            (
                "forbid AI-attribution or tooling references in user-facing text",
                "forbid AI-attribution alone",
                "controller effort PR disclosure yields to repo rules",
            ),
        )
        for old, new, fragment in cases:
            with self.subTest(fragment=fragment):
                self.path(skill).write_text(original, encoding="utf-8")
                self.replace(skill, old, new)
                errors = validate_bundle(self.repo_root)
                self.assertTrue(
                    any(fragment in error for error in errors),
                    errors,
                )
        self.path(skill).write_text(original, encoding="utf-8")

    def test_reports_missing_field_report_contract_markers(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        cases = (
            (
                "compare filtered path *sets*",
                "compare filtered path counts",
                "§1 discovery uses path sets not counts",
            ),
            (
                "Redirect to a file and read `$?`",
                "Read exit status from the harness completion code",
                "§11 file-backed tool exit status",
            ),
            (
                "Read exit status from a value written to a file",
                "Read exit status from the compound command",
                "§8 reading evidence file-backed exit status",
            ),
            (
                "Take the child thread/run ID from the harness spawn result",
                "Require the child to self-report its thread/run ID",
                "§7 child run ID from harness spawn",
            ),
            (
                "**Reading evidence.**",
                "**Evidence notes.**",
                "§8 reading evidence section",
            ),
            (
                "identical before/after screens are the required artifact",
                "screenshots are optional when the UI is unchanged",
                "§12 before/after screens required artifact",
            ),
            (
                "absolute QA evidence directory path",
                "relative QA evidence directory path",
                "§12 absolute QA evidence path in completion report",
            ),
            (
                "quantitative diff/observation numbers",
                "qualitative screenshot impressions",
                "§12 quantitative diff or observation numbers",
            ),
            (
                "manifests and lockfiles byte-identical",
                "manifests and lockfiles approximately unchanged",
                "§14 byte-identical restoration proof",
            ),
            (
                "record both the action and the proof in the ledger",
                "record the action without the proof in the ledger",
                "§14 restoration proof recorded in ledger",
            ),
            (
                "If that proof fails, stop and surface the drift",
                "If that proof fails, continue anyway",
                "§14 restoration drift handling",
            ),
            (
                "you cannot upload the images yourself",
                "you cannot upload the images yourself; prefer embedding private-repo-scoped image URLs when obtainable without new credentials or policy breach",
                "§12 soft PR-upload hedge",
            ),
            (
                "Any literal expected value must either be measured",
                "Literal expected values may be inferred from nearby mocks",
                "§4 literal expected values must be measured",
            ),
            (
                "work on a branch in the main checkout instead",
                "always create a fresh worktree even when generated files are missing",
                "§1 worktree exception for generated gitignored files",
            ),
            (
                "When §1's generated-gitignored-file exception applies, skip the fresh worktree",
                "Always create a fresh worktree after plan approval",
                "§4 worktree handoff honors §1 generated-file exception",
            ),
            (
                "Resolve it before dispatch, not at commit time",
                "Discover commit-gate collisions at commit time",
                "§1 commit-gate preflight against task files",
            ),
            (
                "record it as impossible, state why in one line",
                "treat impossible observations as unverified with no substitute",
                "§13 structurally impossible named observations",
            ),
            (
                "This does not upgrade the outcome: it remains non-passing",
                "This upgrades the outcome to verified when substitutes are strong",
                "§13 impossible observation stays non-passing",
            ),
        )
        for old, new, fragment in cases:
            with self.subTest(fragment=fragment):
                self.path(skill).write_text(original, encoding="utf-8")
                self.replace(skill, old, new)
                errors = validate_bundle(self.repo_root)
                self.assertTrue(
                    any(fragment in error for error in errors),
                    errors,
                )
        self.path(skill).write_text(original, encoding="utf-8")

    def test_rejects_weakened_verified_definition_contract(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        full = (
            "- `verified`: every mandatory observation and artifact exists and the "
            "flow passed; for visual surfaces this includes the published session "
            "evidence (absolute QA path plus diff/observation numbers in the "
            "completion report).\n"
        )
        weakened = (
            "- `verified`: every mandatory observation and artifact exists and the "
            "flow passed.\n"
        )
        self.assertIn(full, original)
        text = original.replace(full, weakened, 1)
        text = text.replace(
            "absolute QA evidence directory path and quantitative diff/observation numbers",
            "a brief QA summary",
            1,
        )
        text = text.replace("absolute QA evidence directory path", "QA evidence directory path")
        text = text.replace(
            "quantitative diff/observation numbers", "observation notes"
        )
        self.path(skill).write_text(text, encoding="utf-8")
        errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(
                "§12 absolute QA evidence path in completion report" in error
                for error in errors
            ),
            errors,
        )
        self.assertTrue(
            any(
                "§12 quantitative diff or observation numbers" in error
                for error in errors
            ),
            errors,
        )
        self.path(skill).write_text(original, encoding="utf-8")

    def test_reports_missing_claude_controller_child_report_actions(self) -> None:
        claude = "skills/shipwright/references/claude-code.md"
        original = self.path(claude).read_text(encoding="utf-8")
        cases = (
            (
                "have the controller persist it to the dispatch's artifact directory",
                "leave the child's final message as the only record",
                "Claude controller-persisted child reports",
            ),
            (
                "expect it, reject it",
                "expect it, and accept it when present",
                "Claude expected rejected env effort",
            ),
            (
                "the ledger is a local artifact, not a reply — record it there",
                "treat the child agent ID as unavailable when it must not be shown to the user",
                "Claude child agent ID recorded in ledger",
            ),
        )
        for old, new, fragment in cases:
            with self.subTest(fragment=fragment):
                self.path(claude).write_text(original, encoding="utf-8")
                self.replace(claude, old, new)
                # Keep the matching precondition so only the controller action is missing.
                remaining = self.path(claude).read_text(encoding="utf-8")
                if fragment == "Claude controller-persisted child reports":
                    self.assertIn(
                        "Claude Code's subagent tooling prevents children from writing report files",
                        remaining,
                    )
                elif fragment == "Claude expected rejected env effort":
                    self.assertIn(
                        "Children will keep offering environment-variable-sourced effort",
                        remaining,
                    )
                else:
                    self.assertIn(
                        "The controller independently reads the child session record when exposed",
                        remaining,
                    )
                errors = validate_bundle(self.repo_root)
                self.assertTrue(
                    any(fragment in error for error in errors),
                    errors,
                )
        self.path(claude).write_text(original, encoding="utf-8")

    def test_reports_missing_post_plan_handoff_override(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(
            skill,
            "do not present Superpowers `writing-plans` execution options",
            "may present Superpowers writing-plans execution options",
        )
        self.replace(
            skill,
            "offer `superpowers:executing-plans` / Inline Execution",
            "offer Inline Execution when useful",
        )
        self.replace(
            skill,
            "Shipwright overrides that handoff",
            "Shipwright may follow that handoff",
        )
        self.replace(
            skill,
            "do not wait for the user to choose an execution mode",
            "ask the user which execution mode to use",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "post-plan execution handoff override",
            "post-plan Inline Execution rejection",
            "post-plan handoff ownership",
            "post-plan no execution-mode ask",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_review_and_bounded_remediation_contracts(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(skill, "fresh independent reviewer", "reviewer")
        self.replace(skill, "at most two ordinary remediation cycles", "several cycles")
        self.replace(skill, "one final escalated attempt", "escalate if needed")
        self.replace(
            skill,
            "at most two context-repair redispatches",
            "context-repair redispatches as needed",
        )
        self.replace(
            skill,
            "If the second redispatch still returns `NEEDS_CONTEXT`, set `BLOCKED`",
            "If context is still missing, retry",
        )
        self.replace(
            skill,
            "`resumable: awaiting user context`",
            "resumable later",
        )
        self.replace(
            skill,
            "Do not dispatch again automatically.",
            "Retry if useful.",
        )
        self.replace(
            skill,
            "the user supplies the missing context and explicitly asks to continue",
            "more context appears",
        )
        self.replace(
            skill,
            "reset the two-redispatch context-repair budget",
            "continue the existing retry budget",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "independent review",
            "two remediation",
            "escalated remediation",
            "context-repair retry cap",
            "NEEDS_CONTEXT terminal transition",
            "NEEDS_CONTEXT ledger state",
            "NEEDS_CONTEXT automatic stop",
            "NEEDS_CONTEXT user-authorized reopen",
            "NEEDS_CONTEXT post-intervention budget",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_qa_routes_and_terminal_states(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        for old, new in (
            ("agent-browser", "browser-tool"),
            ("Playwright", "browser-regression-tool"),
            ("argent", "mobile-tool"),
            ("partially verified", "partial"),
            ("unverified", "not checked"),
            ("BLOCKED_QA", "QA_STOP"),
        ):
            self.replace(skill, old, new)
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "agent-browser",
            "Playwright",
            "Argent",
            "partially verified",
            "unverified",
            "BLOCKED_QA",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_argent_mcp_probe_contracts(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        self.replace(
            skill,
            "loaded argent MCP toolset",
            "argent CLI on PATH",
        )
        self.replace(
            skill,
            "CLI presence alone does not establish the capability",
            "CLI presence is enough to proceed",
        )
        errors = validate_bundle(self.repo_root)
        for fragment in (
            "Argent mobile QA MCP-tool probe",
            "Argent CLI not sufficient for mobile QA",
        ):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_each_missing_standalone_qa_outcome_definition(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed; for visual surfaces this includes the published session evidence (absolute QA path plus diff/observation numbers in the completion report).\n",
            "- `partially verified`: every core observation passed, but a named non-core planned observation was unavailable.\n",
            "- `unverified`: the flow could not run, the interaction surface was unavailable, or core evidence is missing.\n",
        )
        for definition in definitions:
            with self.subTest(definition=definition.split(":", 1)[0]):
                self.assertIn(definition, original)
                self.path(skill).write_text(
                    original.replace(definition, "", 1), encoding="utf-8"
                )
                self.assert_error("QA outcome definition")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_qa_outcome_definitions_must_be_active_markdown(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed; for visual surfaces this includes the published session evidence (absolute QA path plus diff/observation numbers in the completion report).\n",
            "- `partially verified`: every core observation passed, but a named non-core planned observation was unavailable.\n",
            "- `unverified`: the flow could not run, the interaction surface was unavailable, or core evidence is missing.\n",
        )
        wrappers = (
            ("backtick fence", "```text\n{} ```\n"),
            ("tilde fence", "~~~text\n{} ~~~\n"),
            ("HTML comment", "<!--\n{}-->\n"),
        )
        for definition in definitions:
            without_active = original.replace(definition, "", 1)
            for label, wrapper in wrappers:
                with self.subTest(outcome=definition.split(":", 1)[0], context=label):
                    spoof = wrapper.format(definition)
                    self.path(skill).write_text(
                        without_active + "\n" + spoof, encoding="utf-8"
                    )
                    self.assert_error("QA outcome definition")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_indented_code_cannot_supply_qa_outcome_definitions(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed; for visual surfaces this includes the published session evidence (absolute QA path plus diff/observation numbers in the completion report).\n",
            "- `partially verified`: every core observation passed, but a named non-core planned observation was unavailable.\n",
            "- `unverified`: the flow could not run, the interaction surface was unavailable, or core evidence is missing.\n",
        )
        for definition in definitions:
            without_active = original.replace(definition, "", 1)
            for indentation in ("    ", "\t"):
                with self.subTest(
                    outcome=definition.split(":", 1)[0], indentation=repr(indentation)
                ):
                    self.path(skill).write_text(
                        without_active + "\n" + indentation + definition,
                        encoding="utf-8",
                    )
                    self.assert_error("QA outcome definition")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_fenced_literal_html_comment_does_not_hide_active_qa_definitions(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        marker = "## 13. Record QA outcomes\n"
        for label, fenced_literal in (
            ("backtick", "```text\n<!-- literal code text\n```\n"),
            ("tilde", "~~~text\n<!-- literal code text\n~~~\n"),
        ):
            with self.subTest(fence=label):
                self.path(skill).write_text(
                    original.replace(marker, fenced_literal + "\n" + marker, 1),
                    encoding="utf-8",
                )
                self.assertEqual([], validate_bundle(self.repo_root))
        self.path(skill).write_text(original, encoding="utf-8")

    def test_inline_code_literal_html_comment_does_not_hide_active_qa_definitions(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        marker = "## 13. Record QA outcomes\n"
        self.replace(skill, marker, "`<!-- literal code text`\n\n" + marker)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_invalid_backtick_info_string_does_not_hide_active_qa_definitions(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        marker = "## 13. Record QA outcomes\n"
        self.replace(skill, marker, "```text`invalid\n\n" + marker)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_qa_outcome_fences_preserve_marker_length_and_indentation_rules(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definition = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed; for visual surfaces this includes the published session evidence (absolute QA path plus diff/observation numbers in the completion report).\n"
        )
        without_active = original.replace(definition, "", 1)
        wrappers = (
            ("longer backtick closer", "````text\n{} `````\n"),
            ("longer tilde closer", "~~~~text\n{} ~~~~~\n"),
            ("three-space backtick", "   ```text\n{}   ```\n"),
            ("three-space tilde", "   ~~~text\n{}   ~~~\n"),
            ("too-short backtick closer", "````text\n{} ```\n````\n"),
            ("too-short tilde closer", "~~~~text\n{} ~~~\n~~~~\n"),
        )
        for label, wrapper in wrappers:
            with self.subTest(context=label):
                self.path(skill).write_text(
                    without_active + "\n" + wrapper.format(definition),
                    encoding="utf-8",
                )
                self.assert_error("QA outcome definition")
        self.path(skill).write_text(original, encoding="utf-8")

    def test_reports_missing_authorization_boundaries(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        for old, new in (
            ("Restore declared project state", "Ignore declared project state"),
            (
                "Add/upgrade dependencies, mutate lockfile contents intentionally",
                "Change dependencies freely",
            ),
            ("paid quota", "resources"),
            ("push; open a PR; deploy; publish", "release actions"),
            ("Destructive filesystem or git action", "Risky action"),
        ):
            self.replace(skill, old, new)
        errors = validate_bundle(self.repo_root)
        self.assertGreaterEqual(
            sum("authorization boundary" in error for error in errors), 4, errors
        )

    def test_reports_missing_restoration_proof_contract(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        cases = (
            (
                "manifests and lockfiles byte-identical",
                "manifests and lockfiles look fine",
                "§14 byte-identical restoration proof",
            ),
            (
                "record both the action and the proof in the ledger",
                "mention the action casually",
                "§14 restoration proof recorded in ledger",
            ),
            (
                "If that proof fails, stop and surface the drift",
                "If that proof fails, ignore the drift",
                "§14 restoration drift handling",
            ),
        )
        for old, new, fragment in cases:
            with self.subTest(fragment=fragment):
                self.path(skill).write_text(original, encoding="utf-8")
                self.replace(skill, old, new)
                errors = validate_bundle(self.repo_root)
                self.assertTrue(
                    any(fragment in error for error in errors),
                    errors,
                )
        self.path(skill).write_text(original, encoding="utf-8")

    def test_reports_stale_public_name_and_profile_dependency(self) -> None:
        skill = "skills/shipwright/SKILL.md"
        path = self.path(skill)
        original = path.read_text(encoding="utf-8")
        legacy_skill = "-".join(("full", "dev"))
        for stale in ("$" + legacy_skill, legacy_skill + "-implementer"):
            with self.subTest(stale=stale):
                try:
                    path.write_text(original + f"\n{stale}\n", encoding="utf-8")
                    self.assert_error("stale public name/profile dependency")
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_stale_scan_covers_all_scoped_surfaces_and_legacy_forms(self) -> None:
        legacy_skill = "-".join(("full", "dev"))
        stale_forms = ("$" + legacy_skill, "/" + legacy_skill, legacy_skill + "-worker")

        plugin_paths = (
            "legacy-profile.toml",
            "legacy-command",
        )
        for relative_path in plugin_paths:
            for stale in stale_forms:
                with self.subTest(surface=relative_path, stale=stale):
                    path = self.path(relative_path)
                    path.write_text(stale + "\n", encoding="utf-8")
                    self.assert_error(relative_path)
                    path.unlink()

        readme = "README.md"
        original_readme = self.path(readme).read_text(encoding="utf-8")
        bullet = next(
            line for line in original_readme.splitlines() if line.startswith("- `shipwright`")
        )
        for stale in stale_forms:
            with self.subTest(surface=readme, stale=stale):
                self.path(readme).write_text(
                    original_readme.replace(bullet, f"{bullet} {stale}", 1),
                    encoding="utf-8",
                )
                self.assert_error(readme)
        self.path(readme).write_text(original_readme, encoding="utf-8")

    def test_stale_scan_reports_undecodable_and_unreadable_scoped_files(self) -> None:
        undecodable = self.path("undecodable.asset")
        undecodable.write_bytes(b"\xff\xfe\xfd")
        self.assert_error("cannot inspect undecodable.asset")
        undecodable.unlink()

        unreadable = self.path("unreadable.asset")
        unreadable.write_text("ordinary text\n", encoding="utf-8")
        original_read_bytes = Path.read_bytes

        def fail_selected(path: Path) -> bytes:
            if path == unreadable:
                raise OSError("simulated read failure")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=fail_selected):
            self.assert_error("cannot inspect unreadable.asset")

    def test_stale_scan_reports_unreadable_scoped_directory_when_permissions_apply(self) -> None:
        blocked = self.path("unreadable-directory")
        blocked.mkdir()
        legacy_skill = "-".join(("full", "dev"))
        (blocked / "legacy-command").write_text("$" + legacy_skill + "\n", encoding="utf-8")
        blocked.chmod(0)
        try:
            errors = validate_bundle(self.repo_root)
        finally:
            blocked.chmod(0o700)
        expected_fragment = (
            "cannot inspect directory unreadable-directory"
        )
        if not any(expected_fragment in error for error in errors):
            self.skipTest("runtime can enumerate mode-000 directories")
        self.assertTrue(
            any(expected_fragment in error for error in errors),
            errors,
        )

    def test_stale_scan_reports_directory_enumeration_errors_through_walk_boundary(self) -> None:
        failed = self.path("unreadable-directory")

        def fail_walk(top: Path, onerror: object = None) -> list[object]:
            self.assertEqual(self.path("."), Path(top))
            self.assertIsNotNone(onerror)
            error = PermissionError(13, "simulated enumeration failure", str(failed))
            onerror(error)  # type: ignore[operator]
            return []

        with mock.patch.object(validator.os, "walk", side_effect=fail_walk):
            errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(
                "cannot inspect directory unreadable-directory"
                in error
                and "simulated enumeration failure" in error
                for error in errors
            ),
            errors,
        )

    def test_stale_scan_skips_only_nul_marked_binary_files(self) -> None:
        binary = self.path("image.bin")
        legacy_skill = "-".join(("full", "dev")).encode()
        binary.write_bytes(b"\x00$" + legacy_skill)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_stale_scan_ignores_git_metadata(self) -> None:
        git_object = self.path(".git/objects/aa/object")
        git_object.parent.mkdir(parents=True)
        git_object.write_bytes(b"\xff")
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_stale_scan_covers_historical_documents_inside_repository_root(self) -> None:
        historical = self.path("docs/history.md")
        historical.parent.mkdir(parents=True)
        legacy_skill = "-".join(("full", "dev"))
        historical.write_text(
            "$" + legacy_skill + "\n" + legacy_skill + "-worker\n", encoding="utf-8"
        )
        self.assert_error("docs/history.md")

    def test_accumulates_multiple_invariant_failures(self) -> None:
        codex_manifest = self.path(".codex-plugin/plugin.json")
        codex_manifest.unlink()
        self.replace(
            "skills/shipwright/references/claude-code.md",
            "claude-opus-4-6",
            "claude-other",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any(".codex-plugin/plugin.json" in error for error in errors), errors)
        self.assertTrue(any("Claude controller gate" in error for error in errors), errors)

    def test_field_and_version_diagnostics_include_their_source_paths(self) -> None:
        codex_path = ".codex-plugin/plugin.json"
        claude_path = ".claude-plugin/plugin.json"

        codex = self.read_json(codex_path)
        codex["repository"] = "wrong"
        self.write_json(codex_path, codex)
        claude = self.read_json(claude_path)
        claude["version"] = "1.0.0"
        self.write_json(claude_path, claude)
        errors = validate_bundle(self.repo_root)
        for relative_path, field in (
            (codex_path, "repository"),
            (claude_path, "version"),
        ):
            self.assertTrue(
                any(relative_path in error and field in error for error in errors), errors
            )

    def test_main_success_contract(self) -> None:
        stdout = StringIO()
        with mock.patch.object(validator, "_repository_root", return_value=self.repo_root):
            with redirect_stdout(stdout):
                status = validator.main()
        self.assertEqual(0, status)
        self.assertEqual("Shipwright validation passed.\n", stdout.getvalue())

    def test_main_failure_contract(self) -> None:
        missing = ".codex-plugin/plugin.json"
        self.path(missing).unlink()
        stdout = StringIO()
        with mock.patch.object(validator, "_repository_root", return_value=self.repo_root):
            with redirect_stdout(stdout):
                status = validator.main()
        self.assertEqual(1, status)
        self.assertEqual(
            "Shipwright validation failed:\n"
            f"- missing required JSON file: {missing}\n",
            stdout.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
