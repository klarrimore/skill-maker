# Optimizing the Description for Triggering

The `description` field is the primary mechanism an agent uses to decide whether to load a
skill. Tune it with realistic queries, balanced near misses, repeated trigger measurements,
and held-out selection. The evaluator keeps this loop separate from ordinary task evals.

This file covers activation only. For post-activation execution quality and efficiency, read
`references/skill-optimization.md`.

## Build the query set

Store about 20 balanced positive and negative records in `evals/trigger_queries.json`:

```json
{
  "version": 1,
  "queries": [
    {"query": "turn this workflow into a reusable skill", "should_trigger": true, "split": "train"},
    {"query": "review this pull request", "should_trigger": false, "split": "held_out"}
  ]
}
```

Balance: both `train` and `held_out` splits must contain both `should_trigger: true` and
`should_trigger: false` entries. Without both labels in a split the audit reports a coverage
error.

Negative queries should be **near-misses** that share domain vocabulary with the skill but need
a different tool. For a PDF extraction skill, a near-miss negative would be "create a PDF"
(creation, not extraction). Avoid obviously irrelevant negatives that the agent would never
confuse.

Hold out roughly 40 percent of the queries (typically 8 of 20); revision isolation for the
held-out split follows `references/evaluation.md`. Run three repetitions per query
so the trigger rate (≥0.5 = pass) is statistically meaningful.

Run fresh sanity queries (not from the training or held-out sets) after every edit to detect
unintended regression.

## Review and run

Render the query set with `assets/eval_review.html` or present it inline when no display is
available. Let the author correct queries before tuning the description. Then run at least three
repetitions per query:

```bash
python -m scripts.skill_eval run ./skill-maker \
  --workspace /tmp/trigger-run --trigger --runs 3 \
  --adapter-arg python3 --adapter-arg /path/to/adapter.py
```

The adapter receives `operation: trigger`, the query, the current description, and a workspace
output directory. It returns `triggered: true` or `false`. A query passes when its trigger rate
is at least 0.5. The evaluator records every repetition and writes `trigger_results.json` with
per-query rates and train/held-out scores.

Use train failures to propose a more specific, slightly pushy description. Re-run both splits,
then select by the held-out score, not the training score. A description should say what the
skill does and when to use it, stay under 1024 characters, avoid keyword stuffing, and pass the
bundled validator's angle-bracket hardening check.

## Human review and fallback

Show the before and after descriptions, the query-level rates, and the held-out score to the
human before applying a winner. Run 5 to 10 fresh sanity queries after the edit. If no adapter
exists, perform the same repetitions manually and save the prompts, outputs, rates, and scores;
do not claim a quantitative comparison from a single session.
