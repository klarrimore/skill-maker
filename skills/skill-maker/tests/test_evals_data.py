"""Data-integrity and fixture-behavior checks for skill-maker evals."""

import json
import unittest
from pathlib import Path

from evals.grade_artifacts import grade
from scripts.eval_models import EvalSchemaError, load_eval_suite, load_trigger_queries
from scripts.quick_validate import validate_skill

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = SKILL_ROOT / "evals"


class TestEvalsJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))

    def test_versioned_contract_loads(self):
        suite = load_eval_suite(SKILL_ROOT)
        self.assertEqual(suite.skill_name, "skill-maker")
        self.assertEqual(len(suite.evals), 6)
        self.assertEqual({case.split for case in suite.evals}, {"train", "held_out"})
        self.assertTrue(all(case.failure_modes for case in suite.evals))
        self.assertTrue(all(case.expectations for case in suite.evals))
        self.assertTrue(all(item.kind == "judge" for case in suite.evals for item in case.expectations))

    def test_ids_and_names_are_unique(self):
        ids = [item["id"] for item in self.data["evals"]]
        names = [item["name"] for item in self.data["evals"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(names), len(set(names)))

    def test_referenced_input_files_exist(self):
        for case in self.data["evals"]:
            for rel in case["files"]:
                with self.subTest(eval_id=case["id"], file=rel):
                    self.assertTrue((SKILL_ROOT / rel).exists())

    def test_unknown_expectation_kind_is_rejected(self):
        broken = json.loads(json.dumps(self.data))
        broken["evals"][0]["expectations"] = [{"kind": "unknown"}]
        path = EVALS_DIR / "evals.json"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(EvalSchemaError):
                load_eval_suite(SKILL_ROOT)
        finally:
            path.write_text(original, encoding="utf-8")


class TestTriggerQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queries = load_trigger_queries(SKILL_ROOT)

    def test_versioned_queries_have_both_splits_and_labels(self):
        self.assertEqual(len(self.queries), 20)
        self.assertEqual({item["split"] for item in self.queries}, {"train", "held_out"})
        for split in ("train", "held_out"):
            subset = [item for item in self.queries if item["split"] == split]
            self.assertTrue(any(item["should_trigger"] for item in subset))
            self.assertTrue(any(not item["should_trigger"] for item in subset))

    def test_queries_are_unique(self):
        texts = [item["query"] for item in self.queries]
        self.assertEqual(len(texts), len(set(texts)))


class TestJudgePrompts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = sorted((EVALS_DIR / "judges").glob("*.md"))

    def test_judge_prompt_files_exist(self):
        self.assertGreaterEqual(len(self.prompts), 1)

    def test_each_judge_prompt_has_required_components(self):
        for path in self.prompts:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for heading in ("## Task and Evaluation Criterion", "## Definitions", "## Examples", "## Structured Output Format"):
                    self.assertIn(heading, text)
                self.assertIn("PASS:", text)
                self.assertIn("FAIL:", text)
                self.assertIn("borderline", text.lower())
                self.assertIn('"critique"', text)
                self.assertIn('"result"', text)


class TestFixtureBehavior(unittest.TestCase):
    def test_broken_fixture_fails_validation_and_stays_broken(self):
        broken = EVALS_DIR / "files" / "broken-skill"
        valid, _ = validate_skill(broken)
        self.assertFalse(valid)
        text = (broken / "SKILL.md").read_text(encoding="utf-8")
        for token in ("name: Weekly_Log_Summary", "<error logs>", "author:", "version:"):
            self.assertIn(token, text)

    def test_broken_fixture_fails_grading(self):
        results = grade(EVALS_DIR / "files" / "broken-skill")
        self.assertTrue(any(not item["passed"] for item in results))

    def test_standup_and_skip_fixtures_are_valid(self):
        for name in ("standup-summary", "skip-evals-skill", "eval-suite-valid"):
            with self.subTest(name=name):
                valid, message = validate_skill(EVALS_DIR / "files" / name)
                self.assertTrue(valid, message)

    def test_standup_fixture_passes_grading(self):
        results = grade(EVALS_DIR / "files" / "standup-summary")
        self.assertTrue(all(item["passed"] for item in results), results)


class TestSkillItselfIsGradeable(unittest.TestCase):
    def test_skill_validates_and_passes_legacy_artifact_checks(self):
        valid, message = validate_skill(SKILL_ROOT)
        self.assertTrue(valid, message)
        results = grade(SKILL_ROOT)
        self.assertTrue(all(item["passed"] for item in results), results)


if __name__ == "__main__":
    unittest.main()
