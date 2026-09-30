#!/usr/bin/env python3
"""Compatibility wrapper for the shipped deterministic artifact grader.

Use ``python -m scripts.skill_eval audit`` for the complete evaluation suite.
This dev-only module remains for existing self-eval commands and delegates all
artifact policy to ``scripts.skill_eval.grade_artifact``.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.skill_eval import grade_artifact  # noqa: E402


def grade(skill_dir):
    return grade_artifact(Path(skill_dir))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to the produced skill directory")
    parser.add_argument("--out", help="Write the report to this path as well as stdout")
    args = parser.parse_args()
    results = grade(Path(args.skill_dir).resolve())
    passed = sum(1 for item in results if item["passed"])
    report = {
        "expectations": results,
        "summary": {
            "passed": passed,
            "failed": len(results) - passed,
            "total": len(results),
            "pass_rate": round(passed / float(len(results)), 2) if results else 0.0,
        },
    }
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
