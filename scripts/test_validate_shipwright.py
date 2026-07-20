#!/usr/bin/env python3
"""Regression tests for the deterministic Shipwright bundle validator."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from validate_shipwright import validate_bundle  # noqa: E402


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

    def test_reports_wrong_skill_frontmatter_name(self) -> None:
        self.replace(
            "plugins/shipwright/skills/shipwright/SKILL.md",
            "name: shipwright",
            "name: wrong-name",
        )
        self.assert_error("frontmatter name")

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


if __name__ == "__main__":
    unittest.main()
