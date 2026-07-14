#!/usr/bin/env python3
"""Render assets/eval_review.html with real data (fills the three placeholders).

Usage:
    python3 .claude/skills/run-skill-maker/render_review.py [skill_dir] [out_html]

Defaults: skill_dir = skills/skill-maker (relative to cwd), out_html = /tmp/eval_review_rendered.html
Reads name/description from the skill's SKILL.md frontmatter and EVAL_DATA from
evals/trigger_queries.json. Exits 1 if any placeholder is left unfilled.
"""

import json
import sys
from pathlib import Path


def main():
    skill_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "skills/skill-maker").resolve()
    out_html = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/eval_review_rendered.html")

    sys.path.insert(0, str(skill_dir))
    from scripts.utils import parse_frontmatter

    frontmatter, _body = parse_frontmatter((skill_dir / "SKILL.md").read_text())
    eval_data = (skill_dir / "evals" / "trigger_queries.json").read_text().strip()

    html = (skill_dir / "assets" / "eval_review.html").read_text()
    html = html.replace("__SKILL_NAME_PLACEHOLDER__", frontmatter["name"])
    html = html.replace("__SKILL_DESCRIPTION_PLACEHOLDER__", frontmatter["description"])
    html = html.replace("__EVAL_DATA_PLACEHOLDER__", eval_data)

    if "PLACEHOLDER" in html:
        print("ERROR: unfilled placeholder remains in output", file=sys.stderr)
        sys.exit(1)

    out_html.write_text(html)
    queries = json.loads(eval_data)
    print(f"Rendered {out_html} ({frontmatter['name']}, {len(queries)} trigger queries)")


if __name__ == "__main__":
    main()
