# AGENTS.md

Repo-wide agent guidance. This file is canonical: `CLAUDE.md` and `.github/copilot-instructions.md` are thin forwarders that point here, so add new instructions to this file (or to the docs it points at), not to them.

## What ships

This repo is a workspace; the deliverable is the self-contained skill folder `skills/skill-maker/`. Its `SKILL.md`, `references/`, `scripts/`, `assets/`, and `LICENSE.txt` are the whole artifact. Everything at the root is dev config that stays behind: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `.github/`, `.claude/`, `docs/`.

Two trees inside the skill are dev-only — `tests/` and `evals/` — kept in source control but excluded from the packaged `.skill`. `README.md` has the full layout.

## Building the skill

The skill's own references are the authority on authoring; reach for them instead of restating the rules here:

- `skills/skill-maker/references/spec-reference.md` — before touching frontmatter: the field-by-field schema, naming rules, character limits (including the description-length budget), and the portable-vs-platform-locked line.
- `skills/skill-maker/references/authoring-guide.md` — before writing the body: anatomy, progressive disclosure, style, and the do's and don'ts.
- `skills/skill-maker/references/description-optimization.md` — when tuning the `description` for triggering: the eval-driven method.

## Verifying changes

Run the smoke driver; it exercises the validator, packager, tests, and eval-review UI, and exits non-zero on the first failure:

```bash
bash .claude/skills/run-skill-maker/smoke.sh
```

Individual surfaces, direct-invocation snippets, and gotchas live in the run-skill-maker skill (`.claude/skills/run-skill-maker/SKILL.md`). Run the bundled scripts as modules from the skill directory — `cd skills/skill-maker && python -m scripts.quick_validate .` — since the package-relative imports break under a path invocation.

## Canonical instructions

Each file below is the single source of truth for its topic; load it in full when its condition applies.

- `.agents/instructions/agent-safety.instructions.md` — before building or modifying an agent's tool access, content filtering, or multi-agent composition.
- `.agents/instructions/markdown-gfm.instructions.md` — whenever writing or editing Markdown.
- `.agents/instructions/update-docs-on-code-change.instructions.md` — when a code change needs matching doc work (READMEs, API docs, `CHANGELOG.md`).

`.github/instructions/` holds per-client forwarders to these for auto-discovery; edit the canonical file, not the forwarder. Keep new reusable agent assets in `.agents/` (see `.agents/README.md`).

## Agent skills

### Issue tracker

Issues and PRDs live in this repo's GitHub Issues, driven by the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: the five canonical roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` plus `docs/adr/` at the repo root. Neither exists yet — `/domain-modeling` creates them lazily when a term or decision actually gets resolved. See `docs/agents/domain.md`.
