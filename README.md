# skill-maker

This repository is a workspace for building, validating, and packaging **skill-maker**, an
Agent Skill that helps create, improve, evaluate, and validate other Agent Skills, conformant
to the open [agentskills.io](https://agentskills.io) standard.

The deliverable skill lives in `skills/skill-maker/` and is self-contained: its `SKILL.md`,
`requirements.txt`, `references/`, `scripts/`, `assets/`, and `LICENSE.txt` are everything
that ships. The `tests/` and `evals/` directories are kept in source control but excluded
from the packaged `.skill`. Build tooling and repo configuration live at the repository
root and are not part of the skill.

## Quick start

Run from the skill directory:

```bash
cd skills/skill-maker
pip install -r requirements.txt
python -m scripts.quick_validate .
python -m scripts.skill_eval audit . --workspace /tmp/skill-maker-audit
python -m scripts.package_skill . ../../dist
python -m scripts.install_skill .            # installs to ~/.agents/skills/
```

The evaluation CLI is provider-neutral. Configure an executable that implements the
`skill-eval/v1` JSON protocol for `run` and `improve`; `audit` and `benchmark` remain
offline. See `skills/skill-maker/references/evaluation.md`.

## Requirements

- Python 3.8+
- PyYAML

## Layout

```
skill-maker/                         repository (workspace)
  skills/
    skill-maker/                     the deliverable skill (self-contained)
      SKILL.md                       skill entry point
      requirements.txt               PyYAML, for the bundled scripts
      references/                    loaded on demand
        spec-reference.md
        spec-provenance.md
        authoring-guide.md
        scripts.md
        evaluation.md
        description-optimization.md
        environment-adaptations.md
        schemas.md
      scripts/                       run as modules from this directory
        quick_validate.py            zero-network spec validator
        eval_models.py               versioned eval contract loader
        eval_adapter.py              skill-eval/v1 command adapter
        eval_store.py                atomic evidence and redacted audit log
        skill_eval.py                audit, run, benchmark, improve CLI
        package_skill.py             validate then zip into a .skill
        install_skill.py             build a clean copy then install it into a skills dir
        utils.py                     shared SKILL.md parsing + build-exclusion rules
      assets/
        eval_review.html             review-view template
      LICENSE.txt                    Apache-2.0
      tests/                         dev-only; kept in source control, excluded from the .skill
      evals/                         dev-only; versioned cases, fixtures, and evidence
        README.md
        evals.json                   typed task-eval definitions
        trigger_queries.json         versioned trigger cases with train/held-out splits
        judge_labels.json             held-out judge calibration labels
        grade_artifacts.py           compatibility wrapper for shipped artifact grading
        failure-modes.md             FM-1 through FM-16 error-analysis catalogue
        judges/                      seed LLM-as-judge prompts for subjective self-improvement checks
        files/                       valid and broken skill fixtures
  docs/                              dev config, not shipped
    agents/                          issue tracker, triage labels, domain docs
    research/                        primary-source investigations
  .agents/                           canonical reusable instruction documents
    README.md
    instructions/
    *.instructions.md
  scripts/                           dev tooling: smoke driver (smoke.sh), review-UI renderer (render_review.py), usage notes (README.md)
  AGENTS.md                          repo-wide agent guidance (dev config, not shipped)
  CLAUDE.md                          Claude Code bootstrap (routes to AGENTS.md)
  .github/                           copilot-instructions.md and instructions/ (client bootstrap)
  Project_Architecture_Blueprint.md  generated repository architecture reference
  README.md  .gitignore
```

## Validate and package a skill

Run from the target skill's directory, where its `scripts/` package lives:

```bash
skills-ref validate .                 # reference validator, if installed
python -m scripts.quick_validate .    # bundled fallback
python -m scripts.package_skill . ../../dist
```

Run the automated audit/evaluation loop when an explicit `skill-eval/v1` adapter is available;
otherwise use the documented manual fallback:

```bash
python -m scripts.skill_eval audit . --workspace /tmp/skill-audit
python -m scripts.skill_eval run . --workspace /tmp/skill-run --adapter-arg python3 --adapter-arg ADAPTER
python -m scripts.skill_eval benchmark . --workspace /tmp/skill-run
```

See `skills/skill-maker/references/evaluation.md` and
`skills/skill-maker/references/description-optimization.md`.

## Install and use the skill

Place the `skills/skill-maker/` directory where your agent looks for skills, such as
`~/.agents/skills/skill-maker/` for a user-global install. The bundled installer does this
for you, stripping the dev-only `tests/` and `evals/` trees:

```bash
cd skills/skill-maker
python -m scripts.install_skill .                    # -> ~/.agents/skills/skill-maker/
python -m scripts.install_skill . --target DIR       # any skills directory
python -m scripts.install_skill . --force            # replace an existing install
```

The `cd` is required, not decoration: the bundled scripts import package-relatively
(`scripts.*`), so running them from the repository root fails with
`No module named scripts.install_skill`.

## License

Apache-2.0. See `skills/skill-maker/LICENSE.txt`.
