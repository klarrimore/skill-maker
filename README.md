# skill-creator

An Agent Skill for creating, improving, evaluating, and validating other Agent Skills,
conformant to the open [agentskills.io](https://agentskills.io) standard.

Derived from Anthropic's `skill-creator` (anthropics/skills, Apache-2.0) and restructured
for the standard: a lean `SKILL.md` under the ~5000-token / 500-line budget, depth pushed
into `references/` (progressive disclosure), agent-agnostic language for cross-client
portability, and a spec-aligned validator.

## Layout

```
skill-creator/
  SKILL.md            Lean orchestrator (the skill entry point)
  references/         Loaded on demand
    spec-reference.md           Exact frontmatter schema, naming, structure, portability
    authoring-guide.md          Anatomy, writing patterns, full do's and don'ts
    evaluation.md               Test, grade, benchmark, review, improve workflow
    description-optimization.md Eval-driven triggering method
    environment-adaptations.md  Capability-based adaptations (no subagents/display/CLI)
    schemas.md                  JSON schemas for evals/grading/benchmark
  scripts/            Run as modules from the skill root: python -m scripts.<name>
    quick_validate.py   Zero-network spec validator (fallback for `skills-ref validate`)
    package_skill.py    Validate then zip into a .skill for hosts that accept uploads
    run_eval.py run_loop.py aggregate_benchmark.py improve_description.py
    generate_report.py utils.py   Optional eval/optimization automation (needs a claude-style CLI)
  agents/             Subagent instructions (grader, comparator, analyzer)
  eval-viewer/        Human review view generator
  assets/             Templates
  LICENSE.txt         Apache-2.0
```

## Use

Install by placing the `skill-creator/` directory where your agent looks for skills, e.g.
`.agents/skills/skill-creator/` (project) or `~/.agents/skills/skill-creator/` (user).

Validate:

```bash
skills-ref validate ./skill-creator          # canonical (pip install skills-ref)
python -m scripts.quick_validate .            # bundled fallback, run from the skill root
```

## License

Apache-2.0. See LICENSE.txt.
