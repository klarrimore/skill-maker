---
description: 'Doc-sync conventions for skill-maker: which docs track which code, and how CHANGELOG.md and the skill version move'
applyTo: 'skills/skill-maker/**,scripts/**'
---

# Update docs on code change

A change is done when every doc that describes the changed surface describes it as it now is.

## Surfaces to sync

Match each changed surface to the docs that track it:

- Added, renamed, or removed file under `skills/skill-maker/references/` or `scripts/`: the `## Bundled resources` list in `skills/skill-maker/SKILL.md`, and the layout or further-reading list in `README.md`. The self-audit flags misses as `resource.unaddressed` and `script.unlisted`: `cd skills/skill-maker && python -m scripts.skill_eval audit . --workspace <tmpdir>`.
- Script CLI flag, exit code, or invocation: `scripts/README.md`.
- Validator, eval pipeline, or package/install architecture: the matching section of `Project_Architecture_Blueprint.md`.
- Eval set, audit check, or eval run mode: `skills/skill-maker/evals/README.md`.
- Authoring rule or spec interpretation: the one reference that owns it (see AGENTS.md "Building the skill"); point to it from elsewhere rather than restating it.

## CHANGELOG.md and version

`CHANGELOG.md` follows Keep a Changelog. Each user-facing change gets a bullet under its release:

- Heading `## [X.Y.0] - YYYY-MM-DD`, then `### Added` / `### Changed` / `### Fixed` sections of past-tense bullets naming the file or flag.
- A version bump sets `metadata.version` in `skills/skill-maker/SKILL.md` to `"X.Y"` and opens `### Changed` with `Bumped skill-maker to vX.Y.`
- Close the release with a compare link: `[X.Y.0]: https://github.com/klarrimore/skill-maker/compare/vX.(Y-1)...vX.Y` (tags are `vX.Y`, headings `X.Y.0`).
- Insert a new release directly under `# Changelog - skill-maker`, leaving the previous release's heading intact above its bullets.

## Check

Run the smoke driver from AGENTS.md "Verifying changes" (`scripts/smoke.sh`); it must end with `ALL OK`.
