"""Structural checks on skill-maker's own SKILL.md body and references.

These guard the core-loop contract: shared steps appear once, every step ends on
a checkable "Done when" condition, the human-review rule and Gotchas live in
SKILL.md, the writable copy has one name (candidate), and every bundled script
and reference is still reached by a pointer in the body.
"""

import re
import unittest
from pathlib import Path

from scripts.skill_eval import _audit_skill

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
STEP_START = re.compile(r"^(?:\d+\.|-) ", re.MULTILINE)


def _section(heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", SKILL_TEXT, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def _steps(text: str):
    starts = [m.start() for m in STEP_START.finditer(text)]
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]


class TestCoreLoop(unittest.TestCase):
    def test_every_step_states_a_done_condition(self):
        steps = _steps(_section("Core loop"))
        self.assertGreaterEqual(len(steps), 6, "core loop has no bold-labelled steps")
        missing = [s.strip().splitlines()[0] for s in steps if "Done when" not in s]
        self.assertEqual(missing, [])

    def test_step_labels_are_not_repeated(self):
        steps = _steps(_section("Core loop"))
        unlabelled = [s.splitlines()[0] for s in steps if not re.match(r"(?:\d+\.|-) \*\*", s)]
        self.assertEqual(unlabelled, [], "every core-loop step opens with a bold label")
        labels = [re.match(r"(?:\d+\.|-) \*\*(.+?)\*\*", s).group(1).lower() for s in steps]
        self.assertEqual(len(labels), len(set(labels)), labels)

    def test_path_specific_steps_sit_outside_the_shared_steps(self):
        shared = re.search(r"### Shared steps\n(.*?)(?=^### )", _section("Core loop"), re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(shared, "core loop has no '### Shared steps' block")
        for label in ("**Inspect", "**Capture", "**Draft"):
            self.assertNotIn(label, shared.group(1))

    def test_shared_actions_are_stated_once(self):
        for phrase in ("--mode import", "smallest justified change"):
            self.assertEqual(SKILL_TEXT.count(phrase), 1, phrase)

    def test_human_review_rule_is_in_the_core_loop(self):
        self.assertRegex(_section("Core loop"), r"human\s+before\s+critiquing\s+or\s+rewriting")


class TestGotchas(unittest.TestCase):
    def test_gotchas_cover_module_invocation_and_em_dash(self):
        gotchas = _section("Gotchas")
        self.assertIn("python -m scripts.", gotchas)
        self.assertIn("U+2014", gotchas)


class TestOneTermForTheWritableCopy(unittest.TestCase):
    def test_candidate_is_the_only_name(self):
        stale = ("writable copy", "writable workspace", "workspace-owned")
        for path in [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]:
            text = path.read_text(encoding="utf-8").lower()
            for phrase in stale:
                self.assertNotIn(phrase, text, f"{path.name}: {phrase}")


class TestResourcePointers(unittest.TestCase):
    def test_no_trailing_bundled_resources_list(self):
        self.assertNotIn("## Bundled resources", SKILL_TEXT)

    def test_every_resource_is_reached_by_a_pointer(self):
        report = _audit_skill(SKILL_ROOT)
        unreached = [f["id"] for f in report["findings"]
                     if f["id"].startswith(("script.unlisted.", "resource.unaddressed."))]
        self.assertEqual(unreached, [])


if __name__ == "__main__":
    unittest.main()
