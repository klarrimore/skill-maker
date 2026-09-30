# skill-maker evals

This directory dogfoods the reusable evaluator against the skill-maker skill. It is source
controlled and deliberately excluded from packaged and installed skills. The generic evaluator
lives under `scripts/` and is shipped so another skill can use the same contract.

## Files

- `evals.json`: version 1 typed task cases. Each case has a train or held-out split, failure-mode
  mappings, input files, and deterministic or judge expectations.
- `trigger_queries.json`: version 1 balanced trigger queries with train and held-out splits.
- `judge_labels.json`: held-out calibration examples for the seed judge rubrics.
- `failure-modes.md`: the error-analysis catalogue from FM-1 through FM-16.
- `judges/`: binary, failure-mode-specific rubrics for transcript-dependent checks.
- `files/broken-skill/`: deliberately invalid, read-only input for copy-first testing.
- `files/standup-summary/`: valid, intentionally thin installed-skill input.
- `files/skip-evals-skill/`: dedicated uncontaminated input for eval 6.
- `files/eval-suite-valid/`: small deterministic suite used by unit and smoke tests.
- `grade_artifacts.py`: compatibility wrapper around `scripts.skill_eval.grade_artifact`.

## Run the suite

Run from `skills/skill-maker/`:

```bash
python -m scripts.skill_eval audit . --workspace /tmp/skill-maker-audit
python -m scripts.skill_eval run . --workspace /tmp/skill-maker-run \
  --runs 1 --adapter-arg python3 --adapter-arg tests/fixtures/fake_eval_adapter.py
python -m scripts.skill_eval benchmark . --workspace /tmp/skill-maker-run
python -m scripts.skill_eval improve . --workspace /tmp/skill-maker-improve \
  --max-iterations 1 --adapter-arg python3 --adapter-arg tests/fixtures/fake_eval_adapter.py
```

A task run records both configurations. A baseline failure is an explicit grading result, not an
omitted case. Eval 3 is a trigger-specific case and may be run separately:

```bash
python -m scripts.skill_eval run . --workspace /tmp/skill-maker-trigger \
  --trigger --runs 3 --adapter-arg python3 --adapter-arg /path/to/adapter.py
```

The adapter is optional for `audit` and `benchmark`. Without one, follow the manual fallback in
`../references/environment-adaptations.md`; do not fabricate model metrics.

## Fixture safety

Treat every `files/` entry as read-only. The evaluator copies inputs into a workspace before an
adapter sees them. In particular, do not repair `broken-skill` in place. The smoke suite and unit
tests verify that it retains its malformed name, angle-bracket description, and stray frontmatter
fields. Eval 6 has its own clean fixture so eval 4's metadata cannot contaminate it.

## Judging and evidence

Use deterministic expectations whenever an artifact property can be checked locally. Judge
expectations are binary and remain advisory until their rubric has held-out human labels. Review
outputs before rewriting. `audit.json`, `grading.json`, `benchmark.json`, `benchmark.md`,
`trigger_results.json`, `history.json`, and metadata-only `audit.jsonl` make the run reproducible.
