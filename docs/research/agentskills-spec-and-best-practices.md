# Agent Skills Open Standard — Specification and Best Practices

## Scope & method

This is a primary-source investigation of the **Agent Skills** open standard published at
[agentskills.io](https://agentskills.io/home). Every claim below is traced either to the
official documentation pages, to the specification source in the official
[`agentskills/agentskills`](https://github.com/agentskills/agentskills) repository, or to the
official `skills-ref` reference validator source code in that same repository. No blog posts,
third-party summaries, or model memory were used.

Sources used, and how:

- The documentation site at agentskills.io (rendered pages and their `.md` twins listed in
  [`/llms.txt`](https://agentskills.io/llms.txt)).
- The repository [`agentskills/agentskills`](https://github.com/agentskills/agentskills),
  cloned and inspected at commit
  [`69ef37e9424c0a7ea9dd2293b559e43ec8176379`](https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379)
  ("docs: add OpenClaw to client showcase (#492)", committed 2026-08-09). The specification
  source file is
  [`docs/specification.mdx`](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx).
- The reference validator source under
  [`skills-ref/src/skills_ref/`](https://github.com/agentskills/agentskills/tree/main/skills-ref/src/skills_ref).
- The PyPI metadata for the `skills-ref` package, used only to check the repo's "also on PyPI"
  claim: [`https://pypi.org/pypi/skills-ref/json`](https://pypi.org/pypi/skills-ref/json).

**Accessed:** 2026-09-17.

A note on authority, because it shapes how to read everything else. The repository's
[`AGENTS.md`](https://github.com/agentskills/agentskills/blob/main/AGENTS.md) states plainly:
"`docs/specification.mdx` is authoritative for format requirements. Explanatory documentation,
examples, tests, and implementations do not add requirements to the format." It adds that
`skills-ref/` is "a demonstration artifact, not a production SDK or a source of additional
format requirements." So there are three distinct tiers throughout this document:

- **(a) Spec-mandated** — text in `docs/specification.mdx`.
- **(b) Documented recommendation** — the guides under `/skill-creation/` and
  `/client-implementation/`.
- **(c) Implementation behavior / de-facto convention** — what `skills-ref` actually does, what
  `CONTRIBUTING.md` describes, and conventions other clients happen to share. These do **not**
  add normative requirements.

Where these layers disagree, that is called out explicitly.

---

## 1. What an Agent Skill is

A skill is a folder containing a `SKILL.md` file, and optionally other directories:

> "At its core, a skill is a folder containing a `SKILL.md` file. This file includes metadata
> (`name` and `description`, at minimum) and instructions that tell an agent how to perform a
> specific task. Skills can also bundle scripts, reference materials, templates, and other
> resources." — [`agentskills.io/home`](https://agentskills.io/home)

The specified directory layout ([spec, "Directory structure"](https://agentskills.io/specification)):

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

The spec says the directory "contain[s], at minimum, a `SKILL.md` file" and that "a skill
directory may contain any files and directories beyond the required `SKILL.md`." The
`scripts/`, `references/`, `assets/` split is stated to be "conventions … recommendations for
organizing common types of content," not hard requirements.

`SKILL.md` itself "must contain YAML frontmatter followed by Markdown content"
([spec, "`SKILL.md` format"](https://agentskills.io/specification)).

### Progressive disclosure (the core loading model)

The spec defines a three-tier loading model
([spec, "Progressive disclosure"](https://agentskills.io/specification)):

1. **Metadata** (~100 tokens): the `name` and `description` fields, loaded at startup for all
   skills.
2. **Instructions** (< 5000 tokens recommended): the full `SKILL.md` body, loaded when the
   skill is activated.
3. **Resources** (as needed): `scripts/`, `references/`, `assets/` files, loaded only when
   required.

The client-implementation guide renders the same model as a table with slightly different
numbers, ~50–100 tokens per catalog entry for tier 1
([adding-skills-support](https://agentskills.io/client-implementation/adding-skills-support)).
Both figures are first-party; the spec says "~100", the client guide says "~50-100". This is a
minor, non-substantive variance, not a conflict.

The home page frames the same three stages as **Discovery** (name + description), **Activation**
(full `SKILL.md`), **Execution** (follow instructions, run scripts, load referenced files)
([home, "How do Agent Skills work?"](https://agentskills.io/home)).

---

## 2. Frontmatter schema

The full field table, quoted verbatim from
[spec, "Frontmatter"](https://agentskills.io/specification):

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | Yes | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. |
| `description` | Yes | Max 1024 characters. Non-empty. Describes what the skill does and when to use it. |
| `license` | No | License name or reference to a bundled license file. |
| `compatibility` | No | Max 500 characters. Indicates environment requirements (intended product, system packages, network access, etc.). |
| `metadata` | No | Arbitrary key-value mapping for additional metadata (a map from string keys to string values). |
| `allowed-tools` | No | Space-separated string of pre-approved tools the skill may use. (Experimental) |

**Type/limit summary (spec text):**

- `name` — required, string, **1–64 characters**.
- `description` — required, string, **1–1024 characters**, non-empty.
- `license` — optional, string; "keeping it short" is "recommend[ed]."
- `compatibility` — optional, string, **1–500 characters if provided**; "Should only be included
  if your skill has specific environment requirements."
- `metadata` — optional; "A map from string keys to string values."
- `allowed-tools` — optional; "A space-separated string"; explicitly "Experimental. Support for
  this field may vary between agent implementations."

### `name` — exact rules

The spec's detailed rules for the required `name` field
([spec, "`name` field"](https://agentskills.io/specification)) are:

- Must be 1–64 characters.
- May only contain unicode lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`).
- Must not start or end with a hyphen (`-`).
- Must not contain consecutive hyphens (`--`).
- Must match the parent directory name.

Spec-provided valid examples: `pdf-processing`, `data-analysis`, `code-review`. Invalid
examples: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing`
(consecutive hyphens).

**Internal inconsistency in the spec, worth flagging:** the prose says "unicode lowercase
alphanumeric characters" but then parenthesizes the ASCII range `a-z, 0-9`. The reference
validator resolves this in favor of *Unicode*: it normalizes with NFKC and accepts any
`str.isalnum()` character, then rejects uppercase via `name != name.lower()`
([`validator.py:37-58`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/validator.py#L37-L58)).
Its tests explicitly assert that Chinese (`技能`), Russian (`мой-навык`, `навык`), and
decomposed-accent (`café`) names are valid
([`test_validator.py:165-290`](https://github.com/agentskills/agentskills/blob/main/skills-ref/tests/test_validator.py#L165-L290)).
The parenthetical `a-z, 0-9` was in fact *corrected* in a commit ("fix name field character
range to include digits") to match the table's "letters, numbers," wording, but the word
"unicode" and the ASCII parenthetical still coexist
([commit `6868401`](https://github.com/agentskills/agentskills/commit/6868401b64f791e9ff565f29beb6338826b73a2b)).
Treat the character set as an unresolved ambiguity in the spec text.

The git history also shows the spec originally read `(a-z and -)` and was changed to
`(a-z, 0-9)` — see the same commit. This is the closest thing to a documented spec
clarification.

### `description` rules

- "Must be 1-1024 characters."
- "Should describe both what the skill does and when to use it."
- "Should include specific keywords that help agents identify relevant tasks."

The spec gives a good example (extract/fill/merge PDFs, "Use when working with PDF documents or
when the user mentions PDFs, forms, or document extraction.") and a poor one
("Helps with PDFs.") ([spec, "`description` field"](https://agentskills.io/specification)).

### Minimal and full frontmatter examples (spec)

Minimal:

```yaml
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

With optional fields:

```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

### Which fields are portable vs platform-locked

The spec itself does not use the terms "portable" or "platform-locked." Its normative field set
is the six fields above. However, `AGENTS.md` emphasizes the intent: "Agent Skills is a small,
portable, client-neutral format. Keep the format small: new requirements impose costs on every
implementation"
([`AGENTS.md`](https://github.com/agentskills/agentskills/blob/main/AGENTS.md)).

The strongest first-party signal that extra fields are client-specific is the spec's `metadata`
description: it exists so that "Clients can use this to store additional properties not defined
by the Agent Skills spec," with the recommendation to "make your key names reasonably unique to
avoid accidental conflicts" ([spec, "`metadata` field"](https://agentskills.io/specification)).
Read together with `AGENTS.md`'s authority rule, fields outside the six are implementation
extensions, not part of the format. The docs do not enumerate a platform-locked field list;
that enumeration in this repo is therefore partly de-facto knowledge (see Gaps below).

---

## 3. Body / instruction conventions

**Spec-mandated:** "The Markdown body after the frontmatter contains the skill instructions.
There are no format restrictions. Write whatever helps agents perform the task effectively."
Recommended sections: "Step-by-step instructions; Examples of inputs and outputs; Common edge
cases" ([spec, "Body content"](https://agentskills.io/specification)).

**Spec-mandated structural budgets:**

- "Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate
  files."
- Tier 2 is "< 5000 tokens recommended."
- "Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains."
- Reference paths are "relative paths from the skill root."

**Recommended directory roles** ([spec, "Optional directories"](https://agentskills.io/specification)):

- `scripts/` — "executable code that agents can run"; scripts should "be self-contained or
  clearly document dependencies," "include helpful error messages," and "handle edge cases
  gracefully." Common languages are "Python, Bash, and JavaScript," but "supported languages
  depend on the agent implementation."
- `references/` — "additional documentation that agents can read when needed," with named
  examples `REFERENCE.md`, `FORMS.md`, and domain files (`finance.md`, `legal.md`). "Keep
  individual reference files focused."
- `assets/` — "static resources": templates, images, data files.

The best-practices guide adds the crucial linking rule: "tell the agent *when* to load each
file. 'Read `references/api-errors.md` if the API returns a non-200 status code' is more useful
than a generic 'see references/ for details'"
([best-practices, "Structure large skills with progressive disclosure"](https://agentskills.io/skill-creation/best-practices)).

---

## 4. Naming rules and portability

### Naming (spec)

Covered in §2. The one behavioral nuance the spec does not state but the validator enforces:

- `skills-ref` **accepts both `SKILL.md` and lowercase `skill.md`**, preferring the uppercase
  form:
  > "Prefers SKILL.md (uppercase) but accepts skill.md (lowercase)."
  > — [`parser.py:12-27`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/parser.py#L12-L27)

  The spec always writes `SKILL.md`; this lenient behavior is implementation, not spec.

### Portable vs platform-locked

The spec does not define portability. The closest first-party material is:

- `AGENTS.md`: "small, portable, client-neutral format" and "Preserve the distinction between
  the format and choices made by skill authors, clients, models, or implementations."
- The client guide's note on location: "While the Agent Skills specification does not mandate
  where skill directories live (it only defines what goes inside them)…"
  ([adding-skills-support](https://agentskills.io/client-implementation/adding-skills-support)).
- `allowed-tools` is marked **Experimental**, and the spec warns "Support for this field may vary
  between agent implementations."
- `compatibility` is the spec's sanctioned place for environment requirements.

There is no first-party list of "platform-locked" fields. Concrete client extensions (e.g.
`context: fork`, `disable-model-invocation`, `agents/openai.yaml`) are **not** described on
agentskills.io; those come from individual client docs (not investigated here) and should be
treated as tier-(c) de-facto knowledge. The repo's own portability list should be read with that
caveat.

### Directory placement (convention, explicitly not spec)

The spec "does not mandate where skill directories live." The client guide names the de-facto
convention
([adding-skills-support, "Where to scan"](https://agentskills.io/client-implementation/adding-skills-support)):

| Scope | Path | Purpose |
| --- | --- | --- |
| Project | `<project>/.<your-client>/skills/` | Client's native location |
| Project | `<project>/.agents/skills/` | Cross-client interoperability |
| User | `~/.<your-client>/skills/` | Client's native location |
| User | `~/.agents/skills/` | Cross-client interoperability |

It states: "The `.agents/skills/` paths have emerged as a widely-adopted convention for
cross-client skill sharing." It also notes some implementations additionally scan
`.claude/skills/`, ancestor directories up to the git root, XDG config directories, and
user-configured paths. On collisions: "**project-level skills override user-level skills**"
(the guide calls this "the universal convention across existing implementations") and the
harness should "log a warning when a collision occurs."

The quickstart confirms the VS Code default is `.agents/skills/`
([quickstart](https://agentskills.io/skill-creation/quickstart)).

**Security recommendation from the client guide (not spec):** project-level skills "come from
the repository being worked on, which may be untrusted… Consider gating project-level skill
loading on a trust check."

---

## 5. Validation and how to run it

The spec's only validation statement:

> "Use the [skills-ref] reference library to validate your skills: `skills-ref validate ./my-skill`.
> This checks that your `SKILL.md` frontmatter is valid and follows all naming conventions."
> — [spec, "Validation"](https://agentskills.io/specification)

### `skills-ref` — what it is

- Python package `skills-ref`, version `0.1.0` in the repo's
  [`pyproject.toml`](https://github.com/agentskills/agentskills/blob/main/skills-ref/pyproject.toml),
  requires Python `>=3.11`, deps `click` and `strictyaml`. Console script is
  `skills-ref = "skills_ref.cli:main"`.
- The README carries an explicit disclaimer:
  > "This library is intended for demonstration purposes only. It is not meant to be used in
  > production."
  > — [`skills-ref/README.md:5-6`](https://github.com/agentskills/agentskills/blob/main/skills-ref/README.md)
- `CONTRIBUTING.md` says: "We're still determining the direction for the reference library and
  are not accepting code contributions to it at this time."
  ([CONTRIBUTING.md](https://github.com/agentskills/agentskills/blob/main/CONTRIBUTING.md))

### CLI commands

From [`cli.py`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/cli.py):

- `skills-ref validate <skill_path>` — exits `0` on valid, `1` on errors; accepts either a
  directory or a direct path to a `SKILL.md`/`skill.md` file (it uses the parent directory).
- `skills-ref read-properties <skill_path>` — prints frontmatter properties as JSON, exits `1`
  on parse error.
- `skills-ref to-prompt <skill_path>...` — emits the `<available_skills>` XML block for an agent
  system prompt.

CLI paths are declared `click.Path(exists=True)`, so a missing path is a usage error before
validation even runs.

### What the validator actually checks

`validate_metadata` in
[`validator.py:118-147`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/validator.py#L118-L147)
checks:

1. **Only allowed top-level fields** — `ALLOWED_FIELDS` is exactly `name`, `description`,
   `license`, `allowed-tools`, `metadata`, `compatibility`. Any other key produces
   "Unexpected fields in frontmatter".
2. **`name` is present**, then `_validate_name`: non-empty string, NFKC-normalized, ≤64 chars,
   lowercase, no leading/trailing hyphen, no `--`, all chars `isalnum()` or `-`, and directory
   name must equal the name (after normalization).
3. **`description` is present**, then `_validate_description`: non-empty string, ≤1024 chars.
4. **`compatibility`**, if present: must be a string, ≤500 chars.

Limits are module constants:
`MAX_SKILL_NAME_LENGTH = 64`, `MAX_DESCRIPTION_LENGTH = 1024`, `MAX_COMPATIBILITY_LENGTH = 500`
([`validator.py:10-12`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/validator.py#L10-L12)).

The parser additionally requires the file to *start with* `---` and to be closed with `---`,
and requires the frontmatter to parse as a YAML mapping
([`parser.py:42-59`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/parser.py#L42-L59)).
It coerces `metadata` values to strings: `{str(k): str(v) …}`
([`parser.py:61-62`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/parser.py#L61-L62)).

**Important gaps between validator behavior and spec text** (the validator is *not* a second
spec):

- The validator rejects any top-level field outside the six. The spec never says extra fields
  are forbidden; it only says extra properties should go in `metadata`. Under the `AGENTS.md`
  authority rule, "exactly six recognized fields" is implementation behavior, not a spec
  requirement.
- The validator's `compatibility` check enforces `≤500` but **not** a minimum of 1, despite the
  spec saying "1-500 characters if provided." An empty string passes the validator.
- The validator does not check `allowed-tools` type at all, despite the spec calling it a
  "space-separated string."
- The validator accepts lowercase `skill.md`; the spec only names `SKILL.md`.
- The validator implements NFKC normalization and Unicode `isalnum()` names; the spec's
  parenthetical says `a-z, 0-9`.
- The validator does not check body length, line counts, or reference-file depth; those are
  spec *recommendations*, not validation rules.
- The validator does **not** check for angle brackets or reserved words (see Gaps).

### Skills-ref on PyPI

The package is published on PyPI as `skills-ref` (version `0.1.1` at access time), so "also on
PyPI" is true. But two discrepancies are worth recording:

- The PyPI long description advertises the console command as `agentskills validate …`, not
  `skills-ref validate …` as in the repo's own `pyproject.toml` and README.
  ([PyPI JSON](https://pypi.org/pypi/skills-ref/json))
- The PyPI project's URLs point at `github.com/anthropics/agentskills` (the pre-move org), and
  the JSON `ownership.roles[].user` is `BjoernBethge`, not an Anthropic account. The official
  install instructions in the repo README are local (`pip install -e .`). Treat the PyPI
  artifact as convenience distribution rather than the canonical installation path.

### Lenient validation (client guide)

For client implementors, the guide recommends relaxing strict constraints to maximize
compatibility ([adding-skills-support, "Lenient validation"](https://agentskills.io/client-implementation/adding-skills-support)):

- Name doesn't match parent dir → warn, load anyway.
- Name exceeds 64 chars → warn, load anyway.
- Description missing/empty → **skip** the skill (essential for disclosure).
- YAML completely unparseable → **skip** the skill.
- Malformed YAML with unquoted colons (e.g. `description: Use this skill when: the user …`) →
  try a fallback that quotes or block-scalarizes it.

The guide is explicit: "The specification defines strict constraints on the `name` field …
The lenient approach above deliberately relaxes these to improve compatibility with skills
authored for other clients."

---

## 6. Best practices for authoring

All from [best-practices](https://agentskills.io/skill-creation/best-practices) unless noted.

**Ground skills in real expertise.**
- The primary anti-pattern is asking an LLM to generate a skill from general knowledge, yielding
  "vague, generic procedures ('handle errors appropriately,' 'follow best practices for
  authentication')."
- Two extraction methods: (1) "Extract from a hands-on task" — complete a real task, capture
  steps that worked, corrections, input/output formats, context provided; (2) "Synthesize from
  existing project artifacts" — internal docs, runbooks, API specs, code review comments,
  version-control history, real failure cases and resolutions.

**Refine with real execution.**
- Run against real tasks and feed *all* results (not just failures) back in.
- "Read agent execution traces, not just final outputs." Common trace problems: instructions too
  vague, instructions that don't apply but are followed anyway, too many options with no default.

**Spend context wisely.**
- "Add what the agent lacks, omit what it knows." Test: "Would the agent get this wrong without
  this instruction?" If no, cut it.
- "Design coherent units" — scope like a function; too narrow forces co-loading, too broad is
  hard to trigger precisely.
- "Aim for moderate detail" — exhaustive documentation can hurt; concise stepwise guidance with a
  working example outperforms completeness.
- "Structure large skills with progressive disclosure" — keep `SKILL.md` under 500 lines / 5,000
  tokens; move detail to `references/`; say *when* to load each.

**Calibrate control.**
- "Match specificity to fragility": give freedom where variation is fine and explain *why*; be
  prescriptive where operations are fragile or a sequence must be exact.
- "Provide defaults, not menus."
- "Favor procedures over declarations" (teach the class of problem, not one instance).

**Reusable instruction patterns.**
- **Gotchas sections** — highest-value content is "environment-specific facts that defy
  reasonable assumptions." Keep gotchas in `SKILL.md` because the agent may not know to load a
  reference file; when an agent makes a mistake you correct, add the correction there.
- **Templates for output format** — concrete structures beat prose; inline short ones, put long
  or conditional ones in `assets/`.
- **Checklists** for multi-step workflows.
- **Validation loops** — do, run validator, fix, repeat until pass.
- **Plan-validate-execute** for batch/destructive operations — create an intermediate plan,
  validate against a source of truth, then execute.
- **Bundle reusable scripts** when traces show the agent reinventing the same logic each run.

The guide explicitly ties triggering optimization and output evaluation together as "Next
steps," pointing to the two companion guides.

---

## 7. Description optimization / triggering

From [optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions).

**How triggering works.**
- "The `description` field … is the primary mechanism agents use to decide whether to load a
  skill."
- "This means the description carries the entire burden of triggering."
- Nuance: "agents typically only consult skills for tasks that require knowledge or capabilities
  beyond what they can handle alone. A simple, one-step request like 'read this PDF' may not
  trigger a PDF skill even if the description matches perfectly."

**Writing effective descriptions.**
- Use imperative phrasing ("Use this skill when…").
- Focus on user intent, not implementation.
- "Err on the side of being pushy" — list contexts including when the user doesn't name the
  domain.
- Keep it concise; spec enforces a hard limit of 1024 characters.

**Trigger eval queries.**
- Build ~20 queries: 8–10 should-trigger, 8–10 should-not-trigger.
- Vary phrasing, explicitness, detail, and complexity. Most useful should-trigger queries are
  ones where the connection isn't obvious.
- "The most valuable negative test cases are **near-misses**" that share keywords but need
  something different.
- Add realism: file paths, personal context, column names, company names, casual language, typos.
- JSON shape: `[{ "query": "...", "should_trigger": true }, …]`.

**Measuring.**
- Run each query with the skill installed and observe whether the agent loaded `SKILL.md`.
- "Run each query multiple times (3 is a reasonable starting point) and compute a **trigger
  rate**."
- Pass threshold "0.5 is a reasonable default": should-trigger passes above it, should-not-trigger
  passes below it.
- The guide provides a Bash+`jq` harness using `claude -p "$query" --output-format json` and
  inspecting Skill tool calls, explicitly telling the reader to replace the detection logic per
  client.

**Avoiding overfitting.**
- Split into **train (~60%)** and **validation (~40%)**, with a proportional mix of positives and
  negatives, shuffled once and kept fixed.
- Use only train failures to guide changes; select the best iteration by validation pass rate.
- "Five iterations is usually enough."
- Best description may not be the last iteration.

**Applying.**
- Confirm under 1024 characters, then sanity-check with 5–10 *fresh* queries.
- Worked before/after: `Process CSV files.` → an imperative description naming summary stats,
  derived columns, charts, cleaning, and trigger contexts "even if they don't explicitly mention
  'CSV' or 'analysis.'"

The guide also points to Anthropic's `skill-creator` Skill at
`github.com/anthropics/skills/tree/main/skills/skill-creator` as automating the loop.

---

## 8. Evaluation of skill output quality

From [evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills).

**Test cases.** Three parts: prompt, expected output, optional input files. Store in
`evals/evals.json` inside the skill directory:

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "…",
      "expected_output": "…",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": ["…"]
    }
  ]
}
```

Guidance: start with 2–3 cases; vary phrasing/detail/formality; cover edge cases; use realistic
context. Add assertions only after the first run.

**Running evals.** Run each case **with** the skill and **without** it (or against a previous
version snapshot). Workspace layout:

```
csv-analyzer/
├── SKILL.md
└── evals/evals.json
csv-analyzer-workspace/
└── iteration-1/
    ├── eval-<name>/{with_skill,without_skill}/{outputs,timing.json,grading.json}
    └── benchmark.json
```

Each run starts from a clean context. For an existing skill, snapshot it and use the snapshot as
the baseline (`old_skill/`).

**Timing.** Record `total_tokens` and `duration_ms` in `timing.json`. In Claude Code, subagent
completion notifications carry these.

**Assertions.** Verifiable statements about output. Good: "The output file is valid JSON";
specific/countable. Weak: "The output is good"; too-brittle exact-phrase checks. Some qualities
(style, visual design) are better left to human review.

**Grading.** Produce `grading.json` with per-assertion PASS/FAIL plus evidence. Principles:
"Require concrete evidence for a PASS"; use scripts for mechanical checks; review the assertions
themselves for too-easy / too-hard / unverifiable. Blind comparison between two versions is
suggested for holistic quality.

**Aggregating.** `benchmark.json` holds per-configuration pass rate, time, tokens (mean/stddev)
and a `delta`. "delta tells you what the skill costs … and what it buys."

**Pattern analysis.** Remove assertions that always pass in both configs; investigate ones that
always fail; study ones that pass with the skill and fail without; tighten instructions when
results are inconsistent; check time/token outliers via execution transcripts.

**Human review.** Record actionable feedback per test case in `feedback.json`.

**Iteration loop.** Combine failed assertions, human feedback, and execution transcripts; give
all three plus the current `SKILL.md` to an LLM to propose changes. Guidelines for that
prompting: generalize from feedback, keep the skill lean, explain the why, bundle repeated work.
Loop: propose → apply → rerun in `iteration-<N+1>/` → grade/aggregate → human review → repeat.

The same `skill-creator` Skill is credited with automating much of this.

---

## 9. Scripts

From [using-scripts](https://agentskills.io/skill-creation/using-scripts).

**One-off commands.** Reference existing package runners directly without a `scripts/` dir:
`uvx`, `pipx`, `npx`, `bunx`, `deno run`, `go run`. Tips: pin versions; state prerequisites in
`SKILL.md` or the `compatibility` field; move complex commands into scripts.

**Referencing scripts.** Use relative paths from the skill directory root; list available scripts
in `SKILL.md` so the agent knows they exist. "script execution paths (in code blocks) are relative
to the skill directory root, because the agent runs commands from there."

**Self-contained scripts.** Inline dependency metadata per language: Python (PEP 723 `# /// script`
blocks, run with `uv run`), Deno (`npm:`/`jsr:` specifiers), Bun (pinned imports, auto-install),
Ruby (`bundler/inline`). Pin versions for reproducibility.

**Designing scripts for agentic use.**
- Avoid interactive prompts — "a hard requirement of the agent execution environment"; agents
  run in non-interactive shells.
- Document usage with `--help`.
- Write helpful error messages that say what went wrong, what was expected, what to try.
- Use structured output (JSON/CSV/TSV); send data to stdout and diagnostics to stderr.
- Idempotency, input constraints, `--dry-run`, meaningful documented exit codes, safe defaults,
  predictable output size (harnesses often truncate at ~10–30K chars).

---

## 10. Adding skills support to a client (portability-relevant)

From [adding-skills-support](https://agentskills.io/client-implementation/adding-skills-support).
Included here because it is the first-party source for discovery paths, collision rules, and
which behaviors are deliberately non-normative.

- Three-tier progressive disclosure, as in §1.
- Discovery scans project and user scopes; `.agents/skills/` is the cross-client convention;
  `.claude/skills/` is scanned by some for pragmatic compatibility; ancestor dirs / XDG /
  user-configured paths also seen. Discovery looks for "subdirectories containing a file named
  exactly `SKILL.md`"; skip `.git/`, `node_modules/`; optionally respect `.gitignore`; bound depth
  (4–6) and count (~2000).
- Collision precedence: project over user.
- Trust: gate project-level loading on a trusted-folder check.
- Parsing: split frontmatter on `---`, parse YAML, body is everything after the closing `---`;
  handle malformed YAML leniently.
- Catalog: `name`, `description`, optional `location`; ~50–100 tokens per skill; hide filtered
  skills entirely; omit the catalog entirely when no skills exist.
- Activation: model-driven (file-read or a dedicated tool) and user-explicit (`/skill-name`,
  `$skill-name`); dedicated tools should constrain the name parameter to an enum; resource
  listing should not eagerly read files; allowlist skill directories for read permission.
- Context management: protect skill content from compaction, dedupe activations, optional
  subagent delegation.

The guide provides a recommended prompt snippet and an `<available_skills>` XML example matching
`skills-ref to-prompt` output.

---

## 11. Versioning / evolution of the spec

- **There is no spec version number, tag, or changelog on the site or in the repo.** The
  repository has no git tags at all (`git tag -l` returned nothing at access time). The spec is
  therefore effectively unversioned; conformance is defined by the current spec text. This is an
  inference from the absence of any versioning artifact, not a statement the docs make.
- The format was "originally developed by [Anthropic], released as an open standard, and has been
  adopted by a growing number of agent products"
  ([home, "Open development"](https://agentskills.io/home); same text in the repo README).
- `CONTRIBUTING.md` frames the project as early-stage and deliberately conservative: "We maintain
  a high bar for additions to the spec — it is much easier to add things to a specification than
  to remove them." It is "not accepting … major architectural changes" and not accepting skill
  submissions.
- `AGENTS.md` sets the design bar: "new requirements impose costs on every implementation and
  should address demonstrated interoperability needs, not hypothetical completeness."
- The repository's history (145 commits, 2025-12-18 through 2026-08-09 at access time) shows only
  clarifications to wording, examples, and the field table — no added or removed frontmatter
  fields. Examples: fixing the `name` character range to include digits
  ([`6868401`](https://github.com/agentskills/agentskills/commit/6868401b64f791e9ff565f29beb6338826b73a2b)),
  clarifying the `metadata` key/value types
  ([`3f3bbec`](https://github.com/agentskills/agentskills/commit/3f3bbec8133ce7fcde5aa9fc42556cd15cab8646)),
  and changing `allowed-tools` from "Space-delimited list" to "Space-separated string"
  ([`6f92fcd`](https://github.com/agentskills/agentskills/commit/6f92fcd)).
- The site navigation groups content into "For skill creators" and "For client implementors,"
  with redirects from older routes (`/integrate-skills` → adding-skills-support,
  `/what-are-skills` → `/`) — evidence the docs are being reorganized over time
  ([`docs/docs.json`](https://github.com/agentskills/agentskills/blob/main/docs/docs.json)).

---

## Gaps / unverified

Things the first-party sources are silent on, or where this repo's claims could **not** be
confirmed. These are explicitly *not* claims; they are open items.

1. **"The bundled validator also rejects angle brackets (`<`, `>`)."**
   This repo's `spec-reference.md` asserts it, but the primary validator does not check for angle
   brackets. `grep` over `skills-ref/src/` finds no such rule; `_validate_description` only checks
   non-empty and ≤1024 ([`validator.py:70-84`](https://github.com/agentskills/agentskills/blob/main/skills-ref/src/skills_ref/validator.py#L70-L84)).
   The spec does not mention angle brackets either. The claim appears to originate outside
   agentskills.io (plausibly a different client's or Anthropic's skill tooling) and is
   **unverified against the agentskills.io primary sources**.

2. **Reserved words in skill names.** The repo says "some clients reserve certain words … and
   reject a name that contains one on upload," and "the standard does not define a reserved-word
   list." The last clause matches the sources (no list appears), but the existence and behavior of
   client-side reserved words is not described anywhere on agentskills.io. Unverified.

3. **`~/.agent/skills/` (singular "agent").** The repo lists this as a "User-global Agent CLI
   location." The first-party client guide lists `~/.agents/skills/` (plural) and
   `.claude/skills/`; it does **not** mention `~/.agent/skills/`. Possibly a typo in the repo or
   an undocumented path. Unverified against primary sources.

4. **`.skill` zip uploads.** The repo calls a zipped `.skill` "a host convenience offered by some
   hosts … not part of the open standard." No agentskills.io page mentions `.skill`, packaging, or
   zip distribution. The "not part of the standard" half is defensible (the spec defines folders,
   not archives), but the existence/convention is unverified from first-party sources.

5. **Ecosystem commands (`gh skill`, `npx skills add <owner/repo>`).** The repo cites these as
   ecosystem tooling. Neither appears in the agentskills.io docs or the official repo. Unverified.

6. **`metadata.version`.** The spec's examples use `metadata: { version: "1.0" }`, but the spec
   does **not** define a `version` field for the skill itself, nor any versioning scheme.
   `metadata` is "arbitrary key-value mapping." Do not treat `version` as a spec field.

7. **Skill-to-skill composition.** The repo states "The standard does not support skill-to-skill
   composition." The first-party docs never discuss composition at all, so this is an inference
   from silence rather than a documented prohibition.

8. **Security.** The spec is silent on security. The only first-party security-adjacent guidance
   is the client guide's project-level trust check and the warning in `AGENTS.md` to distinguish
   format from implementation choices. The repo's "treat third-party skills like an unaudited
   dependency" framing is sound but is not a spec statement.

9. **Token-count precision.** Tier 1 is "~100 tokens" in the spec and "~50-100" in the client
   guide; tier 2 is "< 5000 tokens recommended." Exact tokenization is model-dependent and the
   spec does not specify a tokenizer.

10. **Client extension fields.** The repo's list of platform-locked fields (`context: fork`,
    `user-invocable`, `model`, `disable-model-invocation`, `agents/openai.yaml`) is not on
    agentskills.io. It may be accurate per individual clients, but it is not verifiable here
    without reading each client's own docs (out of scope).

11. **`skills-ref` production use.** The README says demonstration-only; `CONTRIBUTING.md` says
    the library's direction is undecided and code contributions are closed right now. Any plan
    that depends on `skills-ref` as a stable dependency should account for this.

12. **PyPI ownership / entry point.** The PyPI `skills-ref` package's advertised CLI is
    `agentskills`, its URLs point to the old `anthropics/agentskills` org, and its PyPI owner is
    an individual (`BjoernBethge`). The canonical install path in the repo README is a local
    editable install. Verify provenance before relying on the PyPI artifact.

---

## Implications for this repo

Where the primary sources refine or contradict what `skills-maker` currently claims. Page
citations refer to this repo's files; no repo files were modified except this research file.

1. **Remove or qualify the angle-bracket claim** in
   `skills/skill-maker/references/spec-reference.md` (`description rules`, lines ~86–87) and in
   `skills/skill-maker/references/description-optimization.md` (`Step 4`, line ~104). The official
   `skills-ref` validator does not reject `<`/`>` and the spec is silent. As written, the repo
   presents an implementation-specific rule as if it were part of the standard, and then relies on
   it during re-validation. Either drop it or attribute it clearly: "not checked by `skills-ref`;
   some clients may sanitize markup."

2. **Reframe "exactly six recognized fields."** The spec never says extra fields are forbidden;
   the *validator* rejects them, and `AGENTS.md` explicitly says implementations do not add
   requirements. The repo's `spec-reference.md` line 32 ("There are exactly six recognized
   fields") and the portability warning at lines 171–173 should distinguish spec fields (six
   defined) from validator enforcement (rejects extras). This matters because a skill that puts
   client extensions at top level is still *spec-conformant*, just not portable.

3. **The `name` character-set nuance is understated.** The repo line 36/68 says "Lowercase letters,
   digits, and hyphens … (`a-z`, `0-9`)". The spec says "unicode lowercase alphanumeric" and the
   validator genuinely accepts Unicode (Chinese, Russian, accented) names. The repo's ASCII-only
   phrasing is stricter than both the spec prose and the validator. Add the Unicode point, or at
   least note the spec's own `a-z` parenthetical is inconsistent with its "unicode" wording.

4. **`~/.agent/skills/` is likely wrong.** `spec-reference.md` line 185 lists
   `~/.agent/skills/`. The first-party client guide lists `~/.agents/skills/` and never this
   singular path. Verify before keeping; if it is meant to be a real client path, attribute it to
   that client.

5. **`compatibility` minimum is not enforced by `skills-ref`.** The repo correctly quotes
   "1 to 500 characters," which matches the spec. Worth noting the validator only enforces the
   upper bound (empty string passes), so "validate before distributing" is a weaker guarantee
   than the table implies.

6. **"Canonical validator" wording.** The spec calls `skills-ref` a "reference library" and its
   README calls it "demonstration purposes only … not meant to be used in production." The repo's
   `spec-reference.md` line 194 says "Canonical validator." Softening to "reference validator
   (demonstration-grade; not a production SDK)" better matches the primary source and the fact
   that code contributions to it are currently closed.

7. **`.skill` zip, `gh skill`, `npx skills add`, and reserved words** (`spec-reference.md` lines
   72–75 and 198–199) are not supported by any agentskills.io primary source. Keep them only if
   they can be attributed to specific clients/tools; otherwise label them clearly as de-facto
   ecosystem convention rather than standard behavior.

8. **Versioning statement.** The repo says the standard is "intentionally minimal and unversioned"
   (`spec-reference.md` line 5). This is accurate in effect (no tags, no version field), but it is
   an inference from absence. Consider saying "the spec publishes no version number; conformance
   is the current text" rather than asserting intent.

9. **What the repo gets right and should keep:** the field table and exact limits (64 / 1024 / 500
   with the correct `compatibility` lower bound), the name rules including directory match and
   `--` prohibition, the three-tier progressive-disclosure model, the 500-line / 5000-token body
   budget, the "one level deep" reference rule, the "tell the agent when to load each file" rule,
   the `description`-carries-triggering framing, the pushy-imperative description guidance, the
   20-query / 3-runs / 0.5-threshold / 60-40 train-validation loop, the eval workspace layout, and
   the agentic script-design rules. All of these are direct or faithful paraphrases of the
   primary sources.

10. **Nothing in the primary sources contradicts** the repo's core authoring guidance (ground in
    real expertise, refine with traces, add only what the agent lacks, calibrate specificity to
    fragility, prefer defaults over menus, gotchas, templates, checklists, validation loops,
    plan-validate-execute, bundle repeated scripts). Those sections are well-aligned with
    [best-practices](https://agentskills.io/skill-creation/best-practices) and
    [evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills).
