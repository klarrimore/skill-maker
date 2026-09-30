# skill-maker

This repository builds, validates, evaluates, packages, and installs **skill-maker**,
an Agent Skill for creating and improving other portable Agent Skills that follow the
open [agentskills.io](https://agentskills.io) format.

The deliverable lives in `skills/skill-maker/`. Its `SKILL.md`, `requirements.txt`,
`references/`, `scripts/`, `assets/`, and `LICENSE.txt` are the portable skill unit.
The repository's `tests/` and `evals/` trees are development resources: packaging and
installation exclude them.

## Prerequisites

- Python 3.8 or newer
- PyYAML, installed from `skills/skill-maker/requirements.txt`
- An optional executable implementing the provider-neutral `skill-eval/v1` adapter
  protocol for task runs, trigger runs, and improvement

## Complete workflow

Run the bundled modules from `skills/skill-maker/`. Use `.` for this repository's
skill or replace it with a path to another skill, such as `../my-skill`.

### 1. Validate the skill

Run the reference validator when it is installed, then run the zero-network bundled
validator:

```bash
cd skills/skill-maker
if command -v skills-ref >/dev/null 2>&1; then
  skills-ref validate .
fi
python3 -m scripts.quick_validate .
```

Fix validation errors before packaging or evaluation. Body-size and portability
warnings are reported separately so you can make an explicit tradeoff.

### 2. Audit the evaluation contract

The audit is offline. It validates the skill, typed eval and trigger schemas, fixture
paths, train/held-out coverage, failure-mode mappings, judge calibration, and safety
boundaries:

```bash
python3 -m scripts.skill_eval audit . --workspace /tmp/skill-maker-audit
```

Review `audit.json` and fix error findings before running model-backed evaluations.

### 3. Run paired task evaluations

Configure an explicit adapter command. The evaluator runs each selected case with
and without the skill and writes request, response, grading, and audit artifacts under
the workspace:

```bash
python3 -m scripts.skill_eval run . \
  --workspace /tmp/skill-run \
  --runs 3 \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

The adapter must implement `skill-eval/v1`. A baseline failure returns exit code `1`
but still produces a complete paired record; it is evidence, not a missing run.
Use `--eval-id ID` or `--split train|held_out` to select task cases. Command
expectations are denied by default; explicitly review them before adding
`--allow-command-checks`.

### 4. Check trigger behavior

Trigger evaluation requires at least three repetitions per query and uses a `0.5`
trigger-rate threshold:

```bash
python3 -m scripts.skill_eval run . \
  --trigger \
  --runs 3 \
  --workspace /tmp/skill-trigger \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

Held-out trigger labels are used for selection, not exposed to the adapter.

### 5. Benchmark completed runs

Benchmarking reads completed `grading.json` files and does not call an adapter:

```bash
python3 -m scripts.skill_eval benchmark . --workspace /tmp/skill-run
```

This writes `benchmark.json` and `benchmark.md`. It rejects missing pairs, skipped
repetitions, duplicate records, and mixed protocols. Use `--eval-id`, `--split`, or
`--runs` when aggregating an intentional subset.

### 6. Improve in a sandbox

Improvement requires both train and held-out cases plus an explicit adapter. Candidates
are revised, validated, evaluated, and promoted only inside the workspace:

```bash
python3 -m scripts.skill_eval improve . \
  --workspace /tmp/skill-improve \
  --runs 3 \
  --max-iterations 3 \
  --adapter-arg python3 \
  --adapter-arg /path/to/skill-eval-adapter.py
```

Inspect `history.json` and `best-skill/` before applying any result. The source skill
is never overwritten. Revision requests receive train failure evidence only; held-out
prompts, labels, results, and scores remain unavailable. Missing token or duration
metrics remain unavailable rather than being treated as zero.

### 7. Package and install

Package only after validation:

```bash
python3 -m scripts.package_skill . ../../dist
```

Install to the default user skill directory, or use an explicit target:

```bash
python3 -m scripts.install_skill .
python3 -m scripts.install_skill . --target /tmp/skills --dry-run
python3 -m scripts.install_skill . --target /tmp/skills --force
```

The installer preserves the skill name, removes root `tests/` and `evals/`, and
never searches another checkout for missing skill resources. Run all commands as
modules from `skills/skill-maker/`; invoking `python3 scripts/<name>.py` directly
breaks the package-relative imports.

## Manual fallback

If no non-interactive adapter is available, use the offline audit and validator, then
copy read-only inputs into a workspace, run prompts manually, save outputs and
transcripts, grade deterministic expectations, and present paired results for review.
Do not invent baseline, timing, token, or trigger metrics. See
`skills/skill-maker/references/environment-adaptations.md`.

## Repository layout

```text
skill-maker/                         repository workspace
  skills/skill-maker/                deliverable skill
    SKILL.md                          skill entry point
    references/                       authoring, evaluation, and schema guides
    scripts/                          shipped validators, evaluator, package, install tools
    assets/                           review UI template
    tests/                            development-only unit tests
    evals/                            development-only cases, fixtures, and evidence
  scripts/                            repository smoke driver and development tooling
  docs/                               research, issue, and domain documentation
  .agents/                            canonical reusable instructions
  AGENTS.md                           repository guidance
  README.md                           this workflow
  CHANGELOG.md                        release history
```

## Verify repository changes

From the repository root, run the end-to-end smoke workflow:

```bash
bash scripts/smoke.sh
```

For the unit and integration suite:

```bash
cd skills/skill-maker
python3 -m unittest discover -s tests -t .
```

The smoke workflow also verifies packaging and installation boundaries, source
immutability, evaluator-script inclusion, and the review UI. A screenshot is optional
when a headless Chrome or Chromium executable is available.

## Further reading

- [`SKILL.md`](skills/skill-maker/SKILL.md): the authored workflow for skill creation.
- [`evaluation.md`](skills/skill-maker/references/evaluation.md): adapter protocol,
  artifacts, grading, benchmarking, and improvement.
- [`schemas.md`](skills/skill-maker/references/schemas.md): versioned JSON contracts.
- [`authoring-guide.md`](skills/skill-maker/references/authoring-guide.md): writing
  and progressive-disclosure guidance.
- [`description-optimization.md`](skills/skill-maker/references/description-optimization.md):
  trigger-query design and selection.
- [`scripts/README.md`](scripts/README.md): repository smoke and development commands.
- [`Project_Architecture_Blueprint.md`](Project_Architecture_Blueprint.md): repository
  architecture reference.

## License

Apache-2.0. See [`skills/skill-maker/LICENSE.txt`](skills/skill-maker/LICENSE.txt).
