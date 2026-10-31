import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.eval_adapter import CommandAdapter
from scripts.eval_models import load_eval_suite
from scripts.skill_eval import (
    ConfigurationError,
    _audit_skill,
    _score,
    benchmark_records,
    benchmark_skill,
    execute_cases,
    execute_triggers,
    improve_skill,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "files" / "eval-suite-valid"
ADAPTER = ROOT / "tests" / "fixtures" / "fake_eval_adapter.py"


class TestSkillEvalIntegration(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.workspace, ignore_errors=True)
        self.adapter = CommandAdapter([sys.executable, str(ADAPTER)])

    def test_audit_is_offline_and_classifies_findings(self):
        report = _audit_skill(FIXTURE)
        self.assertTrue(report["passed"])
        self.assertTrue(any(item["category"] == "advisory" for item in report["findings"]))

    def test_run_grades_both_configurations(self):
        suite = load_eval_suite(FIXTURE)
        rows = execute_cases(FIXTURE, suite, self.workspace, self.adapter, 1, list(suite.evals))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["configuration"] for row in rows}, {"with_skill", "without_skill"})
        self.assertEqual(sum(row["status"] == "passed" for row in rows), 1)

    def test_benchmark_rejects_partial_pairs(self):
        with self.assertRaises(ConfigurationError):
            benchmark_records([{"protocol": "skill-eval/v1", "eval_id": 1, "run_number": 1, "configuration": "with_skill", "summary": {"pass_rate": 1}, "metrics": {}}], FIXTURE, self.workspace)

    def test_benchmark_writes_json_and_markdown(self):
        suite = load_eval_suite(FIXTURE)
        execute_cases(FIXTURE, suite, self.workspace, self.adapter, 1, list(suite.evals))
        report = benchmark_skill(FIXTURE, self.workspace)
        self.assertGreater(report["deltas"]["pass_rate"], 0)
        self.assertTrue((self.workspace / "benchmark.json").exists())
        self.assertTrue((self.workspace / "benchmark.md").exists())

    def test_benchmark_run_selector_ignores_later_repetitions(self):
        suite = load_eval_suite(FIXTURE)
        execute_cases(FIXTURE, suite, self.workspace, self.adapter, 2, list(suite.evals))
        report = benchmark_skill(FIXTURE, self.workspace, runs=1)
        self.assertEqual(report["metadata"]["runs_per_configuration"], 1)
    def test_benchmark_rejects_missing_selected_eval(self):
        suite = load_eval_suite(FIXTURE)
        execute_cases(FIXTURE, suite, self.workspace, self.adapter, 1, [suite.evals[0]])
        with self.assertRaises(ConfigurationError):
            benchmark_skill(FIXTURE, self.workspace)

    def test_benchmark_flags_expectations_that_pass_in_both_configurations(self):
        rows = []
        for configuration in ("with_skill", "without_skill"):
            rows.append({
                "protocol": "skill-eval/v1",
                "eval_id": 1,
                "eval_name": "train-report",
                "split": "train",
                "run_number": 1,
                "configuration": configuration,
                "status": "passed",
                "expectations": [{"kind": "text_contains", "text": "same", "passed": True}],
                "summary": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1},
                "metrics": {"duration_ms": 1, "total_tokens": 1, "tool_calls": 0},
                "adapter_error": None,
            })
        report = benchmark_records(rows, FIXTURE, self.workspace)
        self.assertTrue(any(item["code"] == "non_discriminating_expectation" for item in report["diagnostics"]))

    def test_unavailable_metrics_remain_unavailable_for_selection(self):
        score = _score([{
            "configuration": "with_skill",
            "split": "held_out",
            "expectations": [{"kind": "text_contains", "passed": True}],
            "metrics": {"duration_ms": None, "total_tokens": None},
        }], "held_out")
        self.assertEqual(score, (1.0, None, None, None))

    def test_command_expectation_is_denied_and_logged(self):
        fixture = self.workspace / "command-skill"
        shutil.copytree(str(FIXTURE), str(fixture))
        data = json.loads((fixture / "evals" / "evals.json").read_text(encoding="utf-8"))
        data["evals"][0]["expectations"].append({
            "kind": "command",
            "argv": [sys.executable, "-c", "raise SystemExit(0)"],
        })
        (fixture / "evals" / "evals.json").write_text(json.dumps(data), encoding="utf-8")
        suite = load_eval_suite(fixture)
        rows = execute_cases(fixture, suite, self.workspace, self.adapter, 1, [suite.evals[0]])
        self.assertTrue(any(not item["passed"] and item["kind"] == "command" for row in rows for item in row["expectations"]))
        audit = (self.workspace / "audit.jsonl").read_text(encoding="utf-8")
        self.assertIn('"decision": "deny"', audit)

    def test_trigger_adapter_errors_fail_negative_queries_too(self):
        code = "import json; print(json.dumps({'protocol':'skill-eval/v1','status':'error','error':'adapter down'}))"
        report = execute_triggers(
            FIXTURE,
            self.workspace / "trigger-errors",
            CommandAdapter([sys.executable, "-c", code]),
            3,
        )
        self.assertTrue(all(not item["passed"] for item in report["runs"]))
        self.assertTrue(all(item["adapter_error"] for item in report["runs"]))

    def test_trigger_requests_hide_labels(self):
        report = execute_triggers(FIXTURE, self.workspace / "trigger-success", self.adapter, 3)
        self.assertTrue(all(item["adapter_error"] is None for item in report["runs"]))
        self.assertTrue(all(item["passed"] for item in report["runs"]))

    def test_improve_promotes_held_out_winner_without_touching_source(self):
        before = {path.relative_to(FIXTURE): path.read_bytes() for path in FIXTURE.rglob("*") if path.is_file()}
        history = improve_skill(FIXTURE, self.workspace, self.adapter, 1, 2)
        self.assertEqual(history["current_best"], "v1")
        best = Path(history["best_skill"])
        self.assertTrue((best / "SKILL.md").exists())
        self.assertEqual(history["iterations"][1]["grading_result"], "won")
        after = {path.relative_to(FIXTURE): path.read_bytes() for path in FIXTURE.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(json.loads((self.workspace / "history.json").read_text())["current_best"], "v1")
        revision_request = json.loads((self.workspace / "runs" / "v1-revise" / "request.json").read_text(encoding="utf-8"))
        self.assertNotIn("held-out", json.dumps(revision_request))
        self.assertFalse((self.workspace / "iterations" / "v1" / "revision" / "source" / "evals").exists())
        # Sanitized paths: stored request must use $ISOLATED placeholders.
        self.assertEqual(revision_request["skill_path"], "$ISOLATED/source/eval-suite-valid")
        self.assertEqual(revision_request["candidate_path"], "$ISOLATED/candidate/eval-suite-valid")
        self.assertEqual(revision_request["output_dir"], "$ISOLATED/output")
        # No persistent revision source survives in the workspace.
        self.assertFalse((self.workspace / "iterations" / "v1" / "revision" / "source").exists())

    def test_improve_refuses_staging_inside_workspace(self):
        """When temp directory resolves inside the workspace, improve must fail closed."""
        from unittest import mock
        # Force TemporaryDirectory to create inside the workspace.
        inner = self.workspace / "staging"
        inner.mkdir()
        with mock.patch("tempfile.mkdtemp", return_value=str(inner)):
            with self.assertRaises(ConfigurationError) as ctx:
                improve_skill(FIXTURE, self.workspace, self.adapter, 1, 1)
            self.assertIn("inside the workspace", str(ctx.exception))
        shutil.rmtree(str(inner), ignore_errors=True)

    def test_improve_refuses_symlinked_staging_into_workspace(self):
        """A symlink-to-workspace as TMPDIR must also fail after resolve()."""
        from unittest import mock
        # Create a directory outside the workspace, then symlink workspace
        # content into it so a lexical child "looks outside" but resolves inside.
        outside = Path(tempfile.mkdtemp())
        link = outside / "wslink"
        link.symlink_to(self.workspace.resolve())
        with mock.patch("tempfile.tempdir", str(link)):
            with self.assertRaises(ConfigurationError) as ctx:
                improve_skill(FIXTURE, self.workspace, self.adapter, 1, 1)
            self.assertIn("inside the workspace", str(ctx.exception))
        shutil.rmtree(str(outside), ignore_errors=True)


class TestAuditPortableResources(unittest.TestCase):
    """Integration tests for portable-resource audit warnings in _audit_skill."""

    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _make_skill(self, name="test-skill", body="---\nname: test-skill\ndescription: Test.\n---\nDo things.\n", extra_files=None):
        skill_dir = self.tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(body)
        if extra_files:
            for path, content in extra_files.items():
                full = skill_dir / path
                full.parent.mkdir(parents=True, exist_ok=True)
                full.write_text(content)
        return skill_dir

    def test_clean_skill_no_resource_warnings(self):
        """A skill with all resources/scripts named in the body gets no resource findings."""
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Use scripts/run.py for processing.\n"
            "Read references/guide.md for setup.\n"
            "Read assets/logo.png for branding.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "scripts/run.py": "print('hello')",
            "scripts/__init__.py": "",
            "references/guide.md": "# Guide",
            "assets/logo.png": "meta",
            "references/deep/topic.md": "# Topic",
        })
        report = _audit_skill(skill_dir)
        # Should have no script.unlisted or resource.unaddressed findings,
        # but resource.reference-depth for the nested file.
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertNotIn("script.unlisted.scripts/run.py", finding_ids)
        self.assertNotIn("resource.unaddressed.references/guide.md", finding_ids)
        self.assertNotIn("resource.unaddressed.assets/logo.png", finding_ids)
        # The deep reference stays as an advisory and gets no unaddressed warning.
        self.assertIn("resource.reference-depth.references/deep/topic.md", finding_ids)
        self.assertNotIn("resource.unaddressed.references/deep/topic.md", finding_ids)

    def test_nested_asset_gets_no_direct_resource_warning(self):
        """A file under assets/subdir/ should not get a resource.unaddressed finding."""
        body = "---\nname: test-skill\ndescription: Test.\n---\nMain work.\n"
        skill_dir = self._make_skill(body=body, extra_files={
            "assets/deep/icon.png": "meta",
        })
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertNotIn("resource.unaddressed.assets/deep/icon.png", finding_ids)
        self.assertNotIn("resource.reference-depth.assets/deep/icon.png", finding_ids)

    def test_unlisted_and_unaddressed_produce_findings(self):
        """A skill with unlisted scripts and unaddressed/nested resources gets warnings."""
        body = (
            "---\nname: test-skill\ndescription: Test.\nallowed-tools: Read\n---\n"
            "Do the main work.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "scripts/run.py": "print('run')",
            "scripts/helper.py": "print('helper')",
            "references/guide.md": "# Guide",
            "references/deep/topic.md": "# Deep topic",
            "assets/icon.png": "meta",
        })
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertIn("skill.allowed-tools", finding_ids)
        self.assertIn("script.unlisted.scripts/run.py", finding_ids)
        self.assertIn("script.unlisted.scripts/helper.py", finding_ids)
        self.assertIn("resource.unaddressed.references/guide.md", finding_ids)
        self.assertIn("resource.unaddressed.assets/icon.png", finding_ids)
        self.assertIn("resource.reference-depth.references/deep/topic.md", finding_ids)

    def test_adding_body_pointers_clears_resource_warnings(self):
        """After adding explicit pointers to SKILL.md, resource/script warnings disappear."""
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Use scripts/run.py for processing.\n"
            "Read references/guide.md for setup.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "scripts/run.py": "print('run')",
            "references/guide.md": "# Guide",
        })
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertNotIn("script.unlisted.scripts/run.py", finding_ids)
        self.assertNotIn("resource.unaddressed.references/guide.md", finding_ids)

    def test_allowed_tools_warns_regardless_of_value(self):
        """allowed-tools warns even when empty string, so the check is presence not truthiness."""
        body = "---\nname: test-skill\ndescription: Test.\nallowed-tools: ''\n---\nBody.\n"
        skill_dir = self._make_skill(body=body)
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertIn("skill.allowed-tools", finding_ids)

    def test_same_basename_in_assets_does_not_mask_unlisted_script(self):
        """A file assets/run.py must not suppress the unlisted-script warning for scripts/run.py."""
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Read assets/run.py for the runner.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "scripts/run.py": "print('run')",
            "assets/run.py": "# runner reference",
        })
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        self.assertIn("script.unlisted.scripts/run.py", finding_ids)
        self.assertNotIn("script.unlisted.assets/run.py", finding_ids)

    def test_same_basename_in_assets_does_not_mask_unaddressed_resource(self):
        """A file assets/guide.md must not suppress the unaddressed warning for references/guide.md."""
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Read assets/guide.md for the guide.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "references/guide.md": "# Guide",
            "assets/guide.md": "# Asset guide",
        })
        report = _audit_skill(skill_dir)
        finding_ids = {f["id"] for f in report["findings"]}
        # references/guide.md must still be flagged even though assets/guide.md is named.
        self.assertIn("resource.unaddressed.references/guide.md", finding_ids)
        self.assertNotIn("resource.unaddressed.assets/guide.md", finding_ids)


class TestAuditDeadPointersAndToc(unittest.TestCase):
    """Audit warnings for dead skill-relative pointers and long references without a TOC."""

    setUp = TestAuditPortableResources.setUp
    _make_skill = TestAuditPortableResources._make_skill

    def _findings(self, skill_dir, prefix):
        return [f for f in _audit_skill(skill_dir)["findings"] if f["id"].startswith(prefix)]

    def test_dead_pointer_in_body_is_flagged(self):
        body = "---\nname: test-skill\ndescription: Test.\n---\nRun `scripts/missing.py` first.\n"
        skill_dir = self._make_skill(body=body)
        found = self._findings(skill_dir, "resource.dead-pointer.")
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding["id"], "resource.dead-pointer.SKILL.md:scripts/missing.py")
        self.assertEqual(finding["severity"], "warning")
        self.assertEqual(finding["status"], "open")
        self.assertEqual(finding["path"], "SKILL.md")
        self.assertIn("scripts/missing.py", finding["evidence"])
        self.assertIn("line 5", finding["evidence"])
        self.assertTrue(finding["fix"])

    def test_dead_pointer_in_reference_is_flagged(self):
        body = "---\nname: test-skill\ndescription: Test.\n---\nRead references/guide.md.\n"
        skill_dir = self._make_skill(body=body, extra_files={
            "references/guide.md": "# Guide\n\nRender with `scripts/render.py`.\n",
        })
        ids = {f["id"] for f in self._findings(skill_dir, "resource.dead-pointer.")}
        self.assertEqual(ids, {"resource.dead-pointer.references/guide.md:scripts/render.py"})

    def test_existing_paths_and_examples_are_not_flagged(self):
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Run `scripts/run.py`, then read references/guide.md.\n"
            "Name the full path (e.g. `scripts/example.py`).\n"
            "For example, \"Read references/api-errors.md if the call fails\".\n"
            "The repo copy lives at skills/test-skill/scripts/elsewhere.py.\n"
        )
        skill_dir = self._make_skill(body=body, extra_files={
            "scripts/run.py": "print('run')",
            "references/guide.md": "# Guide\n",
        })
        self.assertEqual(self._findings(skill_dir, "resource.dead-pointer."), [])

    def test_example_marker_wrapped_onto_previous_line_is_not_flagged(self):
        body = (
            "---\nname: test-skill\ndescription: Test.\n---\n"
            "Tell the agent when to read each file (for\n"
            "example, \"Read references/api-errors.md if the call fails\").\n"
        )
        skill_dir = self._make_skill(body=body)
        self.assertEqual(self._findings(skill_dir, "resource.dead-pointer."), [])

    def _long_reference(self, header, lines=320):
        return header + "".join("line {}\n".format(i) for i in range(lines))

    def test_long_reference_without_toc_is_flagged(self):
        body = "---\nname: test-skill\ndescription: Test.\n---\nRead references/big.md.\n"
        skill_dir = self._make_skill(body=body, extra_files={
            "references/big.md": self._long_reference("# Big\n\n## First section\n"),
        })
        found = self._findings(skill_dir, "resource.missing-toc.")
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding["id"], "resource.missing-toc.references/big.md")
        self.assertEqual(finding["severity"], "warning")
        self.assertEqual(finding["path"], "references/big.md")
        self.assertIn("323 lines", finding["evidence"])
        self.assertTrue(finding["fix"])

    def test_long_reference_with_toc_and_short_reference_are_not_flagged(self):
        body = "---\nname: test-skill\ndescription: Test.\n---\nRead references/big.md and references/small.md.\n"
        skill_dir = self._make_skill(body=body, extra_files={
            "references/big.md": self._long_reference("# Big\n\n## Contents\n\n- [First](#first)\n"),
            "references/small.md": self._long_reference("# Small\n", lines=250),
        })
        self.assertEqual(self._findings(skill_dir, "resource.missing-toc."), [])


if __name__ == "__main__":
    unittest.main()
