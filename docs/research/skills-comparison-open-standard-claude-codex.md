# Agent Skills Across Ecosystems — Open Standard vs. Claude vs. Codex

## Scope & method

This is a **synthesis**, not new primary research. It pulls the cross-cutting divergences out of
three sibling documents in this directory, each independently primary-sourced against official
docs and pinned repository commits:

- [`agentskills-spec-and-best-practices.md`](./agentskills-spec-and-best-practices.md) — the open
  agentskills.io standard. Accessed 2026-09-30, pinned to
  [`agentskills/agentskills@69ef37e`](https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379).
- [`claude-skills-spec-and-best-practices.md`](./claude-skills-spec-and-best-practices.md) —
  Anthropic's Claude Developer Platform, Claude Code, and claude.ai. Accessed 2026-09-30, pinned
  to [`anthropics/skills@8a1541c`](https://github.com/anthropics/skills/commit/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4).
- [`codex-skills-spec-and-best-practices.md`](./codex-skills-spec-and-best-practices.md) — OpenAI
  Codex and the separate AGENTS.md convention. Accessed 2026-09-30, pinned to
  [`openai/codex@0b43721`](https://github.com/openai/codex/commit/0b43721d8d1f734658e41bffe12a6ba6c9240abd),
  [`openai/skills@49f948f`](https://github.com/openai/skills/commit/49f948faa9258a0c61caceaf225e179651397431),
  [`openai/plugins@5fd93af`](https://github.com/openai/plugins/commit/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f),
  and [`agentsmd/agents.md@ba9474a`](https://github.com/agentsmd/agents.md/commit/ba9474a69e9a2c0c4176713843b78e8f54377941)
  (first commit).

Every row below traces to a specific section of one of those three files, which in turn traces to
a primary source. Where a claim needed a sharper citation than "see the sibling file," the
original URL/commit is repeated here too. Nothing in this document was independently re-fetched;
treat any date-sensitive claim as accurate as of 2026-09-30, the shared access date of all three
inputs.

---

## 1. Timeline and governance

| Date | Event | Source |
| --- | --- | --- |
| 2025-08-19 | AGENTS.md's repository's first commit. Multi-vendor from inception (OpenAI Codex, Amp, Jules, Cursor, Factory named as founding contributors); now stewarded by the Agentic AI Foundation (Linux Foundation) | codex file §8.1, citing `agentsmd/agents.md@ba9474a` |
| 2025-10-16 | Anthropic launches Claude's proprietary Skills feature — Claude apps, Claude Code, and the Developer Platform simultaneously | claude file §14, citing [claude.com/blog/skills](https://claude.com/blog/skills) |
| 2025-12-16 | First commit to `agentskills/agentskills` (`init`) | agentskills file §11 (corrected from an earlier draft's 2025-12-18, which was the *second* commit) |
| 2025-12-18 | Anthropic publishes Agent Skills as an open standard, per its own blog's update log | claude file §14 |
| 2026-06-22/23 | `openai/skills` (flat skills catalog) deprecated in favor of `openai/plugins` | codex file §6 |

**The load-bearing fact: Claude's proprietary Skills feature predates the open standard by about
two months.** The open standard was extracted from Claude's already-shipped design, not the
reverse (claude file §14). AGENTS.md predates both, and is an entirely separate lineage — the
agents.md project's own site never mentions "skill" anywhere (codex file, Scope & method; §8.1),
so any resemblance between `.agents/skills/` (the Skills discovery convention) and `AGENTS.md`
(the always-loaded guidance file) is a naming coincidence, not a shared origin. See §7 below for
how Codex, the one client implementing both, keeps them distinct.

Codex explicitly builds on the open standard by its own account: "Skills build on the [open agent
skills standard](https://agentskills.io)" (codex file §1). Claude Code says the same of itself:
"Claude Code skills follow the [Agent Skills](https://agentskills.io) open standard... Claude Code
extends the standard with additional features" (claude file, Scope & method). Both vendors
describe themselves as extending, not replacing, the six-field core — but each extends and
*enforces* it differently, which is the rest of this document.

---

## 2. Frontmatter fields: what each surface actually recognizes

The open standard defines exactly six fields (`name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`). Both vendors confirm this is the portable core, then diverge on
enforcement:

| Surface | Fields it reads/enforces | Extra fields beyond the six | Source |
| --- | --- | --- | --- |
| **Open standard** (`skills-ref` reference validator) | All six, `name`/`description` required | None — extra top-level keys are a validation error | agentskills file §5 |
| **Claude Code** (local/interactive) | All six **plus 14 more** (see §5 below); `name`/`description` both **optional**, with fallbacks | `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell` | claude file §4 |
| **Claude export surfaces** (claude.ai upload, Skills API, `package_skill.py`) | Exactly the six; violating this is a **hard error**, not a silent drop | None allowed — quoted error: `Unexpected key(s) in SKILL.md frontmatter: argument-hint. Allowed properties are: allowed-tools, compatibility, description, license, metadata, name` | claude file §3 |
| **Codex runtime loader** (`codex-rs/skills/src/parser.rs`) | Only `name`, `description`, `metadata.short-description` — **everything else, including `license`/`compatibility`/`allowed-tools`, is silently ignored, not rejected** | None modeled in the deserializer at all | codex file §2.1 |
| **Codex `quick_validate.py`** (authoring-time only, not the runtime loader) | Five of six — `{name, description, license, allowed-tools, metadata}`, **missing `compatibility`** | None allowed beyond those five | codex file §2.2, §Implications-1 |
| **Codex `agents/openai.yaml`** (separate file, not `SKILL.md` frontmatter) | `interface.*`, `dependencies.tools[].*`, `policy.*` — a wholly separate schema | N/A — this isn't SKILL.md frontmatter at all | codex file §5 |

**The practical trap this creates**: a skill using the spec's own `compatibility` field —
allowed by the open standard, allowed by `skills-ref`, allowed by this repo's own validator, and
silently *ignored but harmless* by Codex's runtime — will still be **rejected** by Codex's own
bundled authoring tool (`quick_validate.py`) with an "Unexpected key" error, because that script's
allow-list has only five fields, not six (codex file, Implications #1). No single validator in
this entire ecosystem currently agrees with every other validator on the exact same six-field
allow-list in practice, even though all of them *cite* the same six-field standard.

---

## 3. `name` and `description`: four independent rule sets

| Rule | Open standard (`skills-ref`) | Claude (`skill-creator`'s `quick_validate.py`) | Codex runtime loader | Codex `quick_validate.py` |
| --- | --- | --- | --- | --- |
| `name` charset | Unicode-aware: NFKC-normalized, `str.isalnum()` — accepts Chinese, Russian, decomposed accents | ASCII-only: `^[a-z0-9-]+$` | **No charset check at all** — only a length cap | ASCII-only: `^[a-z0-9-]+$` (matches Claude's) |
| `name` length | ≤64 chars, NFKC-normalized | ≤64 chars | ≤64 raw chars (no normalization) — plus a **129-char** cap on the derived, plugin-namespaced qualified name | ≤64 chars |
| `name` must equal directory | **Yes, enforced** | **Not enforced anywhere in Claude's ecosystem** | **Not enforced** — falls back to directory name only when `name` is absent | Not checked |
| `name` reserved words | None defined by the standard | `anthropic`, `claude` forbidden as substrings (Claude Code docs; **not** checked by `quick_validate.py` itself) | None found | None found |
| `description` required/non-empty | Yes, hard requirement | Yes in prose, but `quick_validate.py`'s own check is guarded by `if description:` — an empty string silently **passes** | Yes, hard requirement — missing/empty is a load failure | Same `if description:` gap as Claude's — empty string **passes** |
| `description` length | ≤1024 chars | ≤1024 chars (`quick_validate.py`); Claude Code truncates at 1,536 for its own listing budget; claude.ai Help Center says 200 (unresolved internal inconsistency, claude file §3) | **No upper-length check at load time** — a 5,000-char description loads fine; only the *display/catalog* renderer truncates at 1,024 chars for matching purposes | ≤1024 chars |
| `description` angle brackets | Not mentioned by the spec text; unverified against `skills-ref` (agentskills file, Gap #1) | **Rejected** — "Description cannot contain angle brackets (< or >)" | **Not rejected** at runtime | **Rejected** — identical error string to Claude's |

**The angle-bracket rule has one lineage, not two.** A direct diff between Anthropic's
`skill-creator/scripts/quick_validate.py` and Codex's own `skill-creator/scripts/quick_validate.py`
shows the same function name (`validate_skill`), the same control flow, and matching error strings
verbatim (codex file, Implications #3). This is a shared-ancestor convention — plausibly tracing
back to Anthropic's original `skill-creator` reference tooling, which the open standard's own
best-practices guide points to (agentskills file §7) — not two vendors independently converging on
the same answer. This repo's own bundled validator applies the identical rule
(`skills/skill-maker/scripts/quick_validate.py`, per `spec-provenance.md`), so all three
implementations very likely share one lineage.

**Empty-string laxness is convergent, not shared**: the open standard's own `skills-ref` has an
analogous gap on `compatibility` (no enforced minimum length despite the spec text saying "1–500
characters if provided" — agentskills file §5), and *both* vendors' `quick_validate.py` scripts
have the identical `if description:` guard-skips-empty-string bug independently. Three different
codebases, three different instances of the same class of validation gap.

---

## 4. Discovery, precedence, and collision behavior

This is the sharpest three-way divergence in the entire comparison.

| | Open standard's stated convention | Claude Code | Codex |
| --- | --- | --- | --- |
| Collision rule | **"Project-level skills override user-level skills"** — called "the universal convention across existing implementations" | **"Enterprise over personal, and personal over project"** — the literal reverse of the open standard's stated convention for the personal/project pair | **Neither overrides** — same-named skills from different scopes **coexist**; Codex's own doc says outright: "If two skills share the same `name`, Codex doesn't merge them; both can appear in skill selectors" |
| Extra hierarchy tiers | None defined | Enterprise, personal, project, nested, plugin (namespaced), claude.ai-synced — five extra tiers | Repo (3 paths), User (2 paths, one deprecated), Admin, System — six scopes total |
| What resolves a name at invocation time | Not addressed (the standard has no explicit-invocation concept) | `/skill-name` unambiguously targets one skill per precedence order above | A bare `$skill-name` mention **only resolves when exactly one loaded skill has that name and no installed connector shares the slug** — a collision makes plain-text mentions **silently fail to resolve** |
| Source | agentskills file §4 | claude file §5 | codex file §3.1, §9.3 |

So of the three implementations investigated, **zero** actually implement the open standard's own
described "universal convention." Claude Code inverts it (for personal/project); Codex sidesteps
override semantics entirely in favor of coexistence-plus-ambiguity. An author relying on the open
standard's collision guidance to reason about what happens when they accidentally reuse a name
will be wrong about the actual behavior on both major clients investigated here.

**Directory-placement convention**: both vendors use the plural `.agents/skills/` — neither uses
the singular `~/.agent/skills/` that this repo's reference material had flagged as unverified
(agentskills file, Gap #3; codex file, Implications #5, confirming via Codex's own
`AGENTS_DIR_NAME`/`SKILLS_DIR_NAME` constants). Claude Code additionally scans `.claude/skills/`
natively; Codex does not scan `.claude/skills/` as an ongoing discovery path, but *does* import
from it via a one-time migration (see §6 below).

---

## 5. Client-specific frontmatter extensions

Neither vendor's extension set has any counterpart in the other vendor's ecosystem or in the open
standard — these are two unrelated grammars bolted onto the same six-field core.

**Claude Code's 14 extension fields** (full table: claude file §4): `when_to_use`,
`argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`,
`model`, `effort`, `context` (with `fork`), `agent`, `background`, `hooks`, `paths`, `shell`. These
live inline in `SKILL.md`'s own YAML frontmatter, are silently ignored by Claude Code itself if
misspelled, but cause a **hard export failure** the moment the skill is packaged for claude.ai/API
use (§2 above).

**Codex's extension is a separate file, not extra frontmatter keys**: `agents/openai.yaml`, with
its own `interface`/`dependencies`/`policy` schema (codex file §5). Codex's runtime loader doesn't
even parse most `SKILL.md` frontmatter keys beyond the three it wants (§2 above), so there's no
Codex equivalent of "extra keys silently ignored in frontmatter" — the extension mechanism is
structurally different: a whole separate optional file, versus inline frontmatter fields.

One naming collision worth flagging for anyone writing both: Claude's export-validation error
message and Codex's `agents/openai.yaml` both use the word "interface," but they mean unrelated
things and use different casing conventions (`agents/openai.yaml`'s `interface` block is
`snake_case`; the *plugin manifest's* own differently-scoped `interface` block, confirmed against
a real `plugins/figma/.codex-plugin/plugin.json`, is `camelCase` — codex file §5). Three
non-interchangeable schemas share the word "interface" across this ecosystem.

---

## 6. Cross-vendor compatibility: Codex imports from Claude Code

This is the one concrete interoperability bridge found across all three research passes, and it
runs in one direction only (Codex → consumes Claude Code's format; nothing found reciprocating):

1. **One-time migration**: Codex ships an `external-agent-migration` crate that specifically
   detects `.claude/skills/*/SKILL.md` and `CLAUDE.md`, copies the skill directory tree byte-for-
   byte except `SKILL.md`'s own text, which gets `CLAUDE.md`→`AGENTS.md` and
   `claude`/`claude code`/`claude-code`/`claude_code`/`claudecode` (case-insensitive, word-boundary
   matched) rewritten to `Codex` (codex file §6.1).
2. **Ongoing, no-import-step recognition**: Codex's plugin loader natively recognizes Claude Code's
   own plugin manifest filename and location — `.claude-plugin/plugin.json` and
   `.claude-plugin/marketplace.json` — as alternate, permanently-supported manifest paths alongside
   its own `.codex-plugin/plugin.json` (codex file §6.1, citing `DISCOVERABLE_PLUGIN_MANIFEST_PATHS`
   and `MARKETPLACE_MANIFEST_RELATIVE_PATHS` directly from source). A Claude Code *plugin* can be
   dropped into Codex's plugin discovery path as-is. A **standalone** `.claude/skills/` directory
   outside any plugin structure has no such ongoing path — only the one-time migration in (1)
   applies to it.

Practical consequence for this repo: a skill authored here and later placed under `.claude/skills/`
for Claude Code use is *also* a supported Codex import source, with one caveat — any prose inside
its own `SKILL.md` that names "Claude" or "Claude Code" will be mechanically rewritten on import.
A skill that avoids naming its host product in its own body (already good cross-platform practice)
sidesteps this entirely (codex file, Implications #9).

---

## 7. AGENTS.md vs. Skills — not the same axis, and only Codex documents both

Since Codex is the only one of the two clients investigated here that also implements AGENTS.md,
this comparison is necessarily Codex-only, but it matters for anyone writing guidance that
mentions both files:

| | AGENTS.md | Agent Skills (`SKILL.md`) |
| --- | --- | --- |
| Loaded | **Always**, every task, concatenated from every applicable directory | **Progressively** — name+description always visible; full body only once selected |
| Structure | None required — plain Markdown | YAML frontmatter, `name`+`description` required |
| Size cap | 32 KiB total across all applicable files (Codex: `project_doc_max_bytes`) | Catalog ~2%/8,000 chars (Codex); a selected skill's own body capped separately (8,000 bytes on Codex, ~2,000 tokens; no hard cap stated by the open standard beyond a 5,000-token recommendation) |
| Selection | None — everything discovered is included | Implicit (description match) or explicit (`$name`/`/skill-name`) |
| Governance | Agentic AI Foundation / Linux Foundation, multi-vendor | Originated at Anthropic, now open at agentskills.io |

Source: codex file §8.2, §8.3. The practical rule of thumb it synthesizes: put something in
AGENTS.md when it should shape *every* task regardless of what the task is (build commands, style,
review rules); put it in a Skill when it's a self-contained procedure only some tasks need,
especially one worth loading on demand or invoking explicitly by name.

---

## 8. Packaging and distribution

| | Open standard | Claude | Codex |
| --- | --- | --- | --- |
| Canonical unit | A folder | A folder, or a `.skill` zip (`ZIP_DEFLATED`, folder as archive root) — **confirmed real and first-party** via `package_skill.py`, resolving the open-standard file's own "unverified" flag on this | A folder, or a plugin bundle |
| Zip format | Not mentioned anywhere on agentskills.io — "host convenience... not part of the open standard" | `.skill`, produced and validated (pre-zip) by Anthropic's own tooling | No `.skill`-equivalent found; distribution is via plugins instead |
| Plugin/bundle format | Not addressed | N/A (claude.ai/API don't have a "plugin" concept distinct from a Skill upload) | **Two coexisting manifest layouts**: current-default `.codex-plugin/plugin.json` ("compatibility" layout, what every real example still uses) and a newer portable root `plugin.json` declaring an `agent-plugins.org` schema |
| Validation before packaging | `skills-ref validate` (explicitly demonstration-only) | `package_skill.py` **runs `quick_validate.py` before zipping and refuses on failure** | `quick_validate.py` is a separate authoring-time tool, not gated into any packaging step found |

Source: agentskills file §5, §9 (Gaps); claude file §9; codex file §6.

---

## 9. Token/character budgets, side by side

| Tier | Open standard | Claude | Codex |
| --- | --- | --- | --- |
| Tier 1 (catalog: name+description, always loaded) | ~100 tokens/skill (spec text), ~50–100 (client guide) | ~100 tokens/skill; catalog capped at **1% of context window**; each entry's description+`when_to_use` truncated at **1,536 chars** | Catalog capped at **2% of context window, or 8,000 chars if unknown**; each entry's description truncated at **1,024 chars** (`MAX_CATALOG_SKILL_DESCRIPTION_CHARS`) |
| Tier 2 (selected skill's body) | "< 5,000 tokens recommended" (soft) | Same <5,000-token/<500-line figures repeated verbatim; **5,000-token cap per skill / 25,000-token combined cap on post-compaction re-attachment** | **8,000-byte hard cap** (`MAX_SKILL_PROMPT_BYTES`, ~2,000 tokens) — tighter than the spec's own recommendation, applying to standalone skills too whenever the skills extension is active (the default case) |
| Tier 3 (resources) | "As needed," no cap stated | None until accessed | None additional found beyond tier-2's cap on the body that references them |

Note the asymmetry: Claude's tier-2 number (5,000 tokens) matches the open standard's own
recommendation; Codex's hard tier-2 cap (8,000 bytes ≈ 2,000 tokens) is **less than half** of that
— a body comfortably under this repo's own soft warning threshold (5,000 tokens / 500 lines) can
still be more than double what Codex will inject before silently truncating it mid-instruction
(codex file, Implications #6). Source: claude file §1; codex file §4.1, §4.1.1.

---

## 10. Security and governance posture

Both vendors have built substantially more developed, product-specific tooling than the open
standard addresses (which is silent on security beyond "gate project-level loading on a trust
check" — agentskills file §4):

- **Claude**: an enterprise risk-tier table (code execution, instruction manipulation, MCP
  references, network access, hardcoded credentials, filesystem scope, tool invocations, each
  rated High/Medium), an eight-step review checklist, evaluation gates before production
  (triggering accuracy, isolation, coexistence, instruction-following, cross-model testing,
  separation-of-duties review), and optional automated content scanning for claude.ai/Cowork
  uploads — explicitly **not** covering the Skills API (claude file §13, §15).
- **Codex**: no equivalent enterprise security guide was found in this research pass; Codex's
  security-adjacent behavior found was narrower — escaping/sanitizing display text for
  synced/imported content (paralleling Claude Code's own synced-skill sanitization) and the
  `[[skills.config]]` disable-by-path/name mechanism. This asymmetry may reflect what each research
  pass happened to find rather than a real capability gap; it was not independently confirmed that
  Codex lacks equivalent enterprise tooling.

---

## Implications for `skill-maker`

Concrete, cross-cutting points worth acting on, consolidating the individual "Implications"
sections of the three sibling files:

1. **The six-field allow-list is not universally agreed even among validators that cite the same
   standard.** This repo's own validator, the open standard's `skills-ref`, and Claude's
   `quick_validate.py` all check exactly six fields. Codex's own bundled `quick_validate.py` checks
   only five (missing `compatibility`). A skill using `compatibility` legitimately will fail
   Codex's own authoring tool even though it's spec-conformant and loads fine in Codex's actual
   runtime. Worth a one-line caveat wherever this repo claims cross-client validator parity.
2. **The directory-must-equal-`name` rule is an open-standard-only requirement.** Neither Claude's
   nor Codex's ecosystem enforces it anywhere. This repo should keep enforcing it regardless (it's
   the strictly stricter, superset rule, and it's what makes a skill portable to the open
   standard's own reference validator), but should not claim it as a universally-enforced rule —
   only as this repo's own portability guarantee.
3. **Angle-bracket rejection and the six-field allow-list are inherited conventions, not
   independent validation**: this repo's validator very likely shares a common `skill-creator`
   lineage with both Anthropic's and OpenAI's bundled validators (matching function names, control
   flow, and error strings). Worth documenting as "this convention traces to a shared tooling
   ancestor," not "three vendors independently agreed."
4. **Collision/precedence guidance needs a caveat, not a single answer.** The open standard's
   "project overrides user" convention is not what either investigated client actually does:
   Claude Code inverts it for personal/project; Codex does neither and instead lets same-named
   skills coexist with silent-failure-on-ambiguous-mention. Any authoring guidance this repo gives
   about choosing skill names to avoid collisions should say this plainly rather than assume one
   universal resolution rule.
5. **Body-length guidance should mention Codex's materially tighter hard cap** (8,000 bytes ≈
   2,000 tokens) alongside the open standard's own 5,000-token soft recommendation that this repo's
   validator currently warns against. A skill that's clean by this repo's own budget can still be
   silently truncated mid-instruction on Codex.
6. **If this repo ever documents "installing for Codex,"** use `~/.agents/skills` or a repo-local
   `.agents/skills`, not `~/.codex/skills` — Codex's own source calls the latter "deprecated...
   kept for backward compatibility," even though Codex's own bundled `skill-creator` skill still
   tells authors to use it (an inconsistency inside Codex's own tooling, not this repo's error to
   fix).
7. **A skill placed under `.claude/skills/` is automatically a Codex-import candidate.** Authors
   targeting both ecosystems should avoid naming "Claude" or "Claude Code" in their `SKILL.md`
   prose if they want predictable behavior after a Codex import rewrites those mentions.
