# Changelog - skill-maker

## July 15, 2026

### New

- **Automated Unit Tests**: Added the repo's first automated pytest suite (`skills/skill-maker/tests/`), covering `parse_frontmatter`, the `validate_skill`/`body_warnings` error paths, and the packaging-exclusion predicates. Dev-only dependency declared in `requirements-dev.txt`.

### Housekeeping

- **Consolidated frontmatter parsing**: Collapsed three divergent frontmatter parsers (one of them dead code, unused) into a single `parse_frontmatter` in `utils.py`, used by both `validate_skill` and `body_warnings`.
- **Packaging exclusions extended**: `tests/` and `.pytest_cache/` are now excluded from the packaged `.skill`, matching the existing treatment of `evals/` and `__pycache__`.
- **Agent skills configuration**: Added `docs/agents/issue-tracker.md` (GitHub Issues via `gh`) and `docs/agents/domain.md` (single-context domain docs), linked from a new "Agent skills" section in `AGENTS.md`.

## July 4, 2026

### Improvements

- **Sharpened skill-maker SKILL.md**: pruned a triple-stated core loop down to a single cycle plus the numbered procedure, tightened the triggering `description` (dropped the identity restatement and a duplicated spec-compliance branch), and cut two half-redundant guidance sections. Bumped to v1.2.

## June 21, 2026

### New

- **Evaluation Test Suite**: Added a dogfood eval set with task evals for skill creation, validation, and description optimization, plus 20 trigger-query test cases and a deliberately malformed skill fixture for testing validation failures.

- **Project Architecture Blueprint**: Added a reusable architecture blueprint generator skill for producing structured project documentation.

- **agentskills.io Standard Conformance**: Migrated all skills from the GitHub-specific `.github/skills/` path to the cross-client `.agents/skills/` interoperability path, bringing each into full compliance with the open agentskills.io standard.

- **Skill-Authoring Standards**: Ported comprehensive skill-authoring guidance including a skill-vs-always-on decision gate, reserved-word name advisory, portability operations, inline dependency declarations, and documented anti-patterns.

### Improvements

- **Reorganized Skill Layout**: Moved skill-maker under `skills/` directory, genericized the installation step, and reordered the Step 1 workflow lead for better clarity.

- **Refactored Internal Structure**: Cleaned up and reorganized project internals.

- **Documentation Reconciled**: Removed references to a non-existent benchmark viewer, aligned eval documentation with what actually ships, and corrected misleading "review view" language.

### Housekeeping

- Removed an installed skill that was checked in by mistake.
