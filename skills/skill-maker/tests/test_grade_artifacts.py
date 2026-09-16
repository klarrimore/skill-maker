import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from evals.grade_artifacts import grade, main

GOOD = "---\nname: my-skill\ndescription: Does a thing. Use it when needed.\n---\nBody.\n"


def _by_text(results, needle):
    """Return the single check whose text contains needle."""
    matches = [r for r in results if needle in r["text"]]
    assert len(matches) == 1, f"expected one check matching {needle!r}, got {len(matches)}"
    return matches[0]


class TestGrade(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _write_skill(self, dir_name, content):
        skill_dir = self.tmp_path / dir_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def test_missing_skill_md_short_circuits(self):
        skill_dir = self.tmp_path / "my-skill"
        skill_dir.mkdir()
        results = grade(skill_dir)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["passed"])

    def test_unparseable_frontmatter_stops_after_parse_check(self):
        skill_dir = self._write_skill("my-skill", "no frontmatter here\n")
        results = grade(skill_dir)
        self.assertTrue(results[0]["passed"])  # SKILL.md exists
        self.assertFalse(_by_text(results, "Frontmatter parses as YAML")["passed"])
        # It should stop before the name/description checks.
        self.assertEqual(len(results), 2)

    def test_all_checks_pass_for_valid_skill(self):
        skill_dir = self._write_skill("my-skill", GOOD)
        results = grade(skill_dir)
        self.assertTrue(all(r["passed"] for r in results), results)

    def test_flags_non_kebab_name(self):
        skill_dir = self._write_skill(
            "My_Skill", "---\nname: My_Skill\ndescription: Does a thing.\n---\nBody.\n"
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "kebab-case")["passed"])

    def test_accepts_unicode_name(self):
        skill_dir = self._write_skill(
            "café", "---\nname: café\ndescription: Does a thing.\n---\nBody.\n"
        )
        results = grade(skill_dir)
        self.assertTrue(_by_text(results, "kebab-case")["passed"])

    def test_flags_uppercase_unicode_name(self):
        skill_dir = self._write_skill(
            "Мой-Навык", "---\nname: Мой-Навык\ndescription: Does a thing.\n---\nBody.\n"
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "kebab-case")["passed"])

    def test_flags_name_directory_mismatch(self):
        skill_dir = self._write_skill(
            "other-dir", "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n"
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "matches the skill directory name")["passed"])

    def test_flags_description_over_limit(self):
        desc = "x" * 1025
        skill_dir = self._write_skill(
            "my-skill", f"---\nname: my-skill\ndescription: {desc}\n---\nBody.\n"
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "1024 characters or fewer")["passed"])

    def test_flags_angle_brackets_in_description(self):
        skill_dir = self._write_skill(
            "my-skill",
            "---\nname: my-skill\ndescription: Summarizes <error logs>.\n---\nBody.\n",
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "no angle brackets")["passed"])

    def test_flags_extra_frontmatter_field(self):
        skill_dir = self._write_skill(
            "my-skill",
            "---\nname: my-skill\ndescription: Does a thing.\nauthor: jo\n---\nBody.\n",
        )
        results = grade(skill_dir)
        check = _by_text(results, "only recognized fields")
        self.assertFalse(check["passed"])
        self.assertIn("author", check["evidence"])

    def test_flags_body_over_line_budget(self):
        body = "\n".join(f"line {i}" for i in range(600))
        skill_dir = self._write_skill(
            "my-skill", f"---\nname: my-skill\ndescription: Does a thing.\n---\n{body}\n"
        )
        results = grade(skill_dir)
        self.assertFalse(_by_text(results, "under the 500-line budget")["passed"])


class TestGraderMain(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _write_skill(self, dir_name, content):
        skill_dir = self.tmp_path / dir_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def _run_main(self, argv):
        buf = io.StringIO()
        with mock.patch("sys.argv", argv), redirect_stdout(buf):
            code = main()
        return code, buf.getvalue()

    def test_returns_zero_and_full_report_on_valid_skill(self):
        skill_dir = self._write_skill("my-skill", GOOD)
        out = self.tmp_path / "grading.json"
        code, stdout = self._run_main(
            ["grade_artifacts", str(skill_dir), "--out", str(out)]
        )
        self.assertEqual(code, 0)
        report = json.loads(out.read_text())
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["summary"]["pass_rate"], 1.0)
        self.assertEqual(report["summary"]["passed"], report["summary"]["total"])
        # stdout mirrors the written report.
        self.assertIn('"summary"', stdout)

    def test_returns_one_on_invalid_skill(self):
        skill_dir = self._write_skill(
            "other-dir", "---\nname: my-skill\ndescription: Summarizes <logs>.\n---\nBody.\n"
        )
        code, _ = self._run_main(["grade_artifacts", str(skill_dir)])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
