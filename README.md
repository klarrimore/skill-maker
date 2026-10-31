# skill-maker

This repository builds, validates, evaluates, packages, and installs **skill-maker**,
an Agent Skill for creating and improving other portable Agent Skills that follow the
open [agentskills.io](https://agentskills.io) format.

The deliverable lives in `skills/skill-maker/`. Its `SKILL.md`, `requirements.txt`,
`references/`, `scripts/`, `assets/`, and `LICENSE.txt` are the portable skill unit.
The skill's `tests/` and `evals/` trees are development resources: packaging and
installation exclude them.

## Prerequisites

- Python 3.8 or newer
- PyYAML, installed from `skills/skill-maker/requirements.txt`
- Optional: an executable implementing the provider-neutral `skill-eval/v1` adapter
  protocol, needed for task runs, trigger runs, and improvement
- Optional: the `skills-ref` reference validator

Install PyYAML into a virtual environment from the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r skills/skill-maker/requirements.txt
```

Every command below, including the smoke workflow and unit tests, needs PyYAML.
Without it they fail with `ModuleNotFoundError: No module named 'yaml'`.

## Complete workflow

Run the bundled modules from `skills/skill-maker/`. Use `.` for this repository's
skill or replace it with a path to another skill, such as `../my-skill`. Run them as
modules (`python3 -m scripts.<name>`); invoking `python3 scripts/<name>.py` directly
breaks the package-relative imports.

### 1. Validate the skill

Run the reference validator when it is installed, then run the zero-network bundled
validator. Strict mode (default) is required for packaging and installation:

```bash
cd skills/skill-maker
if command -v skills-ref >/dev/null 2>&1; then
  skills-ref validate .
fi
python3 -m scripts.quick_validate .
```

Use import mode for read-only compatibility inspection of an existing client-specific
skill before deciding whether to convert:

```bash
python3 -m scripts.quick_validate ../existing-skill --mode import --json
```

Import mode reports client extensions and name mismatches as warnings, not errors.
A skill must pass strict mode to be packaged or installed. The validator exits `0`
when the skill is valid for the mode, `1` on diagnostic errors, and `2` on usage
errors.

### 2. Audit the evaluation contract

The audit is offline. It validates the skill, typed eval and trigger schemas, fixture
paths, train/held-out coverage, failure-mode mappings, judge calibration, and safety
boundaries:

```bash
python3 -m scripts.skill_eval audit . --workspace /tmp/skill-maker-audit
```

The audit writes `audit.json` to the workspace. Fix error findings before running
model-backed evaluations. Portable-resource warnings are advisory:

| Warning ID | Raised when |
| --- | --- |
| `skill.allowed-tools` | The frontmatter contains the experimental `allowed-tools` pre-approval field. |
| `resource.unaddressed.<path>` | A packaged reference or asset is not named in the `SKILL.md` body. |
| `resource.reference-depth.<path>` | A file sits below `references/<subdir>/`. |
| `resource.dead-pointer.<source>:<path>` | `SKILL.md` or a reference points to a missing `scripts/`, `references/`, or `assets/` path. |
| `resource.missing-toc.<path>` | A long reference has no "Contents" heading near the top. |
| `script.unlisted.<path>` | A bundled script is not named in the `SKILL.md` body. |

### 3. Run paired task evaluations

Configure an explicit adapter command with one `--adapter-arg` per argv element. The
evaluator re-runs the audit first and stops if it fails. It then runs each selected
case with and without the skill and writes request, response, grading, and audit
artifacts under the workspace:

```bash
python3 -m scripts.skill_eval run . \
  --workspace /tmp/skill-run \
  --runs 3 \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

The adapter must implement `skill-eval/v1` (see
[`evaluation.md`](skills/skill-maker/references/evaluation.md#adapter-protocol)).
`--runs` defaults to `1` and `--timeout` (seconds per adapter call) defaults to
`300`. Use `--eval-id ID` (repeatable) or `--split train|held_out` to select task
cases. Command expectations are denied by default; review them before adding
`--allow-command-checks`.

A failing case, including a baseline failure, returns exit code `1` but still
produces a complete paired record; it is evidence, not a missing run.

To exercise the pipeline without a model, run the deterministic development adapter
against the fixture skill that the smoke workflow uses. Expect exit code `1`: the
fixture records baseline failures on purpose. The workspace then holds paired
`runs/` records ready for step 5:

```bash
python3 -m scripts.skill_eval run evals/files/eval-suite-valid \
  --workspace /tmp/skill-run-fake \
  --adapter-arg python3 \
  --adapter-arg tests/fixtures/fake_eval_adapter.py
python3 -m scripts.skill_eval benchmark evals/files/eval-suite-valid \
  --workspace /tmp/skill-run-fake
```

### 4. Check trigger behavior

Trigger evaluation requires at least three repetitions per query, so pass
`--runs 3` or more. A query passes when its trigger rate against a `0.5` threshold
matches its `should_trigger` label:

```bash
python3 -m scripts.skill_eval run . \
  --trigger \
  --runs 3 \
  --workspace /tmp/skill-trigger \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

`--trigger` cannot be combined with `--eval-id` or `--split`. Trigger requests send
the adapter only the query and the skill description; train and held-out labels stay
in the evaluator.

### 5. Benchmark completed runs

Benchmarking reads completed `grading.json` files and does not call an adapter:

```bash
python3 -m scripts.skill_eval benchmark . --workspace /tmp/skill-run
```

This writes `benchmark.json` and `benchmark.md` to the workspace. It rejects missing
pairs, skipped repetitions, duplicate records, and mixed protocols with exit code `2`.
Use `--eval-id`, `--split`, or `--runs` when aggregating an intentional subset.

### 6. Improve in a sandbox

Improvement requires both train and held-out cases plus an explicit adapter. Candidates
are revised in an isolated temporary staging directory, then copied into the workspace
for validation, evaluation, and promotion:

```bash
python3 -m scripts.skill_eval improve . \
  --workspace /tmp/skill-improve \
  --runs 3 \
  --max-iterations 3 \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

Inspect `history.json` and `best-skill/` in the workspace before applying any result.
The source skill is never overwritten. Revision requests receive train failure
evidence only; held-out prompts, labels, results, and scores remain unavailable.
Revision adapters receive paths inside a temporary staging directory outside the
workspace; the stored request persists sanitized `$ISOLATED/...` path placeholders
rather than live filesystem paths. This is not an OS security sandbox.

### 7. Package and install

Package only after validation. The packager validates again, then writes
`<skill-name>.skill` (a zip archive) to the output directory, or the current
directory when none is given:

```bash
python3 -m scripts.package_skill . ../../dist   # -> dist/skill-maker.skill
```

Install to the default user skill directory, `~/.agents/skills`, or use an explicit
target. `--dry-run` reports actions without writing, `--force` replaces an existing
installation, and `--json` emits a machine-readable result:

```bash
python3 -m scripts.install_skill .
python3 -m scripts.install_skill . --target /tmp/skills --dry-run
python3 -m scripts.install_skill . --target /tmp/skills --force
```

Packaging and installation preserve the skill name, exclude the skill's root `tests/`
and `evals/` trees and Python caches, and never search another checkout for missing
skill resources.

### Exit codes

The `skill_eval` subcommands exit `0` on success, `1` when an audit, case, or trigger
query fails, and `2` on configuration errors such as an invalid flag combination or
incomplete grading records. Results and configuration errors are printed as JSON on
stdout; argument-parsing errors print plain usage text. See
[`evaluation.md`](skills/skill-maker/references/evaluation.md#commands-and-exit-codes)
for the full contract.

## Manual fallback

If no non-interactive adapter is available, use the offline audit and validator, then
copy read-only inputs into a workspace, run prompts manually, save outputs and
transcripts, grade deterministic expectations, and present paired results for review.
Do not invent baseline, timing, token, or trigger metrics. See
[`environment-adaptations.md`](skills/skill-maker/references/environment-adaptations.md).

## Repository layout

```text
skill-maker/                          repository workspace
  skills/skill-maker/                 deliverable skill
    SKILL.md                          skill entry point
    requirements.txt                  runtime dependency (PyYAML)
    LICENSE.txt                       Apache-2.0 license
    references/                       authoring, spec, evaluation, and schema guides
    scripts/                          shipped validators, evaluator, package, install tools
    assets/                           review UI template
    tests/                            development-only unit tests and fake adapter
    evals/                            development-only cases, fixtures, and evidence
  scripts/                            repository smoke driver and development tooling
  docs/                               research, issue, and domain documentation
  .agents/                            canonical reusable instructions
  .github/                            per-client instruction forwarders
  AGENTS.md                           repository guidance for agents
  CLAUDE.md                           forwarder to AGENTS.md
  Project_Architecture_Blueprint.md   architecture reference
  README.md                           this workflow
  CHANGELOG.md                        release history
```

## Verify repository changes

From the repository root, with PyYAML installed, run the end-to-end smoke workflow.
It exits non-zero on the first failure and ends with `ALL OK`:

```bash
bash scripts/smoke.sh
```

The smoke workflow covers the validator and its fixtures, the unit tests, the
evaluator audit, paired run, benchmark, and sandboxed improvement, packaging and
installation boundaries, and the review UI. When `google-chrome` is on `PATH`, it
also saves a screenshot of the review UI to `/tmp/eval_review_screenshot.png`;
otherwise it prints `skip screenshot`.

To run only the unit and integration suite:

```bash
cd skills/skill-maker
python3 -m unittest discover -s tests -t .
```

## Further reading

- [`SKILL.md`](skills/skill-maker/SKILL.md): the authored workflow for skill creation.
- [`spec-reference.md`](skills/skill-maker/references/spec-reference.md): frontmatter
  schema, naming rules, and character limits.
- [`spec-provenance.md`](skills/skill-maker/references/spec-provenance.md): which
  rules are spec-mandated, documented, or de facto.
- [`authoring-guide.md`](skills/skill-maker/references/authoring-guide.md): writing
  and progressive-disclosure guidance.
- [`scripts.md`](skills/skill-maker/references/scripts.md): writing bundled scripts.
- [`evaluation.md`](skills/skill-maker/references/evaluation.md): adapter protocol,
  artifacts, grading, benchmarking, and improvement.
- [`schemas.md`](skills/skill-maker/references/schemas.md): versioned JSON contracts.
- [`description-optimization.md`](skills/skill-maker/references/description-optimization.md):
  trigger-query design and selection.
- [`skill-optimization.md`](skills/skill-maker/references/skill-optimization.md):
  post-activation optimization playbook for task quality, context cost, and tool efficiency.
- [`scripts/README.md`](scripts/README.md): repository smoke and development commands.
- [`Project_Architecture_Blueprint.md`](Project_Architecture_Blueprint.md): repository
  architecture reference.

## License

Apache-2.0. See [`skills/skill-maker/LICENSE.txt`](skills/skill-maker/LICENSE.txt).
