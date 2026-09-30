# Environment Adaptations

The evaluation contract is constant. Adapt execution to available capabilities without inventing
measurements or weakening the safety boundary.

## No non-interactive agent command

Use the manual path: copy each input into a workspace, read the skill, run the prompt, save the
final output and transcript, grade deterministic expectations, and show paired results to the
human. Skip baseline benchmarking when there is no independent baseline. Do not send a revision
request or promote a candidate without an adapter that can actually write a workspace-owned
candidate.

## No subagents

Run cases one at a time, but preserve the same `with_skill`/baseline pairing and run metadata.
Do not call a sequential run a parallel comparison. Human review compensates for the missing
independent agents.

## No display

Write `benchmark.md`, outputs, and the rendered trigger-review HTML to the workspace. Present the
paths and query/output summaries for review. Do not skip human review because a browser is absent.

## Packaging and installation

`quick_validate`, `package_skill`, `install_skill`, `eval_models`, `eval_adapter`, `eval_store`,
and `skill_eval` require Python 3.8+ and the existing PyYAML dependency. Packaging and installing
a target skill still strips that target's root `tests/` and `evals/`; the shipped evaluator
modules under `scripts/` remain available. Evaluation workspaces and adapter commands are
source-development concerns and are never copied into the target artifact.

## Read-only installed skills

Never point an adapter output or revision destination at an installed skill. Copy it to a
workspace-owned candidate whose directory keeps the original skill name, validate there, and
promote only a copied winner. The original directory remains byte-identical.

## Command checks and least privilege

Command expectations are denied unless the operator passes `--allow-command-checks`. When enabled,
the evaluator uses only the literal validated argv, `shell=False`, a bounded timeout, a minimal
`PATH` environment, and the output folder as cwd. Every allow or deny decision is recorded in
metadata-only `audit.jsonl`.

## One rule everywhere

Get outputs in front of the human before criticizing or rewriting the skill. If a capability is
missing, record the fallback and the evidence that actually exists rather than manufacturing a
pass rate, timing, token count, or trigger result.
