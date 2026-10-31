"""Data-integrity and fixture-behavior checks for skill-maker evals."""

import ast
import json
import re
import unittest
from pathlib import Path

from evals.grade_artifacts import grade
from scripts.eval_models import EvalSchemaError, load_eval_suite, load_judge_labels, load_trigger_queries
from scripts.quick_validate import validate_skill
from scripts.skill_eval import _audit_skill
from scripts.utils import parse_frontmatter

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = SKILL_ROOT / "evals"
JUDGE_SECTIONS = (
    "## Task and Evaluation Criterion",
    "## Inputs",
    "## Definitions",
    "## Examples",
    "## Structured Output Format",
)

JUDGE_ENVELOPE_FIELDS = {"protocol", "operation", "run_id", "rubric"}


def _judge_request_fields():
    """Return the keys of the judge request dict that scripts/skill_eval.py builds."""
    tree = ast.parse((SKILL_ROOT / "scripts" / "skill_eval.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "judge_request" for t in node.targets):
            return {key.value for key in node.value.keys}
    raise AssertionError("judge_request not found in scripts/skill_eval.py")


def _sections(text, marker):
    """Map each heading that starts with `marker` to the text up to the next heading of any level."""
    sections, title, lines = {}, None, []
    for line in text.splitlines():
        if line.startswith("#"):
            if title is not None:
                sections[title] = "\n".join(lines)
            title, lines = (line[len(marker):].strip() if line.startswith(marker) else None), []
        elif title is not None:
            lines.append(line)
    if title is not None:
        sections[title] = "\n".join(lines)
    return sections


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

    def test_audit_reports_no_judge_doing_a_deterministic_check(self):
        findings = _audit_skill(SKILL_ROOT)["findings"]
        objective = [item["id"] for item in findings if item["id"].startswith("eval.objective-judge.")]
        self.assertEqual(objective, [])

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
        self.assertEqual(len(self.queries), 24)
        self.assertEqual({item["split"] for item in self.queries}, {"train", "held_out"})
        for split in ("train", "held_out"):
            subset = [item for item in self.queries if item["split"] == split]
            self.assertTrue(any(item["should_trigger"] for item in subset))
            self.assertTrue(any(not item["should_trigger"] for item in subset))

    def test_post_activation_optimization_is_a_positive_in_both_splits(self):
        # A skill that fires but performs poorly or costs too much routes to
        # references/skill-optimization.md; both splits must exercise that path.
        expected = {
            "my code-review skill loads fine, but once it kicks in it burns way too many tokens and re-reads the same files over and over. can you make it leaner without losing quality?": "train",
            "the skill fires when it should, but the reports it produces are mediocre and it takes forever - figure out why the output is weak and fix the skill": "held_out",
        }
        by_text = {item["query"]: item for item in self.queries}
        for text, split in expected.items():
            with self.subTest(split=split):
                self.assertIn(text, by_text)
                self.assertTrue(by_text[text]["should_trigger"])
                self.assertEqual(by_text[text]["split"], split)

    def test_queries_are_unique(self):
        texts = [item["query"] for item in self.queries]
        self.assertEqual(len(texts), len(set(texts)))


def _table_rows(text, first_cell_prefix):
    """Yield the cells of each three-column Markdown table row whose first cell starts with the prefix."""
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0].startswith(first_cell_prefix):
            yield cells


def _catalogue_rows():
    """Map each FM id in failure-modes.md to its row, keyed by the table's header names."""
    text = (EVALS_DIR / "failure-modes.md").read_text(encoding="utf-8")
    rows, header = {}, None
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] == "ID":
            header = cells
        elif header and cells[0].startswith("FM-"):
            rows[cells[0]] = dict(zip(header, cells))
    return rows


def _caught_by():
    """Map each FM id in failure-modes.md to its 'Caught by' cell."""
    return {fm: row["Caught by"] for fm, row in _catalogue_rows().items()}


def _cited_evals(cell):
    """Eval ids a 'Caught by' cell cites, written as 'Eval N'."""
    return {int(n) for n in re.findall(r"\bEval (\d+)\b", cell)}


def _held_out_markers(case):
    """Strings that would show a judge example was lifted from a held-out case."""
    markers = set()
    for rel in case.files:
        parts = Path(rel).parts
        if len(parts) > 2 and parts[:2] == ("evals", "files"):
            markers.add(parts[2])
            front, _ = parse_frontmatter((SKILL_ROOT / rel).read_text(encoding="utf-8"))
            if isinstance(front, dict) and front.get("name"):
                markers.add(str(front["name"]))
    words = case.prompt.lower().split()
    markers.update(" ".join(words[i:i + 6]) for i in range(len(words) - 5))
    return markers


class TestJudgeMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_eval_suite(SKILL_ROOT)

    def test_each_judge_expectation_uses_a_rubric_for_one_of_its_failure_modes(self):
        caught_by = _caught_by()
        for case in self.suite.evals:
            for item in case.expectations:
                if item.kind != "judge":
                    continue
                rubric = item.data["rubric"].replace("evals/", "", 1)
                with self.subTest(eval_id=case.id, rubric=rubric):
                    covering = [fm for fm in case.failure_modes if rubric in caught_by.get(fm, "")]
                    self.assertTrue(covering, "no failure mode of eval {} lists {}".format(case.id, rubric))

    def test_no_judge_example_comes_from_a_held_out_case(self):
        rubrics = {path.name: path.read_text(encoding="utf-8").lower() for path in (EVALS_DIR / "judges").glob("*.md")}
        for case in self.suite.evals:
            if case.split != "held_out":
                continue
            for marker in _held_out_markers(case):
                for name, text in rubrics.items():
                    with self.subTest(eval_id=case.id, rubric=name, marker=marker):
                        self.assertFalse(marker.lower() in text, "held-out material in a judge example")


class TestFailureModeCatalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_eval_suite(SKILL_ROOT)
        cls.caught_by = _caught_by()

    def test_every_eval_failure_mode_has_a_catalogue_row(self):
        for case in self.suite.evals:
            for fm in case.failure_modes:
                with self.subTest(eval_id=case.id, fm=fm):
                    self.assertIn(fm, self.caught_by)

    def test_each_row_cites_exactly_the_evals_that_map_to_it(self):
        for fm, cell in self.caught_by.items():
            expected = {case.id for case in self.suite.evals if fm in case.failure_modes}
            with self.subTest(fm=fm):
                self.assertEqual(_cited_evals(cell), expected, cell)

    def test_every_named_mechanism_exists(self):
        roots = (EVALS_DIR, SKILL_ROOT, SKILL_ROOT / "scripts", SKILL_ROOT.parents[1] / "scripts")
        for fm, cell in self.caught_by.items():
            for token in re.findall(r"`([^`]+)`", cell):
                with self.subTest(fm=fm, token=token):
                    self.assertTrue(
                        any((root / name).is_file() for root in roots for name in (token, token + ".py")),
                        "{} names no existing file".format(token),
                    )

    def test_each_cited_eval_carries_the_expectations_its_clause_names(self):
        by_id = {case.id: case for case in self.suite.evals}
        for fm, cell in self.caught_by.items():
            self.assertNotIn("assertion", cell, "{}: evals.json has no assertion kind".format(fm))
            for clause in cell.split(";"):
                rubrics = set(re.findall(r"`(judges/[^`]+)`", clause))
                for eval_id in _cited_evals(clause):
                    expectations = by_id[eval_id].expectations
                    with self.subTest(fm=fm, eval_id=eval_id):
                        if "regex" in clause:
                            self.assertIn("regex", {item.kind for item in expectations})
                        for rubric in rubrics:
                            self.assertIn(
                                "evals/" + rubric,
                                {item.data.get("rubric") for item in expectations if item.kind == "judge"},
                            )

    def test_file_opens_with_the_catalogue_and_points_to_the_latest_run(self):
        text = (EVALS_DIR / "failure-modes.md").read_text(encoding="utf-8")
        lines = text.splitlines()
        first_table = next(i for i, line in enumerate(lines) if line.startswith("| ID |"))
        self.assertFalse(any(line.startswith("## ") for line in lines[:first_table]), "catalogue must lead the file")
        latest = sorted(path.name for path in (EVALS_DIR / "runs").iterdir() if path.is_dir())[-1]
        self.assertIn("`runs/{}/summary.md`".format(latest), "\n".join(lines[:first_table]))

    def test_status_column_is_single_valued(self):
        allowed = {"Observed", "Confirmed absent", "Not exercised", "Untested"}
        for fm, row in _catalogue_rows().items():
            with self.subTest(fm=fm):
                self.assertIn(row.get("Status"), allowed)
                self.assertNotIn("Gap", row["Caught by"])

    def test_no_pointer_to_a_numbered_step_or_missing_path(self):
        text = (EVALS_DIR / "failure-modes.md").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\bStep \d")
        for token in re.findall(r"`((?:runs|references|judges)/[^`]+)`", text):
            with self.subTest(token=token):
                self.assertTrue((EVALS_DIR / token).exists() or (SKILL_ROOT / token).exists(), token)

    def test_upkeep_section_ends_with_a_done_condition(self):
        text = (EVALS_DIR / "failure-modes.md").read_text(encoding="utf-8")
        section = _sections(text, "## ")["Keeping this current"].strip()
        last = section.split("\n\n")[-1].lstrip("- ")
        self.assertTrue(last.startswith("Done when"), last[:60])


class TestJudgeCalibrationStatus(unittest.TestCase):
    def test_failure_mode_catalogue_does_not_restate_calibration(self):
        text = (EVALS_DIR / "failure-modes.md").read_text(encoding="utf-8")
        self.assertFalse("calibrat" in text.lower(), "calibration status belongs only in evals/README.md")

    def test_readme_calibration_table_matches_held_out_labels(self):
        expected = {}
        for label in load_judge_labels(SKILL_ROOT)["labels"]:
            if label["split"] == "held_out":
                counts = expected.setdefault(label["rubric"], {"pass": 0, "fail": 0})
                counts[label["result"]] += 1
        readme = (EVALS_DIR / "README.md").read_text(encoding="utf-8")
        section = _sections(readme, "## ").get("Judge calibration")
        self.assertIsNotNone(section, "evals/README.md needs a '## Judge calibration' section")
        rows = {
            "evals/" + cells[0].strip("`"): {"pass": int(cells[1]), "fail": int(cells[2])}
            for cells in _table_rows(section, "`judges/")
        }
        rubrics = {"evals/judges/" + path.name for path in (EVALS_DIR / "judges").glob("*.md")}
        self.assertEqual(set(rows), rubrics)
        for rubric in rubrics:
            with self.subTest(rubric=rubric):
                self.assertEqual(rows[rubric], expected.get(rubric, {"pass": 0, "fail": 0}))


class TestJudgePrompts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = sorted((EVALS_DIR / "judges").glob("*.md"))

    def test_judge_prompt_files_exist(self):
        self.assertGreaterEqual(len(self.prompts), 1)

    def test_each_judge_prompt_has_the_shared_section_order(self):
        for path in self.prompts:
            headings = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]
            with self.subTest(path=path.name):
                self.assertEqual(headings, list(JUDGE_SECTIONS))

    def test_each_judge_prompt_has_critiqued_pass_and_fail_examples(self):
        for path in self.prompts:
            examples = _sections(path.read_text(encoding="utf-8"), "### ")
            with self.subTest(path=path.name):
                verdicts = {title.split(":", 1)[1].split()[0] for title in examples if ":" in title}
                self.assertTrue({"PASS", "FAIL"} <= verdicts, sorted(examples))
                for title, body in examples.items():
                    self.assertIn("Critique:", body, title)
                    self.assertRegex(body, r"\nResult: (Pass|Fail)\s*$", title)

    def test_each_judge_prompt_ends_with_critique_first_json(self):
        for path in self.prompts:
            text = path.read_text(encoding="utf-8")
            output = text.split("## Structured Output Format", 1)[1]
            with self.subTest(path=path.name):
                self.assertTrue(text.rstrip().endswith("```"), "trailing text after the output block")
                self.assertLess(output.index('"critique"'), output.index('"result"'))

    def test_each_judge_prompt_names_the_fields_the_evaluator_sends(self):
        fields = _judge_request_fields() - JUDGE_ENVELOPE_FIELDS
        self.assertTrue(fields)
        for path in self.prompts:
            inputs = _sections(path.read_text(encoding="utf-8"), "## ")["Inputs"]
            with self.subTest(path=path.name):
                for field in sorted(fields):
                    self.assertIn("`{}`".format(field), inputs)

    def test_judge_prompts_carry_no_maintainer_notes(self):
        for path in self.prompts:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(text, r"(?m)^(Status:|Feed the judge)")
                self.assertNotIn("calibrat", text.lower())


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

    def test_description_leads_with_the_action_and_covers_optimization(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        description = parse_frontmatter(text)[0]["description"]
        self.assertLessEqual(len(description), 512)
        self.assertTrue(description.startswith("Create"), description[:40])
        self.assertIn("token cost", description)


if __name__ == "__main__":
    unittest.main()
