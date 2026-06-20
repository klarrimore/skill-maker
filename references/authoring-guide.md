# Skill Authoring Guide

How to write a skill that an agent actually uses well. The hard frontmatter and structure
rules are in `spec-reference.md`; this file is about judgment: what to put in the body,
how to phrase it, and what to leave out. Read it before writing the `SKILL.md` body.

## Anatomy of a skill

```
skill-name/
|-- SKILL.md (required)
|   |-- YAML frontmatter (name, description required)
|   \-- Markdown instructions
\-- Bundled resources (optional)
    |-- scripts/    - executable code for deterministic, repetitive tasks
    |-- references/ - docs loaded into context only as needed
    \-- assets/     - files used in output (templates, icons, fonts)
```

## Progressive disclosure in practice

Three loading tiers (full detail in `spec-reference.md`): metadata (`name` + `description`,
always in context), the `SKILL.md` body (in context whenever the skill activates), and
bundled resources (loaded on demand; scripts can execute without being read into context
at all). The practical rules that follow from this:

- Keep `SKILL.md` under 500 lines and roughly 5000 tokens. Approaching the limit is the
  signal to add a layer of hierarchy: move detail into a reference file and leave a clear
  pointer to it.
- Reference files clearly from `SKILL.md`, and say when to read each one, not just that it
  exists.
- For a large reference file (over ~300 lines), add a table of contents at the top.
- When a skill spans multiple variants (frameworks, clouds, domains), organize by variant
  so the agent reads only the one relevant file:

```
cloud-deploy/
|-- SKILL.md            (workflow + which variant to pick)
\-- references/
    |-- aws.md
    |-- gcp.md
    \-- azure.md
```

## Writing patterns

Prefer the imperative.

Define an output format explicitly when one matters:

```markdown
## Report structure
Use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

Show examples; agents pattern-match well against concrete structures:

```markdown
## Commit message format
Example:
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

For longer or conditional output templates, put the template in `assets/` and point to it
rather than inlining a large block.

## Writing style

Explain the why behind each instruction instead of stacking heavy-handed MUSTs. Modern
models have good theory of mind; given the reasoning, they generalize past the literal
text. If you catch yourself writing ALWAYS or NEVER in all caps or building a rigid
scaffold, treat it as a yellow flag: reframe as "do X because Y tends to cause Z" where
the operation allows it. Reserve hard prescription for genuinely fragile steps where one
exact sequence is required.

Write the skill to be general, not welded to the specific examples you tested on. A skill
exists to be run many times across many prompts; if it only works on your three test
cases, it is useless. Draft it, then reread it with fresh eyes and cut.

## Do's and Don'ts

These consolidate the standard's authoring guidance and the most common failure modes.

### Do

- Ground the skill in real expertise. Extract the reusable pattern from a hands-on task,
  or synthesize from real artifacts (runbooks, style guides, API specs, code-review
  comments, version-control history, real failures).
- Refine with real execution. Run the skill on real tasks and feed all results back in,
  not just the failures. Even one execute-then-revise pass noticeably improves quality.
- Read execution traces, not just final outputs, to spot vague instructions, inapplicable
  instructions, or too many options with no default.
- Add only what the agent lacks; omit what it knows. For every line ask: would the agent
  get this wrong without this instruction? If no, cut it.
- Design coherent units of work that compose well, the way you would scope a function.
- Aim for moderate detail. Concise stepwise guidance with a working example beats
  exhaustive documentation.
- Keep `SKILL.md` under 500 lines and roughly 5000 tokens; move detail into `references/`.
- Tell the agent when to load each reference file (for example, "Read
  references/api-errors.md if the API returns a non-200 status"), not a generic "see
  references/".
- Match specificity to fragility. Give freedom where multiple approaches are valid and
  explain why; be prescriptive where operations are fragile or a specific sequence is
  required.
- Provide defaults, not menus. Pick a default tool or approach and mention alternatives
  briefly.
- Favor procedures over declarations: teach how to approach a class of problems, not what
  to produce for one instance.
- Include a "Gotchas" section for environment-specific facts that defy reasonable
  assumptions, and keep gotchas in `SKILL.md` so the agent reads them before hitting the
  situation. When you correct an agent mistake, add it to gotchas.
- Provide output-format templates (inline for short ones, in `assets/` for longer or
  conditional ones).
- Use checklists for multi-step workflows, validation loops (do, validate, fix, repeat),
  and plan-validate-execute for batch or destructive operations.
- Bundle a tested script in `scripts/` when traces show the agent reinventing the same
  logic each run.
- Write the description imperatively, focused on user intent, pushy, and concise (under
  1024 characters), including contexts where the user does not name the domain.
- Make the `name` kebab-case and exactly match the parent directory name.
- Design scripts for non-interactive use: accept input via flags, env, or stdin; document
  usage with `--help`; write helpful errors; emit structured output (JSON, CSV, TSV); send
  data to stdout and diagnostics to stderr; be idempotent; offer `--dry-run` for
  destructive ops; use documented exit codes; pin dependency versions; keep output size
  predictable.
- Validate with `skills-ref validate ./your-skill` (or the bundled validator) before
  distributing.
- Test triggering with eval queries, run each several times, and use a train/validation
  split to avoid overfitting.

### Don't

- Do not ask a model to generate a skill from general knowledge alone. The result is
  vague, generic procedure ("handle errors appropriately", "follow best practices")
  instead of the specific patterns that make a skill valuable. This is the primary
  anti-pattern.
- Do not explain what the agent already knows (what a PDF is, how HTTP works, what a
  migration does).
- Do not scope a skill too narrowly (it forces several skills to co-load and risks
  conflicting instructions) or too broadly (it becomes hard to trigger precisely). A skill
  that both queries a database and administers it is trying to do too much.
- Do not over-document. Covering every edge case makes the agent struggle to find what is
  relevant and pursue dead ends from inapplicable instructions. Often the agent's own
  judgment is better than another paragraph.
- Do not present many equal options ("you can use pypdf, pdfplumber, PyMuPDF, or
  pdf2image"). Give a clear default with an escape hatch.
- Do not write specific-answer instructions ("join orders to customers on customer_id,
  filter region EMEA") when a reusable method is what is needed.
- Do not bury gotchas in a reference file the agent may never load.
- Do not use deeply nested reference chains; keep references one level deep from
  `SKILL.md`.
- Do not write rigid ALWAYS/NEVER directives where reasoning-based instructions work
  better.
- Do not let the description grow past 1024 characters, and do not overfit it by stuffing
  in specific keywords from failed eval queries; address the general category instead.
- Do not write scripts with interactive prompts. Agents run in non-interactive shells; a
  blocking prompt hangs forever.
- Do not emit opaque errors ("Error: invalid input") or free-form output that is hard to
  parse.
- Do not keep instructions the traces show the agent ignoring or wasting time on; simplify
  or remove them.
- Do not write a weak description ("Helps with PDFs"). Under-specification is the single
  most common reason a skill fails to trigger.
- Do not add client-specific frontmatter fields if you want portability; see the
  portability section of `spec-reference.md`.
- Do not ship a skill whose real behavior would surprise a user who only read its
  description, and never ship malware or exploit code.
