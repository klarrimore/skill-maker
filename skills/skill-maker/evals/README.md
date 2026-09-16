# skill-maker evals

Self-test evals for the skill-maker skill itself. skill-maker tells its users to keep
test cases in `evals/evals.json`; this directory makes the skill dogfood that same format.

These files are deliberately excluded from the packaged `.skill`: `scripts/package_skill.py`
skips a root-level `evals/` directory, and `scripts/quick_validate.py` ignores any
`SKILL.md` under it (so the fixtures below do not trip the "exactly one SKILL.md" check).
They ship in source control, not in the distributable artifact.

## Files

- `failure-modes.md` - the error-analysis record: the concrete ways skill-maker fails
  (`FM-1` through `FM-14`) and which eval catches each. The expectations in `evals.json` are
  written against these modes, not borrowed generic qualities. Update this first when a new
  failure appears.
- `judges/` - seed LLM-as-judge prompts for subjective self-improvement failures that are
  not code-checkable. These are not calibrated; replace the examples with held-out-safe
  human-labeled training traces before using them as benchmark judges.
- `evals.json` - six task-execution evals, each mapped to modes in `failure-modes.md`:
  - id 1, create-from-workflow: turn a repeated task into a new, valid skill.
  - id 2, make-spec-compliant: fix and validate a read-only broken fixture.
  - id 3, optimize-description: tune a weak description through the trigger-eval loop.
  - id 4, improve-installed-skill: improve a read-only installed skill without renaming it.
  - id 5, safety-refusal: decline to hide a skill's real behavior behind a benign description.
  - id 6, skip-evals: honor a user who declines the eval loop.
- `trigger_queries.json` - 20 `{query, should_trigger}` entries for the
  description-optimization loop (10 should-trigger, 10 near-miss should-not-trigger). This is
  the shape `../assets/eval_review.html` consumes via `__EVAL_DATA_PLACEHOLDER__`; keep it a
  flat array of `query`/`should_trigger` objects.
- `files/broken-skill/SKILL.md` - the deliberately malformed fixture for eval id 2. It
  violates several spec rules at once (non-kebab name that also mismatches its directory,
  angle brackets in the description, and stray top-level frontmatter keys that belong under
  `metadata`). `smoke.sh` asserts it keeps those violations and rejects it.
- `files/standup-summary/SKILL.md` - a valid but thin skill used as the input for eval id 4.
- `grade_artifacts.py` - code-checks the objectively verifiable expectations against a
  produced skill and emits a `grading.json` report. `evals/__init__.py` exists so it runs as
  a module.

## Running them

Both loops are run by hand; the methodology lives in the references:

- Task evals (`evals.json`): see `../references/evaluation.md`.
- Trigger queries (`trigger_queries.json`): see `../references/description-optimization.md`.

For each run, copy the fixture into the run workspace first (the `files/` entries are
read-only inputs and, in the `broken-skill` case, are asserted to stay broken). Do not edit
`files/broken-skill/SKILL.md` in place; the smoke suite depends on it.

Grade the code-checkable expectations with the bundled grader rather than by eye:

```bash
cd skills/skill-maker
python -m evals.grade_artifacts /path/to/produced-skill --out /path/to/grading.json
```

Remaining expectations (the safety refusal, reporting the validator output to the user,
the wording-quality judgments) are graded by hand from the transcript.

Subjective self-improvement expectations can use the seed prompts in `judges/` after
calibration against human-labeled traces. Keep each judge binary and scoped to one failure
mode; if a check can be turned into a script or validator assertion, do that instead.

## Recording a run

No run results are currently checked in. Record each run so the pipeline is auditable, and
so `failure-modes.md` can move modes from "gap" to "covered" with evidence:

- **Task evals** - with-skill and baseline runs, graded per `../references/evaluation.md`,
  aggregated into `benchmark.json`. After the first run, drop expectations that pass in
  **both** configurations: a non-discriminating assertion measures nothing.
- **Trigger loop** - record the split, per-query trigger rates, and the held-out score as
  `trigger_results.json` (schema in `../references/schemas.md`), then select by the held-out
  score.

Re-run both after any change to `SKILL.md` frontmatter or body, and after a model switch.
`trigger_queries.json` was written against the description current at authoring time;
re-validate it whenever the description changes.

## Sanity checks

A quick check that the fixtures behave as their evals expect (run from the skill root,
`skills/skill-maker/`):

```bash
python -m scripts.quick_validate evals/files/broken-skill   # expect exit 1
python -m scripts.quick_validate evals/files/standup-summary # expect exit 0
python -m evals.grade_artifacts evals/files/broken-skill     # expect exit 1
python -m evals.grade_artifacts .                            # expect exit 0
```

The first should fail with the frontmatter violations eval id 2 expects the agent to fix;
the other three confirm the grader and the valid fixture agree with the validator.
