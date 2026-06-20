# AGENTS.md

This is the central place for repo-wide agent guidance. Read this after the platform bootstrap files (`CLAUDE.md` or `.github/copilot-instructions.md`) for anything that does not have to stay there.

## Repository shape

- `SKILL.md` is the skill entry point and should stay lean.
- `references/` holds deeper material that `SKILL.md` points to on demand.
- `scripts/` contains the executable helpers for validation, packaging, eval, and report generation.
- `agents/` contains reusable subagent instructions for eval work.
- `.github/instructions/` contains path-specific Copilot instructions.
- `.agents/` is the local home for reusable agent assets that should not live in the platform bootstrap files.

## Working rules

- Run Python commands from the repo root as modules.
- Keep skill instructions portable: use the standard frontmatter fields only, and avoid client-specific extensions unless you are intentionally locking to one platform.
- Prefer progressive disclosure. Put detail in `references/` and tell the agent exactly when to load it.
- Keep `SKILL.md` short; move repeated logic into `scripts/` and reusable prompt material into `agents/` or `.agents/`.
- Keep `.github/instructions/` focused on narrow, path-specific rules; keep broader guidance in `AGENTS.md`.

## Common commands

```bash
python -m scripts.quick_validate .
python -m scripts.quick_validate /path/to/other-skill
skills-ref validate .

python -m scripts.package_skill . ./dist

python -m scripts.run_eval --eval-set path/to/evals.json --skill-path . --runs-per-query 1
python -m scripts.run_loop --eval-set path/to/evals.json --skill-path . --model <model-id>

python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
python eval-viewer/generate_review.py <workspace>
python eval-viewer/generate_review.py <workspace> --static <output.html>
```

## Eval workflow

- Validate before packaging.
- Use train/holdout splits in `run_loop.py`; choose the best description by test score, not train score.
- `run_eval.py` and `run_loop.py` call `claude -p` and unset `CLAUDECODE` so they can run inside Claude Code sessions.
- The HTML review view should come from `eval-viewer/generate_review.py`, not a hand-rolled page.

## `.agents/`

Use `.agents/` for local reusable agent assets:

- `.agents/agents/` for prompt fragments or agent-specific instructions
- `.agents/commands/` for reusable command templates or task wrappers
- `.agents/skills/` for local skill-related helpers

Keep files there small, focused, and cross-client friendly.
