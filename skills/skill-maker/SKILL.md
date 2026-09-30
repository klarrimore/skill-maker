---
name: skill-maker
description: Use this skill whenever the user wants to author a skill from scratch, turn a workflow or repeated task into a reusable skill, edit or refactor an existing skill, make a skill spec-compliant or portable, test or benchmark a skill, or optimize a skill description for better triggering, even if they do not say the word "skill" explicitly.
license: Apache-2.0
compatibility: Portable across any skills-compatible agent that reads the agentskills.io format. Bundled validation and packaging scripts require Python 3.8+ and PyYAML.
metadata:
  author: klarrimore
  standard: agentskills.io
  version: "1.10"
---

# Skill Maker

Create and improve portable Agent Skills. A skill is a directory containing
`SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. Keep the
portable artifact self-contained. Resolve bundled paths relative to this skill's
own root. Do not search another checkout for missing skill resources.

## Core loop

1. Capture the workflow, trigger conditions, output format, dependencies, edge cases,
   and whether objective test cases are useful.
2. Research real artifacts such as runbooks, schemas, API documentation, examples,
   and failure reports. Prefer observed expertise over generic procedure.
3. Draft the skill with progressive disclosure. Keep the body under 500 lines and
   roughly 5000 tokens. Move detailed domain material into focused references.
4. Show 2 or 3 realistic prompts to the author, then save approved cases in
   `evals/evals.json`.
5. Evaluate before rewriting:
   ```bash
   python -m scripts.skill_eval audit <skill> --workspace <workspace>
   python -m scripts.skill_eval run <skill> --workspace <workspace> \
     --adapter-arg <executable> --adapter-arg <argument>
   python -m scripts.skill_eval benchmark <skill> --workspace <workspace>
   ```
   Inspect transcripts and artifacts and show outputs to the author. If no explicit
   adapter exists, use the manual fallback in `references/evaluation.md` and do not
   invent model metrics.
6. Tune triggering with balanced train and held-out queries:
   ```bash
   python -m scripts.skill_eval run <skill> --trigger --runs 3 \
     --workspace <workspace> --adapter-arg <executable>
   ```
   Select by held-out results, not training results.
7. Validate before delivery:
   ```bash
   skills-ref validate <skill>
   python -m scripts.quick_validate <skill>
   ```
   The bundled validator is the zero-network fallback. Fix non-zero results; weigh
   body-budget warnings as explicit portability tradeoffs.
8. Package or install only after validation:
   ```bash
   python -m scripts.package_skill <skill> <dist>
   python -m scripts.install_skill <skill> [--target <skills-dir>] [--force]
   ```

## Authoring rules

Read `references/spec-reference.md` before changing frontmatter and
`references/authoring-guide.md` before drafting the body. Use only the six
portable frontmatter fields. `name` must be kebab-case and match the directory.
`description` must say what the skill does and when to use it. Write imperative,
specific instructions and explain why important steps exist. Avoid hidden access,
data exfiltration, misleading descriptions, and client-specific assumptions.
Use a comma, period, colon, or parentheses instead of U+2014.

For an existing or installed skill, preserve its name, copy it to a writable
workspace, make the smallest justified change, and revalidate the copy. Never
modify source fixtures or an installed read-only directory.

## Evaluation and improvement

The shipped evaluator uses the `skill-eval/v1` command adapter. It runs deterministic
expectations locally, sends only `judge` expectations to the adapter, and records
paired with-skill and baseline results. Command expectations are denied unless
`--allow-command-checks` is explicit. They use literal argv, `shell=False`, a bounded
timeout, a minimal environment, and a run output directory as cwd.

Use `improve` only for a sandboxed candidate loop:
```bash
python -m scripts.skill_eval improve <skill> --workspace <workspace> \
  --max-iterations 3 --adapter-arg <executable> --adapter-arg <argument>
```
Candidates and `best-skill/<name>/` stay under the workspace. Held-out prompts,
labels, results, and scores are not sent to revision requests. Promotion requires
a strict held-out improvement, then calibrated judge rate, lower token mean, and
lower duration mean. Unavailable metrics remain unavailable. Review the candidate
outputs before applying any result to the source skill.

Read `references/evaluation.md` for the adapter contract, workspace artifacts,
exit codes, benchmark diagnostics, and manual fallback. Read
`references/description-optimization.md` for trigger tuning and
`references/environment-adaptations.md` when capabilities are limited.

## Bundled resources

- `references/spec-reference.md`: portable frontmatter and body rules.
- `references/authoring-guide.md`: anatomy, style, and progressive disclosure.
- `references/evaluation.md`: audit, run, benchmark, improve, and manual workflows.
- `references/schemas.md`: versioned eval, grading, benchmark, and history contracts.
- `references/description-optimization.md`: trigger-query design and selection.
- `references/environment-adaptations.md`: no-adapter, no-display, and packaging fallbacks.
- `scripts/quick_validate.py`: zero-network validator.
- `scripts/eval_models.py`: strict eval, trigger, and calibration loaders.
- `scripts/eval_adapter.py`: provider-neutral command adapter.
- `scripts/eval_store.py`: atomic artifacts and redacted append-only audit metadata.
- `scripts/skill_eval.py`: `audit`, `run`, `benchmark`, and `improve` CLI.
- `scripts/package_skill.py` and `scripts/install_skill.py`: distribution helpers.
