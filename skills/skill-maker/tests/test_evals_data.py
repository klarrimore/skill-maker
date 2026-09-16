"""Data-integrity and fixture-behavior checks for the skill's own evals.

These guard the eval *inputs* (evals.json, trigger_queries.json, the fixtures)
the same way the smoke driver does, but as importable unit tests so a broken
eval set fails `unittest discover`, not just `smoke.sh`.
"""

import json
import unittest
from pathlib import Path

from evals.grade_artifacts import grade
from scripts.quick_validate import validate_skill

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = SKILL_ROOT / "evals"


class TestEvalsJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))

    def test_skill_name_matches_frontmatter(self):
        self.assertEqual(self.data["skill_name"], "skill-maker")
        self.assertEqual(self.data["skill_name"], SKILL_ROOT.name)

    def test_evals_is_nonempty_list(self):
        self.assertIsInstance(self.data["evals"], list)
        self.assertGreaterEqual(len(self.data["evals"]), 1)

    def test_eval_ids_are_unique_integers(self):
        ids = [e["id"] for e in self.data["evals"]]
        self.assertTrue(all(isinstance(i, int) for i in ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_eval_has_required_shape(self):
        for e in self.data["evals"]:
            with self.subTest(eval_id=e.get("id")):
                self.assertIsInstance(e["prompt"], str)
                self.assertTrue(e["prompt"].strip())
                self.assertIsInstance(e["expected_output"], str)
                self.assertTrue(e["expected_output"].strip())
                self.assertIsInstance(e["files"], list)
                self.assertIsInstance(e["expectations"], list)
                self.assertGreaterEqual(len(e["expectations"]), 1)
                for exp in e["expectations"]:
                    self.assertIsInstance(exp, str)
                    self.assertTrue(exp.strip())

    def test_referenced_input_files_exist(self):
        for e in self.data["evals"]:
            for rel in e["files"]:
                with self.subTest(eval_id=e["id"], file=rel):
                    self.assertTrue(
                        (SKILL_ROOT / rel).exists(),
                        f"eval {e['id']} references missing file {rel}",
                    )


class TestTriggerQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queries = json.loads(
            (EVALS_DIR / "trigger_queries.json").read_text(encoding="utf-8")
        )

    def test_is_flat_list_of_query_objects(self):
        self.assertIsInstance(self.queries, list)
        for q in self.queries:
            with self.subTest(query=q.get("query")):
                self.assertIsInstance(q["query"], str)
                self.assertTrue(q["query"].strip())
                self.assertIsInstance(q["should_trigger"], bool)
                # Exactly the two documented keys, nothing extra.
                self.assertEqual(set(q.keys()), {"query", "should_trigger"})

    def test_has_twenty_queries_split_ten_ten(self):
        self.assertEqual(len(self.queries), 20)
        positives = [q for q in self.queries if q["should_trigger"]]
        negatives = [q for q in self.queries if not q["should_trigger"]]
        self.assertEqual(len(positives), 10)
        self.assertEqual(len(negatives), 10)

    def test_queries_are_unique(self):
        texts = [q["query"] for q in self.queries]
        self.assertEqual(len(texts), len(set(texts)))


class TestFixtureBehavior(unittest.TestCase):
    """The fixtures must keep behaving as their evals assume."""

    def test_broken_fixture_fails_validation(self):
        broken = EVALS_DIR / "files" / "broken-skill"
        valid, _ = validate_skill(broken)
        self.assertFalse(valid)

    def test_broken_fixture_fails_grading(self):
        broken = EVALS_DIR / "files" / "broken-skill"
        results = grade(broken)
        self.assertTrue(any(not r["passed"] for r in results))

    def test_broken_fixture_still_carries_its_violations(self):
        # Mirrors smoke.sh check 2b: an eval run must not silently "fix" the
        # negative fixture in place and disarm eval id 2.
        text = (EVALS_DIR / "files" / "broken-skill" / "SKILL.md").read_text(encoding="utf-8")
        for token in ("name: Weekly_Log_Summary", "<error logs>", "author:", "version:"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_standup_fixture_is_valid(self):
        standup = EVALS_DIR / "files" / "standup-summary"
        valid, message = validate_skill(standup)
        self.assertTrue(valid, message)

    def test_standup_fixture_passes_grading(self):
        standup = EVALS_DIR / "files" / "standup-summary"
        results = grade(standup)
        self.assertTrue(all(r["passed"] for r in results), results)


class TestSkillItselfIsGradeable(unittest.TestCase):
    """Regression guard on the shipped skill: keep skill-maker self-valid."""

    def test_skill_validates(self):
        valid, message = validate_skill(SKILL_ROOT)
        self.assertTrue(valid, message)

    def test_skill_passes_all_grader_checks(self):
        results = grade(SKILL_ROOT)
        self.assertTrue(all(r["passed"] for r in results), results)


if __name__ == "__main__":
    unittest.main()
