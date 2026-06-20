# Evaluating and Improving a Skill

The full workflow for running test cases, getting outputs in front of the user, grading,
benchmarking, and improving the skill. This is one continuous sequence; do not stop
partway through, and do not delegate to a separate testing skill.

This workflow is richest when your environment has subagents and a display. If it does
not, read `environment-adaptations.md` first and substitute the manual path; the structure
below still applies.

## Workspace layout

Put results in `<skill-name>-workspace/` as a sibling of the skill directory. Within it,
organize by iteration (`iteration-1/`, `iteration-2/`, ...), and within each iteration give
each test case its own directory named for what it tests (not just `eval-0/`). Create
directories as you go, not all upfront.

## Step 1: Spawn all runs in the same turn

For each test case, run two configurations in the same turn: one with the skill, one
baseline. Launch everything at once so the runs finish together; do not run all the
with-skill cases first and circle back for baselines.

With-skill run brief:

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files, or "none">
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/with_skill/outputs/
- Outputs to save: <what the user cares about, e.g. "the .docx", "the final CSV">
```

Baseline run, same prompt, baseline depends on context:
- Creating a new skill: no skill at all. Save to `without_skill/outputs/`.
- Improving an existing skill: the old version. Snapshot first
  (`cp -r <skill-path> <workspace>/skill-snapshot/`), point the baseline at the snapshot,
  save to `old_skill/outputs/`.

Write an `eval_metadata.json` per test case (assertions can start empty), schema in
`schemas.md`:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

If an iteration uses new or changed prompts, recreate these files; do not assume they
carry over.

## Step 2: While runs are in progress, draft assertions

Do not idle while runs execute. Draft objectively verifiable assertions with descriptive
names that read clearly in the review view, and explain each to the user. Subjective
skills (writing voice, design quality) are better judged qualitatively; do not force
assertions onto things that need human judgment. Update the `eval_metadata.json` files and
`evals/evals.json` once drafted, and tell the user what they will see: both the
qualitative outputs and the quantitative benchmark.

## Step 3: Capture timing as runs complete

If your runtime reports `total_tokens` and `duration_ms` when a run finishes, save them
immediately to `timing.json` in that run directory; this data is not persisted anywhere
else. Process each notification as it arrives rather than batching.

```json
{ "total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3 }
```

## Step 4: Grade, aggregate, review

1. Grade each run. Read `agents/grader.md` and evaluate each assertion against the
   outputs; save `grading.json` in each run directory. The `grading.json` expectations
   array must use the fields `text`, `passed`, and `evidence` exactly; the viewer depends
   on those names. For assertions checkable programmatically, write and run a script
   instead of eyeballing.
2. Aggregate into a benchmark from the skill root:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass rate, time, and tokens per
   configuration (mean and stddev) plus the delta. Place each with_skill entry before its
   baseline counterpart. If generating `benchmark.json` by hand, follow `schemas.md`
   exactly; the viewer reads those field names literally.
3. Do an analyst pass. Read the benchmark and surface what the aggregates hide:
   non-discriminating assertions (pass regardless of skill), high-variance evals (possibly
   flaky), and time/token tradeoffs. See the "Analyzing Benchmark Results" section of
   `agents/analyzer.md`.
4. Launch the review view with `eval-viewer/generate_review.py` (do not hand-roll HTML):
   ```bash
   nohup python <skill-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "<name>" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2 and later, also pass `--previous-workspace <workspace>/iteration-<N-1>`.
   In a headless environment, use `--static <output_path>` to write a standalone HTML file
   and hand the user a link instead of starting a server.
5. Tell the user where to look: the "Outputs" tab to click through each case and leave
   feedback, the "Benchmark" tab for the quantitative comparison, then "Submit All Reviews"
   when done.

Generate the review view before you start critiquing outputs yourself. Get the examples in
front of the human first.

## Step 5: Read the feedback

When the user is done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels"},
    {"run_id": "eval-1-with_skill", "feedback": ""}
  ],
  "status": "complete"
}
```

Empty feedback means it was fine. Focus on the cases with specific complaints. Kill the
viewer server when done: `kill $VIEWER_PID 2>/dev/null`.

## Improving the skill

This is the heart of the loop. Four ways to think about a change:

1. Generalize from the feedback. You and the user iterate on a few examples because it is
   fast, but the skill has to work on a million prompts you will never see. Resist fiddly
   overfit changes and oppressive MUSTs. If an issue is stubborn, try a different metaphor
   or a different working pattern; it is cheap to try.
2. Keep the prompt lean. Read the transcripts, not just the outputs. If the skill is
   making the agent waste time on something unproductive, cut the part causing it and see
   what happens.
3. Explain the why. Get into the user's head, understand the task behind even a terse or
   frustrated comment, and transmit that understanding into the instructions. Reasoning
   beats rigid structure.
4. Look for repeated work across cases. If every run independently wrote a similar helper
   (a `create_docx.py`, a `build_chart.py`), that is a strong signal to write it once, put
   it in `scripts/`, and have the skill call it.

Take your time on this; thinking is not the blocker. Draft a revision, look at it anew,
improve it.

### The iteration loop

1. Apply the improvements.
2. Rerun all test cases into `iteration-<N+1>/`, including baselines. For a new skill the
   baseline stays `without_skill`. For an existing skill, use judgment: the original the
   user arrived with, or the previous iteration.
3. Launch the viewer with `--previous-workspace` pointing at the prior iteration.
4. Wait for review, read the new feedback, improve again.

Stop when the user is happy, the feedback is all empty, or you are no longer making
meaningful progress.

## Advanced: blind comparison (optional, needs subagents)

For a rigorous "is the new version actually better?" check, give two outputs to an
independent agent without telling it which is which and let it judge, then analyze why the
winner won. Read `agents/comparator.md` and `agents/analyzer.md`. Most skills do not need
this; the human review loop is usually enough.
