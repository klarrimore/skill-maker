"""Checks on references/spec-reference.md and references/spec-provenance.md.

spec-provenance.md assigns every bundled-validator check one authority tier. The
tier table must name exactly the checks scripts/quick_validate.py performs: each
catalog entry below is a fixture that makes the validator emit that check.
"""

import re
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from scripts.quick_validate import inspect_skill
from scripts.utils import ROOT_EXCLUDE_DIRS
from tests.markdown_tables import table_header, table_rows

SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = SKILL_ROOT / "references" / "spec-reference.md"
PROVENANCE = SKILL_ROOT / "references" / "spec-provenance.md"
TIER_HEADING = "## Bundled validator checks by tier"

SPEC, PORTABILITY, HARDENING = "Spec constraint", "Portability rule", "Skill-maker hardening"


def _skill(frontmatter="name: s\ndescription: Does a thing.", body="Body.\n"):
    return f"---\n{frontmatter}\n---\n{body}"


@dataclass(frozen=True)
class Fixture:
    """A skill directory that makes the validator emit one check.

    `skill_md` is the SKILL.md content, or None to omit the file; `nested` adds a second
    SKILL.md in a subdirectory.
    """

    skill_md: str | None = _skill()
    dir_name: str = "s"
    nested: bool = False

    def build(self, parent):
        skill_dir = parent / self.dir_name
        skill_dir.mkdir()
        if self.skill_md is not None:
            (skill_dir / "SKILL.md").write_text(self.skill_md, encoding="utf-8")
        if self.nested:
            (skill_dir / "sub").mkdir()
            (skill_dir / "sub" / "SKILL.md").write_text(_skill(), encoding="utf-8")
        return skill_dir


# Row label -> (expected tier, fixture, emitted message fragment).
# Text the spec requires is a spec constraint, the six-field allow-list is a portability rule,
# and every check neither the spec nor skills-ref requires is skill-maker hardening.
CATALOG = {
    "`SKILL.md` exists": (SPEC, Fixture(skill_md=None), "SKILL.md not found"),
    "Frontmatter is a YAML mapping": (SPEC, Fixture("no frontmatter\n"), "frontmatter"),
    "Exactly one `SKILL.md`": (HARDENING, Fixture(nested=True), "SKILL.md files"),
    "`name` present and a non-empty string": (SPEC, Fixture(_skill("description: Does a thing.")), "Missing 'name'"),
    "`name` character set and hyphens": (SPEC, Fixture(_skill("name: S\ndescription: Does a thing.")), "kebab-case"),
    "`name` at most 64 characters": (SPEC, Fixture(_skill(f"name: {'s' * 65}\ndescription: Does a thing.")), "Maximum is 64"),
    "`name` matches the directory": (SPEC, Fixture(_skill("name: t\ndescription: Does a thing.")), "parent directory"),
    "`description` present and a non-empty string": (SPEC, Fixture(_skill("name: s")), "Missing 'description'"),
    "`description` at most 1024 characters": (SPEC, Fixture(_skill(f"name: s\ndescription: {'d' * 1025}")), "Maximum is 1024"),
    "`license` is a string": (SPEC, Fixture(_skill("name: s\ndescription: Does a thing.\nlicense: 1")), "License must be"),
    "`allowed-tools` is a string": (SPEC, Fixture(_skill("name: s\ndescription: Does a thing.\nallowed-tools: [a]")), "Allowed tools must be"),
    "`compatibility` a string of at most 500 characters": (SPEC, Fixture(_skill(f"name: s\ndescription: Does a thing.\ncompatibility: {'c' * 501}")), "Maximum is 500"),
    "`metadata` maps strings to strings": (SPEC, Fixture(_skill("name: s\ndescription: Does a thing.\nmetadata:\n  k: 1")), "Metadata values"),
    "Only the six spec fields": (PORTABILITY, Fixture(_skill("name: s\ndescription: Does a thing.\nmodel: x")), "Unexpected key"),
    "No angle brackets in `description`": (HARDENING, Fixture(_skill("name: s\ndescription: Does a <thing>.")), "angle brackets"),
    "No em dash in `SKILL.md`": (HARDENING, Fixture(_skill(body="A \u2014 B.\n")), "em dash"),
    "Body under 500 lines": (HARDENING, Fixture(_skill(body="x\n" * 600)), "lines (recommended"),
    "Body under about 5000 tokens": (HARDENING, Fixture(_skill(body="x" * 24000 + "\n")), "tokens (recommended"),
    "Body under 8000 bytes (Codex)": (HARDENING, Fixture(_skill(body="x" * 9000 + "\n")), "8000 bytes"),
    "`description` under 973 characters": (HARDENING, Fixture(_skill(f"name: s\ndescription: {'d' * 1000}")), "within 5%"),
    "ASCII-only `name`": (HARDENING, Fixture(_skill("name: caf\u00e9\ndescription: Does a thing."), dir_name="caf\u00e9"), "non-ASCII"),
}


def _tier_section():
    """Return the text of the provenance file's tier-table section."""
    text = PROVENANCE.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(TIER_HEADING)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


class TestTierTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.section = _tier_section()
        cls.tiers = {row["Check"]: row.get("Tier") for row in table_rows(cls.section)}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _messages_for_fixture(self, fixture):
        """Build the fixture and return every error and warning the validator emits for it."""
        skill_dir = fixture.build(self.tmp)
        report = inspect_skill(skill_dir)
        shutil.rmtree(skill_dir)
        return report["errors"] + report["warnings"]

    def test_every_catalog_fixture_triggers_its_check(self):
        for label, (_, fixture, fragment) in CATALOG.items():
            with self.subTest(label=label):
                self.assertTrue(any(fragment in m for m in self._messages_for_fixture(fixture)), label)

    def test_table_names_exactly_the_validator_checks(self):
        self.assertEqual(sorted(self.tiers), sorted(CATALOG))

    def test_table_states_tier_and_source_only(self):
        # Strict versus import severity is owned by spec-reference.md, not this table.
        self.assertEqual(table_header(self.section), ["Check", "Tier", "Source"])

    def test_each_check_has_one_expected_tier(self):
        for label, (tier, _, _) in CATALOG.items():
            with self.subTest(label=label):
                self.assertEqual(self.tiers.get(label), tier)


# Phrasing that describes a change from an earlier version instead of a present-tense fact.
EDIT_HISTORY = re.compile(
    r"\b(no longer|still holds|that part is unchanged|remains true|not unattested|"
    r"not an isolated invention|this is confirmed)\b",
    re.IGNORECASE,
)
# Backticked paths under the skill's own top-level directories.
PACKAGE_PATH = re.compile(r"`((?:references|scripts|assets|evals|tests)/[^`\s]+\.\w+)`")
# Directories package_skill.py leaves out of the packaged skill.
UNPACKAGED = tuple(name + "/" for name in sorted(ROOT_EXCLUDE_DIRS))


class TestSpecReferenceText(unittest.TestCase):
    FILES = (REFERENCE, PROVENANCE)

    def test_facts_are_stated_in_the_present_tense(self):
        for path in self.FILES:
            with self.subTest(file=path.name):
                text = " ".join(path.read_text(encoding="utf-8").split())
                self.assertEqual(EDIT_HISTORY.findall(text), [])

    def test_pointers_name_packaged_files(self):
        for path in self.FILES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("docs/research", text)
            self.assertNotIn("research investigation", text)
            for target in PACKAGE_PATH.findall(text):
                with self.subTest(file=path.name, target=target):
                    self.assertFalse(target.startswith(UNPACKAGED), target)
                    self.assertTrue((SKILL_ROOT / target).exists(), target)

    def test_no_em_dash(self):
        for path in self.FILES:
            with self.subTest(file=path.name):
                self.assertNotIn("\u2014", path.read_text(encoding="utf-8"))

    def test_extension_field_rule_is_stated_once(self):
        text = " ".join(REFERENCE.read_text(encoding="utf-8").split())
        self.assertEqual(len(re.findall(r"outside (?:these|the) six", text)), 1)
        self.assertEqual(len(re.findall(r"platform-lock in `compatibility`|state it in `compatibility`", text)), 1)
