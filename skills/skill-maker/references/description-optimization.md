# Optimizing the Description for Triggering

The `description` field is the primary mechanism an agent uses to decide whether to load a
skill. Tune it with realistic queries, balanced near misses, repeated trigger measurements,
and held-out selection. The evaluator keeps this loop separate from ordinary task evals.

## Build the query set

Store about 20 unique records in `evals/trigger_queries.json` using the versioned object shape:

```json
{
  "version": 1,
  "queries": [
    {"query": "turn this workflow into a reusable skill", "should_trigger": true, "split": "train"},
    {"query": "review this pull request", "should_trigger": false, "split": "held_out"}
  ]
}
```

Use both labels in both splits. Positive cases should include indirect wording where the user
does not name the skill. Negative cases should be domain-adjacent near misses that share terms
but need another tool. Avoid obviously irrelevant negatives. Hold out roughly 40 percent of the
queries and do not expose their labels or results to a revision adapter.

## Review and run

Render the query set with `scripts/render_review.py` or present it inline when no display is
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
