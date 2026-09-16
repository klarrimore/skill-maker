# Changelog - skill-maker

## [1.6.0] - 2026-09-17

### Added

- Added `scripts/install_skill.py`: builds a clean copy of a skill (dev-only `tests/`/`evals/` and caches stripped) and installs it into a skills directory, defaulting to `~/.agents/skills/`. Supports `--target`, `--force`, `--dry-run`, and `--json`, with documented exit codes and a refuse-unless-`--force` overwrite policy.
- Added `tests/test_install_skill.py` covering the install, force, dry-run, default-target, exclusion, and refusal paths.
- Extended `scripts/smoke.sh` to install the valid fixture into a temp target, assert no dev artifacts land there, and check the exit-2 / `--force` / invalid-skill / dry-run behaviors.
- Documented the installer in `SKILL.md` Step 8 and the bundled-resources catalog, and in `references/environment-adaptations.md`.

### Changed

- Moved the packaging-exclusion rules (`should_exclude`, the `EXCLUDE_*` sets, and a shared `walk_skill` file walker) into `scripts/utils.py`; `package_skill.py` and `install_skill.py` now share one rule set. `should_exclude` remains importable from `scripts.package_skill`.
- Bumped skill-maker to v1.6.

### Fixed

- Restored the documented Python 3.8+ floor: `scripts/utils.py` now starts with `from __future__ import annotations`, so its `tuple[dict, str]` return annotation is stored as a string instead of being evaluated at import time on 3.8.
- Fixed `walk_skill` to resolve its input path first, so `python -m scripts.install_skill .` (the documented invocation) no longer fails with `No such file or directory`: an unresolved `.` dropped the skill-folder prefix from arcnames and the staged directory was never created. Added regression tests in `tests/test_utils.py` and `tests/test_install_skill.py`.

## [1.5.0] - 2026-09-17

### Added

- Added `references/spec-provenance.md`: the authority tiers for any rule, the spec-vs-`skills-ref` divergences, and how spec versioning works
- Added `references/scripts.md`: writing and bundling scripts in depth (choosing a one-off command, inline dependencies, and agent-friendly design)
- Documented the two new references in the `SKILL.md` bundled-resources catalog and the `README.md` layout tree

### Changed

- Reframed the angle-bracket rule: the spec is silent, `skills-ref` does not check it, and the bundled validator rejects it only as a hardening measure
- Described the bundled validator as checking the spec constraints plus hardening checks (angle brackets) and soft body-budget warnings, so it is stricter than the spec
- Softened the validator wording to "reference validator" and labeled it a demonstration library, not a production SDK
- Recorded the Unicode `name` charset nuance and the spec-vs-validator field framing
- Dropped the unverified singular user-scope path; standardized on the plural `~/.agents/skills/` as the cross-client user scope
- Bumped skill-maker to v1.5

### Fixed

- Removed the unverified `metadata.spec-revision` key from the `SKILL.md` frontmatter
- Corrected the `README.md` install path and validator wording
- Added validator-precision notes: `skills-ref` enforces only the `compatibility` upper bound and does not type-check `allowed-tools`

## [1.4.0] - 2026-09-17

### Added

- Added an error-analysis catalogue (`evals/failure-modes.md`) mapping failure modes `FM-1`…`FM-13` to the evals that catch them
- Added three task evals covering an installed-skill improvement, a safety-violating skill, and a user who skips the eval loop
- Added a valid `standup-summary` eval fixture
- Added a code-check grader (`evals/grade_artifacts.py`) that emits `grading.json` for the objectively verifiable expectations
- Documented the `trigger_results.json` schema for a description-optimization run
- Set a description length budget: 256-character target, 512-character working ceiling, 1024-character hard limit
- Added the triage label vocabulary (`docs/agents/triage-labels.md`)
- Added a primary-source investigation of the agentskills.io spec and best practices (`docs/research/`)
- Added `scripts/README.md`, replacing the removed project run skill

### Changed

- Reconciled the description-length wording across `SKILL.md` and the `references/` docs
- Replaced fuzzy eval assertions with observables, and swapped obviously-irrelevant should-not-trigger queries for near-misses
- Exposed `ALLOWED_PROPERTIES` in `scripts/quick_validate.py` so the grader reuses the validator's field set
- Moved the smoke driver and review-UI renderer from `.claude/skills/run-skill-maker/` to repo-root `scripts/`
- Extended `smoke.sh` with fixture-integrity and grader-agreement checks
- Bumped skill-maker to v1.4

### Fixed

- Fixed the grader kebab-case check to reject leading, trailing, and consecutive hyphens
- Fixed the grader to fail missing descriptions on the length and angle-bracket checks
- Replaced stale line-number citations in the research doc with section references

### Removed

- Removed the Claude-specific project run skill and the now-empty `.claude/` tree
- Removed the stale generated `Project_Architecture_Blueprint.md`

## September 17, 2026

### New

- **Eval quality overhaul after an eval audit**: Added `evals/failure-modes.md` (an error-analysis catalogue mapping `FM-1`…`FM-13` to the evals that catch them), three task evals (improve an installed skill without renaming it, decline a safety-violating skill, honor a user who skips the eval loop), a valid `standup-summary` fixture for the new eval, and `evals/grade_artifacts.py` + `evals/__init__.py` — a code-check grader that emits `grading.json` for the objectively verifiable expectations (kebab name, dir match, description limits, recognized fields, validator result, body budget).
- **`trigger_results.json` schema**: Documented the record for a description-optimization run (split, per-query trigger rates, held-out scores) in `references/schemas.md`, with the recording step added to `references/description-optimization.md`.

### Improvements

- **Description length budget**: Added a 256-character target and 512-character working ceiling beneath the 1024-character hard limit, and reconciled the wording across `SKILL.md`, `references/spec-reference.md`, `references/authoring-guide.md`, and `references/description-optimization.md` so every place that states the limit agrees.
- **Sharpened eval expectations**: Replaced fuzzy assertions (for example "pushed into references/ … or short enough") with observables, added a task-specific-guidance assertion, a copy-the-read-only-fixture assertion, and held-out/3-run/multi-context trigger assertions.
- **Near-miss trigger negatives**: Replaced obviously-irrelevant should-not-trigger queries with near-misses that share skill-authoring vocabulary (splitting an `AGENTS.md`, a custom slash command, an informational standard question).
- **Fixture hygiene**: Eval id 2 now works on a copy; `smoke.sh` asserts the broken fixture keeps its violations, the valid fixture validates, and the grader agrees with the validator.

### Housekeeping

- **Exposed `ALLOWED_PROPERTIES`** at module scope in `scripts/quick_validate.py` so the eval grader reuses the validator's field set instead of duplicating it. Bumped to v1.4.
- **Dev tooling moved out of `.claude/`**: Moved the smoke driver and review-UI renderer from `.claude/skills/run-skill-maker/` to the repo-root `scripts/` (documented in `scripts/README.md`), deleted the Claude-specific project run skill and the now-empty `.claude/` tree, and updated `AGENTS.md`/`README.md`. Removed the stale generated `Project_Architecture_Blueprint.md`.

## July 17, 2026

### Housekeeping

- **Tests converted to stdlib `unittest`**: Rewrote `tests/test_utils.py` and `tests/test_quick_validate.py` off pytest and removed `requirements-dev.txt`. The suite now runs under the skill's own PyYAML-only contract (`python -m unittest discover -s tests -t .`), so the "Python 3.8+ and PyYAML, nothing else" promise holds even when the skill folder is uploaded detached from its repo root. Docs and the `run-skill-maker` smoke driver updated to match. Bumped to v1.3.

## July 15, 2026

### New

- **Automated Unit Tests**: Added the repo's first automated pytest suite (`skills/skill-maker/tests/`), covering `parse_frontmatter`, the `validate_skill`/`body_warnings` error paths, and the packaging-exclusion predicates. Dev-only dependency declared in `requirements-dev.txt`.
- **Project run skill**: Added `.claude/skills/run-skill-maker/` — a smoke driver covering the validator, packager, test suite, and eval-review UI (with automated placeholder rendering and headless-Chrome screenshots).

### Improvements

- **Trimmed SKILL.md description**: Removed a residual identity clause from the triggering `description` and deduplicated the "read this when" conditions between the Steps and the Bundled resources catalog.

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

[1.6.0]: https://github.com/klarrimore/skill-maker/compare/v1.5...v1.6
[1.5.0]: https://github.com/klarrimore/skill-maker/compare/v1.4...v1.5
[1.4.0]: https://github.com/klarrimore/skill-maker/compare/v1.3...v1.4
