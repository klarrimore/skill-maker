# skill-maker

An Agent Skill for creating, improving, evaluating, and validating other Agent Skills,
conformant to the open [agentskills.io](https://agentskills.io) standard.

This repo is the skill itself plus the helpers used to author, validate, package, benchmark,
and review it. The core skill lives in `SKILL.md`; supporting depth is pushed into
`references/`, executable helpers live in `scripts/`, and reusable agent guidance lives in
`AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.

## Quick start

```bash
python -m scripts.quick_validate .
python -m scripts.package_skill . ./dist
```

## Requirements

- Python 3.8+
- PyYAML

## Layout

```
skill-maker/
  SKILL.md            Skill entry point
  AGENTS.md           Central repo-wide agent guidance
  CLAUDE.md           Claude Code bootstrap
  .github/copilot-instructions.md  Copilot bootstrap
  references/         Loaded on demand
    spec-reference.md           Exact frontmatter schema, naming, structure, portability
    authoring-guide.md          Anatomy, writing patterns, full do's and don'ts
    evaluation.md               Test, grade, benchmark, review, improve workflow
    description-optimization.md Eval-driven triggering method
    environment-adaptations.md  Capability-based adaptations (no subagents/display/CLI)
    schemas.md                  JSON schemas for evals/grading/benchmark
  .agents/            Local reusable agent assets
    instructions/               Canonical reusable instruction documents
  .github/instructions/  Forwarders for Copilot auto-discovery
  scripts/            Run as modules from the skill root
    quick_validate.py   Zero-network spec validator (fallback for `skills-ref validate`)
    package_skill.py    Validate then zip into a .skill for hosts that accept uploads
    utils.py            Shared SKILL.md parsing helper
  assets/             Templates (the review-view template)
  LICENSE.txt         Apache-2.0
```

## Common commands

Run Python commands from the repo root.

```bash
# Validate a skill
skills-ref validate .
python -m scripts.quick_validate .
python -m scripts.quick_validate /path/to/other-skill

# Package a skill after validation
python -m scripts.package_skill . ./dist
```

The evaluation and description-optimization loops are run by hand; see
`references/evaluation.md` and `references/description-optimization.md`.

## Agent guidance

For repo-wide agent instructions, read `AGENTS.md`. Canonical reusable instruction
documents live under `.agents/instructions/`. `.github/instructions/` contains
forwarders for Copilot auto-discovery.

## Use

Install by placing the `skill-maker/` directory where your agent looks for skills, such as
`.agents/skills/skill-maker/` (project) or `~/.agents/skills/skill-maker/` (user).

## License

Apache-2.0. See LICENSE.txt.
