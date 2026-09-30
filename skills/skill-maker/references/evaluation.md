# Evaluating and Improving a Skill

The bundled evaluator keeps deterministic checks offline and delegates model execution to an
explicit provider-neutral command. It supports paired task runs, trigger runs, benchmarks, and
sandboxed candidate improvement. Human review remains part of the loop: inspect outputs before
rewriting instructions.

## Commands and exit codes

Run from the skill root, where `scripts.*` imports resolve:

```bash
python -m scripts.skill_eval audit ./target-skill --workspace /tmp/skill-audit
python -m scripts.skill_eval run ./target-skill --workspace /tmp/skill-run \
  --runs 3 --adapter-arg python3 --adapter-arg /path/to/agent-adapter.py
python -m scripts.skill_eval run ./target-skill --workspace /tmp/trigger-run \
  --trigger --runs 3 --adapter-arg python3 --adapter-arg /path/to/agent-adapter.py
python -m scripts.skill_eval benchmark ./target-skill --workspace /tmp/skill-run
python -m scripts.skill_eval improve ./target-skill --workspace /tmp/skill-improve \
  --max-iterations 3 --adapter-arg python3 --adapter-arg /path/to/agent-adapter.py
```

The CLI emits one JSON result on stdout. Diagnostics belong on stderr. Exit codes are:

- `0`: the requested operation completed without an error gate;
- `1`: the operation completed but an audit, expectation, trigger, or benchmark error failed;
- `2`: usage, schema, path, adapter configuration, timeout, or other safety configuration error.

`run` returns `1` when a baseline fails an expectation. That is evidence, not a missing row. A
run record is written for every case/configuration/repetition, including adapter failures.

## Evaluation contract

Read `references/schemas.md` for the version 1 JSON contract. Before any adapter starts, the
loader validates typed expectations, input and rubric paths, train/held-out coverage, failure
mode mappings, trigger labels, and duplicate identifiers. Keep objective artifact checks in
code. Use a binary judge only for transcript-dependent quality, and calibrate it with held-out
human labels in `evals/judge_labels.json` before using it as a promotion gate.

A `command` expectation is high impact and is denied by default. Review the literal argv and opt
in explicitly:

```bash
python -m scripts.skill_eval run ./target-skill --workspace /tmp/run \
  --allow-command-checks --adapter-arg python3 --adapter-arg /path/to/adapter.py
```

Commands use `shell=False`, a bounded timeout, a minimal environment, and the run output folder
as their working directory. Shell strings, wildcard discovery, inherited credentials, and paths
outside the workspace are not accepted. Every allow or deny decision is recorded in metadata-only
`audit.jsonl`; prompts, transcripts, rubric contents, credentials, and environment variables are
not copied into that log.

## Adapter protocol

The adapter receives exactly one JSON object on stdin and must emit exactly one JSON object on
stdout. Stderr is bounded diagnostics. The protocol is `skill-eval/v1`:

```json
{
  "protocol": "skill-eval/v1",
  "operation": "task",
  "run_id": "1-with_skill-1",
  "skill_path": "/workspace/skill",
  "configuration": "with_skill",
  "prompt": "the eval prompt",
  "input_files": ["/workspace/run/inputs/source.txt"],
  "output_dir": "/workspace/run/outputs"
}
```

The operation is `task`, `trigger`, `judge`, or `revise`. A successful response has `status`
`ok`, optional `final` and `transcript`, a contained `files` list, and optional `metrics` with
`duration_ms`, `total_tokens`, and `tool_calls`. An error response has `status` `error` and a
non-empty `error`. Malformed JSON, multiple JSON values, nonzero exit, timeouts, and escaping
artifact paths are explicit failures, never fabricated successes.

For a trigger request, return a boolean `triggered`. The evaluator runs every query at least
three times and passes it when the trigger rate is at least 0.5. Revise requests contain only
train failure evidence and a workspace-owned candidate destination. Held-out prompts, labels,
results, and scores are not sent to `revise`.

## Workspace and evidence

The evaluator creates this shape:

```text
workspace/
├── audit.json
├── audit.jsonl
├── runs/<eval-id>-<configuration>-<run-number>/
│   ├── inputs/                 # copied, immutable source inputs
│   ├── outputs/                # adapter artifacts
│   ├── request.json
│   ├── response.json
│   └── grading.json
├── benchmark.json
├── benchmark.md
└── history.json                # improve mode
```

The store writes JSON atomically and appends audit metadata. Source skills and source fixtures
are never used as adapter output directories. Copy a read-only input into a workspace before
editing it.

## Paired task evaluation

1. Run `audit` first and fix error findings. Warnings are visible tradeoffs, not silent passes.
2. Select ordinary task evals. Keep eval 3, the description trigger case, separate from routine
   task regressions when its cost is not justified.
3. Run the same prompt and input files with `with_skill` and `without_skill`, interleaved by
   case and repetition number. The baseline can be no skill or a snapshot of the old skill.
4. Grade deterministic expectations from output artifacts and final/transcript text. Send only
   judge expectations to a judge operation.
5. Present the paired outputs to the human before critiquing or changing the skill.

`benchmark` consumes completed `grading.json` records only. It refuses missing configuration
pairs, mixed protocol versions, and partial repetitions. It reports pass-rate, duration, and
token mean, standard deviation, minimum, maximum, and with-skill-minus-baseline deltas. It also
flags non-discriminating checks, high variance, missing metrics, adapter failures, uncalibrated
judges, absent quality gain, and cost growth without quality gain.

## Sandboxed improvement

`improve` requires a clean audit, at least one train case, at least one held-out case, and an
adapter. It copies the source into `workspace/candidates/v0/<skill-name>/`. For each iteration it:

1. runs the current candidate on train and held-out cases;
2. sends only failed train expectations and cited artifact metadata to `revise`;
3. stages a fresh `candidates/vN/<skill-name>/` copy under the workspace;
4. validates and audits the candidate before running it;
5. evaluates valid candidates against the same baseline and held-out cases;
6. promotes only a strict winner by this ordered score: held-out objective pass rate, calibrated
   judge pass rate, lower mean tokens, then lower mean duration. Ties retain the incumbent;
7. records parentage, scores, validation, audit, and `grading_result` (`baseline`, `won`, `lost`,
   `tie`, or `invalid`) in `history.json`.

The final artifact is copied to `workspace/best-skill/<skill-name>/` so its frontmatter name and
parent directory remain valid. It is revalidated before returning. Promotion does not install,
rename, or overwrite the original source skill.

## Manual fallback

If no non-interactive agent command exists, use the same contract by hand: copy inputs, read the
skill, run each prompt one at a time, save outputs and transcripts, grade deterministic checks,
and show the results for review. Do not invent baseline or benchmark numbers without an
independent baseline. If no display exists, write `benchmark.md` and the review HTML to the
workspace and provide the paths for human inspection. A model adapter is optional; audit,
validation, packaging, and artifact grading remain offline.
