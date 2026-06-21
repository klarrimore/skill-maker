# skill-maker evals

Self-test evals for the skill-maker skill itself. skill-maker tells its users to keep
test cases in `evals/evals.json`; this directory makes the skill dogfood that same format.

These files are deliberately excluded from the packaged `.skill`: `scripts/package_skill.py`
skips a root-level `evals/` directory, and `scripts/quick_validate.py` ignores any
`SKILL.md` under it (so the fixture below does not trip the "exactly one SKILL.md" check).
They ship in source control, not in the distributable artifact.

## Files

- `evals.json` - three task-execution evals, one per core flow, following the schema in
  `../references/schemas.md`:
  - id 1, create-from-workflow: turn a repeated task into a new, valid skill.
  - id 2, make-spec-compliant: fix and validate the broken fixture below.
  - id 3, optimize-description: tune a weak description through the trigger-eval loop.
- `trigger_queries.json` - ~20 `{query, should_trigger}` entries for the
  description-optimization loop, written against skill-maker's current description. This is
  the shape `../assets/eval_review.html` consumes via `__EVAL_DATA_PLACEHOLDER__`.
- `files/broken-skill/SKILL.md` - a deliberately malformed skill used as input for eval
  id 2. It violates several spec rules at once (non-kebab name that also mismatches its
  directory, angle brackets in the description, and stray top-level frontmatter keys that
  belong under `metadata`).

## Running them

Both loops are run by hand; the methodology lives in the references:

- Task evals (`evals.json`): see `../references/evaluation.md`.
- Trigger queries (`trigger_queries.json`): see `../references/description-optimization.md`.

A quick sanity check that the fixture is genuinely broken (run from the skill root,
`skills/skill-maker/`):

```bash
python -m scripts.quick_validate evals/files/broken-skill
```

It should fail with the frontmatter violations eval id 2 expects the agent to fix.
