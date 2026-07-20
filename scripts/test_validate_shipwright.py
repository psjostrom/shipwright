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
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

import validate_shipwright as validator  # noqa: E402


validate_bundle = validator.validate_bundle


class ShipwrightValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temporary_directory.name)

        shutil.copytree(
            REPOSITORY_ROOT / "plugins" / "shipwright",
            self.repo_root / "plugins" / "shipwright",
        )
        for relative_path in (
            Path(".agents/plugins/marketplace.json"),
            Path(".claude-plugin/marketplace.json"),
            Path("README.md"),
        ):
            destination = self.repo_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY_ROOT / relative_path, destination)

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
        path = self.path("plugins/shipwright/.codex-plugin/plugin.json")
        path.write_text("{not-json\n", encoding="utf-8")
        self.assert_error("malformed JSON")

    def test_reports_every_missing_manifest_and_catalog(self) -> None:
        paths = (
            "plugins/shipwright/.codex-plugin/plugin.json",
            "plugins/shipwright/.claude-plugin/plugin.json",
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
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
            "plugins/shipwright/skills/shipwright/SKILL.md",
            "plugins/shipwright/skills/shipwright/references/codex.md",
            "plugins/shipwright/skills/shipwright/references/claude-code.md",
            "plugins/shipwright/skills/shipwright/agents/openai.yaml",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as scratch:
                    moved = Path(scratch) / "missing"
                    self.path(relative_path).rename(moved)
                    self.assert_error(relative_path)
                    moved.rename(self.path(relative_path))

    def test_reports_wrong_manifest_names(self) -> None:
        for relative_path in (
            "plugins/shipwright/.codex-plugin/plugin.json",
            "plugins/shipwright/.claude-plugin/plugin.json",
        ):
            with self.subTest(path=relative_path):
                manifest = self.read_json(relative_path)
                manifest["name"] = "wrong-name"
                self.write_json(relative_path, manifest)
                self.assert_error("name")
                manifest["name"] = "shipwright"
                self.write_json(relative_path, manifest)

    def test_manifest_versions_follow_platform_specific_contracts(self) -> None:
        codex_path = "plugins/shipwright/.codex-plugin/plugin.json"
        claude_path = "plugins/shipwright/.claude-plugin/plugin.json"

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
        for invalid in ("1.0.1", "1.0.0-dev", "1.0.0+codex.local-1"):
            with self.subTest(platform="claude", version=invalid):
                claude["version"] = invalid
                self.write_json(claude_path, claude)
                errors = self.assert_error(claude_path)
                self.assertTrue(any("version" in error for error in errors), errors)

    def test_reports_wrong_skill_frontmatter_name(self) -> None:
        self.replace(
            "plugins/shipwright/skills/shipwright/SKILL.md",
            "name: shipwright",
            "name: wrong-name",
        )
        self.assert_error("frontmatter name")

    def test_skill_frontmatter_accepts_supported_quotes(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        self.replace(skill, "name: shipwright", 'name: "shipwright"')
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_skill_frontmatter_rejects_inactive_malformed_nested_and_duplicate_fields(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        path = "plugins/shipwright/.codex-plugin/plugin.json"
        manifest = self.read_json(path)
        manifest["skills"] = "./other-skills/"
        self.write_json(path, manifest)
        self.assert_error("skills")

    def test_reports_invalid_manifest_and_codex_interface_metadata(self) -> None:
        codex_path = "plugins/shipwright/.codex-plugin/plugin.json"
        claude_path = "plugins/shipwright/.claude-plugin/plugin.json"
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
            "plugins/shipwright/skills/shipwright/agents/openai.yaml",
            "allow_implicit_invocation: false",
            "allow_implicit_invocation: true",
        )
        self.assert_error("allow_implicit_invocation")

    def test_openai_metadata_accepts_supported_unquoted_scalars(self) -> None:
        metadata = "plugins/shipwright/skills/shipwright/agents/openai.yaml"
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
        metadata = "plugins/shipwright/skills/shipwright/agents/openai.yaml"
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

    def test_reports_wrong_marketplace_paths_and_codex_policies(self) -> None:
        codex_path = ".agents/plugins/marketplace.json"
        claude_path = ".claude-plugin/marketplace.json"
        codex = self.read_json(codex_path)
        claude = self.read_json(claude_path)
        codex_entry = next(item for item in codex["plugins"] if item["name"] == "shipwright")
        claude_entry = next(item for item in claude["plugins"] if item["name"] == "shipwright")
        codex_entry["source"]["path"] = "/absolute/shipwright"
        codex_entry["policy"]["installation"] = "REQUIRED"
        codex_entry["policy"]["authentication"] = "NONE"
        claude_entry["source"] = "../shipwright"
        self.write_json(codex_path, codex)
        self.write_json(claude_path, claude)
        errors = validate_bundle(self.repo_root)
        for fragment in ("source.path", "installation", "authentication", "source"):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_public_invocation_identifiers(self) -> None:
        skill_path = "plugins/shipwright/skills/shipwright/SKILL.md"
        readme_path = "README.md"
        self.replace(skill_path, "$shipwright:shipwright", "$shipwright")
        self.replace(skill_path, "/shipwright:shipwright", "/shipwright")
        self.replace(readme_path, "$shipwright:shipwright", "$shipwright")
        self.replace(readme_path, "/shipwright:shipwright", "/shipwright")
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex invocation" in error for error in errors), errors)
        self.assertTrue(any("Claude invocation" in error for error in errors), errors)

    def test_reports_duplicate_skill_workflow_surface(self) -> None:
        duplicate = self.path("plugins/shipwright/platform/codex/SKILL.md")
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text("# duplicate workflow\n", encoding="utf-8")
        self.assert_error("exactly one SKILL.md")

    def test_reports_missing_controller_gate_contracts(self) -> None:
        self.replace(
            "plugins/shipwright/skills/shipwright/references/codex.md",
            "gpt-5.6-sol",
            "gpt-other",
        )
        self.replace(
            "plugins/shipwright/skills/shipwright/references/claude-code.md",
            "claude-opus-4-7",
            "claude-other",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex controller gate" in error for error in errors), errors)
        self.assertTrue(any("Claude controller gate" in error for error in errors), errors)

    def test_reports_missing_child_evidence_and_retry_contracts(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        self.replace(skill, "BLOCKED_RUNTIME", "RUNTIME_STOP")
        self.replace(skill, "one fallback per gated role", "fallback when useful")
        self.replace(skill, "thread/run ID", "child identifier")
        errors = validate_bundle(self.repo_root)
        for fragment in ("BLOCKED_RUNTIME", "runtime retry", "child runtime evidence"):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_review_and_bounded_remediation_contracts(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        self.replace(skill, "fresh independent reviewer", "reviewer")
        self.replace(skill, "at most two ordinary remediation cycles", "several cycles")
        self.replace(skill, "one final escalated attempt", "escalate if needed")
        errors = validate_bundle(self.repo_root)
        for fragment in ("independent review", "two remediation", "escalated remediation"):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_reports_missing_qa_routes_and_terminal_states(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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

    def test_reports_each_missing_standalone_qa_outcome_definition(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed.\n",
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

    def test_reports_missing_authorization_boundaries(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        for old, new in (
            ("Install/download tools", "Use tools"),
            ("paid quota", "resources"),
            ("push; open a PR; deploy; publish", "release actions"),
            ("Destructive filesystem or git action", "Risky action"),
        ):
            self.replace(skill, old, new)
        errors = validate_bundle(self.repo_root)
        self.assertGreaterEqual(
            sum("authorization boundary" in error for error in errors), 4, errors
        )

    def test_reports_stale_public_name_and_profile_dependency(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        for stale in ("$" + "full-dev", "full-dev" + "-implementer"):
            with self.subTest(stale=stale):
                path = self.path(skill)
                original = path.read_text(encoding="utf-8")
                path.write_text(original + f"\n{stale}\n", encoding="utf-8")
                self.assert_error("stale public name/profile dependency")
                path.write_text(original, encoding="utf-8")

    def test_stale_scan_covers_all_scoped_surfaces_and_legacy_forms(self) -> None:
        stale_forms = ("$" + "full-dev", "/" + "full-dev", "full-dev" + "-worker")

        plugin_paths = (
            "plugins/shipwright/legacy-profile.toml",
            "plugins/shipwright/legacy-command",
        )
        for relative_path in plugin_paths:
            for stale in stale_forms:
                with self.subTest(surface=relative_path, stale=stale):
                    path = self.path(relative_path)
                    path.write_text(stale + "\n", encoding="utf-8")
                    self.assert_error(relative_path)
                    path.unlink()

        for relative_path in (
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
        ):
            original = self.read_json(relative_path)
            for stale in stale_forms:
                with self.subTest(surface=relative_path, stale=stale):
                    catalog = json.loads(json.dumps(original))
                    entry = next(
                        item for item in catalog["plugins"] if item["name"] == "shipwright"
                    )
                    entry["legacy_probe"] = stale
                    self.write_json(relative_path, catalog)
                    self.assert_error(relative_path)
            self.write_json(relative_path, original)

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
        undecodable = self.path("plugins/shipwright/undecodable.asset")
        undecodable.write_bytes(b"\xff\xfe\xfd")
        self.assert_error("cannot inspect plugins/shipwright/undecodable.asset")
        undecodable.unlink()

        unreadable = self.path("plugins/shipwright/unreadable.asset")
        unreadable.write_text("ordinary text\n", encoding="utf-8")
        original_read_bytes = Path.read_bytes

        def fail_selected(path: Path) -> bytes:
            if path == unreadable:
                raise OSError("simulated read failure")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=fail_selected):
            self.assert_error("cannot inspect plugins/shipwright/unreadable.asset")

    def test_stale_scan_skips_only_nul_marked_binary_files(self) -> None:
        binary = self.path("plugins/shipwright/image.bin")
        binary.write_bytes(b"\x00$" + b"full-dev")
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_stale_scan_ignores_historical_documents_outside_scope(self) -> None:
        historical = self.path("docs/history.md")
        historical.parent.mkdir(parents=True)
        historical.write_text("$" + "full-dev\nfull-dev" + "-worker\n", encoding="utf-8")
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_reports_every_absent_committed_scenario_case(self) -> None:
        scenario_path = "plugins/shipwright/evals/v1/scenarios.md"
        cases = (
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
        original = self.path(scenario_path).read_text(encoding="utf-8")
        for case in cases:
            with self.subTest(case=case):
                heading = f"### `{case}`\n"
                self.assertIn(heading, original)
                self.path(scenario_path).write_text(
                    original.replace(heading, "", 1), encoding="utf-8"
                )
                self.assert_error(f"scenario case {case}")
        self.path(scenario_path).write_text(original, encoding="utf-8")

    def test_accumulates_multiple_invariant_failures(self) -> None:
        codex_manifest = self.path("plugins/shipwright/.codex-plugin/plugin.json")
        codex_manifest.unlink()
        self.replace(
            "plugins/shipwright/skills/shipwright/references/claude-code.md",
            "claude-opus-4-7",
            "claude-other",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any(".codex-plugin/plugin.json" in error for error in errors), errors)
        self.assertTrue(any("Claude controller gate" in error for error in errors), errors)

    def test_field_and_version_diagnostics_include_their_source_paths(self) -> None:
        codex_path = "plugins/shipwright/.codex-plugin/plugin.json"
        claude_path = "plugins/shipwright/.claude-plugin/plugin.json"
        codex_marketplace_path = ".agents/plugins/marketplace.json"
        claude_marketplace_path = ".claude-plugin/marketplace.json"

        codex = self.read_json(codex_path)
        codex["repository"] = "wrong"
        self.write_json(codex_path, codex)
        claude = self.read_json(claude_path)
        claude["version"] = "1.0.1"
        self.write_json(claude_path, claude)
        codex_catalog = self.read_json(codex_marketplace_path)
        next(
            item for item in codex_catalog["plugins"] if item["name"] == "shipwright"
        )["category"] = "Wrong"
        self.write_json(codex_marketplace_path, codex_catalog)
        claude_catalog = self.read_json(claude_marketplace_path)
        next(
            item for item in claude_catalog["plugins"] if item["name"] == "shipwright"
        )["source"] = "wrong"
        self.write_json(claude_marketplace_path, claude_catalog)

        errors = validate_bundle(self.repo_root)
        for relative_path, field in (
            (codex_path, "repository"),
            (claude_path, "version"),
            (codex_marketplace_path, "category"),
            (claude_marketplace_path, "source"),
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
        missing = "plugins/shipwright/.codex-plugin/plugin.json"
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
