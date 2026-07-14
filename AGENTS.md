# AGENTS.md

This is the central place for repo-wide agent guidance. Read this after the platform bootstrap files (`CLAUDE.md` or `.github/copilot-instructions.md`) for anything that does not have to stay there.

## Repository shape

This repo is a workspace. The deliverable skill is self-contained under `skills/skill-maker/`; build tooling and client config live at the repository root and are not part of the skill.

- `skills/skill-maker/` is the deliverable skill (everything that ships).
  - `skills/skill-maker/SKILL.md` is the skill entry point and should stay lean.
  - `skills/skill-maker/references/` holds deeper material that `SKILL.md` points to on demand.
  - `skills/skill-maker/scripts/` contains the executable helpers for validation and packaging.
  - `skills/skill-maker/assets/` contains templates used in output (the review-view template).
- `.agents/instructions/` contains canonical reusable instruction documents.
- `.github/instructions/` contains lightweight forwarders for platform auto-discovery.
- `.agents/` is the local home for reusable agent assets that should not live in the platform bootstrap files.
  Skills used across repositories live in the user-global `~/.agent/skills/` directory, not in this repo.
- `docs/agents/` holds this repo's Agent skills configuration (issue tracker, domain docs) — see the "Agent skills" section below.

## Working rules

- Run Python commands as modules from the target skill's directory (where its `scripts/` package lives), e.g. `cd skills/skill-maker`.
- Keep skill instructions portable: use the standard frontmatter fields only, and avoid client-specific extensions unless you are intentionally locking to one platform.
- Prefer progressive disclosure. Put detail in `references/` and tell the agent exactly when to load it.
- Keep `SKILL.md` short; move repeated logic into `scripts/` and reusable prompt material into `.agents/`.
- Keep broader guidance in `AGENTS.md`; keep canonical reusable instruction content in `.agents/instructions/`.

## Canonical instruction documents

Agents that honor `AGENTS.md` should load and follow these files as needed:

- `.agents/instructions/agent-safety.instructions.md` for agent/tool governance patterns.
- `.agents/instructions/markdown-gfm.instructions.md` when editing Markdown.
- `.agents/instructions/update-docs-on-code-change.instructions.md` when code changes require documentation updates.

## Common commands

```bash
cd skills/skill-maker

pip install -r requirements.txt              # install Python deps (PyYAML, etc.)
pip install -r ../../requirements-dev.txt    # install dev deps (pytest), for running tests/

skills-ref validate .                  # canonical validator, if installed
python -m scripts.quick_validate .     # bundled fallback
python -m scripts.quick_validate /path/to/other-skill

python -m scripts.package_skill . ../../dist

python -m pytest tests/                # unit tests for scripts/ (dev-only, excluded from packaging)
```

## Eval workflow

- Validate before packaging.
- The evaluation and description-optimization loops are run by hand; the methodology lives in
  `skills/skill-maker/references/evaluation.md` and
  `skills/skill-maker/references/description-optimization.md`.
- Use train/holdout splits when tuning the description; choose the best description by the
  held-out test score, not the train score.
- Present test outputs to the user inline for review before critiquing them yourself.

## `.agents/`

Use `.agents/` for local reusable agent assets:

- `.agents/agents/` for prompt fragments or agent-specific instructions
- `.agents/commands/` for reusable command templates or task wrappers

Keep files there small, focused, and cross-client friendly. Do not add project-local skill copies here; install reusable skills under `~/.agent/skills/`.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at the repo root (neither exists yet — created lazily on demand, e.g. by `/domain-modeling`). See `docs/agents/domain.md`.
