# Claude Agent Skills — Specification and Best Practices

## Scope & method

This is a primary-source investigation of **Anthropic's own implementation** of Agent Skills:
the SKILL.md format, frontmatter, packaging, discovery/loading, and authoring guidance as
documented and shipped for the Claude Developer Platform (Messages API), Claude Code, and
claude.ai. It complements
[`agentskills-spec-and-best-practices.md`](./agentskills-spec-and-best-practices.md), which
covers the open agentskills.io standard; this file does not repeat that content except where
needed to state a divergence. Every claim below is traced to a page or file fetched and read in
this session — no blog posts, third-party summaries, or model memory.

**Accessed:** 2026-09-30.

Primary sources used, and how:

- **Claude Developer Platform docs** (platform.claude.com), fetched directly:
  - [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
  - [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
  - [Get started with Agent Skills in the API](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart)
  - [Claude API skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/claude-api-skill)
  - [Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
  - [Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
  - [Code execution tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)
  - [Skills API reference](https://platform.claude.com/docs/en/api/beta/skills) and
    [Create Skill](https://platform.claude.com/docs/en/api/beta/skills/create)
- **Claude Code docs** (code.claude.com): [Extend Claude with skills](https://code.claude.com/docs/en/skills)
  (fetched in full, ~1150 lines) and [Plugins overview](https://code.claude.com/docs/en/plugins).
- **Anthropic's own announcement and engineering posts**:
  [Introducing Agent Skills](https://claude.com/blog/skills) (redirected from
  `anthropic.com/news/skills`) and
  [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).
- **Claude Help Center** (support.claude.com):
  [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills) and
  [How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills).
- **The `anthropics/skills` GitHub repository**, read at commit
  [`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`](https://github.com/anthropics/skills/commit/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4)
  ("Update claude-api skill: Claude Opus 5.5 default, Claude Sonnet 5.5, build-eval and hillclimb
  guides (#1930)", 2026-09-29): its
  [`README.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/README.md),
  [`spec/agent-skills-spec.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/spec/agent-skills-spec.md),
  [`template/SKILL.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/template/SKILL.md),
  and the official `skill-creator` skill's
  [`SKILL.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/SKILL.md),
  [`scripts/quick_validate.py`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/scripts/quick_validate.py),
  and
  [`scripts/package_skill.py`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/scripts/package_skill.py).
  Files were fetched with `curl` against the raw content, so quotations below are exact.
- Two quotations that first came back through the assistant-summarizing form of `WebFetch` were
  re-verified with a direct `curl -sL` fetch and `grep` against the raw page before being quoted
  verbatim in this file: the Help Center's "200 characters maximum" / `dependencies` field
  (§3), and the announcement blog's "December 18, 2025" open-standard line (§14).

A note on authority. Claude Code's own docs state directly: "Claude Code skills follow the
[Agent Skills](https://agentskills.io) open standard, which works across multiple AI tools.
Claude Code extends the standard with additional features" — [Extend Claude with skills, intro](https://code.claude.com/docs/en/skills).
So the layering in this file is:

- **(a) The open standard's six fields** (`name`, `description`, `license`, `compatibility`,
  `metadata`, `allowed-tools`) — portable across Claude Code, claude.ai uploads, and the Skills
  API, per Claude Code's own table (see §3).
- **(b) Claude-specific validation on top of the standard** — the extra `name`/`description`
  rules (reserved words, no XML tags) that Anthropic's platform docs state but agentskills.io
  does not.
- **(c) Claude Code-only extensions** — the fourteen additional frontmatter fields
  (`disable-model-invocation`, `context`, `model`, etc.) that only function inside Claude Code.
- **(d) Surface-specific behavior** — discovery paths, the Skills API, the code execution
  container, claude.ai's UI — which are product behavior, not format.

---

## 1. What a Skill is, in Anthropic's model

Anthropic's platform docs define a Skill as filesystem-based: "Skills are reusable,
filesystem-based resources that give Claude domain-specific expertise" that "load on demand"
([Agent Skills overview, "Why use Skills"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
The engineering blog frames it structurally: "A skill is a directory containing a SKILL.md file
that contains organized folders of instructions, scripts, and resources that give agents
additional capabilities"
([Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)).

**Progressive disclosure, Claude's numbers.** The overview gives a three-level model matching
the open standard's three tiers, with a token-cost table:

| Level | When loaded | Token cost | Content |
| --- | --- | --- | --- |
| 1: Metadata | Always (at startup) | ~100 tokens per Skill | `name` and `description` |
| 2: Instructions | When Skill is triggered | Under 5k tokens | SKILL.md body |
| 3+: Resources | As needed | None until accessed | Bundled files; scripts run via bash, only output enters context |

— [Agent Skills overview, "How Skills work"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
Best practices repeats the line-count form of the same budget: "Keep SKILL.md body under 500
lines for optimal performance"
([Skill authoring best practices, "Progressive disclosure patterns"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

**The mechanism is literal, not metaphorical, in Claude Code and the API.** Both docs describe
Claude reading files with real shell commands: "Claude invokes: `bash: cat pdf-processing/SKILL.md`"
([overview, "Example: Loading a PDF processing Skill"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
The API version runs in the code-execution sandbox (§7); Claude Code runs it against the real
filesystem, reading `SKILL.md` "using bash Read tools"
([Skill authoring best practices, "Runtime environment"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

**Claude Code adds its own budgets beyond the shared model:**

- The skill *listing* (every skill's name + description, injected every turn) has its own
  character budget, "scales at 1% of the model's context window," configurable via
  `skillListingBudgetFraction`, and drops the lowest-usage skills' descriptions first when it
  overflows — [Extend Claude with skills, "Skill descriptions are cut short"](https://code.claude.com/docs/en/skills).
- Each skill's combined `description` + `when_to_use` text is truncated at **1,536 characters**
  in that listing, configurable via `skillListingMaxDescChars` — same section, and the
  [frontmatter reference table](https://code.claude.com/docs/en/skills#frontmatter-reference).
- After auto-compaction, re-attached skills keep "the first 5,000 tokens of each," sharing a
  combined budget of "25,000 tokens" across all re-attached skills —
  [Extend Claude with skills, "Skill content lifecycle"](https://code.claude.com/docs/en/skills).

None of these three numbers (1% budget, 1,536-char truncation, 5,000/25,000-token compaction
budget) appear in the open standard; they are Claude Code implementation limits.

---

## 2. SKILL.md format and directory structure

Anthropic's structural description matches the open standard: "Every Skill requires a `SKILL.md`
file with YAML frontmatter" followed by a Markdown body
([Agent Skills overview, "Skill structure"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)),
with the same `scripts/`, `references/`(or `reference/`), `assets/` convention shown in worked
examples throughout the best-practices guide. The `skill-creator` skill's own template
directory structure is identical:

```text
skill-name/
├── SKILL.md (required)
└── Bundled Resources (optional)
    ├── scripts/
    ├── references/
    └── assets/
```

The official minimal template, verbatim, from
[`template/SKILL.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/template/SKILL.md):

```yaml
---
name: template-skill

description: Replace with description of the skill and when Claude should use it.
---
```

followed by an "Insert instructions below" placeholder — a two-field minimal frontmatter,
matching the open standard's minimal example.

---

## 3. Frontmatter: the portable six fields, per Claude Code's own table

The single most load-bearing citation in this file is Claude Code's own statement of which
frontmatter fields are spec-portable versus Claude Code-only. Quoting in full
([Extend Claude with skills, "Using skill frontmatter outside Claude Code"](https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code)):

> "Claude Code accepts every field in the table above. Outside Claude Code, you can use only
> the fields in the [Agent Skills](https://agentskills.io) spec:"

| Distribution path | Frontmatter fields you can use |
| --- | --- |
| Claude Code skills at any level, including plugin skills | Every field in the full table (§4) |
| claude.ai skill uploads, the Skills API, and packaging with `package_skill.py` from `anthropics/skills` | `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` |

And critically, this is enforced with a hard failure, not a silent drop:

> "If you include any field the spec doesn't allow, packaging or upload fails with a hard error
> instead of ignoring the field:
> `Unexpected key(s) in SKILL.md frontmatter: argument-hint. Allowed properties are:
> allowed-tools, compatibility, description, license, metadata, name`"

This is a direct, first-party confirmation that Anthropic recognizes the open standard's exact
six-field set as the portable surface, and that everything else is a Claude Code extension. The
error message's field list matches, character for character, `ALLOWED_PROPERTIES` in
`skill-creator`'s own validator (§9).

### Name and description rules, as stated by the Developer Platform

Both the [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#skill-structure)
and [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#skill-structure)
pages state the same rules, verbatim:

`name`:
- Maximum 64 characters
- Must contain only lowercase letters, numbers, and hyphens
- Cannot contain XML tags
- Cannot contain reserved words: **"anthropic", "claude"**

`description`:
- Must be non-empty
- Maximum 1,024 characters
- Cannot contain XML tags

Best practices adds the trigger-writing requirement not in the field-limit box: "Always write in
third person. The description is injected into the system prompt, and inconsistent
point-of-view can cause discovery problems" — Good: "Processes Excel files and generates
reports"; Avoid: "I can help you..." / "You can use this to..."
([best practices, "Writing effective descriptions"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions)).

**These rules are Claude-specific, not open-standard.** The open standard has no "no XML tags"
rule and no reserved-word list (the earlier research file flagged reserved words as
"unverified" against agentskills.io — see §11 for how this file resolves that). See §10 for the
full comparison.

### Internal inconsistency across Anthropic's own surfaces

The **claude.ai-facing Help Center article** states different numbers than every
developer-facing page: "A clear description of what the skill does and when to use it... (200
characters maximum)" and lists `name`, `description`, and **`dependencies`** as the documented
metadata fields, with no mention of `license`, `compatibility`, `metadata`, or `allowed-tools`
([How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)).
This directly conflicts with the 1,024-character `description` limit and the six-field set
stated everywhere else (platform.claude.com, Claude Code docs, and the `skill-creator`
validator). This is a genuine, unresolved discrepancy inside Anthropic's own documentation, not
a misreading on this file's part (verified by fetching the article twice with an exact-quote
prompt). Treat the 1,024-character limit and six-field set as authoritative, since they are
corroborated by the API's own validator source code (§9) and by three independent
developer-facing pages; treat the Help Center's "200 characters" and "dependencies" as either
stale or describing a narrower, older claude.ai-only upload flow.

---

## 4. Claude Code's frontmatter extensions (full field table)

Claude Code's frontmatter reference table lists every field it recognizes
([Extend Claude with skills, "Frontmatter reference"](https://code.claude.com/docs/en/skills#frontmatter-reference)).
Six are the open-standard fields (§3); the rest (fourteen fields) are Claude Code-only:

| Field | Spec status | What it does |
| --- | --- | --- |
| `name` | standard | Command name; defaults to the directory name if omitted |
| `description` | standard | What Claude matches against to trigger the skill |
| `license` | standard | "Claude Code accepts the field but doesn't act on it" |
| `compatibility` | standard | Up to 500 characters; "Claude Code accepts the field but doesn't act on it" |
| `metadata` | standard, **format widened** | The open standard defines it as "a map from string keys to string values." Claude Code's own table calls it a "free-form YAML map for your own key-value data... Claude Code doesn't act on its contents, and **drops a value that isn't a map**" — i.e. Claude Code accepts arbitrary nested YAML under `metadata`, not just a flat string-to-string map, and its only validation is "is this a map at all" |
| `allowed-tools` | standard, **format widened** | The open standard calls it "a space-separated string" and marks it experimental. Claude Code's table states it "Accepts a space- or comma-separated string, or a YAML list" — a strictly larger accepted grammar than the spec text describes |
| `when_to_use` | Claude Code-only | Extra triggering context, appended to `description`, counted in the same 1,536-char cap |
| `argument-hint` | Claude Code-only | Autocomplete hint, e.g. `[issue-number]` |
| `arguments` | Claude Code-only | Named positional args for `$name` substitution |
| `disable-model-invocation` | Claude Code-only | `true` blocks Claude from auto-invoking; only `/name` works |
| `user-invocable` | Claude Code-only | `false` hides it from the `/` menu; only Claude can invoke |
| `disallowed-tools` | Claude Code-only | Removes tools from Claude's pool while the skill is active |
| `model` | Claude Code-only | Overrides the model for the invoking turn |
| `effort` | Claude Code-only | Overrides effort level for the invoking turn |
| `context: fork` | Claude Code-only | Runs the skill as a subagent's prompt, isolated from conversation history |
| `agent` | Claude Code-only | Which subagent type `context: fork` uses (default `general-purpose`) |
| `background` | Claude Code-only | With `context: fork`; `false` blocks the turn until the subagent finishes |
| `hooks` | Claude Code-only | Registers hooks for the rest of the session when the skill is invoked |
| `paths` | Claude Code-only | Glob patterns gating automatic activation to matching files |
| `shell` | Claude Code-only | `bash` (default) or `powershell` for inline `` !`command` `` injection |

Boolean fields accept `yes/no/on/off/1/0` in addition to `true/false` (Claude Code v2.1.218+).
Unrecognized field names are silently ignored inside Claude Code — "Claude Code ignores a field
it doesn't recognize without reporting an error" — but the same nonstandard field causes a hard
failure the moment the skill is packaged or uploaded outside Claude Code (§3). This asymmetry
(permissive locally, strict on export) is itself worth noting for portability: a skill can look
fine in Claude Code and still fail on `claude.ai` upload or Skills API packaging.

**Inside Claude Code, `name` and `description` are both optional, contrary to how the open
standard and every other Claude surface treat them.** Quoting the frontmatter reference directly:
"All fields are optional. Only `description` is recommended so Claude knows when to use the
skill" ([Extend Claude with skills, "Frontmatter reference"](https://code.claude.com/docs/en/skills#frontmatter-reference)).
`name`, if absent, falls back to the directory name (§4 table above); `description`, if absent,
falls back to "the first non-empty line of the markdown content" (same table). This is a real
divergence from the open standard, which makes both fields mandatory, and from claude.ai/Skills
API/`package_skill.py` uploads, which do enforce both as required keys (§3, §9).

**Malformed frontmatter degrades gracefully in Claude Code rather than failing.** "Claude Code
reads the frontmatter only when the opening `---` is the file's first line. Otherwise it treats
the whole file, `---` markers included, as skill content." And: "If the YAML between the markers
doesn't parse, the skill still loads with no fields set" — the skill remains invocable by
directory name via `/skill-name`, it simply can't be model-triggered because `description` is
empty (same source, "Frontmatter reference"). This is the opposite of the open standard client
guide's own recommendation for lenient client implementations, which says a client should
**skip** a skill entirely on unparseable YAML or a missing/empty description (see the companion
file, §5, "Lenient validation"). Claude Code instead always loads the skill body and commands.

**Dynamic context injection**, `` !`command` `` and `` ```! `` fenced blocks, runs shell commands
before the skill body reaches Claude and substitutes their output — a Claude Code-only body
feature with no equivalent in the open standard or the API
([Extend Claude with skills, "Inject dynamic context"](https://code.claude.com/docs/en/skills#inject-dynamic-context)).
It never runs for a skill synced from claude.ai (see §5). String substitutions
(`$ARGUMENTS`, `$0`/`$1`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`,
`${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`) are likewise Claude
Code-only, documented in the same page's ["Available string substitutions"](https://code.claude.com/docs/en/skills#available-string-substitutions)
table.

---

## 5. Discovery, locations, and precedence in Claude Code

Claude Code's location table
([Extend Claude with skills, "Choose where skills load"](https://code.claude.com/docs/en/skills#where-skills-live)):

| Location | Path | Loads in |
| --- | --- | --- |
| Enterprise | `.claude/skills/<name>/SKILL.md` in the managed settings directory | All users where the org deploys it |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All local projects, not Cowork/cloud sessions |
| Project | `.claude/skills/<name>/SKILL.md` | Sessions in that repo |
| Nested | `<subdir>/.claude/skills/<name>/SKILL.md` | Sessions in/below `<subdir>` |
| Additional directory | via `--add-dir` | That session |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Wherever the plugin is enabled, as `/plugin-name:skill-name` |
| claude.ai account | skills enabled for the account | Cowork, cloud, and signed-in terminal sessions |

**Precedence on a name collision directly contradicts the open standard's stated convention.**
Claude Code: "Enterprise over personal, and personal over project. With `deploy` in both
`~/.claude/skills/` and the project's `.claude/skills/`, `/deploy` runs the personal one" —
["Resolve skills that share a name"](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name).
The open standard's client-implementation guide states the opposite as a settled cross-client
norm: "project-level skills override user-level skills," which it calls "the universal
convention across existing implementations" (companion file, §4, citing
[adding-skills-support](https://agentskills.io/client-implementation/adding-skills-support)).
Personal-over-project in Claude Code is the literal reverse of that stated universal convention
for the personal/project pair (agentskills.io also does not define an enterprise tier at all, so
that part of Claude Code's hierarchy has no open-standard counterpart to compare against). A
project skill and a plugin skill both load simultaneously, since plugin skills are namespaced
(`/plugin-name:skill-name`).

**Two reserved directory names**: a skill folder must not be named `synced` (reserved for
skills downloaded from claude.ai) or `anthropic-skills` / start with `anthropic-skills:`
(reserved for the synced-skills namespace) — same page,
["Skill folders also follow these rules"](https://code.claude.com/docs/en/skills#where-skills-live)
and ["Names reserved for synced skills"](https://code.claude.com/docs/en/skills#names-reserved-for-synced-skills).
Neither reservation exists in the open standard, which documents no reserved-word list at all
for directory or skill names (a point the companion research file flagged as unverified — this
is the first-party confirmation that *some* reservations do exist, at least for one client).

**Skills synced from claude.ai** are downloaded into `~/.claude/skills/synced/`, re-checked
"about every 10 minutes," and are read-only from Claude Code's side: "If you or Claude edit a
file under `~/.claude/skills/synced/`, the change isn't saved to your claude.ai account"
([Extend Claude with skills, "Skills synced from claude.ai"](https://code.claude.com/docs/en/skills#how-synced-skills-behave)).
Claude Code also sanitizes synced-skill display text — "it also escapes angle brackets so the
text can't imitate Claude Code's internal formatting" — a runtime hardening measure distinct
from, but philosophically similar to, `skill-maker`'s own angle-bracket rejection (§9, §12).

**Live change detection** watches skill directories and picks up edits mid-session without a
restart, except in bare mode
([Extend Claude with skills, "Edit a skill during a session"](https://code.claude.com/docs/en/skills#live-change-detection)) —
a runtime behavior with no equivalent concept in the open standard, which is silent on live
reloading.

---

## 6. The Skill tool, invocation, and permissions

Claude Code exposes skills as slash commands and as an internal "Skill tool" Claude calls to
invoke one on its own. Permission rules use `Skill(name)` syntax: `Skill(commit)` for exact
match, `Skill(review-pr *)` for prefix match, and denying the bare `Skill` tool disables all
skills ([Extend Claude with skills, "Restrict Claude's skill access"](https://code.claude.com/docs/en/skills#restrict-claudes-skill-access)).
Two frontmatter fields gate who can invoke a skill: `disable-model-invocation: true` (only the
user can run it) and `user-invocable: false` (only Claude can run it) — same page,
["Control who invokes a skill"](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill).
None of this invocation-control vocabulary — the Skill tool, `Skill()` permission syntax,
`disable-model-invocation`, `user-invocable` — exists in the open standard, which describes
triggering only as "the description carries the entire burden."

**On the API side**, there is no equivalent "Skill tool": Claude discovers and reads skills
purely through the code execution tool's bash sub-tool, as described in §1 and §7. The API has
no slash-command or user-invocation concept at all — invocation is always model-driven, gated
only by whether the relevant `skill_id` was listed in `container.skills`.

---

## 7. The Claude Developer Platform / Messages API Skills feature

**Requirement**: "Using Skills through the API requires the code execution tool, whose container
Skills run in"
([Agent Skills overview, "Claude API"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#claude-api)).
Skills are declared per-request via the `container.skills` array, identical shape for pre-built
and custom Skills:

```json
{
  "container": {
    "skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]
  },
  "tools": [{"type": "code_execution_20260521", "name": "code_execution"}]
}
```

— [Quickstart, "Step 2"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart).
Pre-built and custom Skills differ in identifier shape and version scheme
([Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide)):

| Aspect | `type: "anthropic"` | `type: "custom"` |
| --- | --- | --- |
| Skill IDs | short names: `pptx`, `xlsx`, `docx`, `pdf` | generated: `skill_01AbCdEfGhIjKlMnOpQrStUv` |
| Version format | date-based, e.g. `20251013`, or `latest` | `skver_...` or `latest` |
| Availability | all users | private to the uploading workspace |

**Hard technical limits not in the open standard:**
- "You can include up to 20 Skills for each request"
  ([Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide);
  restated at [Skills for enterprise, "Recall limits"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#recall-limits)).
- Custom Skills are **workspace-wide, not scoped to a user or conversation**: "Any API key with
  access to a workspace can read, invoke, and delete every custom Skill uploaded to that
  workspace" — the guide's explicit recommendation for multi-tenant platforms is "create a
  separate workspace for each tenant."

**The Skills API** (`/v1/skills`) — from the
[reference](https://platform.claude.com/docs/en/api/beta/skills). The `anthropic-beta` header is
listed as **optional** on every Skills API endpoint, and the quickstart's own example calls
create/list endpoints with no beta header at all. The `skills-2025-10-02` beta value is one of
dozens of independent beta flags listed on the same page; per the version-lookup endpoints, it
changes only how a version is *addressed* in the URL ("Requests carrying the `skills-2025-10-02`
beta header address versions by their Unix epoch timestamp instead of their version ID") — it is
not a general prerequisite for using Skills:
- `POST /v1/skills` (Create Skill): multipart upload, `files[]` must all "be in the same
  top-level directory and must include a SKILL.md file at the root of that directory." Optional
  `display_name` (max 255 chars, defaults to the frontmatter `name`, not required to be unique).
- `GET /v1/skills`, `GET /v1/skills/{id}`, `DELETE /v1/skills/{id}` — standard CRUD, `source`
  field distinguishes `custom` / `anthropic` / `anthropic_example` / `plugin`.
- `POST /v1/skills/{id}/versions` (new version) and `GET|DELETE /v1/skills/{id}/versions/{version}`.
  A `SkillVersion`'s `name` is "the Skill's immutable kebab-case slug, set at creation from the
  first upload's SKILL.md frontmatter `name` (or its enclosing directory). **Every later upload
  must resolve to the same value.**" This is the API's substitute for the open standard's
  "must match the parent directory name" rule — it enforces *cross-version* name consistency,
  not name-equals-directory-name at upload time (see §10).
- `GET /v1/skills/{id}/versions/{version}/content` downloads a version as a zip archive.

**Long-running operations**: a `pause_turn` stop reason indicates the API paused mid-Skill-run;
replay the response to continue
([Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide)).

**Not covered by Zero Data Retention**: "Agent Skills is not covered by ZDR arrangements. Skill
definitions and execution data are retained according to Anthropic's standard data retention
policy" ([Agent Skills overview, "Data retention"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#data-retention)).

---

## 8. The code execution tool / container (Skills' runtime on the API)

Skills on the API run inside the code execution tool's container. Key facts from the
[Code execution tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool):

**Versions**: `code_execution_20250825` (Bash + file ops); `code_execution_20260120` (adds REPL
state persistence and programmatic tool calling); `code_execution_20260521` (same runtime, adds
a documented 90-second wall-clock limit per Python cell). "Skills also work with older code
execution tool versions such as `code_execution_20250825`: any current code execution tool
version satisfies the Skills requirement"
([Quickstart](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart)).

**Container runtime**: Python 3.11, Linux x86_64, **5 GiB RAM, 5 GiB disk, 1 CPU**. **No
internet access at all** ("Completely disabled for security" / "no outbound network requests
permitted") and **no runtime package installation** — only pre-installed libraries are
available. Containers expire **30 days** after creation and checkpoint after ~5 minutes of
inactivity; an expired container cannot be reused.

**Pre-installed libraries** include pandas, numpy, scipy, scikit-learn, statsmodels, matplotlib,
seaborn, pyarrow, openpyxl, xlsxwriter, pillow, python-pptx, python-docx, pypdf, pdfplumber,
reportlab, sympy, and CLI tools including `unzip`, `7zip`, `rg`, `fd`, `sqlite` — the full list
is in [Pre-installed libraries](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#pre-installed-libraries).

**Pricing**: code execution is free when combined with `web_search`/`web_fetch` tools of
sufficiently recent version; otherwise billed by execution time with a 5-minute minimum, **1,550
free hours per organization per month**, then **$0.05/hour per container**.

This runtime is materially more restrictive than Claude Code's own environment, where skills
"have the same network access as any other program on the user's computer" and package
installation is allowed but discouraged globally
([Agent Skills overview, "Runtime environment constraints"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#runtime-environment-constraints)).
claude.ai sits in between: "Depending on user/admin settings, Skills may have full, partial, or
no network access," and claude.ai "can install packages from npm and PyPI and pull from GitHub
repositories," unlike the API
([best practices, "Package dependencies"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#package-dependencies)).
None of this three-way runtime variance (API sandboxed/no-network, Claude Code full-network,
claude.ai variable) is addressed by the open standard, which is deliberately silent on runtime
guarantees beyond the `compatibility` field.

---

## 9. Packaging: the `.skill` zip format is real and first-party

The companion research file on the open standard flagged the `.skill` zip format as
**"unverified against agentskills.io primary sources"** — no page on agentskills.io mentions
it. This file resolves that: Anthropic's own official tooling defines and produces `.skill`
files. From
[`skill-creator/scripts/package_skill.py`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/scripts/package_skill.py)
(fetched verbatim via `curl`), its own docstring:

```text
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory]
```

The implementation is unambiguous: it builds `f"{skill_name}.skill"` with
`zipfile.ZipFile(skill_filename, 'w', zipfile.ZIP_DEFLATED)`, walks the skill directory, and
excludes `__pycache__`, `node_modules`, `*.pyc`, `.DS_Store`, and a root-level `evals/`
directory. **So `.skill` is confirmed as: a zip archive, `ZIP_DEFLATED`, with the skill's own
folder as the archive root** — matching the claude.ai Help Center's independent statement that
"the ZIP should contain the skill folder as its root (not a subfolder)"
([How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)).

Crucially, `package_skill.py` **runs validation before zipping** and refuses to package on
failure: "Validation failed: {message}. Please fix the validation errors before packaging." It
imports and calls `validate_skill` from a sibling script,
[`quick_validate.py`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/scripts/quick_validate.py)
(also fetched verbatim), whose rules are:

- `ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}`
  — any other top-level key fails with exactly the error string quoted in §3/§4 above (Claude
  Code's docs quote this validator's error message verbatim, confirming it is the same check).
- `name`: required, must be a string, matched against `^[a-z0-9-]+$` (ASCII-only — no Unicode
  allowance, unlike the open standard's `skills-ref` validator), must not start/end with a
  hyphen or contain `--`, and max 64 characters.
- `description`: required, must be a string, **rejects angle brackets** ("Description cannot
  contain angle brackets (< or >)"), max 1024 characters.
- `compatibility`: optional, must be a string if present, max 500 characters (no minimum
  enforced — same gap as the open standard's `skills-ref`).

This is the origin, or at least an implementation that produces the identical error string, of
the "reject angle brackets" and "reject unexpected top-level fields" rules that `skill-maker`'s
own bundled validator applies as hardening (documented in
`skills/skill-maker/references/spec-provenance.md` as a `skill-maker`-only check not required by
agentskills.io). Anthropic's own official `skill-creator` tool independently enforces the same
two rules, which strengthens the case for keeping them as hardening: neither is an agentskills.io
requirement, but both **are** real constraints enforced by Anthropic's canonical skill-authoring
tool. Note that this is an inference from a matching error string and matching allowed-field
set, not a confirmed statement that the Skills API's server-side validation runs this exact
script — the `Create Skill` API reference page documents no validation rules of its own (see
Gap #5 below).

**`quick_validate.py` has its own gaps relative to the rules it is meant to enforce**, worth
recording in the same spirit as the companion file's "gaps between validator behavior and spec
text" section:

- It does **not** check for the reserved words `anthropic`/`claude` that platform.claude.com's
  prose documents for `name` — that rule exists only in the docs, not in this script.
- Both the `name` and `description` checks are guarded by `if name:` / `if description:` after
  `.strip()`. An empty string therefore passes every character-set and length check silently,
  even though the required-key checks earlier in the function only verify the *key* is present
  (`'name' not in frontmatter`), not that its *value* is non-empty. This contradicts the
  "`description`... must be non-empty" rule stated on platform.claude.com and directly parallels
  the open standard's own `skills-ref` validator gap on `compatibility`'s minimum length
  (companion file, §5).
- It performs **no check that the directory name matches `name`** — unlike the open standard's
  `skills-ref`, which enforces exactly that. Combined with the fact that no Anthropic
  platform/API doc states a directory-match rule either (§10), this is one more point of
  evidence that Claude's ecosystem does not implement or require that part of the open standard.

Note the `name` regex here (`^[a-z0-9-]+$`, ASCII-only) does **not** implement Unicode
normalization the way the open standard's reference `skills-ref` validator does (see the
companion file, §2 "Internal inconsistency in the spec"). Anthropic's own validator resolves
the open standard's "unicode lowercase alphanumeric... (a-z, 0-9)" ambiguity in favor of the
strict ASCII reading.

---

## 10. Comparison: Claude's implementation vs. the open agentskills.io standard

This section is the direct point-by-point comparison the task asked for. "Open standard" cites
`agentskills-spec-and-best-practices.md` (agentskills.io, accessed 2026-09-17); "Claude" cites
this file's own sources.

| Dimension | Open agentskills.io standard | Claude (Anthropic) | Divergence |
| --- | --- | --- | --- |
| Required fields | `name`, `description`; both mandatory, non-empty | **Diverges by surface.** claude.ai uploads, the Skills API, and `package_skill.py` all require both keys present (§3, §9), matching the spec. **Inside Claude Code itself, both are optional**: "All fields are optional. Only `description` is recommended," with `name` falling back to the directory name and `description` falling back to "the first non-empty line of the markdown content" (§4) | Genuine divergence, but scoped to Claude Code's local/interactive surface only — not the export/upload surfaces |
| Optional fields | `license`, `compatibility`, `metadata`, `allowed-tools` | Same six fields recognized as portable, explicitly confirmed by Claude Code's own "fields you can use outside Claude Code" table (§3) | Match — direct first-party confirmation |
| Validation behavior on malformed frontmatter | The client-implementation guide's lenient-validation recommendation: skip the skill entirely on unparseable YAML or a missing/empty `description` (companion file, §5) | Claude Code always loads the skill: unparseable YAML "loads with no fields set" rather than being skipped; a missing opening `---` on line 1 makes the *entire file* body text instead of being rejected (§4) | Opposite behavior from the open standard's own recommended lenient-client default |
| `metadata` value type | "A map from string keys to string values" | Claude Code: "free-form YAML map," any value type, only checks "is this a map at all" and silently drops non-map values (§4) | Claude Code accepts a strictly wider grammar than the spec defines |
| `allowed-tools` string format | "A space-separated string" (marked Experimental) | Claude Code: "Accepts a space- or comma-separated string, or a YAML list" (§4) | Claude Code accepts a strictly wider grammar than the spec defines |
| `name` character set | Spec prose says "unicode lowercase alphanumeric," parenthetical says `a-z, 0-9`; the reference `skills-ref` validator accepts Unicode | Platform docs and `skill-creator`'s validator both use plain ASCII `^[a-z0-9-]+$`, max 64 chars | Claude resolves the open standard's own internal ambiguity in favor of strict ASCII |
| `name` extra restrictions | None beyond character set, hyphen rules, and directory match | **Also**: "Cannot contain XML tags"; "Cannot contain reserved words: 'anthropic', 'claude'" (platform docs, §3) | Claude-specific addition, not in the open standard |
| `name` must equal directory name | Yes, spec-mandated | **Not stated** on any Anthropic platform/API doc page. The Skills API instead enforces name **consistency across versions** of the same `skill_id` ("every later upload must resolve to the same value"), derived from name-or-directory at first upload, not a per-upload equality check. Claude Code's `name` field, when set, becomes the command name and can differ from the directory | Genuine divergence: no directory-match requirement documented for Claude's surfaces |
| `description` limit | 1–1024 chars, non-empty | Same 1,024-char ceiling and non-empty rule on every developer-facing surface (contradicted only by the claude.ai Help Center's "200 characters," see §3) | Match on the authoritative developer surfaces; one internal inconsistency (Help Center) |
| `description` extra restrictions | None (angle brackets explicitly unverified/silent in the spec) | "Cannot contain XML tags"; `skill-creator`'s validator concretely rejects `<`/`>` | Claude enforces the exact rule the open-standard research flagged as unverifiable there — now confirmed as a real, first-party Anthropic constraint |
| `allowed-tools` | "Experimental... support may vary" | Enforced concretely in Claude Code (pre-approves tools for the invoking turn, permission-checked); the six-field export path preserves it unmodified | Claude Code gives it real teeth; still not portable behavior per se, since the *effect* varies by client (as the open standard warns) |
| Reserved words | "The standard defines no reserved-word list... check the client you target" | Confirmed: `anthropic`, `claude` are reserved substrings in `name`; separately, Claude Code reserves the skill-folder names `synced` and `anthropic-skills` | First-party confirmation of the open standard's own "unverified" claim about client reserved words |
| Directory layout | `scripts/`, `references/`, `assets/` as *recommended* conventions | Same three names used throughout Anthropic's own docs and template, sometimes `reference/` (singular) in examples | Match, with a minor spelling inconsistency inside Anthropic's own docs (`references/` vs `reference/`) |
| Body budget | "< 500 lines"; "< 5000 tokens recommended" for tier 2 | Identical numbers, restated verbatim across the overview, best practices, and `skill-creator`'s own SKILL.md | Match |
| Progressive disclosure | Three tiers: metadata (~100 tokens), instructions (<5000 tokens), resources (as needed) | Same three tiers and same ~100-token / <5000-token numbers | Match |
| Extra Claude Code-only tier-1 budgets | Not defined by the spec | 1% of context window for the full skill listing; 1,536-char cap per skill's description+`when_to_use`; 5,000-token cap and 25,000-token combined budget on compaction re-attachment | Claude Code-only implementation limits, no open-standard equivalent |
| Packaging/distribution unit | The folder; `.skill` zip explicitly called an unverified "host convenience... not part of the open standard" | **Confirmed first-party**: `.skill` is a real, officially-tooled zip format (`ZIP_DEFLATED`, skill folder as archive root), produced by Anthropic's own `package_skill.py` and expected by the claude.ai upload flow and (per the Skills API) the multipart `files[]` upload | Resolves the open standard's own "unverified" item; `.skill` is real but Claude-specific, not part of agentskills.io |
| Validation tooling | `skills-ref` (Python), explicitly "demonstration... not for production," checks exactly the six fields | `skill-creator`'s `quick_validate.py` checks the identical six-field allowlist, nearly identical name/description rules, PLUS an angle-bracket check the open standard lacks. It does **not** check the `anthropic`/`claude` reserved words (that rule lives only in Anthropic's prose docs, not this script) and, unlike `skills-ref`, does **not** check directory-name match; it also lets an empty `name`/`description` string pass, matching `skills-ref`'s own analogous gap on `compatibility` (§9) | Convergent design (same six-field allowlist), divergent strictness on angle brackets, convergent laxness on empty-string values |
| Directory placement convention | `.<client>/skills/`, `.agents/skills/` (project & user); collision rule "project-level skills override user-level skills," called "the universal convention across existing implementations" | Claude Code: `.claude/skills/` (project), `~/.claude/skills/` (personal), **plus** an enterprise tier and a plugin tier and a claude.ai-synced tier the open standard doesn't define; collision rule is "Enterprise over personal, and personal over project" (§4) | **Direct contradiction, not just an extension**: Claude Code ranks personal above project, the reverse of the open standard's stated universal convention for that pair, in addition to adding two hierarchy tiers (enterprise, plugin) the standard doesn't define |
| Invocation model | Model-driven only, via description matching; no user-invocation vocabulary defined | Model-driven (same) **plus** explicit user-invocation (`/skill-name`), a dedicated "Skill tool," and `Skill(name)`/`Skill(name *)` permission syntax | Claude Code extension; not present in the open standard or the Claude API |
| Frontmatter beyond the six fields | Explicitly "client extension... not part of the format"; the open-standard file could not enumerate Claude Code's actual extension list (called it unverifiable, tier-(c) knowledge) | **Now enumerated and confirmed**: 14 additional fields (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`) — see §4 table | This file supplies the client-extension enumeration the companion file flagged as a gap |
| `context: fork` | Cited by the open-standard file as an example of an unverifiable client extension | Confirmed real and documented: runs the skill's body as a subagent prompt, isolated from conversation history, with `agent`/`background` companion fields | Confirms the open-standard file's example was accurate, now with a primary citation |
| Runtime guarantees | Silent; `compatibility` field is the only sanctioned place to declare requirements | Explicit and surface-dependent: API sandbox has **no network, no package installs**; Claude Code has **full network access**; claude.ai has **variable** network access and *can* install packages | Claude documents concrete runtime tiers the open standard leaves entirely to authors |
| Data retention / ZDR | Not addressed | Explicitly **not covered by Zero Data Retention** on the API; container data retained up to 30 days | Claude-specific compliance detail, no open-standard equivalent |
| Security guidance | Client-guide-level: "gate project-level loading on a trust check" | Far more developed: a full enterprise risk-tier table, a security review checklist, and an optional automated "Skill content scanning" for claude.ai/Cowork uploads (not covering the API) | Claude has substantially more developed, product-specific security tooling |
| Hard numeric limits | None stated beyond the frontmatter character limits | **20 Skills per API request**; Skills API `display_name` max 255 chars; container **5 GiB RAM / 5 GiB disk / 1 CPU**; container **30-day expiry** | Claude-specific infrastructure limits with no open-standard analogue |

---

## 11. Anthropic's official `anthropics/skills` repository

At the commit pinned in "Scope & method" above (`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`, 2026-09-29):

- **Purpose statement**: "This repository contains skills that demonstrate what's possible with
  Claude's skills system" — explicitly labeled a demonstration/reference repo, not the format
  authority: "This repository contains Anthropic's implementation of skills for Claude. For
  information about the Agent Skills standard, see agentskills.io"
  ([README.md](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/README.md)).
- **`spec/` is not a fork of the standard** — its entire content (fetched directly via `curl`)
  is: `"# Agent Skills Spec\n\nThe spec is now located at <https://agentskills.io/specification>"`.
  Anthropic's own repo defers to agentskills.io rather than maintaining a parallel copy. This
  directly answers the open-standard research file's uncertainty about how the two projects
  relate: they are the same specification, and Anthropic's repo does not duplicate it.
- **Licensing is split**: "Many skills in this repo are open source (Apache 2.0)... the document
  creation & editing skills that power Claude's document capabilities... are source-available,
  not open source" (the `docx`, `pdf`, `pptx`, `xlsx` subfolders) — same README.
- **Disclaimer**: "These skills are provided for demonstration and educational purposes only...
  the implementations and behaviors you receive from Claude may differ from what is shown in
  these skills."
- **Installation paths documented**: Claude Code plugin marketplace (`/plugin marketplace add
  anthropics/skills`), claude.ai (already-available example skills, or manual upload), and the
  Claude API (Skills API).
- The `skill-creator` skill's own `SKILL.md` frontmatter is minimal and self-referential:
  `name: skill-creator`, with a description instructing use for "creat[ing] new skills,
  modify[ing] and improv[ing] existing skills, and measur[ing] skill performance" — fetched from
  [`skill-creator/SKILL.md`](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/SKILL.md).
  Its body repeats the same rules captured in §1–§3 (pushy descriptions, <500-line bodies,
  ~100-word/token metadata budget, avoid "ALWAYS" in favor of explained reasoning, bundle
  repeated helper scripts).

---

## 12. Best practices, per Anthropic's own authoring guide

From
[Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
unless noted; this section only records guidance that is Claude-specific or usefully
concrete beyond what the companion open-standard file already covers.

**Concision is measured, not just recommended.** The guide gives a worked ~50-token "good" vs.
~150-token "bad" PDF-extraction example side by side, with the explicit test: "Does this
paragraph justify its token cost?"

**Three explicit "degrees of freedom" tiers**, mapped to fragility, each with a worked example:
high freedom (numbered heuristic steps, e.g. code review), medium freedom (parameterized
pseudocode/scripts), low freedom (an exact command with "Do not modify... or add additional
flags"). The guide's own metaphor: Claude as "a robot exploring a path" — a narrow bridge needs
exact instructions, an open field needs general direction and trust.

**Test across model tiers explicitly**: "Test your Skill with all the models you plan to use it
with," naming Haiku ("Does the Skill provide enough guidance?"), Sonnet ("Is the Skill clear and
efficient?"), and Opus ("Does the Skill avoid over-explaining?") as three distinct authoring
targets — a model-tier testing requirement with no equivalent in the open standard.

**Naming convention preference**: "Consider using gerund form (verb + -ing)" — `processing-pdfs`,
`analyzing-spreadsheets` — as the *preferred* style, with noun-phrase and action-verb forms as
"acceptable alternatives." The open standard states no naming-style preference at all (only the
character-set rule).

**Nested-reference failure mode, with a concrete mechanism**: "Claude may partially read files
when they're referenced from other referenced files... Claude might use commands like `head
-100` to preview content rather than reading entire files." This gives the *mechanism* behind
the open standard's "keep references one level deep" rule (which states the rule but not why).

**Table-of-contents rule for long reference files**: "For reference files longer than 100 lines,
include a table of contents at the top" — a concrete threshold the open standard's guides do not
give.

**MCP tool references must be fully qualified**: `ServerName:tool_name` (e.g.
`BigQuery:bigquery_schema`), "Without the server prefix, Claude may fail to locate the tool" —
a Claude-specific interop rule with no open-standard equivalent (the open standard does not
mention MCP at all in the skill-authoring guides investigated).

**Evaluation-before-documentation**: "Create evaluations BEFORE writing extensive
documentation," with a five-step loop (identify gaps → create evaluations → establish baseline →
write minimal instructions → iterate) and a data-driven JSON eval shape:

```json
{
  "skills": ["pdf-processing"],
  "query": "...",
  "files": ["test-files/document.pdf"],
  "expected_behavior": ["...", "..."]
}
```

This is a different (though closely related) shape from the open standard's `evals/evals.json`
format (`skill_name`, `evals[]` with `id`/`prompt`/`expected_output`/`files`/`assertions`) — the
two are not interchangeable, and Claude Code's own docs say as much explicitly when describing
`claude plugin eval`'s format versus the `skill-creator` plugin's `evals/evals.json` format
([Extend Claude with skills, "Evaluate and iterate on a skill"](https://code.claude.com/docs/en/skills#evaluate-and-iterate-on-a-skill)).

**"Solve, don't defer"** for scripts: handle `FileNotFoundError`/`PermissionError` explicitly
inside bundled scripts rather than letting them raise into Claude's context; justify every
constant ("HTTP requests typically complete within 30 seconds" rather than an unexplained `47`).

**A full authoring/testing checklist** is given verbatim at the end of the guide (core quality,
code and scripts, testing sections) — see
[Checklist for effective Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#checklist-for-effective-skills).

---

## 13. claude.ai's Skills feature

Per the [Help Center](https://support.claude.com/en/articles/12512176-what-are-skills) and the
platform overview:

- **Plan availability**: "Free, Pro, Max, Team, and Enterprise plans," gated on code execution
  being enabled.
- **Four categories**: Anthropic (pre-built, e.g. document skills, invoked automatically),
  Custom (user- or org-authored), **Organization Provisioned** (Team/Enterprise admins can push
  skills org-wide), and **Partner Skills** ("professionally-built skills from partners like
  Notion, Figma, Atlassian, and others").
- **Custom Skill upload is a zip**, "the ZIP should contain the skill folder as its root (not a
  subfolder)" — via Settings > Features
  ([overview, "claude.ai"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#claude-ai);
  Help Center article above).
- **claude.ai custom Skills are per-user, not org-shared**: "Custom Skills are individual to
  each user. They are not shared organization-wide and cannot be centrally managed by admins" —
  this is distinct from the "Organization Provisioned" category, which is admin-pushed rather
  than admin-managing-user-uploads.
- **No cross-surface sync**: uploads to claude.ai, the API, and Claude Code are three entirely
  separate stores — explicitly warned in three different places (overview, enterprise guide,
  Claude Code docs) as "Custom Skills do not sync across surfaces."
- **Optional enterprise content scanning**: "Skill and plugin security scanning," opt-in at
  claude.ai admin settings, scans uploads/edits in claude.ai and Cowork "for signs of malicious
  behavior, such as hidden code execution, sending your data to an outside service, or
  instructions that tamper with Claude's safeguards." A failing skill is blocked; a
  warning-level pass "stays usable behind a caution notice." **This scanning does not cover the
  API**: "Skills you upload through the Skills API... aren't scanned"
  ([Skills for enterprise, "Skill content scanning"](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise#skill-content-scanning)).

---

## 14. Anthropic's own announcement and engineering posts

- **Announcement**: "Introducing Agent Skills," published **October 16, 2025**
  ([claude.com/blog/skills](https://claude.com/blog/skills), redirected from the legacy
  `anthropic.com/news/skills` URL with an HTTP 308). Core line: "Claude can now use Skills to
  improve how it performs specific tasks." Launched across Claude apps (Pro/Max/Team/Enterprise),
  Claude Code, and the Developer Platform (`/v1/skills`) simultaneously.
- **The open standard came later, as a follow-up, not at launch**: "We've published Agent Skills
  as an open standard for cross-platform portability," dated **December 18, 2025** in the same
  post's updates. This establishes the chronology precisely: Claude's proprietary Skills feature
  (Oct 2025) *predates* the open agentskills.io standard (Dec 2025) by about two months — Claude
  Skills were not built "on top of" a pre-existing open standard; the open standard was
  extracted from Claude's shipped design afterward. This matches the open-standard research
  file's own citation that the format "was originally developed by [Anthropic], released as an
  open standard."
- **Engineering post**: "Equipping agents for the real world with Agent Skills," by **Barry
  Zhang, Keith Lazuka, and Mahesh Murag**, published alongside the October 16, 2025 launch
  ([anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)).
  Its authoring-guidance section gives four named steps: "Start with evaluation," "Structure for
  scale," "Think from Claude's perspective," "Iterate with Claude" — a slightly different framing
  of the same iterative-development idea captured in more procedural detail in the best-practices
  page (§12). Security guidance: "install skills only from trusted sources," audit "code
  dependencies and bundled resources," and watch for "instructions or code... that instruct
  Claude to connect to potentially untrusted external network sources."

---

## 15. Enterprise governance (Claude-specific; no open-standard equivalent)

The [Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
guide is entirely Claude-specific — the open standard has no concept of organizational
governance. Highlights not already covered above:

- A **risk-tier table** for vetting third-party skills: code execution, instruction
  manipulation, MCP references, network access patterns, hardcoded credentials, filesystem
  scope, and tool invocations, each rated High/Medium concern.
- An eight-step **review checklist** (read all content, verify script behavior in a sandbox,
  check for adversarial instructions, check for network calls, check for hardcoded credentials,
  list all tool/command invocations, confirm redirect destinations, check for exfiltration
  patterns).
- **Evaluation gates before production**: triggering accuracy, isolation behavior, coexistence
  (does adding this skill steal triggers from others), instruction-following, output quality —
  with a required "3–5 representative queries per Skill" submitted by the skill's author, tested
  across Haiku/Sonnet/Opus, reviewed by someone other than the author ("separation of duties").
- **Versioning discipline**: "If you omit `version`, requests use the latest version, so a new
  version uploaded by anyone in the workspace immediately changes what production agents run" —
  pin explicit versions in production; "Compute checksums of reviewed Skills and verify them at
  deployment time."
- **Recall-limit guidance**: "limit the number of Skills loaded simultaneously to maintain
  reliable recall accuracy," and the hard 20-skills-per-request ceiling from §7 is repeated here
  as the reason to consolidate narrow skills into role-based bundles.

---

## Gaps / unverified

1. **`references/` vs `reference/` (singular).** Anthropic's own docs use both spellings across
   different worked examples (`references/finance.md` in one best-practices example,
   `reference/finance.md` in the "domain-specific organization" pattern in the same document).
   Neither the open standard nor Anthropic's docs resolve this; treat it as a naming convention,
   not a rule, and note that inconsistency exists even within Anthropic's own canonical guide.

2. **The claude.ai Help Center's 200-character description limit and `dependencies` field**
   (§3) could not be reconciled with every other Anthropic surface. This file treats the
   1,024-character limit and six-field set as authoritative (corroborated by the Skills API
   validator's source code, Claude Code's hard-error message, and two independent
   platform.claude.com pages) and flags the Help Center article as either stale or scoped to a
   narrower, undocumented legacy upload path. This was not resolved by re-fetching; it would
   require testing an actual claude.ai upload, which this research did not do.

3. **Exact behavior of `skill_id` collisions or reuse** between Anthropic's `anthropic_example`
   source type and `custom` skills was not tested; the API reference documents the enum values
   but not conflict-resolution behavior.

4. **The precise size limits enforced by the claude.ai upload flow** (beyond "zip, folder as
   root") were not independently found; the Help Center article's specific character ceiling is
   in doubt (see #2), so no other numeric limit from that page is treated as reliable here.

5. **Whether `skill-creator`'s `quick_validate.py` is literally the code path the Skills API
   runs server-side on `POST /v1/skills`**, versus a separate server-side implementation that
   happens to produce the identical error string, was not verified — only that Claude Code's
   docs quote an identical error message. Treat "the same validator" as a strong inference, not
   a confirmed fact.

---

## Implications for `skill-maker`

Where these findings bear on what this repo's own skill (`skills/skill-maker/`) teaches authors,
beyond the generic agentskills.io guidance already in `references/spec-reference.md` and
`references/spec-provenance.md`:

1. **The angle-bracket hardening is now independently corroborated**, not just a `skill-maker`
   house rule. `spec-provenance.md` already correctly labels it "skill-maker hardening... not
   spec requirements" — that framing still holds relative to agentskills.io, but authors
   targeting Claude specifically should know Anthropic's own `skill-creator` tool enforces the
   identical rule, and Claude's platform docs state "Cannot contain XML tags" for both `name`
   and `description`. Worth a one-line cross-reference from `spec-provenance.md` to this file
   so a Claude-targeting author knows the rule isn't `skill-maker`-only paranoia.

2. **Reserved words are real for Claude**: `name` cannot contain "anthropic" or "claude"
   (substring match, per the platform docs' phrasing), and Claude Code separately reserves the
   skill-folder names `synced` and `anthropic-skills`. `skill-maker`'s reference material
   currently treats reserved words as wholly undocumented/unverified at the open-standard layer;
   if `skill-maker` wants to warn authors about Claude specifically, this file gives the exact
   list and citations to do so.

3. **`.skill` packaging is real, Claude-specific, and now has an exact reference
   implementation** (`package_skill.py`): zip, `ZIP_DEFLATED`, skill folder as archive root, run
   `quick_validate.py` first. If `skill-maker` ever adds a "package for Claude" step, this is
   the exact shape to match, and it is now citable as Anthropic's own official tooling rather
   than "a host convenience... not part of the open standard."

4. **The six-field portable set is now directly confirmed by Anthropic**, not just inferred from
   the open standard's own text. Claude Code's docs state in as many words which six fields
   survive export to claude.ai/API/packaging and which do not, with the exact hard-error message
   a skill will get for violating it. This is a stronger citation than what `spec-reference.md`
   currently has for "portable vs. platform-locked," and is worth adding as a citation there.

5. **Directory-name-must-equal-`name`** is an open-standard requirement `skill-maker` should
   continue enforcing for portability, but authors should know **Claude's own surfaces do not
   require or check it** — Claude Code falls back to the directory name only when `name` is
   absent, and the Skills API only requires name consistency *across versions* of the same
   skill, not directory equality. A skill could pass every Claude-specific check while still
   failing the open standard's directory-match rule (or vice versa); `skill-maker` should keep
   checking the open standard's stricter rule regardless, since it is a superset.

6. **Claude Code's frontmatter extensions are a real, large surface**
   (`disable-model-invocation`, `context: fork`, `allowed-tools` with real enforcement, etc.).
   If `skill-maker` ever adds Claude Code-specific authoring guidance (as opposed to generic,
   cross-client guidance), §4 of this file is the field-by-field reference to build it from,
   already distinguishing which fields survive packaging/export and which don't.
