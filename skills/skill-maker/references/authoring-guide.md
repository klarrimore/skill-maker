# Skill Authoring Guide

How to write a skill an agent uses well. Hard frontmatter and structure rules live in
`spec-reference.md`; this file covers judgment: what to put in the body, how to phrase it, and
what to leave out. Read before writing the `SKILL.md` body.

## Decide first: skill or always-on instruction

Not everything should be a skill. Skills are model-invoked on a description match; the model
under-triggers them for behavior that should always be active. Decide the mechanism before
drafting.

- Make it a skill when the content is a discrete, task-class capability invoked by recognizable
  contexts (analyze a filing, build a model, draft in a specific voice). It has a "when," and
  that "when" is not "always."
- Make it an always-on instruction (the client's always-on instruction file, for example
  AGENTS.md or a client-specific equivalent) when the content is ambient discipline that should
  govern all work regardless of task: coding standards, output formatting, tone, "verify before
  claiming done." A skill carrying this fires inconsistently; it has no discrete trigger.

The tell: if the honest trigger description would be "use this on every task," it is not a
skill. Recommend the always-on layer instead, and stop. Catch this at authoring time, so
miscategorized content never ships as a skill.

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
always in context), the `SKILL.md` body (in context whenever the skill activates), and bundled
resources (loaded on demand; scripts can execute without being read into context at all).
Practical rules:

- Keep `SKILL.md` under 500 lines and roughly 5000 tokens. Approaching the limit signals you
  should add a layer of hierarchy: move detail into a reference file, leave a clear pointer.
- Reference files clearly from `SKILL.md`; say when to read each one, not just that it exists.
- For a large reference file (over ~300 lines), add a table of contents at the top.
- When a skill spans multiple variants (frameworks, clouds, domains), organize by variant so
  the agent reads only the relevant file:

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

Explain why behind each instruction instead of stacking heavy-handed MUSTs. Modern models have
good theory of mind; given the reasoning, they generalize past the literal text. If you write
ALWAYS or NEVER in all caps, or build a rigid scaffold, treat it as a yellow flag: reframe as
"do X because Y tends to cause Z" where the operation allows. Reserve hard prescription for
fragile steps that need one exact sequence.

Write the skill to be general, not welded to the examples you tested on. A skill runs many
times across many prompts; if it only works on your three test cases, it is useless. Draft it,
then reread with fresh eyes and cut.

## Do's and Don'ts

These consolidate the standard's authoring guidance and the most common failure modes.

### Do

- Ground the skill in real expertise. Extract the reusable pattern from a hands-on task, or
  synthesize from real artifacts (runbooks, style guides, API specs, code-review comments,
  version-control history, real failures).
- Refine with real execution. Run the skill on real tasks; feed all results back, not just
  failures. One execute-then-revise pass noticeably improves quality.
- Read execution traces, not just final outputs, to spot vague or inapplicable instructions, or
  too many options with no default.
- Add only what the agent lacks; omit what it knows. Ask of every line: would the agent get this
  wrong without this instruction? If no, cut it.
- Design coherent units of work that compose well, as you would scope a function.
- Aim for moderate detail. Concise stepwise guidance with a working example beats exhaustive
  documentation.
- Keep `SKILL.md` under 500 lines and roughly 5000 tokens; move detail into `references/`.
- Tell the agent when to load each reference file (for example, "Read references/api-errors.md
  if the API returns a non-200 status"), not a generic "see references/".
- Match specificity to fragility. Give freedom where multiple approaches are valid, and explain
  why; be prescriptive where operations are fragile or need a specific sequence.
- Provide defaults, not menus. Pick a default tool or approach; mention alternatives briefly.
- Favor procedures over declarations: teach how to approach a class of problems, not what to
  produce for one instance.
- Include a "Gotchas" section for environment-specific facts that defy reasonable assumptions.
  Keep gotchas in `SKILL.md` so the agent reads them before hitting the situation. When you
  correct an agent mistake, add it to gotchas.
- Provide output-format templates (inline for short ones, in `assets/` for longer or conditional
  ones).
- Use checklists for multi-step workflows, validation loops (do, validate, fix, repeat), and
  plan-validate-execute for batch or destructive operations.
- Bundle a tested script in `scripts/` when traces show the agent reinventing the same logic
  each run.
- Write the description imperatively, focused on user intent, pushy, concise (aim for 256
  characters or fewer, treat 512 as the working ceiling, 1024 as the hard limit), including
  contexts where the user does not name the domain.
- Make the `name` kebab-case and match the parent directory name exactly.
- Design scripts for non-interactive use, with helpful errors and structured output. See
  `references/scripts.md` for the full rules on dependencies, idempotency, `--dry-run`, exit
  codes, and output size.
- Validate with `skills-ref validate ./your-skill` (or the bundled validator) before
  distributing.
- Test triggering with eval queries, run each several times, and use a train/validation split
  to avoid overfitting.

### Don't

- Do not ask a model to generate a skill from general knowledge alone. The result is vague,
  generic procedure ("handle errors appropriately", "follow best practices"), not the specific
  patterns that make a skill valuable. This is the primary anti-pattern.
- Do not explain what the agent already knows (what a PDF is, how HTTP works, what a migration
  does).
- Do not scope a skill too narrowly (it forces several skills to co-load and risks conflicting
  instructions) or too broadly (it becomes hard to trigger precisely). A skill that both queries
  and administers a database tries to do too much.
- Do not over-document. Covering every edge case makes the agent struggle to find what is
  relevant, and pursue dead ends from inapplicable instructions. Often the agent's own judgment
  beats another paragraph.
- Do not present many equal options ("you can use pypdf, pdfplumber, PyMuPDF, or pdf2image").
  Give a clear default with an escape hatch.
- Do not write specific-answer instructions ("join orders to customers on customer_id, filter
  region EMEA") when you need a reusable method.
- Do not bury gotchas in a reference file the agent may never load.
- Do not use deeply nested reference chains; keep references one level deep from `SKILL.md`.
- Do not write rigid ALWAYS/NEVER directives where reasoning-based instructions work better.
- Do not let the description grow past the 512-character working ceiling without good reason,
  and never past the 1024-character hard limit. Do not overfit it by stuffing in specific
  keywords from failed eval queries; address the general category instead.
- Do not write scripts with interactive prompts. Agents run in non-interactive shells; a
  blocking prompt hangs forever.
- Do not emit opaque errors ("Error: invalid input") or free-form output that is hard to parse.
- Do not keep instructions the traces show the agent ignoring or wasting time on; simplify or
  remove them.
- Do not write a weak description ("Helps with PDFs"). Under-specification is the single most
  common reason a skill fails to trigger.
- Do not treat a portability rule as a spec rule. A skill with a client-specific top-level field
  is spec-conformant but non-portable, not spec-invalid. The spec defines six fields and does
  not forbid extras. For authority tiers see `references/spec-provenance.md`; for the field set
  see `references/spec-reference.md`.
- Do not ship a skill whose real behavior would surprise a user who only read its description,
  and never ship malware or exploit code.
- Do not give a skill a vague name (`helper`, `utils`, `tools`, `documents`, `data`). The name
  is part of how the skill is recognized; make it specific.
- Do not mix terms for one concept. Pick one term ("API endpoint" or "route" or "path", not all
  three) and use it throughout; inconsistent terminology makes instructions ambiguous.
- Do not reference another skill by name from inside a skill. The standard does not support
  skill-to-skill composition; that is the agent's job. Cross-references also break when the
  referenced skill is renamed, moved, or absent.