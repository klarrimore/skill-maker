# skill-maker

This repository is a workspace for building, validating, and packaging **skill-maker**, an
Agent Skill that helps create, improve, evaluate, and validate other Agent Skills, conformant
to the open [agentskills.io](https://agentskills.io) standard.

The deliverable skill lives in `skills/skill-maker/` and is self-contained: its `SKILL.md`,
`references/`, `scripts/`, `assets/`, and `LICENSE.txt` are everything that ships. Build
tooling and repo configuration live at the repository root and are not part of the skill.

## Quick start

Run from the skill directory:

```bash
cd skills/skill-maker
pip install -r requirements.txt
python -m scripts.quick_validate .
python -m scripts.package_skill . ../../dist
```

## Requirements

- Python 3.8+
- PyYAML

## Layout

```
skill-maker/                         repository (workspace)
  skills/
    skill-maker/                     the deliverable skill (self-contained)
      SKILL.md                       skill entry point
      references/                    loaded on demand
        spec-reference.md
        authoring-guide.md
        evaluation.md
        description-optimization.md
        environment-adaptations.md
        schemas.md
      scripts/                       run as modules from this directory
        quick_validate.py            zero-network spec validator
        package_skill.py             validate then zip into a .skill
        utils.py                     shared SKILL.md parsing helper
      assets/                        templates (the review-view template)
      LICENSE.txt                    Apache-2.0
  AGENTS.md                          repo-wide agent guidance (dev config, not shipped)
  CLAUDE.md  .github/                client bootstrap files (dev config, not shipped)
  README.md  .gitignore
```

## Validate and package a skill

Run from the target skill's directory, where its `scripts/` package lives:

```bash
skills-ref validate .                 # canonical validator, if installed
python -m scripts.quick_validate .    # bundled fallback
python -m scripts.package_skill . ../../dist
```

The evaluation and description-optimization loops are run by hand; see
`skills/skill-maker/references/evaluation.md` and
`skills/skill-maker/references/description-optimization.md`.

## Install and use the skill

Place the `skills/skill-maker/` directory where your agent looks for skills, such as
`~/.agent/skills/skill-maker/` for a user-global install.

## License

Apache-2.0. See `skills/skill-maker/LICENSE.txt`.
