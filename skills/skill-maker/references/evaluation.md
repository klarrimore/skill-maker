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
- `1`: the operation completed but an audit, expectation, trigger, benchmark, or candidate
  validation error failed;
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

Expected outputs and trigger labels remain evaluator-only. They are not included in
`task` or `trigger` requests, which prevents an adapter from passing by reading the
answer key.

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
2. Select ordinary task evals. Keep trigger evals separate from routine task regressions when
   their cost is not justified.
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

Use `benchmark --eval-id`, `--split`, and `--runs` when aggregating a deliberate
subset. Without selectors, every eval in the suite and every contiguous repetition
from 1 through the highest observed run must be present. Missing pairs, skipped
repetitions, duplicate records, and records from another protocol are configuration
errors. Missing provider metrics remain `null` and are skipped by candidate ranking,
never treated as zero.

Revision adapters receive a portable copy of the current candidate without its
`evals/` or `tests/` trees. The evaluator restores the source-controlled eval suite
to the candidate only after revision, so held-out prompts, labels, and results are
not exposed through the revision source path.

## Sandboxed improvement

The optimization playbook (`references/skill-optimization.md`) supplies candidate hypotheses;
this file remains authoritative for execution, isolation, and promotion. The `improve` loop
below remains sequential and does not itself implement population search, model routing, or
multi-agent critique.

`improve` requires a clean audit, at least one train case, at least one held-out case, and an
adapter. It copies the source into `workspace/candidates/v0/<skill-name>/`. For each iteration it:

1. runs the current candidate on train and held-out cases;
2. sends only failed train expectations and cited artifact metadata to `revise`;
3. creates a system temporary directory outside the evaluator workspace as an isolated staging
   root, copies only the portable candidate into it, and provides the adapter with paths inside
   this isolated root. Workspace markers (grading.json, history.json, benchmark.json, evals/,
   tests/) are unreachable by walking ancestors from the provided paths. If the temporary
   directory resolves inside the workspace (e.g. via TMPDIR pointing there), the operation fails
   as a configuration error rather than silently falling back to persistent workspace paths.
4. after a successful revision, copies the isolated candidate into
   `workspace/candidates/vN/<skill-name>/`, attaches the source-controlled `evals/` tree, then
   validates and audits the candidate before running it;
5. promotes only a strict winner by this ordered score: held-out objective pass rate, calibrated
   judge pass rate, lower mean tokens, then lower mean duration. Ties retain the incumbent;
6. persists a sanitized revision request with `$ISOLATED/...` path placeholders instead of live
   temporary or persistent filesystem paths;
7. records parentage, scores, validation, audit, and `grading_result` (`baseline`, `won`, `lost`,
   `tie`, or `invalid`) in `history.json`.

The temporary staging prevents an adapter from discovering the workspace by walking ancestors.
This is not an OS-level security sandbox; a determined adapter that independently scans arbitrary
filesystem roots is not blocked by this isolation layer.

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
