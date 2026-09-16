# Changelog - skill-maker

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
