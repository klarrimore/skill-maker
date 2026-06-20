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
- `claude` CLI for `run_eval.py`, `run_loop.py`, and description-improvement flows

## Layout

```
skill-maker/
  SKILL.md            Skill entry point
  AGENTS.md           Central repo-wide agent guidance
  CLAUDE.md           Claude Code bootstrap
  .github/copilot-instructions.md  Copilot bootstrap
  .github/instructions/  Path-specific Copilot instructions
  references/         Loaded on demand
    spec-reference.md           Exact frontmatter schema, naming, structure, portability
    authoring-guide.md          Anatomy, writing patterns, full do's and don'ts
    evaluation.md               Test, grade, benchmark, review, improve workflow
    description-optimization.md Eval-driven triggering method
    environment-adaptations.md  Capability-based adaptations (no subagents/display/CLI)
    schemas.md                  JSON schemas for evals/grading/benchmark
  scripts/            Run as modules from the skill root
    quick_validate.py   Zero-network spec validator (fallback for `skills-ref validate`)
    package_skill.py    Validate then zip into a .skill for hosts that accept uploads
    run_eval.py run_loop.py aggregate_benchmark.py improve_description.py
    generate_report.py utils.py   Eval/optimization automation
  agents/             Subagent instructions (grader, comparator, analyzer)
  .agents/            Local reusable agent assets
  eval-viewer/        Human review view generator
  assets/             Templates
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

# Run trigger evaluation
python -m scripts.run_eval --eval-set path/to/evals.json --skill-path . --runs-per-query 1

# Run the eval/improve loop
python -m scripts.run_loop --eval-set path/to/evals.json --skill-path . --model <model-id>

# Aggregate benchmark results
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>

# Generate the review viewer
python eval-viewer/generate_review.py <workspace>
python eval-viewer/generate_review.py <workspace> --static <output.html>
```

## Agent guidance

For repo-wide agent instructions, read `AGENTS.md`. It is the central location for
instructions that do not need to stay in the platform bootstrap files. Path-specific
Copilot instructions live under `.github/instructions/`.

## Use

Install by placing the `skill-maker/` directory where your agent looks for skills, such as
`.agents/skills/skill-maker/` (project) or `~/.agents/skills/skill-maker/` (user).

## License

Apache-2.0. See LICENSE.txt.
