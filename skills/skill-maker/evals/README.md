# skill-maker evals

This directory dogfoods the reusable evaluator against the skill-maker skill. It is source
controlled and deliberately excluded from packaged and installed skills. The generic evaluator
lives under `scripts/` and is shipped so another skill can use the same contract.

## Files

- `evals.json`: version 1 typed task cases. Each case has a train or held-out split, failure-mode
  mappings, input files, and deterministic or judge expectations.
- `trigger_queries.json`: version 1 balanced trigger queries with train and held-out splits.
- `judge_labels.json`: held-out calibration examples for the judge rubrics (status: see "Judge
  calibration" below).
- `failure-modes.md`: the error-analysis catalogue from FM-1 through FM-16.
- `judges/`: binary, failure-mode-specific rubrics for transcript-dependent checks.
- `files/broken-skill/`: deliberately invalid, read-only input for copy-first testing.
- `files/standup-summary/`: valid, intentionally thin installed-skill input.
- `files/skip-evals-skill/`: dedicated uncontaminated input for eval 6.
- `files/eval-suite-valid/`: small deterministic suite used by unit and smoke tests.
- `grade_artifacts.py`: compatibility wrapper around `scripts.skill_eval.grade_artifact`.

## Run the suite

Run from `skills/skill-maker/`. The adapter is optional for `audit` and `benchmark`:

```bash
python -m scripts.quick_validate .                              # strict (delivery default)
python -m scripts.quick_validate . --mode import --json          # import (compatibility inspection)
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

Without an adapter, follow the manual fallback in `../references/environment-adaptations.md`;
do not fabricate model metrics.

## Audit warnings

The offline audit (`skill_eval audit`) emits portable-resource warnings alongside schema and
spec violations:

- `skill.allowed-tools` — frontmatter contains the experimental pre-approval field.
- `resource.unaddressed.<path>` — a packaged file under `references/` or `assets/` is not named
  in the SKILL.md body. Direct files only; nested references get a depth warning instead.
- `resource.reference-depth.<path>` — file sits below `references/<subdir>/` instead of
  directly under `references/`.
- `script.unlisted.<path>` — a bundled script under `scripts/` is not named in the body.
- `resource.dead-pointer.<source>:<path>` — `SKILL.md` or a reference names a `scripts/`,
  `references/`, or `assets/` path that does not exist (lines marked "e.g." or "for example"
  are treated as illustrations and skipped).
- `resource.missing-toc.<path>` — a long reference under `references/` has no "Contents"
  heading near the top (the authoring guide owns the threshold).

Add explicit one-line purpose pointers to clear resource/script findings.

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

## Judge calibration

This is the one place that states how far the judges can be trusted. `skill_eval` treats a rubric
as calibrated as soon as `judge_labels.json` holds any held-out label for it, so the audit raises
no calibration warning and judge results enter the calibrated pass rate. Every rubric currently
has exactly one held-out label, and each is a `pass`:

| Rubric | Held-out pass | Held-out fail |
| --- | --- | --- |
| `judges/generic-procedure-detection.md` | 1 | 0 |
| `judges/safety-least-surprise.md` | 1 | 0 |
| `judges/self-improvement-overfitting.md` | 1 | 0 |
| `judges/self-improvement-scope.md` | 1 | 0 |
| `judges/skip-evals-scope.md` | 1 | 0 |

A pass-only label shows that a judge accepts one good response; it says nothing about whether the
judge rejects a bad one. Read judge pass rates as advisory until each rubric has reviewed held-out
`fail` labels drawn from real runs. A 4-case dry run on 2026-09-30
(`runs/2026-09-30/judge-dry-run.md`) confirmed the then-current prompts parse and discriminate on
fresh cases; that was a smoke test, not calibration. `tests/test_evals_data.py` keeps this table in
step with `judge_labels.json`.
