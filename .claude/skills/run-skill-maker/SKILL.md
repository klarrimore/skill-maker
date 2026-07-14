---
name: run-skill-maker
description: Run, test, validate, package, or screenshot the skill-maker project. Use when asked to run the validator or packager, run the test suite, smoke-test the repo, render or screenshot the eval review UI, or confirm the scripts still work after a change.
---

# Run skill-maker

skill-maker is not a server or GUI app — its runnable surfaces are two Python CLI
scripts (`quick_validate`, `package_skill`), a pytest suite, and one static HTML
asset (`assets/eval_review.html`, an eval-review UI with placeholder tokens).
All paths below are relative to the **repo root**.

## Run (agent path) — the smoke driver

One command exercises every surface and exits non-zero on the first failure:

```bash
bash .claude/skills/run-skill-maker/smoke.sh
```

Checks: validator passes on the skill, rejects the broken fixture, pytest passes,
the internal functions import and run directly, packaging produces a `.skill` zip
free of dev artifacts, the eval-review UI renders from real data, and (if
`google-chrome` exists) a screenshot lands at `/tmp/eval_review_screenshot.png` —
open that file to see the UI.

To render/screenshot the review UI alone:

```bash
python3 .claude/skills/run-skill-maker/render_review.py   # -> /tmp/eval_review_rendered.html
google-chrome --headless --disable-gpu --window-size=1200,1600 \
  --screenshot=/tmp/eval_review_screenshot.png file:///tmp/eval_review_rendered.html
```

## Run (individual surfaces)

All must run **from `skills/skill-maker/`, as modules** (see Gotchas):

```bash
cd skills/skill-maker
python3 -m scripts.quick_validate .                    # validate (exit 0 = valid)
python3 -m scripts.quick_validate evals/files/broken-skill  # expect exit 1
python3 -m pytest tests/ -q                            # unit tests
python3 -m scripts.package_skill . ../../dist          # validate + zip -> dist/skill-maker.skill
```

## Direct invocation

Most changes here touch the internals, not the CLI. To exercise a changed function
without the full script, import and call it (still from `skills/skill-maker/`):

```bash
cd skills/skill-maker
python3 -c "
from scripts.utils import parse_frontmatter
fm, body = parse_frontmatter(open('SKILL.md').read())
print(fm['name'], '| body lines:', body.count('\n'))
"
python3 -c "
from scripts.quick_validate import validate_skill, body_warnings
print(validate_skill('.'))          # (True, 'Skill is valid!')
print(body_warnings('.'))           # [] when under budget
"
python3 -c "
from pathlib import Path
from scripts.package_skill import should_exclude
print(should_exclude(Path('my-skill/tests/x.py')))  # True
"
```

## Prerequisites

Python 3.8+ with PyYAML (runtime) and pytest (dev). On this machine both were
already present; otherwise:

```bash
pip install -r skills/skill-maker/requirements.txt   # PyYAML
pip install -r requirements-dev.txt                  # pytest (repo root, NOT the skill dir)
```

Screenshots need any headless-capable Chrome/Chromium (`google-chrome` here).

## Gotchas

- **Scripts break unless run as modules from `skills/skill-maker/`.**
  `python3 scripts/quick_validate.py .` fails with
  `ModuleNotFoundError: No module named 'scripts'` — the internal imports are
  package-relative. Always `cd skills/skill-maker && python3 -m scripts.<name>`.
- **`eval_review.html` has three placeholders, not two** — `__SKILL_NAME_PLACEHOLDER__`,
  `__SKILL_DESCRIPTION_PLACEHOLDER__`, and `__EVAL_DATA_PLACEHOLDER__` (the skill's own
  docs mention only two). `render_review.py` fills all three from `SKILL.md`
  frontmatter + `evals/trigger_queries.json` and exits 1 if any placeholder survives.
- **Packaging validates first** — a spec violation (bad frontmatter, nested SKILL.md)
  blocks `package_skill` entirely; fix validation before debugging packaging.
- **pytest leaves `.pytest_cache`/`__pycache__` in the skill dir.** Both are
  gitignored and excluded from packaging; `smoke.sh` deletes them on exit anyway.
- **`requirements-dev.txt` lives at the repo root**, not in the skill dir —
  the skill's own `requirements.txt` stays runtime-only by design.

## Troubleshooting

- `ModuleNotFoundError: No module named 'scripts'` → you ran a script by path;
  use `python3 -m scripts.<name>` from `skills/skill-maker/`.
- `ERROR: unfilled placeholder remains in output` from `render_review.py` →
  a placeholder token in `assets/eval_review.html` was renamed; update the
  three `.replace()` calls in the renderer.
