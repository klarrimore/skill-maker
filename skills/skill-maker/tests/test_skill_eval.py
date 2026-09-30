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


if __name__ == "__main__":
    unittest.main()
