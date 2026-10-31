---
name: skill-maker
description: Use this skill whenever the user wants to author a skill from scratch, turn a workflow or repeated task into a reusable skill, edit or refactor an existing skill, make a skill spec-compliant or portable, test or benchmark a skill, or optimize a skill description for better triggering, even if they do not say the word "skill" explicitly.
license: Apache-2.0
compatibility: Portable across any skills-compatible agent that reads the agentskills.io format. Bundled validation and packaging scripts require Python 3.8+ and PyYAML.
metadata:
  author: klarrimore
  standard: agentskills.io
  version: "1.13"
---

# Skill Maker

Create and improve portable Agent Skills. A skill is a directory containing
`SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. Keep the
portable artifact self-contained. Resolve bundled paths relative to this skill's
own root. Do not search another checkout for missing resources.

## Core loop

The core loop branches by task. Each path starts with the same foundation:

- **Decide** whether the content is a skill (discrete task-class capability) or an
  always-on instruction (ambient discipline). Read `references/authoring-guide.md`.
- **Inspect** an existing skill with import mode before changing it:
  ```bash
  python -m scripts.quick_validate <skill> --mode import --json
  ```
  Import mode reports client extensions and name mismatches as warnings so you
  can examine an existing skill without rejecting it. Always **deliver** with
  strict validation:
  ```bash
  python -m scripts.quick_validate <skill>
  ```
  Strict mode rejects non-portable fields and is required by package/install.
- **Capture** expertise, triggers, output format, dependencies, and boundaries
  from real artifacts (runbooks, schemas, API docs, failure reports).
- **Draft** the portable core: `name` (kebab-case, matching directory),
  `description` (action + scope + trigger signal), and concise body with
  progressive disclosure. Keep the body under 500 lines / ~5000 tokens.
- **Add direct conditional resource pointers**: name each `scripts/` and
  `references/` file in the body with a one-line purpose and when to read it.
  Bundled scripts not named in `SKILL.md` trigger audit warnings.
  Flatten references to one level under `references/`.
  Read `references/scripts.md` when bundling executable code.
  Read `references/spec-provenance.md` when tracing the authority tier of
  a spec, validator, or hardening rule.
  Use `assets/eval_review.html` to present trigger-review results when a
  browser is available (fill `__EVAL_DATA_PLACEHOLDER__`,
  `__SKILL_NAME_PLACEHOLDER__`, and `__SKILL_DESCRIPTION_PLACEHOLDER__`
  with real data before opening).
- **Establish or preserve** task and trigger baselines before edits. Read
  `references/evaluation.md` and `references/description-optimization.md`. Read
  `references/skill-optimization.md` when diagnosing task quality, context cost, or tool
  efficiency, or when choosing among optimization experiments.
- **Make the smallest justified change** to a writable copy; never modify source
  fixtures or an installed read-only directory.
- **Run paired evidence** (with-skill vs baseline), then select by held-out
  results.
- **Strictly validate**, then package or install:
  ```bash
  python -m scripts.package_skill <skill> <dist>
  python -m scripts.install_skill <skill> [--target <dir>] [--force]
  ```

### Create a new skill

Follow the core loop foundation. Draft the portable core with only the six
recognized frontmatter fields (the `allowed-tools` default is in
`references/authoring-guide.md`). Agent-agnostic output uses
only the portable fields. Client-specific fields, install paths, precedence,
plugins, hosted IDs, and marketplace metadata remain opt-in target adapters
outside the canonical artifact; do not invent an adapter when no target was
requested.

### Update an existing skill

1. Preserve the skill name and unrelated behavior.
2. Inspect with import mode to surface client extensions without silently deleting them.
3. Copy to a writable workspace. Make the smallest justified change.
4. Revalidate strictly on the copy.
5. Require an explicit portable-conversion decision before stripping or relocating
   client extensions.

### Improve a skill (sandboxed candidate loop)

```bash
python -m scripts.skill_eval improve <skill> --workspace <workspace> \
  --max-iterations 3 --adapter-arg <executable> --adapter-arg <argument>
```

Isolation, held-out handling, and promotion: `references/evaluation.md`.

## Authoring rules

Read `references/spec-reference.md` before changing frontmatter and
`references/authoring-guide.md` before drafting the body. Use only the six
portable frontmatter fields by default. `name` must be kebab-case and match the
directory. `description` must say what the skill does and when to use it, with
a first-sentence routing signal. Write imperative, specific instructions and
explain why important steps exist. Avoid hidden access, data exfiltration,
misleading descriptions, and client-specific assumptions.
Use a comma, period, colon, or parentheses instead of U+2014.

Passing validation is not a safety review; see `references/authoring-guide.md`.

## Evaluation and improvement

The shipped evaluator uses the `skill-eval/v1` command adapter. It runs
deterministic expectations locally, sends only `judge` expectations to the
adapter, and records paired with-skill and baseline results. Command
expectations are denied unless `--allow-command-checks` is explicit.
Import `scripts/utils.py` for shared helpers (`parse_frontmatter`,
`should_exclude`, `walk_skill`) when writing custom evaluation or
packaging tools.

The offline audit (`python -m scripts.skill_eval audit`) now includes
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

## Bundled resources

- `references/spec-reference.md`: portable frontmatter and body rules, strict vs
  import validation, adapter concerns.
- `references/authoring-guide.md`: anatomy, style, progressive disclosure, and
  existing-skill conversion.
- `references/evaluation.md`: audit, run, benchmark, improve, and manual workflows.
- `references/schemas.md`: versioned eval, grading, benchmark, and history contracts.
- `references/description-optimization.md`: trigger-query design and selection.
- `references/skill-optimization.md`: post-activation optimization playbook for task quality,
  context cost, and tool efficiency.
- `references/environment-adaptations.md`: no-adapter, no-display, and packaging fallbacks.
- `scripts/quick_validate.py`: zero-network validator with `--mode strict|import` and `--json`.
- `scripts/eval_models.py`: strict eval, trigger, and calibration loaders.
- `scripts/eval_adapter.py`: provider-neutral command adapter.
- `scripts/eval_store.py`: atomic artifacts and redacted append-only audit metadata.
- `scripts/skill_eval.py`: `audit`, `run`, `benchmark`, and `improve` CLI.
- `scripts/package_skill.py` and `scripts/install_skill.py`: distribution helpers.
