import io
import shutil
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from scripts.package_skill import package_skill

GOOD = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n"


def _package_quietly(skill_path, output_dir):
    """package_skill, with its progress prints swallowed to keep test output clean."""
    with redirect_stdout(io.StringIO()):
        return package_skill(skill_path, output_dir)


class TestPackageSkill(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)
        self.out_dir = self.tmp_path / "dist"

    def _make_skill(self, name="my-skill"):
        skill_dir = self.tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(GOOD)
        return skill_dir

    # --- error paths return None -----------------------------------------
    def test_returns_none_for_nonexistent_path(self):
        self.assertIsNone(_package_quietly(self.tmp_path / "nope", self.out_dir))

    def test_returns_none_when_path_is_a_file(self):
        f = self.tmp_path / "afile"
        f.write_text("x")
        self.assertIsNone(_package_quietly(f, self.out_dir))

    def test_returns_none_when_skill_md_missing(self):
        empty = self.tmp_path / "empty"
        empty.mkdir()
        self.assertIsNone(_package_quietly(empty, self.out_dir))

    def test_returns_none_when_validation_fails(self):
        skill_dir = self.tmp_path / "bad"
        skill_dir.mkdir()
        # Name is not kebab-case and mismatches the directory -> validation fails,
        # so packaging must refuse and produce no artifact.
        (skill_dir / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: x\n---\nBody.\n")
        self.assertIsNone(_package_quietly(skill_dir, self.out_dir))
        self.assertFalse(any(self.out_dir.glob("*.skill")) if self.out_dir.exists() else False)

    # --- happy path -------------------------------------------------------
    def test_packages_valid_skill(self):
        skill_dir = self._make_skill()
        result = _package_quietly(skill_dir, self.out_dir)
        self.assertIsNotNone(result)
        result = Path(result)
        self.assertTrue(result.exists())
        self.assertEqual(result.name, "my-skill.skill")
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        # Files are stored relative to the skill's parent, so paths are prefixed
        # with the skill folder name.
        self.assertIn("my-skill/SKILL.md", names)

    def test_creates_output_directory_if_absent(self):
        skill_dir = self._make_skill()
        self.assertFalse(self.out_dir.exists())
        _package_quietly(skill_dir, self.out_dir)
        self.assertTrue(self.out_dir.exists())

    def test_excludes_dev_artifacts_from_zip(self):
        skill_dir = self._make_skill()
        # Seed exactly the artifacts should_exclude is meant to drop.
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "guide.md").write_text("keep me")
        (skill_dir / "tests").mkdir()
        (skill_dir / "tests" / "test_x.py").write_text("drop me")
        (skill_dir / "evals").mkdir()
        (skill_dir / "evals" / "evals.json").write_text("{}")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "__pycache__").mkdir()
        (skill_dir / "scripts" / "__pycache__" / "x.pyc").write_text("bytecode")
        (skill_dir / "scripts" / "utils.pyc").write_text("bytecode")
        (skill_dir / ".pytest_cache").mkdir()
        (skill_dir / ".pytest_cache" / "cache").write_text("x")
        (skill_dir / ".DS_Store").write_text("x")

        result = Path(_package_quietly(skill_dir, self.out_dir))
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()

        self.assertIn("my-skill/SKILL.md", names)
        self.assertIn("my-skill/references/guide.md", names)
        for forbidden in ("tests/", "evals/", "__pycache__", ".pytest_cache", ".pyc", ".DS_Store"):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(forbidden in n for n in names),
                    f"{forbidden} leaked into the .skill: {names}",
                )

    def test_evals_excluded_only_at_root(self):
        # A directory literally named 'evals' nested below the root is content,
        # not the dev-only root evals/, so it must be packaged.
        skill_dir = self._make_skill()
        nested = skill_dir / "references" / "evals"
        nested.mkdir(parents=True)
        (nested / "note.md").write_text("keep")
        result = Path(_package_quietly(skill_dir, self.out_dir))
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        self.assertIn("my-skill/references/evals/note.md", names)


if __name__ == "__main__":
    unittest.main()
