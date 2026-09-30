# JSON Schemas

This document defines the JSON schemas used by skill-maker.

---

## evals.json

`evals/evals.json` is version 1 of the repository-native task contract. The
loader in `scripts.eval_models` rejects unknown fields, duplicate ids/names,
empty expectations, missing inputs, and paths that escape the skill root.

```json
{
  "version": 1,
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "name": "csv-summary",
      "split": "held_out",
      "prompt": "Summarize the attached CSV.",
      "expected_output": "A summary report is produced.",
      "files": ["evals/files/sample.csv"],
      "failure_modes": ["FM-2"],
      "expectations": [
        {"kind": "file_exists", "path": "summary.json"},
        {"kind": "json_value", "path": "summary.json", "key": "rows", "equals": 10},
        {"kind": "text_contains", "target": "final", "value": "summary"}
      ]
    }
  ]
}
```

Required case fields are `id`, `name`, `split` (`train` or `held_out`),
`prompt`, `expected_output`, `files`, `failure_modes`, and non-empty typed
`expectations`. Expectation kinds are:

- `file_exists`: output path relative to the run's `outputs/` directory.
- `text_contains` and `text_excludes`: `target` is `final` or `transcript`,
  plus a literal `value`.
- `regex`: `target` plus a Python regular-expression `pattern`.
- `json_value`: output `path`, dotted `key`, and JSON `equals` value.
- `validator`: expected `valid` boolean, optionally with a skill-relative
  `path`.
- `command`: literal `argv`, optional `exit_code` and bounded
  `timeout_seconds`; denied unless `--allow-command-checks` is explicit.
- `judge`: skill-relative `rubric` and expected binary `result` (`pass` or
  `fail`). Judge results do not count as a calibrated benchmark gate until
  `evals/judge_labels.json` has a held-out human label for that rubric.

Input and rubric paths are relative to the skill root. Output paths are
relative to the assigned run output directory. All are containment-checked.

---

## trigger_queries.json

The versioned trigger input uses an object rather than the legacy flat array:

```json
{
  "version": 1,
  "queries": [
    {"query": "turn this workflow into a skill", "should_trigger": true, "split": "train"}
  ]
}
```

Each query has a unique `query`, boolean `should_trigger`, and `split`.
Both labels and both splits are required. Trigger runs use at least three
repetitions and a 0.5 trigger-rate threshold.

---

## judge_labels.json

Human calibration labels are kept separate from prompts and model results:

```json
{
  "version": 1,
  "labels": [
    {
      "rubric": "evals/judges/scope.md",
      "example": "The candidate preserves unrelated behavior.",
      "result": "pass",
      "split": "held_out"
    }
  ]
}
```

`rubric`, `example`, `result`, and `split` are required. A held-out label is
required before a judge expectation can contribute to an improvement gate.

---

## trigger_results.json

The record of a trigger-evaluation run. It is written to the run workspace so
the train/held-out split, per-query trigger rates, and selected score remain
auditable rather than living only in the conversation.

```json
{
  "protocol": "skill-eval/v1",
  "skill_name": "meeting-actions",
  "description": "Turns meeting transcripts into action-item lists.",
  "runs_per_query": 3,
  "threshold": 0.5,
  "runs": [
    {
      "query": "pull the action items out of this transcript",
      "should_trigger": true,
      "split": "train",
      "trigger_rate": 1.0,
      "passed": true
    }
  ],
  "scores": {"train": 0.90, "held_out": 0.85},
  "selected": "current"
}
```

**Fields:**
- `protocol`: `skill-eval/v1`.
- `skill_name`: Name matching the skill's frontmatter.
- `description`: Description evaluated by the adapter.
- `runs_per_query`: How many times each query was run; at least 3.
- `threshold`: Trigger-rate cutoff for a pass (`0.5`).
- `runs[].query` / `runs[].should_trigger`: The eval-set entry.
- `runs[].split`: `"train"` or `"held_out"`.
- `runs[].trigger_rate`: Fraction of repetitions that triggered.
- `runs[].passed`: Whether the observed rate matches the expected label.
- `scores`: Aggregate train and held-out query scores.
- `selected`: Current description selection; candidate revision remains a
  separate operation.

---

## history.json

Tracks version progression in Improve mode. Located at workspace root.

```json
{
  "protocol": "skill-eval/v1",
  "started_at": "2026-09-30T10:30:00+00:00",
  "skill_name": "pdf",
  "current_best": "v1",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "train_score": [0.65, 0.0, -1200.0, -30.0],
      "held_out_score": [0.65, 0.0, -1200.0, -30.0],
      "validation": {"valid": true},
      "audit": {"passed": true},
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "train_score": [0.90, 0.0, -1300.0, -32.0],
      "held_out_score": [0.85, 0.0, -1250.0, -31.0],
      "validation": {"valid": true},
      "audit": {"passed": true},
      "grading_result": "won",
      "is_current_best": true
    }
  ],
  "best_skill": "/tmp/improve/best-skill/pdf"
}
```

**Fields:**
- `started_at`: ISO timestamp of when improvement started
- `skill_name`: Name of the skill being improved
- `current_best`: Version identifier of the best performer
- `iterations[].version`: Version identifier (`v0`, `v1`, ...)
- `iterations[].parent`: Parent version this was derived from
- `iterations[].train_score` / `held_out_score`: ordered score tuples of
  objective pass rate, calibrated judge pass rate, negative token mean, and
  negative duration mean. A missing metric is `null`, not zero, and is skipped
  during score comparison.
- `iterations[].validation` / `iterations[].audit`: candidate checks
- `iterations[].grading_result`: `baseline`, `won`, `lost`, `tie`, or `invalid`
- `iterations[].is_current_best`: Whether this is the current best version
- `best_skill`: Workspace path to the revalidated
  `best-skill/<skill-name>/` copy

---

## grading.json

Output from the `skill-eval/v1` runner. Located at
`<workspace>/runs/<run-id>/grading.json`.

```json
{
  "protocol": "skill-eval/v1",
  "eval_id": 1,
  "eval_name": "csv-summary",
  "split": "held_out",
  "configuration": "with_skill",
  "run_number": 1,
  "status": "passed",
  "expectations": [
    {
      "kind": "file_exists",
      "text": "file_exists: {\"path\": \"summary.json\"}",
      "passed": true,
      "evidence": "summary.json exists"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "pass_rate": 1.0
  },
  "metrics": {
    "duration_ms": 1200,
    "total_tokens": null,
    "tool_calls": null
  },
  "adapter_error": null,
  "artifacts": ["outputs/summary.json"]
}
```

**Fields:**
- `protocol`, `eval_id`, `eval_name`, `split`, `configuration`, and
  `run_number` identify the paired run.
- `expectations[]` contains `kind`, `text`, `passed`, `evidence`, and
  optional `calibrated` for judge results.
- `summary` contains `passed`, `failed`, `total`, and `pass_rate`.
- `metrics` contains `duration_ms`, `total_tokens`, and `tool_calls`; missing
  provider metrics remain `null`, not zero.
- `adapter_error` is explicit when the process or protocol fails.
- `artifacts` lists adapter-reported output paths already checked for
  containment.

The legacy `execution_metrics`, `timing`, claims, notes, and feedback fields
remain acceptable historical evidence in recorded runs but are not required by
the `skill-eval/v1` runner.

---

## metrics.json

Output from the executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**Fields:**
- `tool_calls`: Count per tool type
- `total_tool_calls`: Sum of all tool calls
- `total_steps`: Number of major execution steps
- `files_created`: List of output files created
- `errors_encountered`: Number of errors during execution
- `output_chars`: Total character count of output files
- `transcript_chars`: Character count of transcript

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

**How to capture:** When a subagent task completes, the task notification includes `total_tokens` and `duration_ms`. Save these immediately: they are not persisted anywhere else and cannot be recovered after the fact.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## benchmark.json

Output from Benchmark mode. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "your-executor-model-id",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale",
        "Fell back to text overlay for non-fillable fields"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },

  "notes": [
    "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
    "Eval 3 shows high variance (50% ± 40%) - may be flaky or model-dependent",
    "Without-skill runs consistently fail on table extraction expectations",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

**Fields:**
- `metadata`: Skill path, timestamp, selected eval IDs, and repetitions.
- `runs[]`: Individual grading records. `configuration` is exactly
  `"with_skill"` or `"without_skill"`, and `result` contains `pass_rate`,
  `passed`, `failed`, `total`, `time_seconds`, `tokens`, `tool_calls`, and
  `errors`. The original `expectations` and evidence remain alongside it.
- `run_summary`: Statistical aggregates per configuration. Each configuration
  contains `pass_rate`, `objective_pass_rate`, `calibrated_judge_pass_rate`,
  `time_seconds`, and `tokens`, each with mean, standard deviation, minimum,
  and maximum where metrics exist.
- `run_summary.delta` and `deltas`: With-skill-minus-baseline pass-rate,
  time, and token differences.
- `diagnostics`: Explicit adapter failures, non-discriminating or
  uncalibrated judges, high variance, missing metrics, absent quality gain,
  and cost growth without quality gain.
- `notes`: Human-readable interpretation notes.

Benchmark aggregation is deterministic and refuses incomplete configuration
pairs, partial repetitions, and mixed protocol versions. Judge-derived scores
remain separate from objective scores until calibrated.

**Important:** Consumers should use the exact `configuration`, `result`, and
`run_summary` field names. `configurations` and `deltas` are retained as
machine-readable aliases for the evaluator's richer report.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A provides a complete solution with proper formatting and all required fields. Output B is missing the date field and has formatting inconsistencies.",
  "rubric": {
    "A": {
      "content": {
        "correctness": 5,
        "completeness": 5,
        "accuracy": 4
      },
      "structure": {
        "organization": 4,
        "formatting": 5,
        "usability": 4
      },
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": {
        "correctness": 3,
        "completeness": 2,
        "accuracy": 3
      },
      "structure": {
        "organization": 3,
        "formatting": 2,
        "usability": 3
      },
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["Complete solution", "Well-formatted", "All fields present"],
      "weaknesses": ["Minor style inconsistency in header"]
    },
    "B": {
      "score": 5,
      "strengths": ["Readable output", "Correct basic structure"],
      "weaknesses": ["Missing date field", "Formatting inconsistencies", "Partial data extraction"]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    },
    "B": {
      "passed": 3,
      "total": 5,
      "pass_rate": 0.60,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    }
  }
}
```

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "Brief summary of why comparator chose winner"
  },
  "winner_strengths": [
    "Clear step-by-step instructions for handling multi-page documents",
    "Included validation script that caught formatting errors"
  ],
  "loser_weaknesses": [
    "Vague instruction 'process the document appropriately' led to inconsistent behavior",
    "No script for validation, agent had to improvise"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": ["Minor: skipped optional logging step"]
    },
    "loser": {
      "score": 6,
      "issues": [
        "Did not use the skill's formatting template",
        "Invented own approach instead of following step 3"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace 'process the document appropriately' with explicit steps",
      "expected_impact": "Would eliminate ambiguity that caused inconsistent behavior"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read skill -> Followed 5-step process -> Used validation script",
    "loser_execution_pattern": "Read skill -> Unclear on approach -> Tried 3 different methods"
  }
}
```
