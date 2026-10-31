---
name: skill-maker
description: Create, edit, test, and optimize portable Agent Skills (SKILL.md directories). Use when the user wants to author a skill from scratch, turn a workflow or repeated task into a reusable skill, refactor an existing skill, make one spec-compliant or portable, test or benchmark it, tune its description so it triggers reliably, or improve the output quality and token cost of a skill that already fires, even if they do not say the word "skill".
license: Apache-2.0
compatibility: Portable across any skills-compatible agent that reads the agentskills.io format. Bundled validation and packaging scripts require Python 3.8+ and PyYAML.
metadata:
  author: klarrimore
  standard: agentskills.io
  version: "1.14"
---

# Skill Maker

Create and improve portable Agent Skills. A skill is a directory containing
`SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. Keep the
portable artifact self-contained. Resolve bundled paths relative to this skill's
own root. Do not search another checkout for missing resources.

## Core loop

Every task runs the shared steps in order. Steps 2 and 4 hand off to your task
path (create, update, or improve) below. The **candidate** is the copy of the
skill you edit: a directory in a workspace you own whose name matches the
skill's `name`. Source fixtures and installed skills stay byte-identical; edit
and validate only the candidate.

### Shared steps

1. **Decide** whether the content is a skill (discrete task-class capability) or
   an always-on instruction (ambient discipline). Read
   `references/authoring-guide.md`. Done when you can name the task class the
   skill serves, or you have routed the content to an always-on instruction file
   and stopped.
2. **Prepare** the candidate by running your task path's preparation step.
   Done when that step's condition holds.
3. **Establish or preserve** task and trigger baselines before any edit. Read
   `references/evaluation.md` and `references/description-optimization.md`. Read
   `references/skill-optimization.md` when diagnosing task quality, context cost,
   or tool efficiency, or when choosing among optimization experiments. Read
   `references/schemas.md` when writing or debugging `evals/evals.json` or
   reading grading, benchmark, or history records. Done when every eval and
   trigger query has a recorded baseline result (no skill for a new skill, the
   current version otherwise).
4. **Change** the candidate by running your task path's change step, making the
   smallest justified change. Done when every edit traces to a captured
   requirement or a failing baseline result.
5. **Compare** with paired evidence: run each eval with the skill and against
   the baseline, then show the outputs to the human before critiquing or
   rewriting the candidate. Select by held-out results. Done when every eval has
   a with-skill and a baseline result and the human has seen the outputs.
6. **Deliver** with strict validation (`scripts/quick_validate.py`), then
   package (`scripts/package_skill.py`) or install (`scripts/install_skill.py`):
   ```bash
   python -m scripts.quick_validate <candidate>
   python -m scripts.package_skill <candidate> <dist>
   python -m scripts.install_skill <candidate> [--target <dir>] [--force]
   ```
   Strict mode rejects non-portable fields and is required by package/install.
   Done when strict validation exits 0 and the package or install command
   exits 0.

### Create a new skill

- **Capture** (step 2) expertise, triggers, inputs, output format, dependencies,
  and boundaries from real artifacts (runbooks, schemas, API docs, failure
  reports), then create the candidate directory. Done when every trigger, input,
  output format, and boundary is tied to a source artifact.
- **Draft** (step 4) the portable core: `name` (kebab-case, matching directory),
  `description` (action + scope + trigger signal), and a concise body with
  progressive disclosure, under 500 lines / ~5000 tokens. Use only the six
  recognized frontmatter fields (the `allowed-tools` default is in
  `references/authoring-guide.md`). Client-specific fields, install paths,
  precedence, plugins, hosted IDs, and marketplace metadata are opt-in target
  adapters outside the canonical artifact; add one only when a target was
  requested. Name each `scripts/` and `references/` file in the body with a
  one-line purpose and when to read it, and keep references one level under
  `references/`. Read `references/scripts.md` when bundling executable code.
  Read `references/spec-provenance.md` when tracing the authority tier of
  a spec, validator, or hardening rule.
  Use `assets/eval_review.html` to present trigger-review results when a
  browser is available (fill `__EVAL_DATA_PLACEHOLDER__`,
  `__SKILL_NAME_PLACEHOLDER__`, and `__SKILL_DESCRIPTION_PLACEHOLDER__`
  with real data before opening).
  Done when the audit reports no `script.unlisted` or `resource.unaddressed`
  findings for the candidate.

### Update an existing skill

- **Inspect** (step 2) the source with import mode, then copy it into the
  candidate:
  ```bash
  python -m scripts.quick_validate <skill> --mode import --json
  ```
  Import mode reports client extensions and name mismatches as warnings so you
  can examine an existing skill without rejecting it. Done when every import
  warning is listed with a keep, convert, or drop decision and the candidate
  directory exists.
- **Edit** (step 4) the candidate, preserving the skill name and unrelated
  behavior. Strip or relocate client extensions only after the user makes an
  explicit portable-conversion decision. Done when the diff against the source
  touches only the requested behavior and the decided extensions.

### Improve a skill (sandboxed candidate loop)

- **Run** `scripts/skill_eval.py` in improve mode (steps 2 to 5); it copies the
  skill into workspace candidates, revises on train failures, and promotes by
  held-out results:
  ```bash
  python -m scripts.skill_eval improve <skill> --workspace <workspace> \
    --max-iterations 3 --adapter-arg <executable> --adapter-arg <argument>
  ```
  Isolation, held-out handling, and promotion: `references/evaluation.md`.
  Show the paired outputs to the human (step 5), then deliver
  `<workspace>/best-skill/<skill-name>/` (step 6). Done when `history.json`
  records a `grading_result` for every candidate and the human has seen the
  promoted candidate's outputs.

## Gotchas

- Run bundled scripts as modules from the skill root
  (`python -m scripts.quick_validate`); the package imports resolve only from
  there.
- Use a comma, period, colon, or parentheses instead of U+2014 (em dash); the
  validator rejects it.

## Authoring rules

Read `references/spec-reference.md` before changing frontmatter and
`references/authoring-guide.md` before drafting the body. Use only the six
portable frontmatter fields by default. `name` must be kebab-case and match the
directory. `description` must say what the skill does and when to use it, with
a first-sentence routing signal. Write imperative, specific instructions and
explain why important steps exist. Avoid hidden access, data exfiltration,
misleading descriptions, and client-specific assumptions.

Passing validation is not a safety review; see `references/authoring-guide.md`.

## Evaluation and improvement

The shipped evaluator uses the `skill-eval/v1` command adapter. It runs
deterministic expectations locally, sends only `judge` expectations to the
adapter, and records paired with-skill and baseline results. Command
expectations are denied unless `--allow-command-checks` is explicit.
Read `scripts/eval_models.py` when an eval, trigger, or calibration file fails
to load, `scripts/eval_adapter.py` when writing an adapter command, and
`scripts/eval_store.py` when reading workspace artifacts or audit metadata.
Import `scripts/utils.py` for shared helpers (`parse_frontmatter`,
`should_exclude`, `walk_skill`) when writing custom evaluation or
packaging tools.

The offline audit (`python -m scripts.skill_eval audit`) includes
progressive-disclosure and portable-resource warnings:
- `skill.allowed-tools`: frontmatter carries the experimental pre-approval field.
- `resource.unaddressed.<path>`: a packaged reference or asset not named in
  the body.
- `resource.reference-depth.<path>`: file nested below `references/<subdir>/`.
- `script.unlisted.<path>`: a bundled script not named in the body.

Read `references/evaluation.md` for the adapter contract, workspace artifacts,
exit codes, benchmark diagnostics, and manual fallback. Read
`references/description-optimization.md` for trigger tuning and
`references/environment-adaptations.md` when capabilities are limited.
