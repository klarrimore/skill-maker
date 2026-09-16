import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from scripts.install_skill import (
    EXIT_EXISTS,
    EXIT_USAGE,
    InstallError,
    install_skill,
    main,
)

GOOD = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n"


class TestInstallSkill(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)
        self.target = self.tmp_path / "skills"

    def _make_skill(self, name="my-skill", body=GOOD):
        skill_dir = self.tmp_path / "src" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(body)
        return skill_dir

    def test_installs_valid_skill(self):
        skill = self._make_skill()
        result = install_skill(skill, target=self.target)
        self.assertTrue(result["installed"])
        self.assertEqual(result["skill"], "my-skill")
        dest = Path(result["destination"])
        self.assertEqual(dest, (self.target / "my-skill").resolve())
        self.assertTrue((dest / "SKILL.md").exists())
        self.assertEqual(result["files"], 1)

    def test_creates_target_directory(self):
        skill = self._make_skill()
        self.assertFalse(self.target.exists())
        install_skill(skill, target=self.target)
        self.assertTrue(self.target.exists())

    def test_installs_to_default_target_when_none(self):
        skill = self._make_skill()
        with mock.patch("scripts.install_skill.DEFAULT_TARGET", self.target):
            result = install_skill(skill)
        dest = Path(result["destination"])
        self.assertTrue(dest.exists())
        self.assertEqual(dest.parent, self.target.resolve())

    def test_excludes_dev_artifacts(self):
        skill = self._make_skill()
        (skill / "tests").mkdir()
        (skill / "tests" / "test_x.py").write_text("drop")
        (skill / "evals").mkdir()
        (skill / "evals" / "evals.json").write_text("{}")
        (skill / "references").mkdir()
        (skill / "references" / "guide.md").write_text("keep")
        (skill / "scripts").mkdir()
        (skill / "scripts" / "__pycache__").mkdir()
        (skill / "scripts" / "__pycache__" / "x.pyc").write_text("drop")
        (skill / ".DS_Store").write_text("drop")

        install_skill(skill, target=self.target)
        installed = self.target / "my-skill"
        self.assertTrue((installed / "references" / "guide.md").exists())
        self.assertFalse((installed / "tests").exists())
        self.assertFalse((installed / "evals").exists())
        self.assertFalse((installed / "scripts" / "__pycache__").exists())
        self.assertFalse((installed / ".DS_Store").exists())

    def test_refuses_existing_without_force(self):
        skill = self._make_skill()
        install_skill(skill, target=self.target)
        with self.assertRaises(InstallError) as ctx:
            install_skill(skill, target=self.target)
        self.assertEqual(ctx.exception.code, EXIT_EXISTS)

    def test_force_replaces_existing(self):
        skill = self._make_skill()
        install_skill(skill, target=self.target)
        (skill / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Updated.\n---\nBody.\n"
        )
        install_skill(skill, target=self.target, force=True)
        self.assertIn(
            "Updated.", (self.target / "my-skill" / "SKILL.md").read_text()
        )

    def test_dry_run_writes_nothing(self):
        skill = self._make_skill()
        result = install_skill(skill, target=self.target, dry_run=True)
        self.assertFalse(result["installed"])
        self.assertFalse(self.target.exists())

    def test_refuses_invalid_skill(self):
        skill = self._make_skill(
            body="---\nname: Bad_Name\ndescription: x\n---\nBody.\n"
        )
        with self.assertRaises(InstallError) as ctx:
            install_skill(skill, target=self.target)
        self.assertEqual(ctx.exception.code, EXIT_USAGE)

    def test_refuses_missing_skill_md(self):
        skill = self.tmp_path / "empty"
        skill.mkdir()
        with self.assertRaises(InstallError) as ctx:
            install_skill(skill, target=self.target)
        self.assertEqual(ctx.exception.code, EXIT_USAGE)

    def test_installs_from_relative_dot_path(self):
        # Regression: `install_skill .` is the documented invocation, but the
        # unresolved path made walk_skill drop the skill-folder prefix and the
        # staged directory was never created.
        skill = self._make_skill()
        cwd = Path.cwd()
        os.chdir(skill)
        self.addCleanup(os.chdir, cwd)

        result = install_skill(".", target=self.target)

        self.assertTrue(result["installed"])
        self.assertTrue((self.target / "my-skill" / "SKILL.md").exists())

    def test_refuses_installing_onto_itself(self):
        skill = self._make_skill()
        # The target is the skill's own parent, so the destination is the source.
        with self.assertRaises(InstallError):
            install_skill(skill, target=skill.parent)


class TestInstallCli(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)
        self.target = self.tmp_path / "skills"

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        return ctx.exception.code, out.getvalue(), err.getvalue()

    def _make_skill(self, name="my-skill"):
        skill_dir = self.tmp_path / "src" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(GOOD)
        return skill_dir

    def test_success_exit_zero(self):
        skill = self._make_skill()
        code, out, _ = self._run([str(skill), "--target", str(self.target)])
        self.assertEqual(code, 0)
        self.assertIn("Installed", out)

    def test_json_output(self):
        skill = self._make_skill()
        code, out, _ = self._run(
            [str(skill), "--target", str(self.target), "--json"]
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["installed"])

    def test_existing_exit_two(self):
        skill = self._make_skill()
        self._run([str(skill), "--target", str(self.target)])
        code, _, err = self._run([str(skill), "--target", str(self.target)])
        self.assertEqual(code, EXIT_EXISTS)
        self.assertIn("--force", err)

    def test_dry_run_reports_without_writing(self):
        skill = self._make_skill()
        code, out, _ = self._run(
            [str(skill), "--target", str(self.target), "--dry-run"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Would install", out)
        self.assertFalse(self.target.exists())

    def test_bad_usage_exit_one(self):
        code, _, _ = self._run([])
        self.assertEqual(code, EXIT_USAGE)


if __name__ == "__main__":
    unittest.main()
