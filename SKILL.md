---
name: skill-maker
description: Create new agent skills, modify and improve existing ones, and measure skill performance, following the open agentskills.io standard for cross-platform portability. Use this skill whenever the user wants to author a skill from scratch, turn a workflow or repeated task into a reusable skill, edit or refactor an existing skill, make a skill spec-compliant or portable, validate SKILL.md frontmatter, test or benchmark a skill, or optimize a skill description for better triggering, even if they do not say the word "skill" explicitly.
license: Apache-2.0
compatibility: Portable across any skills-compatible agent that reads the agentskills.io format. Bundled validation and packaging scripts require Python 3.8+ and PyYAML. The optional automated evaluation and description-optimization scripts additionally require subagent support and a claude-style CLI; the manual workflow they automate runs in any environment.
metadata:
  author: klarrimore
  based-on: anthropics-skills-skill-creator
  standard: agentskills.io
  spec-revision: "2025-12-18"
  version: "1.1"
---

# Skill Maker

Create new skills and iteratively improve them, conforming to the open Agent Skills
standard (agentskills.io). A skill is a folder containing a `SKILL.md` file (YAML
frontmatter plus Markdown instructions) and optional bundled `scripts/`, `references/`,
and `assets/`. The whole point of the standard is portability: a skill built to the
core format runs unchanged across the ~40 skills-compatible agents (Claude, Claude Code,
Codex, Gemini CLI, Copilot, Cursor, VS Code, and more). Stay on the core format and
the skill stays portable; reach for a client-specific frontmatter field and it does not.

## The core loop

1. Figure out what the skill is for and roughly how it should work.
2. Draft the skill (`SKILL.md` plus any bundled resources).
3. Run agent-with-access-to-the-skill on a few realistic test prompts.
4. Evaluate the outputs with the user, qualitatively and (where it fits) quantitatively.
5. Rewrite the skill based on that feedback.
6. Repeat until satisfied, then expand the test set and try at larger scale.
7. Optimize the `description` for reliable triggering.
8. Validate against the spec, then hand back the skill folder.

Your job is to figure out where the user is in this loop and jump in there. If they
say "I want a skill for X", help narrow it, draft it, write test cases, run them, and
iterate. If they already have a draft, go straight to evaluate-and-improve. If they say
"skip the evals, just vibe with me", do that. Stay flexible.

If you keep a task list, add the loop steps to it so none get skipped.

## Communicating with the user

Users range from career engineers to people who just opened a terminal for the first
time. Read context cues and match your phrasing. "Evaluation" and "benchmark" are
usually fine; only use "JSON" or "assertion" unbidden if the user has shown they know
those terms. Briefly define a term when in doubt. A short definition costs little; a
confused user costs more.

---

## Creating a skill

### Step 1: Capture intent

The current conversation may already contain the workflow to capture (the user says
"turn this into a skill"). If so, mine the history first: the tools used, the sequence
of steps, corrections the user made, the input and output formats observed. Then confirm
the gaps before moving on. Pin down four things:

1. What should this skill let the agent do?
2. When should it trigger? (which user phrases and contexts)
3. What is the expected output format?
4. Do we want test cases? Skills with objectively verifiable outputs (file transforms,
   data extraction, code generation, fixed workflows) benefit from them. Subjective
   skills (writing voice, visual design) usually do not. Suggest a default by skill type
   and let the user decide.

### Step 2: Interview and research

Ask about edge cases, input and output formats, example files, success criteria, and
dependencies before writing test prompts. If research helps (looking up an API, a file
format, a similar skill), do it now, in parallel via subagents if your environment has
them, otherwise inline. Come prepared so the user carries less of the load.

The single most valuable input is real expertise, not general knowledge. Do not generate
a skill from what a model already knows: that produces vague, generic procedure ("handle
errors appropriately", "follow best practices"). Extract the real pattern from a hands-on
task, or synthesize from real artifacts: runbooks, style guides, API specs, code-review
comments, version-control history, and actual failure cases.

### Step 3: Write the SKILL.md

Fill in the frontmatter and body. The exact, current frontmatter schema and naming rules
(field-by-field constraints, character limits, what makes a skill portable vs
platform-locked) live in **`references/spec-reference.md`**. Read it before writing
frontmatter. The how-to-write-well guidance (anatomy, progressive disclosure, writing
patterns, the full do's and don'ts) lives in **`references/authoring-guide.md`**. Read it
before writing the body.

The two fields that matter most:

- **name**: the skill identifier. Lowercase letters, digits, and hyphens only, 1 to 64
  characters, no leading/trailing/double hyphens, and it must match the parent directory
  name exactly. `pdf-processing`, not `PDF_Processing`.
- **description**: the primary and essentially only triggering mechanism. It carries the
  entire burden of getting the skill loaded, so state both what the skill does and when
  to use it, including contexts where the user does not name the domain directly. Agents
  tend to under-trigger, so make it a little pushy: list the cases, "even if they do not
  explicitly mention X". Keep it under 1024 characters. No angle brackets.

Then write the body: the actual instructions, in the imperative, explaining the why
behind each step rather than stacking rigid ALWAYS/NEVER rules. Keep `SKILL.md` under
500 lines and roughly 5000 tokens; move anything longer into `references/` and point to
it with a clear "read this when..." instruction. This is progressive disclosure, and it
is the core discipline of the standard: only `name` and `description` load at startup,
the body loads on activation, and bundled resources load on demand.

### Safety and the principle of least surprise

A skill must not contain malware, exploit code, or anything that compromises system
security, and its actual behavior must not surprise a user who only read its description.
Do not build misleading skills, or skills meant to enable unauthorized access, data
exfiltration, or similar. (Benign creative framings like "roleplay as an X" are fine.)

### Step 4: Test cases

After drafting, write 2 to 3 realistic test prompts: the kind of thing a real user would
actually type. Show them to the user ("Here are a few test cases I'd like to try, look
right?") and run them. Save the prompts to `evals/evals.json` (schema in
**`references/schemas.md`**). Hold off on writing assertions; draft those while the runs
are in progress.

### Step 5: Evaluate and improve

Run the test prompts, get the outputs in front of the user fast, gather feedback, then
rewrite. The full evaluation workflow (running with-skill and baseline runs, drafting
assertions, grading, aggregating a benchmark, launching the review viewer, reading
feedback, and the improvement heuristics) lives in **`references/evaluation.md`**. The
short version of how to improve: generalize from feedback rather than overfitting to the
test prompts, keep the prompt lean by cutting instructions the transcripts show the agent
ignoring, explain the why, and bundle a script in `scripts/` when every run reinvents the
same helper. Read the transcripts, not just the final outputs.

### Step 6: Optimize the description

The description determines triggering, so after the skill works, tune it. The full
eval-driven method (build ~20 trigger queries split should-trigger / should-not-trigger
with an emphasis on near-misses, run each several times for a trigger rate, use a
train/validation split to avoid overfitting, iterate) lives in
**`references/description-optimization.md`**. Optional automation is in
`scripts/run_loop.py`; it requires a claude-style CLI, so treat it as a fast path where
supported and the manual method as the portable default.

### Step 7: Validate against the spec

Before handing the skill back, validate it. The canonical validator from the standard is
the reference library:

```bash
skills-ref validate ./skill-maker
```

If `skills-ref` is not installed, use the bundled zero-network validator, which checks
the same spec constraints (frontmatter fields, the 64/1024/500 character limits, kebab
naming, name-matches-directory) plus soft warnings on body length:

```bash
python -m scripts.quick_validate ./skill-maker
```

Fix anything it flags before distributing.

### Step 8: Distribute

A skill is just a folder, and the folder is the unit of distribution. Place it where the
target agent looks. For cross-client portability the emerging convention is
`.agents/skills/<name>/` (project scope) or `~/.agents/skills/<name>/` (user scope);
many clients also read their own native path (for example `.claude/skills/`). Project
scope overrides user scope on a name collision. Source control the folder; that is the
versioning story.

Some hosts (claude.ai, the Skills API) additionally accept a zipped `.skill` upload. If
the `present_files` tool is available and the user wants a downloadable artifact, package
it:

```bash
python -m scripts.package_skill ./skill-maker ./dist
```

This validates first, then writes `<name>.skill`. Hand the user the resulting path. The
`.skill` zip is a host convenience, not part of the open standard; the portable artifact
is the folder.

---

## Environment adaptations

The loop above is the same everywhere, but the mechanics shift with what your runtime can
do (subagents or not, a display or not, a model CLI or not, a packaging tool or not).
Rather than special-casing product names, adapt by capability. The full matrix (no
subagents, no display, headless/static viewer output, packaging, updating an installed
skill in a read-only path) is in **`references/environment-adaptations.md`**. Read it when
your environment lacks one of those capabilities.

One rule that holds regardless of environment: when you run test cases, get the outputs in
front of the human to review before you start critiquing and rewriting yourself. Generate
the review view first.

---

## Updating an existing skill

The user may want to update an installed skill rather than create one. If so:

- **Preserve the name.** Keep the directory name and the `name` frontmatter field
  unchanged. If the skill is `research-helper`, the output stays `research-helper`, not
  `research-helper-v2`.
- **Copy to a writable location first.** Installed skill paths are often read-only. Copy
  to `/tmp/<name>/`, edit there, validate and package from the copy.
- **Re-validate after editing**, since a rename or a new frontmatter field can break
  spec-conformance or portability.

---

## Bundled resources

Read these on demand; they are deliberately kept out of `SKILL.md` to honor the token
budget.

References:
- `references/spec-reference.md` - exact agentskills.io frontmatter schema, naming rules, file structure, and the portable-vs-platform-locked distinction. Read before writing frontmatter.
- `references/authoring-guide.md` - skill anatomy, progressive disclosure, writing patterns and style, and the full do's and don'ts. Read before writing the body.
- `references/evaluation.md` - the full test, grade, benchmark, review, and improve workflow.
- `references/description-optimization.md` - the eval-driven method for tuning triggering.
- `references/environment-adaptations.md` - capability-based adaptations for runtimes lacking subagents, a display, or a packaging tool.
- `references/schemas.md` - JSON structures for evals.json, grading.json, benchmark.json, and the rest.

Scripts (run as modules from the skill root, e.g. `python -m scripts.quick_validate`):
- `scripts/quick_validate.py` - zero-network spec validator (fallback for `skills-ref validate`).
- `scripts/package_skill.py` - validate then zip into a `.skill` for hosts that accept uploads.
- `scripts/run_eval.py`, `scripts/run_loop.py`, `scripts/aggregate_benchmark.py`, `scripts/improve_description.py`, `scripts/generate_report.py`, `scripts/utils.py` - optional evaluation and description-optimization automation (require a claude-style CLI and subagents).

Agents (subagent instructions; read when spawning one):
- `agents/grader.md` - evaluate assertions against an output.
- `agents/comparator.md` - blind A/B comparison of two outputs.
- `agents/analyzer.md` - analyze why one version beat another.

Other:
- `eval-viewer/generate_review.py` - build the human review view (use this, do not hand-roll HTML).
- `assets/eval_review.html` - template for the trigger-eval review step.

---

Core loop, one more time, because it is the whole game: figure out what the skill is for;
draft or edit it; run it on real prompts; evaluate the outputs with the user; validate
against the spec; repeat until good; hand back the folder. Keep `SKILL.md` lean and let
the references carry the depth. Good luck.
