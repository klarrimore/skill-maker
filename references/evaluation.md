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

1. Grade each run by hand. Evaluate each assertion against the outputs and save
   `grading.json` in each run directory. Grade strictly against the assertion text, cite the
   specific evidence in the output that makes each pass or fail, and do not give credit for
   near-misses or intentions. The `grading.json` expectations array must use the fields
   `text`, `passed`, and `evidence` exactly. For assertions checkable programmatically, write
   and run a script instead of eyeballing.
2. Aggregate into a benchmark. Build `benchmark.json` (and a readable `benchmark.md` summary)
   by hand following `schemas.md` exactly. Report pass rate, time, and tokens per
   configuration (mean and stddev) plus the with-skill-minus-baseline delta. Place each
   with_skill entry before its baseline counterpart.
3. Do an analyst pass. Read the benchmark and surface what the aggregates hide:
   non-discriminating assertions (pass regardless of skill, so they tell you nothing),
   high-variance evals (possibly flaky, rerun before trusting), and time/token tradeoffs
   (a small quality gain that doubles cost may not be worth it).
4. Present the outputs to the user for review before you critique them yourself. Show each
   case in the conversation: the prompt, the with-skill output, and the baseline output side
   by side, plus the per-case pass rates from the benchmark. If an output is a file the user
   must open (a `.docx`, an `.xlsx`, a chart), save it to the workspace and tell them the
   path. Ask for feedback inline ("How does each look? Anything you would change?").
5. Get the examples in front of the human first; do not start rewriting from your own
   read of the outputs before the user has weighed in.

## Step 5: Read the feedback

Gather feedback inline as the user responds, one case at a time. Empty or "looks fine"
responses mean that case is good; focus on the cases with specific complaints, and restate
each complaint as the underlying problem before you act on it.

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
3. Present the new outputs against the prior iteration's so the user can see what changed.
4. Wait for review, read the new feedback, improve again.

Stop when the user is happy, the feedback is all empty, or you are no longer making
meaningful progress.

## Advanced: blind comparison (optional, needs subagents)

For a rigorous "is the new version actually better?" check, give two outputs to a separate
agent instance without telling it which is which, let it judge against the assertions, then
analyze why the winner won. Randomize which output is presented first so position does not
bias the judgment, and have the judge cite specific evidence. Most skills do not need this;
the human review loop is usually enough.
