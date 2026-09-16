#!/usr/bin/env python3
"""Code-check the objectively verifiable expectations for a produced skill.

Usage (from the skill root, skills/skill-maker/):
    python -m evals.grade_artifacts <skill-dir> [--out grading.json]

Emits a `grading.json`-shaped report (see references/schemas.md) covering only the
expectations that can be checked without judgment. Expectations that need a transcript
(the safety refusal, reporting the validator output to the user) are graded by hand.

Exit 0 when every code check passes, 1 otherwise. `evals/` is dev-only and excluded
from the packaged `.skill`.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.quick_validate import (  # noqa: E402
    ALLOWED_PROPERTIES,
    body_warnings,
    validate_skill,
)
from scripts.utils import parse_frontmatter  # noqa: E402

KEBAB = re.compile(r"^[a-z0-9-]+$")


def _check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def grade(skill_dir):
    results = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [_check(
            "Produces a skill directory containing a SKILL.md file",
            False,
            f"No SKILL.md at {skill_md}",
        )]
    results.append(_check(
        "Produces a skill directory containing a SKILL.md file",
        True,
        str(skill_md),
    ))

    try:
        frontmatter, _body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        results.append(_check("Frontmatter parses as YAML", False, str(exc)))
        return results
    results.append(_check("Frontmatter parses as YAML", True, "parse_frontmatter succeeded"))

    name = str(frontmatter.get("name", "")).strip()
    dir_name = skill_dir.name
    results.append(_check(
        "Frontmatter name is kebab-case with no leading/trailing/consecutive hyphen",
        bool(KEBAB.match(name)),
        f"name={name!r}",
    ))
    results.append(_check(
        "Frontmatter name matches the skill directory name",
        name == dir_name,
        f"name={name!r}, dir={dir_name!r}",
    ))

    description = str(frontmatter.get("description", "")).strip()
    results.append(_check(
        "Description is 1024 characters or fewer",
        len(description) <= 1024,
        f"length={len(description)}",
    ))
    results.append(_check(
        "Description contains no angle brackets",
        "<" not in description and ">" not in description,
        "clean" if "<" not in description and ">" not in description
        else f"contains angle brackets: {description!r}",
    ))

    extra = sorted(set(frontmatter.keys()) - ALLOWED_PROPERTIES)
    results.append(_check(
        "Frontmatter uses only recognized fields (no client-specific extension)",
        not extra,
        f"unexpected={extra}" if extra else "no extra fields",
    ))

    valid, message = validate_skill(skill_dir)
    results.append(_check(
        "Bundled validator reports the skill as valid",
        valid,
        message,
    ))

    over_budget = [w for w in body_warnings(skill_dir) if "lines" in w]
    results.append(_check(
        "SKILL.md body is under the 500-line budget",
        not over_budget,
        over_budget[0] if over_budget else "under budget",
    ))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to the produced skill directory")
    parser.add_argument("--out", help="Write the report to this path as well as stdout")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    results = grade(skill_dir)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    report = {
        "expectations": results,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 2) if total else 0.0,
        },
    }
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
