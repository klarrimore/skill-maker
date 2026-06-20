# AGENTS.md

This is the central place for repo-wide agent guidance. Read this after the platform bootstrap files (`CLAUDE.md` or `.github/copilot-instructions.md`) for anything that does not have to stay there.

## Repository shape

- `SKILL.md` is the skill entry point and should stay lean.
- `references/` holds deeper material that `SKILL.md` points to on demand.
- `scripts/` contains the executable helpers for validation and packaging.
- `assets/` contains templates used in output (the review-view template).
- `.agents/instructions/` contains canonical reusable instruction documents.
- `.github/instructions/` contains lightweight forwarders for platform auto-discovery.
- `.agents/` is the local home for reusable agent assets that should not live in the platform bootstrap files.

## Working rules

- Run Python commands from the repo root as modules.
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
python -m scripts.quick_validate .
python -m scripts.quick_validate /path/to/other-skill
skills-ref validate .

python -m scripts.package_skill . ./dist
```

## Eval workflow

- Validate before packaging.
- The evaluation and description-optimization loops are run by hand; the methodology lives in
  `references/evaluation.md` and `references/description-optimization.md`.
- Use train/holdout splits when tuning the description; choose the best description by the
  held-out test score, not the train score.
- Present test outputs to the user inline for review before critiquing them yourself.

## `.agents/`

Use `.agents/` for local reusable agent assets:

- `.agents/agents/` for prompt fragments or agent-specific instructions
- `.agents/commands/` for reusable command templates or task wrappers
- `.agents/skills/` for local skill-related helpers

Keep files there small, focused, and cross-client friendly.
