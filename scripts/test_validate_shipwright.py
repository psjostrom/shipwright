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
            Path(".cursor-plugin/marketplace.json"),
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
            "plugins/shipwright/.cursor-plugin/plugin.json",
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".cursor-plugin/marketplace.json",
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
            "plugins/shipwright/skills/shipwright/references/cursor.md",
            "plugins/shipwright/skills/shipwright/agents/openai.yaml",
            "plugins/shipwright/evals/v1/claude-code-runbook.md",
            "plugins/shipwright/evals/v1/cursor-runbook.md",
            "plugins/shipwright/evals/v1/codex-runbook.md",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as scratch:
                    moved = Path(scratch) / "missing"
                    self.path(relative_path).rename(moved)
                    self.assert_error(relative_path)
                    moved.rename(self.path(relative_path))

    def test_reports_missing_claude_runbook_contracts(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/claude-code-runbook.md"
        required_markers = (
            "## Prerequisites",
            "## Safety boundaries",
            "## Copy/paste prompt for Claude Code",
            "## Required cases and repetitions",
            "## Evidence bundle",
            "## Result rubric",
            "## Return template",
            "/shipwright:shipwright",
            "Claude Code 2.1.117 or newer",
            "Superpowers 6.1.1 or newer",
            "claude-opus-4-6",
            "xhigh or stronger",
            "one broad smoke pass",
            "3/3 exact passes",
            "at least 2/3 intended",
            "3/3 safe choices",
            "PASS",
            "FAIL",
            "UNVERIFIED",
            "disposable fixture repository",
            "credentials",
            "paid external services",
            "must not modify Shipwright",
            'shipwright_checkout="$(pwd -P)"',
            'shipwright_status="<clean>"',
            'fixture_root="$(mktemp -d)"',
            'git -C "$fixture_root" init',
            "evaluation-input/claude-code-runbook.md",
            "evaluation-input/scenarios.md",
            'environment_seed="$fixture_root/evaluation-input/environment-seed.md"',
            "printf 'shipwright_commit=%s\\n' \"$shipwright_commit\" > \"$environment_seed\"",
            "shipwright_status<<END_SHIPWRIGHT_STATUS",
            "END_SHIPWRIGHT_STATUS",
            "printf 'shipwright_plugin_source=%s\\n' \"$shipwright_checkout/plugins/shipwright\" >> \"$environment_seed\"",
            "printf 'evidence_dir=%s\\n' \"$evidence_dir\" >> \"$environment_seed\"",
            "Read evaluation-input/environment-seed.md along with",
            "Failure to create or read environment-seed.md makes the evaluation `UNVERIFIED`.",
            "shipwright_prepare_claude_evaluation() {",
            "SUPERPOWERS_PLUGIN_DIR",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "env -i",
            'HOME="$isolated_home"',
            'XDG_CONFIG_HOME="$isolated_xdg_config"',
            'XDG_CACHE_HOME="$isolated_xdg_cache"',
            'CLAUDE_CONFIG_DIR="$isolated_claude_config"',
            "--setting-sources project",
            '--plugin-dir "$superpowers_plugin_dir"',
            "If Claude Code is below 2.1.117, stop and mark the evaluation `UNVERIFIED`.",
            "If Superpowers is below 6.1.1, stop and mark the evaluation `UNVERIFIED`.",
            "Stop and report UNVERIFIED if Claude Code is below 2.1.117, Superpowers is below 6.1.1",
            "Accept compatible newer Claude Code and Superpowers versions.",
            "below-minimum Claude Code or Superpowers version",
            ".git/info/exclude",
            'git -C "$fixture_root" check-ignore -q "$evidence_dir"',
            '--plugin-dir "$shipwright_checkout/plugins/shipwright"',
            'cd "$fixture_root"',
            'evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"',
            "Failure of copy/setup, ignore verification, isolated process setup, explicit authentication, or fixture-rooted plugin loading",
        )
        for index, marker in enumerate(required_markers):
            with self.subTest(marker=marker):
                replacement = f"__missing_contract_{index}__"
                self.replace(runbook_path, marker, replacement)
                self.assert_error("Claude runbook")
                self.replace(runbook_path, replacement, marker)

    def test_reports_every_missing_claude_runbook_case(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/claude-code-runbook.md"
        for case in validator.CLAUDE_RUNBOOK_CASES:
            with self.subTest(case=case):
                self.replace(runbook_path, f"`{case}`", f"`removed-{case}`")
                self.assert_error(f"missing delegated Claude case {case}")
                self.replace(runbook_path, f"`removed-{case}`", f"`{case}`")

    def test_reports_missing_cursor_runbook_contracts(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/cursor-runbook.md"
        required_markers = (
            "## Prerequisites",
            "## Safety boundaries",
            "## Copy/paste prompt for Cursor",
            "## Required cases and repetitions",
            "## Evidence bundle",
            "## Result rubric",
            "## Return template",
            "plugin skill discovery, Task subagents, and current-turn model/effort evidence",
            "Superpowers 6.1.1 or newer",
            "Grok 4.5",
            "high or stronger",
            "one broad smoke pass",
            "3/3 exact passes",
            "at least 2/3 intended",
            "3/3 safe choices",
            "PASS",
            "FAIL",
            "UNVERIFIED",
            "disposable fixture repository",
            "credentials",
            "paid external services",
            "must not modify Shipwright",
            'shipwright_checkout="$(pwd -P)"',
            'shipwright_status="<clean>"',
            'fixture_root="$(mktemp -d)"',
            'git -C "$fixture_root" init',
            "evaluation-input/cursor-runbook.md",
            "evaluation-input/scenarios.md",
            'environment_seed="$fixture_root/evaluation-input/environment-seed.md"',
            "printf 'shipwright_commit=%s\\n' \"$shipwright_commit\" > \"$environment_seed\"",
            "shipwright_status<<END_SHIPWRIGHT_STATUS",
            "END_SHIPWRIGHT_STATUS",
            "printf 'shipwright_plugin_source=%s\\n' \"$shipwright_checkout/plugins/shipwright\" >> \"$environment_seed\"",
            "printf 'cursor_plugins_local=%s\\n' \"$cursor_plugins_local\" >> \"$environment_seed\"",
            "printf 'evidence_dir=%s\\n' \"$evidence_dir\" >> \"$environment_seed\"",
            "Read evaluation-input/environment-seed.md along with",
            "Failure to create or read environment-seed.md makes the evaluation `UNVERIFIED`.",
            "shipwright_prepare_cursor_evaluation() {",
            "SUPERPOWERS_PLUGIN_DIR",
            'cursor_plugins_local="$fixture_root/.cursor/plugins/local"',
            'ln -sfn "$shipwright_checkout/plugins/shipwright" "$cursor_plugins_local/shipwright"',
            "Do not run install-cursor.sh against the host ~/.cursor/plugins/local during setup",
            "If Superpowers is below 6.1.1, stop and mark the evaluation `UNVERIFIED`.",
            "Stop and report UNVERIFIED if Cursor lacks plugin discovery, Task subagents, or current-turn model evidence, Superpowers is below 6.1.1",
            "Accept compatible newer Cursor and Superpowers versions.",
            "below-minimum Superpowers version is active; Cursor lacks plugin discovery",
            ".git/info/exclude",
            'git -C "$fixture_root" check-ignore -q "$evidence_dir"',
            "fixture-local plugin symlink loading route",
            'evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"',
            "Failure of copy/setup, ignore verification, fixture-local plugin staging, or fixture-rooted plugin loading",
        )
        for index, marker in enumerate(required_markers):
            with self.subTest(marker=marker):
                replacement = f"__missing_cursor_contract_{index}__"
                self.replace(runbook_path, marker, replacement)
                self.assert_error("Cursor runbook")
                self.replace(runbook_path, replacement, marker)

    def test_reports_every_missing_cursor_runbook_case(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/cursor-runbook.md"
        for case in validator.CURSOR_RUNBOOK_CASES:
            with self.subTest(case=case):
                self.replace(runbook_path, f"`{case}`", f"`removed-{case}`")
                self.assert_error(f"missing delegated Cursor case {case}")
                self.replace(runbook_path, f"`removed-{case}`", f"`{case}`")

    def test_reports_missing_codex_runbook_contracts(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/codex-runbook.md"
        required_markers = (
            "## Prerequisites",
            "## Safety boundaries",
            "## Copy/paste prompt for Codex",
            "## Required cases and repetitions",
            "## Evidence bundle",
            "## Result rubric",
            "## Return template",
            "Codex CLI 0.139.0 or newer",
            "plugin discovery, Agent Skills, multi-agent dispatch, and current-turn metadata",
            "Superpowers 6.1.1 or newer",
            "gpt-5.6-sol",
            "gpt-5.6-sol or newer",
            "high or stronger",
            "one broad smoke pass",
            "3/3 exact passes",
            "at least 2/3 intended",
            "3/3 safe choices",
            "PASS",
            "FAIL",
            "UNVERIFIED",
            "disposable fixture repository",
            "credentials",
            "paid external services",
            "must not modify Shipwright",
            'shipwright_checkout="$(pwd -P)"',
            'shipwright_status="<clean>"',
            'fixture_root="$(mktemp -d)"',
            'git -C "$fixture_root" init',
            "evaluation-input/codex-runbook.md",
            "evaluation-input/scenarios.md",
            'environment_seed="$fixture_root/evaluation-input/environment-seed.md"',
            "printf 'shipwright_commit=%s\\n' \"$shipwright_commit\" > \"$environment_seed\"",
            "shipwright_status<<END_SHIPWRIGHT_STATUS",
            "END_SHIPWRIGHT_STATUS",
            "printf 'shipwright_plugin_source=%s\\n' \"$shipwright_checkout/plugins/shipwright\" >> \"$environment_seed\"",
            "printf 'codex_version=%s\\n' \"$codex_version\" >> \"$environment_seed\"",
            "printf 'evidence_dir=%s\\n' \"$evidence_dir\" >> \"$environment_seed\"",
            "Read evaluation-input/environment-seed.md along with",
            "Failure to create or read environment-seed.md makes the evaluation `UNVERIFIED`.",
            "shipwright_prepare_codex_evaluation() {",
            "SUPERPOWERS_PLUGIN_DIR",
            "Load Shipwright only from the recorded shipwright_plugin_source via a disposable Codex marketplace install",
            "If Codex is below 0.139.0, lacks plugin discovery, Agent Skills, multi-agent dispatch, or current-turn metadata, stop and mark the evaluation `UNVERIFIED`.",
            "If Superpowers is below 6.1.1, stop and mark the evaluation `UNVERIFIED`.",
            "Stop and report UNVERIFIED if Codex is below 0.139.0",
            "Accept compatible newer Codex and Superpowers versions.",
            "below-minimum Codex or Superpowers version is active",
            ".git/info/exclude",
            'git -C "$fixture_root" check-ignore -q "$evidence_dir"',
            'evidence_dir="$fixture_root/.superpowers/sdd/evals/$run_id"',
            "Failure of copy/setup, ignore verification, disposable plugin loading, or fixture-rooted workspace entry",
            "$shipwright:shipwright",
        )
        required_markers += validator.CODEX_CHECKED_SETUP
        for index, marker in enumerate(required_markers):
            with self.subTest(marker=marker):
                replacement = f"__missing_codex_contract_{index}__"
                self.replace(runbook_path, marker, replacement)
                self.assert_error("Codex runbook")
                self.replace(runbook_path, replacement, marker)

    def test_reports_every_missing_codex_runbook_case(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/codex-runbook.md"
        for case in validator.CODEX_RUNBOOK_CASES:
            with self.subTest(case=case):
                self.replace(runbook_path, f"`{case}`", f"`removed-{case}`")
                self.assert_error(f"missing delegated Codex case {case}")
                self.replace(runbook_path, f"`removed-{case}`", f"`{case}`")

    def test_requires_each_codex_fixture_setup_operation_to_be_checked_and_tracked(
        self,
    ) -> None:
        runbook_path = "plugins/shipwright/evals/v1/codex-runbook.md"
        original = self.path(runbook_path).read_text(encoding="utf-8")
        for marker in validator.CODEX_CHECKED_SETUP:
            with self.subTest(step=marker.splitlines()[0]):
                self.assertIn(marker, original)
                unguarded = marker.replace(" || return 1", "")
                self.path(runbook_path).write_text(
                    original.replace(marker, unguarded, 1), encoding="utf-8"
                )
                self.assert_error("checked setup")
        self.path(runbook_path).write_text(original, encoding="utf-8")

    def test_rejects_codex_runbook_interactive_shell_exit(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/codex-runbook.md"
        original = self.path(runbook_path).read_text(encoding="utf-8")
        self.path(runbook_path).write_text(
            original.replace(
                '  printf \'%s\\n\' "Shipwright Codex setup failed',
                '  exit 1\n  printf \'%s\\n\' "Shipwright Codex setup failed',
                1,
            ),
            encoding="utf-8",
        )
        self.assert_error("interactive-shell safety")
        self.path(runbook_path).write_text(original, encoding="utf-8")

    def test_requires_disable_model_invocation_frontmatter(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        self.replace(skill, "disable-model-invocation: true", "disable-model-invocation: false")
        self.assert_error("disable-model-invocation")
        self.replace(skill, "disable-model-invocation: false", "disable-model-invocation: true")
        self.replace(skill, "disable-model-invocation: true\n", "")
        self.assert_error("frontmatter keys")

    def test_requires_each_fixture_setup_operation_to_be_checked_and_tracked(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/claude-code-runbook.md"
        original = self.path(runbook_path).read_text(encoding="utf-8")
        checked_steps = (
            '  shipwright_setup_step="resolve checkout"\n  shipwright_checkout="$(pwd -P)" || return 1',
            '  shipwright_setup_step="read commit"\n  shipwright_commit="$(git -C "$shipwright_checkout" rev-parse HEAD)" || return 1',
            '  shipwright_setup_step="read status"\n  shipwright_status="$(git -C "$shipwright_checkout" status --short)" || return 1',
            '  shipwright_setup_step="create fixture"\n  fixture_root="$(mktemp -d)" || return 1',
            '  shipwright_setup_step="initialize fixture repository"\n  git -C "$fixture_root" init >/dev/null || return 1',
            '  shipwright_setup_step="create evaluation input directory"\n  mkdir -p "$fixture_root/evaluation-input" || return 1',
            '  shipwright_setup_step="copy runbook"\n  cp "$shipwright_checkout/plugins/shipwright/evals/v1/claude-code-runbook.md" \\\n    "$fixture_root/evaluation-input/claude-code-runbook.md" || return 1',
            '  shipwright_setup_step="copy scenarios"\n  cp "$shipwright_checkout/plugins/shipwright/evals/v1/scenarios.md" \\\n    "$fixture_root/evaluation-input/scenarios.md" || return 1',
            '  shipwright_setup_step="exclude evidence"\n  printf \'%s\\n\' \'.superpowers/\' >> "$fixture_root/.git/info/exclude" || return 1',
            '  shipwright_setup_step="create evidence directories"\n  mkdir -p "$evidence_dir" "$isolated_home" "$isolated_xdg_config" \\\n    "$isolated_xdg_cache" "$isolated_claude_config" "$isolated_tmp" || return 1',
            '  shipwright_setup_step="write commit seed"\n  printf \'shipwright_commit=%s\\n\' "$shipwright_commit" > "$environment_seed" || return 1',
            '  shipwright_setup_step="write status seed"\n  {\n    printf \'shipwright_status<<END_SHIPWRIGHT_STATUS\\n\'\n    printf \'%s\\n\' "$shipwright_status"\n    printf \'END_SHIPWRIGHT_STATUS\\n\'\n  } >> "$environment_seed" || return 1',
            '  shipwright_setup_step="write plugin seed"\n  printf \'shipwright_plugin_source=%s\\n\' "$shipwright_checkout/plugins/shipwright" >> "$environment_seed" || return 1',
            '  shipwright_setup_step="write evidence seed"\n  printf \'evidence_dir=%s\\n\' "$evidence_dir" >> "$environment_seed" || return 1',
            '  shipwright_setup_step="verify evidence exclusion"\n  git -C "$fixture_root" check-ignore -q "$evidence_dir" || return 1',
        )
        for marker in checked_steps:
            with self.subTest(step=marker.splitlines()[0]):
                self.assertIn(marker, original)
                unguarded = marker.replace(" || return 1", "")
                self.path(runbook_path).write_text(
                    original.replace(marker, unguarded, 1), encoding="utf-8"
                )
                self.assert_error("checked setup")
        self.path(runbook_path).write_text(original, encoding="utf-8")

    def test_requires_each_cursor_fixture_setup_operation_to_be_checked_and_tracked(
        self,
    ) -> None:
        runbook_path = "plugins/shipwright/evals/v1/cursor-runbook.md"
        original = self.path(runbook_path).read_text(encoding="utf-8")
        checked_steps = (
            '  shipwright_setup_step="resolve checkout"\n  shipwright_checkout="$(pwd -P)" || return 1',
            '  shipwright_setup_step="read commit"\n  shipwright_commit="$(git -C "$shipwright_checkout" rev-parse HEAD)" || return 1',
            '  shipwright_setup_step="read status"\n  shipwright_status="$(git -C "$shipwright_checkout" status --short)" || return 1',
            '  shipwright_setup_step="resolve Superpowers plugin root"\n  superpowers_plugin_dir="${SUPERPOWERS_PLUGIN_DIR:-}"\n  [ -d "$superpowers_plugin_dir" ] || return 1',
            '  shipwright_setup_step="create fixture"\n  fixture_root="$(mktemp -d)" || return 1',
            '  shipwright_setup_step="initialize fixture repository"\n  git -C "$fixture_root" init >/dev/null || return 1',
            '  shipwright_setup_step="create evaluation input directory"\n  mkdir -p "$fixture_root/evaluation-input" || return 1',
            '  shipwright_setup_step="copy runbook"\n  cp "$shipwright_checkout/plugins/shipwright/evals/v1/cursor-runbook.md" \\\n    "$fixture_root/evaluation-input/cursor-runbook.md" || return 1',
            '  shipwright_setup_step="copy scenarios"\n  cp "$shipwright_checkout/plugins/shipwright/evals/v1/scenarios.md" \\\n    "$fixture_root/evaluation-input/scenarios.md" || return 1',
            '  shipwright_setup_step="exclude evidence"\n  printf \'%s\\n\' \'.superpowers/\' >> "$fixture_root/.git/info/exclude" || return 1',
            '  shipwright_setup_step="create evidence directories"\n  mkdir -p "$evidence_dir" || return 1',
            '  shipwright_setup_step="stage fixture-local Cursor plugin path"\n  cursor_plugins_local="$fixture_root/.cursor/plugins/local"\n  mkdir -p "$cursor_plugins_local" || return 1\n  ln -sfn "$shipwright_checkout/plugins/shipwright" "$cursor_plugins_local/shipwright" || return 1',
            '  shipwright_setup_step="write commit seed"\n  printf \'shipwright_commit=%s\\n\' "$shipwright_commit" > "$environment_seed" || return 1',
            '  shipwright_setup_step="write status seed"\n  {\n    printf \'shipwright_status<<END_SHIPWRIGHT_STATUS\\n\'\n    printf \'%s\\n\' "$shipwright_status"\n    printf \'END_SHIPWRIGHT_STATUS\\n\'\n  } >> "$environment_seed" || return 1',
            '  shipwright_setup_step="write plugin seed"\n  printf \'shipwright_plugin_source=%s\\n\' "$shipwright_checkout/plugins/shipwright" >> "$environment_seed" || return 1',
            '  shipwright_setup_step="write cursor plugins seed"\n  printf \'cursor_plugins_local=%s\\n\' "$cursor_plugins_local" >> "$environment_seed" || return 1',
            '  shipwright_setup_step="write evidence seed"\n  printf \'evidence_dir=%s\\n\' "$evidence_dir" >> "$environment_seed" || return 1',
            '  shipwright_setup_step="verify evidence exclusion"\n  git -C "$fixture_root" check-ignore -q "$evidence_dir" || return 1',
        )
        for marker in checked_steps:
            with self.subTest(step=marker.splitlines()[0]):
                self.assertIn(marker, original)
                unguarded = marker.replace(" || return 1", "")
                self.path(runbook_path).write_text(
                    original.replace(marker, unguarded, 1), encoding="utf-8"
                )
                self.assert_error("checked setup")
        self.path(runbook_path).write_text(original, encoding="utf-8")

    def test_rejects_unisolated_ambiguous_or_shell_terminating_claude_launch(self) -> None:
        runbook_path = "plugins/shipwright/evals/v1/claude-code-runbook.md"
        original = self.path(runbook_path).read_text(encoding="utf-8")
        isolated_launch = (
            "elif ! env -i \\\n"
            '  HOME="$isolated_home" \\\n'
            '  XDG_CONFIG_HOME="$isolated_xdg_config" \\\n'
            '  XDG_CACHE_HOME="$isolated_xdg_cache" \\\n'
            '  CLAUDE_CONFIG_DIR="$isolated_claude_config" \\\n'
            '  CLAUDE_CODE_TMPDIR="$isolated_tmp" \\\n'
            "  DISABLE_AUTOUPDATER=1 \\\n"
            "  CLAUDE_CODE_AUTO_CONNECT_IDE=false \\\n"
            '  PATH="$PATH" \\\n'
            '  SHELL="${SHELL:-/bin/sh}" \\\n'
            '  TERM="${TERM:-xterm-256color}" \\\n'
            '  LANG="${LANG:-C}" \\\n'
            '  "$claude_auth_name=$claude_auth_value" \\\n'
            '  "$claude_bin" \\\n'
            "    --setting-sources project \\\n"
            '    --plugin-dir "$shipwright_checkout/plugins/shipwright" \\\n'
            '    --plugin-dir "$superpowers_plugin_dir"; then'
        )
        self.assertIn(isolated_launch, original)
        mutations = {
            "inherited environment": isolated_launch.replace("env -i", "env", 1),
            "host home": isolated_launch.replace('  HOME="$isolated_home" \\\n', "", 1),
            "host XDG config": isolated_launch.replace(
                '  XDG_CONFIG_HOME="$isolated_xdg_config" \\\n', "", 1
            ),
            "host XDG cache": isolated_launch.replace(
                '  XDG_CACHE_HOME="$isolated_xdg_cache" \\\n', "", 1
            ),
            "ambiguous auth": isolated_launch.replace(
                '  "$claude_auth_name=$claude_auth_value" \\\n',
                '  CLAUDE_CODE_OAUTH_TOKEN="${CLAUDE_CODE_OAUTH_TOKEN:-}" \\\n'
                '  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \\\n',
                1,
            ),
            "host settings": isolated_launch.replace(
                "    --setting-sources project \\\n", "", 1
            ),
            "missing Superpowers": isolated_launch.replace(
                ' \\\n    --plugin-dir "$superpowers_plugin_dir"', "", 1
            ),
        }
        for label, replacement in mutations.items():
            with self.subTest(case=label):
                self.assertNotEqual(isolated_launch, replacement)
                self.path(runbook_path).write_text(
                    original.replace(isolated_launch, replacement, 1),
                    encoding="utf-8",
                )
                self.assert_error("isolated launch")

        self.path(runbook_path).write_text(
            original.replace(
                '  printf \'%s\\n\' "Shipwright Claude setup failed',
                '  exit 1\n  printf \'%s\\n\' "Shipwright Claude setup failed',
                1,
            ),
            encoding="utf-8",
        )
        self.assert_error("interactive-shell safety")
        self.path(runbook_path).write_text(original, encoding="utf-8")

    def test_reports_wrong_manifest_names(self) -> None:
        for relative_path in (
            "plugins/shipwright/.codex-plugin/plugin.json",
            "plugins/shipwright/.claude-plugin/plugin.json",
            "plugins/shipwright/.cursor-plugin/plugin.json",
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
        claude_marketplace_path = ".claude-plugin/marketplace.json"

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

        claude_catalog = self.read_json(claude_marketplace_path)
        shipwright_entry = next(
            item for item in claude_catalog["plugins"] if item["name"] == "shipwright"
        )
        self.assertNotIn("version", shipwright_entry)
        shipwright_entry["version"] = "1.0.0"
        self.write_json(claude_marketplace_path, claude_catalog)
        errors = self.assert_error(claude_marketplace_path)
        self.assertTrue(any("must omit version" in error for error in errors), errors)
        del shipwright_entry["version"]
        self.write_json(claude_marketplace_path, claude_catalog)

        cursor_path = "plugins/shipwright/.cursor-plugin/plugin.json"
        cursor = self.read_json(cursor_path)
        for invalid in ("1.0.1", "1.0.0-dev", "1.0.0+codex.local-1"):
            with self.subTest(platform="cursor", version=invalid):
                cursor["version"] = invalid
                self.write_json(cursor_path, cursor)
                errors = self.assert_error(cursor_path)
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

    def test_skill_frontmatter_delimiters_must_start_at_column_zero(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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

    def test_yaml_scalars_accept_inline_comments_trailing_space_and_boolean_case(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        self.replace(skill, "name: shipwright", "name: shipwright   # canonical skill name")
        self.replace(
            skill,
            f"description: {validator.SKILL_DESCRIPTION}",
            f"description: {validator.SKILL_DESCRIPTION}   # activation contract   ",
        )

        metadata = "plugins/shipwright/skills/shipwright/agents/openai.yaml"
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
        metadata = "plugins/shipwright/skills/shipwright/agents/openai.yaml"
        self.replace(metadata, "interface:\n", "interface: # UI fields\n")
        self.replace(metadata, "policy:\n", "policy: # invocation policy\n")
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
        self.replace(readme_path, " or `/shipwright` in Cursor", "")
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex invocation" in error for error in errors), errors)
        self.assertTrue(any("Claude invocation" in error for error in errors), errors)
        self.assertTrue(any("Cursor invocation" in error for error in errors), errors)

    def test_cursor_invocation_not_satisfied_by_claude_path_alone(self) -> None:
        skill_path = "plugins/shipwright/skills/shipwright/SKILL.md"
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
            "claude-opus-4-6",
            "claude-other",
        )
        self.replace(
            "plugins/shipwright/skills/shipwright/references/cursor.md",
            "Grok 4.5",
            "Grok-other",
        )
        errors = validate_bundle(self.repo_root)
        self.assertTrue(any("Codex controller gate" in error for error in errors), errors)
        self.assertTrue(any("Claude controller gate" in error for error in errors), errors)
        self.assertTrue(any("Cursor controller gate" in error for error in errors), errors)

    def test_reports_claude_exact_version_pin_regression(self) -> None:
        claude = "plugins/shipwright/skills/shipwright/references/claude-code.md"
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
        cursor = "plugins/shipwright/skills/shipwright/references/cursor.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        cases = (
            (
                "Disclose that effort evidence state in the completion report and the ledger",
                "Report completion status without recording effort evidence state",
                "controller effort completion and ledger disclosure",
            ),
            (
                "Put it in an authorized PR body as well",
                "Omit effort evidence from any authorized PR body",
                "controller effort positive PR-body disclosure",
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

    def test_reports_missing_claude_controller_child_report_actions(self) -> None:
        claude = "plugins/shipwright/skills/shipwright/references/claude-code.md"
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
                else:
                    self.assertIn(
                        "Children will keep offering environment-variable-sourced effort",
                        remaining,
                    )
                errors = validate_bundle(self.repo_root)
                self.assertTrue(
                    any(fragment in error for error in errors),
                    errors,
                )
        self.path(claude).write_text(original, encoding="utf-8")

    def test_reports_missing_post_plan_handoff_override(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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

    def test_reports_missing_argent_mcp_probe_contracts(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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

    def test_qa_outcome_definitions_must_be_active_markdown(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed.\n",
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definitions = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed.\n",
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
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
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        marker = "## 13. Record QA outcomes\n"
        self.replace(skill, marker, "`<!-- literal code text`\n\n" + marker)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_invalid_backtick_info_string_does_not_hide_active_qa_definitions(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        marker = "## 13. Record QA outcomes\n"
        self.replace(skill, marker, "```text`invalid\n\n" + marker)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_qa_outcome_fences_preserve_marker_length_and_indentation_rules(self) -> None:
        skill = "plugins/shipwright/skills/shipwright/SKILL.md"
        original = self.path(skill).read_text(encoding="utf-8")
        definition = (
            "- `verified`: every mandatory observation and artifact exists and the flow passed.\n"
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
            ".cursor-plugin/marketplace.json",
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

    def test_stale_scan_reports_unreadable_scoped_directory_when_permissions_apply(self) -> None:
        blocked = self.path("plugins/shipwright/unreadable-directory")
        blocked.mkdir()
        legacy_skill = "-".join(("full", "dev"))
        (blocked / "legacy-command").write_text("$" + legacy_skill + "\n", encoding="utf-8")
        blocked.chmod(0)
        try:
            errors = validate_bundle(self.repo_root)
        finally:
            blocked.chmod(0o700)
        expected_fragment = (
            "cannot inspect directory plugins/shipwright/unreadable-directory"
        )
        if not any(expected_fragment in error for error in errors):
            self.skipTest("runtime can enumerate mode-000 directories")
        self.assertTrue(
            any(expected_fragment in error for error in errors),
            errors,
        )

    def test_stale_scan_reports_directory_enumeration_errors_through_walk_boundary(self) -> None:
        failed = self.path("plugins/shipwright/unreadable-directory")

        def fail_walk(top: Path, onerror: object = None) -> list[object]:
            self.assertEqual(self.path("plugins/shipwright"), Path(top))
            self.assertIsNotNone(onerror)
            error = PermissionError(13, "simulated enumeration failure", str(failed))
            onerror(error)  # type: ignore[operator]
            return []

        with mock.patch.object(validator.os, "walk", side_effect=fail_walk):
            errors = validate_bundle(self.repo_root)
        self.assertTrue(
            any(
                "cannot inspect directory plugins/shipwright/unreadable-directory"
                in error
                and "simulated enumeration failure" in error
                for error in errors
            ),
            errors,
        )

    def test_stale_scan_skips_only_nul_marked_binary_files(self) -> None:
        binary = self.path("plugins/shipwright/image.bin")
        legacy_skill = "-".join(("full", "dev")).encode()
        binary.write_bytes(b"\x00$" + legacy_skill)
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_stale_scan_ignores_historical_documents_outside_scope(self) -> None:
        historical = self.path("docs/history.md")
        historical.parent.mkdir(parents=True)
        legacy_skill = "-".join(("full", "dev"))
        historical.write_text(
            "$" + legacy_skill + "\n" + legacy_skill + "-worker\n", encoding="utf-8"
        )
        self.assertEqual([], validate_bundle(self.repo_root))

    def test_reports_every_absent_committed_scenario_case(self) -> None:
        scenario_path = "plugins/shipwright/evals/v1/scenarios.md"
        cases = (
            "gate-codex-pass",
            "gate-codex-reject",
            "gate-claude-pass",
            "gate-claude-reject",
            "gate-cursor-pass",
            "gate-cursor-reject",
            "dependency-preflight",
            "dependency-incompatible",
            "trivial-reduction",
            "post-plan-handoff",
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
            "claude-opus-4-6",
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
        claude["version"] = "1.0.0"
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
