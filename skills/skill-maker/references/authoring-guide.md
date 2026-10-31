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
  A pointer that names the full skill-relative path (e.g. `references/guide.md`) satisfies the
  audit check; a bare filename does not if a file in a different directory shares the same
  basename.
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

## The portable core

Agent-agnostic output uses only the six portable frontmatter fields (`name`, `description`,
`license`, `allowed-tools`, `metadata`, `compatibility`).

Client-specific fields (`context: fork`, `user-invocable`, `model`, platform-specific policy
files) are spec-conformant extensions that lock the skill to the clients that read them. Keep
them out of the portable core. If you need one, document it in `compatibility` so users are
not surprised.

## Converting an existing client-specific skill

1. **Inspect** the existing skill with import mode to see what client extensions it carries
   without rejecting it:
   ```bash
   python -m scripts.quick_validate <skill> --mode import --json
   ```
   Import mode reports unknown fields, name mismatches, angle brackets, em dashes, and
   optional-field violations as warnings, not errors.
2. **Decide** whether to convert to portable or leave it client-specific. Conversion means
   removing or relocating client extensions into `compatibility` and resolving all warnings.
3. When converting, **copy** the skill, resolve warnings explicitly, and pass strict validation.
   Never let import-mode validity authorize packaging or installation.
4. When preserving an existing client extension, **keep** the extension documented in
   `compatibility` and accept that the skill is not portable to other clients.

## First-sentence routing signal

The first sentence of `description` is the primary signal an agent uses to decide whether to
activate the skill. Make the first sentence state the action and the domain:

- Good: "Extracts text and tables from PDF files. Use when working with PDF documents, forms,
  or document extraction."
- Poor: "A skill for working with PDFs that helps you extract data." (the action is buried)
- Poor: "Helps with PDFs." (no action)

The first ~30 characters carry the most weight. Lead with the verb and the object. Push trigger
keywords into the second sentence so a short first sentence already communicates the function.

## Near-miss boundaries

Add near-miss negative trigger queries that share domain vocabulary with the skill but should
not trigger it. This prevents false positives from conceptually adjacent tasks. For example,
a PDF extraction skill should have a negative query like "create a PDF" (creation, not
extraction) or "sign this document" (signing, not extraction). The audit checks that negative
queries share recognizable terms with the description.

## Default omission of `allowed-tools`

The `allowed-tools` field is experimental; support varies by agent. The portable core omits it
by default: pre-approval is client-specific and requires explicit trust review. If a target
adapter requires it, add it only after reviewing the tool list against the skill's real needs.
The offline audit warns when `allowed-tools` is present.

## Format validation is not a safety review

The bundled validator checks format constraints (frontmatter, field types, name rules, body
budgets). It does not inspect whether the skill's behavior matches its description, ships
malware, or exfiltrates data. A passing strict validation means the skill is portable-spec
conformant, not that it is safe.

The spec is silent on security, but skills execute bundled scripts with the agent's permissions,
and their instructions are processed at operator level. Treat any third-party skill like an
unaudited dependency: inspect before installing, prefer trusted sources, and sandbox script
execution.

## Do's and Don'ts

These consolidate the standard's authoring guidance and the most common failure modes.

### Do

- Ground the skill in real expertise. Extract the reusable pattern from a hands-on task, or
  synthesize from real artifacts (runbooks, style guides, API specs, code-review comments,
  version-control history, real failures). Asking a model to generate a skill from general
  knowledge alone is the primary anti-pattern: it yields vague, generic procedure ("handle errors
  appropriately", "follow best practices"), not the specific patterns that make a skill valuable.
- Refine with real execution. Run the skill on real tasks; feed all results back, not just
  failures. One execute-then-revise pass noticeably improves quality.
- Read execution traces, not just final outputs, to spot vague or inapplicable instructions, or
  too many options with no default. Simplify or remove instructions the traces show the agent
  ignoring or wasting time on.
- Add only what the agent lacks; omit what it knows (what a PDF is, how HTTP works, what a
  migration does). Ask of every line: would the agent get this wrong without this instruction?
  If no, cut it.
- Design coherent units of work that compose well, as you would scope a function. Too narrow
  forces several skills to co-load and risks conflicting instructions; too broad makes the skill
  hard to trigger precisely (a skill that both queries and administers a database does too much).
- Aim for moderate detail. Concise stepwise guidance with a working example beats exhaustive
  documentation: covering every edge case makes the agent struggle to find what is relevant and
  pursue dead ends from inapplicable instructions. Often the agent's own judgment beats another
  paragraph.
- Keep `SKILL.md` under 500 lines and roughly 5000 tokens; move detail into `references/`.
- Tell the agent when to load each reference file (for example, "Read references/api-errors.md
  if the API returns a non-200 status"), not a generic "see references/". Name the full
  skill-relative path, not just the filename.
- Match specificity to fragility. Give freedom where multiple approaches are valid, and explain
  why; be prescriptive where operations are fragile or need a specific sequence.
- Provide defaults, not menus. Pick a default tool or approach; mention alternatives briefly as
  an escape hatch, rather than listing equal options ("pypdf, pdfplumber, PyMuPDF, or pdf2image").
- Favor procedures over declarations: teach how to approach a class of problems, not what to
  produce for one instance ("join orders to customers on customer_id, filter region EMEA" is an
  answer, not a reusable method).
- Include a "Gotchas" section for environment-specific facts that defy reasonable assumptions.
  Keep gotchas in `SKILL.md` so the agent reads them before hitting the situation. When you
  correct an agent mistake, add it to gotchas.
- Provide output-format templates (inline for short ones, in `assets/` for longer or conditional
  ones).
- Use checklists for multi-step workflows, validation loops (do, validate, fix, repeat), and
  plan-validate-execute for batch or destructive operations.
- Read `references/scripts.md` before bundling executable code; it owns when to bundle and the
  script design checklist.
- Validate with `skills-ref validate ./your-skill` (or the bundled validator) before
  distributing.
- Test triggering with eval queries, run each several times, and use a train/validation split
  to avoid overfitting.
- Keep references one level deep from `SKILL.md`. The offline audit warns when packaged files
  sit below `references/<subdirectory>/…`.

### Don't

- Do not let the description grow past the 512-character working ceiling without good reason,
  and never past the 1024-character hard limit. Do not overfit it by stuffing in specific
  keywords from failed eval queries; address the general category instead.
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
- Do not name a specific host product or vendor in the skill's own `name` field or body prose
  (for example, writing "this Claude Code skill..." or "when using Codex..."). Two
  independently confirmed reasons make this cost real, not hypothetical: Claude's platform
  docs reject a `name` containing the substrings "anthropic" or "claude" outright, and
  separately, Codex's own cross-agent migration tooling mechanically rewrites literal,
  word-boundary-matched mentions of "claude", "claude code", "claude-code", "claude_code",
  and "claudecode" to "Codex" inside an imported `SKILL.md`'s own prose, silently changing
  what the skill says about itself on import. Describe behavior by capability instead, the
  same way `references/environment-adaptations.md` already does, and see
  `references/spec-reference.md`'s name rules for the same guidance applied to `name` itself.
- Do not mix terms for one concept. Pick one term ("API endpoint" or "route" or "path", not all
  three) and use it throughout; inconsistent terminology makes instructions ambiguous.
- Do not reference another skill by name from inside a skill. The standard does not support
  skill-to-skill composition; that is the agent's job. Cross-references also break when the
  referenced skill is renamed, moved, or absent.