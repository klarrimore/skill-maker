---
name: skill-maker
description: Use this skill whenever the user wants to author a skill from scratch, turn a workflow or repeated task into a reusable skill, edit or refactor an existing skill, make a skill spec-compliant or portable, test or benchmark a skill, or optimize a skill description for better triggering, even if they do not say the word "skill" explicitly.
license: Apache-2.0
compatibility: Portable across any skills-compatible agent that reads the agentskills.io format. Bundled validation and packaging scripts require Python 3.8+ and PyYAML.
metadata:
  author: klarrimore
  standard: agentskills.io
  spec-revision: "2025-12-18"
  version: "1.2"
---

# Skill Maker

Create new skills and iteratively improve them, conforming to the open Agent Skills
standard (agentskills.io). A skill is a folder containing a `SKILL.md` file (YAML
frontmatter plus Markdown instructions) and optional bundled `scripts/`, `references/`,
and `assets/`. The whole point of the standard is portability: a skill built to the
core format runs unchanged across every skills-compatible agent. Stay on the core format and
the skill stays portable; reach for a client-specific frontmatter field and it does not.

## The core loop

The work is a cycle, not a checklist: **draft → run on real prompts → evaluate with the
user → rewrite → repeat**, then optimize the `description` for triggering, validate against
the spec, and hand back the folder. What makes it a loop is the repeat: most of the value
comes from cycling draft-and-evaluate several times, not from marching the procedure once.
The numbered Steps below are that procedure in full; this is its shape.

Your job is to figure out where the user is in this cycle and jump in there. If they
say "I want a skill for X", help narrow it, draft it, write test cases, run them, and
iterate. If they already have a draft, go straight to evaluate-and-improve. If they say
"skip the evals, just vibe with me", do that. Stay flexible.

If you keep a task list, add the Steps below to it so none get skipped.

## Communicating with the user

Skill authors range from career engineers to people who just opened a terminal.
"Evaluation" and "benchmark" are usually fine; only use "JSON" or "assertion" unbidden if
the user has shown they know those terms, and briefly define a term when in doubt.

---

## Creating a skill

### Step 1: Capture intent

Before anything else, confirm this should be a skill at all and
not an always-on instruction; see the "Decide first" section in references/authoring-guide.md.

The current conversation may already contain the workflow to capture (the user says
"turn this into a skill"). If so, mine the history first: the tools used, the sequence
of steps, corrections the user made, the input and output formats observed. Then confirm
the gaps before moving on.

Pin down four things:

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

A skill's actual behavior must not surprise a user who only read its description: no
hidden unauthorized access, data exfiltration, or misleading intent behind a benign-looking
description. (Openly benign creative framings like "roleplay as an X" are fine.)

### Step 4: Test cases

After drafting, write 2 to 3 realistic test prompts: the kind of thing a real user would
actually type. Show them to the user ("Here are a few test cases I'd like to try, look
right?") and run them. Save the prompts to `evals/evals.json` (schema in
**`references/schemas.md`**). Hold off on writing assertions; draft those while the runs
are in progress.

### Step 5: Evaluate and improve

Run the test prompts, get the outputs in front of the user fast, gather feedback, then
rewrite. The full evaluation workflow (running with-skill and baseline runs, drafting
assertions, grading by hand, aggregating a benchmark, presenting the outputs for review,
reading feedback, and the improvement heuristics) lives in **`references/evaluation.md`**. The
short version of how to improve: generalize from feedback rather than overfitting to the
test prompts, keep the prompt lean by cutting instructions the transcripts show the agent
ignoring, explain the why, and bundle a script in `scripts/` when every run reinvents the
same helper. Read the transcripts, not just the final outputs.

### Step 6: Optimize the description

The description determines triggering, so after the skill works, tune it. The full
eval-driven method (build ~20 trigger queries split should-trigger / should-not-trigger
with an emphasis on near-misses, run each several times for a trigger rate, use a
train/validation split to avoid overfitting, iterate) lives in
**`references/description-optimization.md`**. Run it by hand; the method is the portable
default and needs no special tooling.

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
target agent looks. In this workspace, reusable skills live under
`~/.agent/skills/<name>/` for user-global installs. For cross-client portability, many
clients also read `.agents/skills/<name>/` (project scope), `~/.agents/skills/<name>/`
(user scope), or a client-specific `.<client>/skills/` directory. Project scope
overrides user scope on a name collision. Source control the folder when it is meant to
travel with a project; otherwise keep reusable personal skills in the user-global path.

Some hosts (a hosted skills app or a skills API) additionally accept a zipped `.skill` upload. If
your client can surface a file to the user and they want a downloadable artifact, package
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
do (subagents or not, a display or not, an agent CLI or not, a packaging tool or not).
Rather than special-casing product names, adapt by capability. The full matrix (no
subagents, no display, headless presentation, packaging, updating an installed
skill in a read-only path) is in **`references/environment-adaptations.md`**. Read it when
your environment lacks one of those capabilities.

One rule that holds regardless of environment: when you run test cases, get the outputs in
front of the human to review before you start critiquing and rewriting yourself. Present
the outputs for review first.

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
- `references/spec-reference.md` - exact agentskills.io frontmatter schema, naming rules, file structure, and the portable-vs-platform-locked distinction.
- `references/authoring-guide.md` - skill anatomy, progressive disclosure, writing patterns and style, and the full do's and don'ts.
- `references/evaluation.md` - the full test, grade, benchmark, review, and improve workflow.
- `references/description-optimization.md` - the eval-driven method for tuning triggering.
- `references/environment-adaptations.md` - capability-based adaptations for runtimes lacking subagents, a display, or a packaging tool.
- `references/schemas.md` - JSON structures for evals.json, grading.json, benchmark.json, and the rest.

Scripts (run as modules from the skill root, e.g. `python -m scripts.quick_validate`):
- `scripts/quick_validate.py` - zero-network spec validator (fallback for `skills-ref validate`).
- `scripts/package_skill.py` - validate then zip into a `.skill` for hosts that accept uploads.

Assets:
- `assets/eval_review.html` - template for the trigger-query review used in description optimization (Step 6); fill the placeholders by hand. There is no separate benchmark viewer; present benchmark results inline or as a `benchmark.md` summary.

Evals (self-tests; not shipped - excluded from the packaged `.skill`):
- `evals/` - an example `evals.json`, trigger queries, and a broken-skill fixture that exercise this skill on its own format. See `evals/README.md`.
