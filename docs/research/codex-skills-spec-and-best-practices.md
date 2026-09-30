# OpenAI Codex — Skills and AGENTS.md: Specification and Best Practices

## Scope & method

This is a primary-source investigation of how **OpenAI Codex** (the Codex CLI, the ChatGPT
desktop app's Codex surface, and the Codex IDE extension) implements **Agent Skills**
(`SKILL.md`) and the separate **AGENTS.md** convention. It complements
`docs/research/agentskills-spec-and-best-practices.md` (which covers the open agentskills.io
standard) by documenting what is specific to Codex's implementation, and calling out where Codex
diverges from, extends, or predates that open standard.

Sources used, and how:

- **Codex's own documentation**, currently hosted at `learn.chatgpt.com` (canonical entry points
  `https://developers.openai.com/codex/skills` and `https://developers.openai.com/codex/guides/agents-md`
  both issue an HTTP 308 redirect to `https://learn.chatgpt.com/docs/build-skills` and
  `https://learn.chatgpt.com/docs/agent-configuration/agents-md` respectively). Fetched the raw
  Markdown twins (`…/build-skills.md`, `…/agent-configuration/agents-md.md`) directly with `curl`
  so the text quoted below is the page source, not a model-generated summary. Also fetched, raw,
  `https://developers.openai.com/plugins/build/plugins.md` (this one does **not** redirect to
  `learn.chatgpt.com`, as of the access date).
- The [`openai/codex`](https://github.com/openai/codex) repository, cloned and inspected at commit
  [`0b43721d8d1f734658e41bffe12a6ba6c9240abd`](https://github.com/openai/codex/commit/0b43721d8d1f734658e41bffe12a6ba6c9240abd)
  ("Copy selected file paths as plain text in the TUI (#49564)", 2026-09-30) — in particular the
  `codex-rs/skills/`, `codex-rs/ext/skills/`, and `codex-rs/core/src/agents_md.rs` crates, the
  bundled sample skills under `codex-rs/skills/src/assets/samples/`, the repo's own dev-only
  skills under `.codex/skills/`, and the repo's own root `AGENTS.md`.
- The [`openai/skills`](https://github.com/openai/skills) repository (the former skills catalog),
  inspected at commit
  [`49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/commit/49f948faa9258a0c61caceaf225e179651397431)
  ("[codex] Update skill installer post-install guidance (#507)", 2026-06-23). Its `README.md` was
  marked deprecated in commit
  [`778b0e6129cf18cbaee3bf11479f583fadae8d03`](https://github.com/openai/skills/commit/778b0e6129cf18cbaee3bf11479f583fadae8d03)
  ("Deprecate skills repository (#496)", 2026-06-22).
- The [`openai/plugins`](https://github.com/openai/plugins) repository (the repo the deprecated
  `openai/skills` README now points readers to), inspected at commit
  [`5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f`](https://github.com/openai/plugins/commit/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f)
  ("Enable GitHub API OAuth and document public clients (#395)", 2026-09-28).
- [agents.md](https://agents.md/) and its repository
  [`agentsmd/agents.md`](https://github.com/agentsmd/agents.md), a complete (non-shallow) clone
  whose **first commit is
  [`ba9474a69e9a2c0c4176713843b78e8f54377941`](https://github.com/agentsmd/agents.md/commit/ba9474a69e9a2c0c4176713843b78e8f54377941),
  dated 2025-08-19** ("Initial commit"). Text quoted below comes from the site's actual React
  source (`components/*.tsx`) at the current tip
  [`d001185d792eb6402a58e4cbef1c228b309ec25d`](https://github.com/agentsmd/agents.md/commit/d001185d792eb6402a58e4cbef1c228b309ec25d)
  ("Rename agents-md_Charter.pdf to Technical_Charter.pdf", 2026-09-10) — read directly from the
  cloned repo, not paraphrased by a fetch tool. A `grep -rni skill` over the entire site source
  (`pages/`, `components/`) and the repo's own `README.md`/`AGENTS.md` returns **zero matches**:
  the agents.md project's own materials never mention Agent Skills or `SKILL.md` in any form.

**Accessed:** 2026-09-30.

A note on what counts as primary here. Codex's
[`docs/skills.md`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/docs/skills.md)
and `docs/agents_md.md` inside the `openai/codex` repository are now one-line stubs that just point
at the hosted docs site — `docs/skills.md` reads only "For information about skills, refer to
[this documentation](https://developers.openai.com/codex/skills)." This is consistent with the
repo's own
[`AGENTS.md:32`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/AGENTS.md#L32),
which says: "Do not add general product or user-facing documentation to the `docs/` folder. The
official Codex documentation lives elsewhere." So the hosted docs site is
the actual source of truth for user-facing behavior, and the Rust source is the actual source of
truth for what Codex does at runtime — the two do not always agree (see §3 and §8), and where they
disagree that is called out explicitly, the same way the sibling research file treats
`docs/specification.mdx` versus `skills-ref` as different authority tiers.

Also note: I could not establish the true commit that first introduced Skills or AGENTS.md support
to `openai/codex`, because a shallow clone's `--diff-filter=A` walk only reaches the clone's
history boundary, not the real origin. I have not asserted an introduction date for either feature
in Codex; all Codex-side dates below are either the pinned inspection commit (current state) or
explicitly marked as unverified.

---

## 1. Does Codex have native Agent Skills support, and is it the agentskills.io format?

**Yes — Codex has first-party, native support for the `SKILL.md` format, and its own documentation
states explicitly that it builds on the open agentskills.io standard.**

Verbatim, from the Codex docs (`https://learn.chatgpt.com/docs/build-skills.md`, fetched
2026-09-30):

> "Use agent skills to extend ChatGPT and Codex with task-specific capabilities. A skill packages
> instructions, resources, and optional scripts so either product can follow a workflow reliably.
> Skills build on the [open agent skills standard](https://agentskills.io)."

And later, in the "Best practices" section, the same page links directly to
`https://agentskills.io/specification` as one of its "for more examples" references.

This is corroborated by the runtime: Codex ships a Rust crate (`codex-rs/skills/`) and an
extension crate (`codex-rs/ext/skills/`) whose entire job is to discover directories containing a
`SKILL.md` file, parse YAML frontmatter with `name` and `description`, and inject qualifying
skills' descriptions into the model's context — the same three-tier progressive-disclosure model
(name+description → full body → on-demand resources) documented at agentskills.io. Codex also
ships a bundled `skill-creator` skill
([`codex-rs/skills/src/assets/samples/skill-creator/SKILL.md`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md))
whose own frontmatter, directory
layout (`SKILL.md` / `scripts/` / `references/` / `assets/`), and vocabulary ("progressive
disclosure," "discovery," "activation") mirror the open standard's terms precisely.

So: **Codex is a real agentskills.io client**, not merely AGENTS.md-only. It is, however, its own
implementation with its own parser, its own (looser) validation, and several Codex-specific
extensions layered on top (`agents/openai.yaml`, four discovery scopes, `$skill-name` mention
syntax, "Record & Replay" skill authoring, and a plugin packaging format). Those are documented in
the sections below.

---

## 2. The `SKILL.md` format as Codex documents it

From `learn.chatgpt.com/docs/build-skills.md`:

> "A skill is a directory with a `SKILL.md` file plus optional scripts and references. The
> `SKILL.md` file must include `name` and `description`."

Documented directory layout (identical in spirit to the open spec, plus one Codex-specific
addition):

```
my-skill/
├── SKILL.md        # Required: instructions + metadata
├── scripts/        # Optional: executable code
├── references/     # Optional: documentation
├── assets/         # Optional: templates, resources
└── agents/
    └── openai.yaml # Optional: appearance and dependencies
```

Minimal example given on the page:

```md
---
name: skill-name
description: Explain exactly when this skill should and should not trigger.
---

Skill instructions for ChatGPT or Codex to follow.
```

"Codex detects skill changes automatically. If an update doesn't appear, restart Codex."

### 2.1 What Codex's runtime parser actually enforces (this is stricter/looser than the doc implies)

The documentation above states `name` and `description` are required, but does not describe
character-set, length, or format rules the way agentskills.io's `docs/specification.mdx` does. The
Rust source is unambiguous, and it is **substantially more lenient than the open spec**:

`codex-rs/skills/src/parser.rs` (`parse_skill_frontmatter_metadata`) only deserializes three
frontmatter values — `name`, `description`, and `metadata.short-description` — via:

```rust
struct SkillFrontmatter {
    name: Option<String>,
    description: Option<String>,
    metadata: SkillFrontmatterMetadata,   // only reads metadata["short-description"]
}
```

Because this struct has no `#[serde(deny_unknown_fields)]`, **any other top-level key — including
the open spec's `license`, `compatibility`, and `allowed-tools` — is silently ignored by the
loader that actually runs skills.** It is not rejected and produces no warning; it simply has no
effect on Codex's behavior. This is primarily a proof by construction — the `SkillFrontmatter`
deserializer above only has fields for `name`, `description`, and `metadata`, so serde has nothing
else to populate from those keys. As a repo-wide cross-check, a `grep -rn "allowed-tools\|allowed_tools" codex-rs
--include=*.rs` (run across the entire `openai/codex` source tree, not just the skills crates)
turns up only an unrelated concept — a `ToolPolicy.allowed_tools` field used by the guardian/reviewer
extensions to allow-list *tool execution*, nothing to do with `SKILL.md` frontmatter — which further
confirms no code path anywhere in the repo reads an `allowed-tools` key from a skill's frontmatter.

The validation the parser does apply
([`parser.rs:82-197`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/parser.rs#L82-L197)):

- `name`: if missing or empty after whitespace-collapsing, **falls back to a directory-derived
  default.** The fallback function,
  [`default_skill_name`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/loader/host.rs#L394-L403),
  takes the `SKILL.md` path's **parent directory's own name** (i.e. the skill folder name),
  whitespace-collapses it, and falls back further to the literal string `"skill"` if that is
  empty. The only length/format check applied to an explicit `name` at this stage is a
  **64-character maximum** — there is **no** charset check, no lowercase requirement, no hyphen
  rule, no `--`-consecutive-hyphen check, and no requirement that `name` match the containing
  directory. All of those are open-spec `name` rules (see the sibling research file, §2) that
  Codex's parser does not enforce at this stage.

  A second, later check does apply, but to a *derived* value, not the raw frontmatter `name`: once
  a skill is namespaced (skills bundled inside a plugin get their name qualified with a
  plugin-derived prefix), the resulting *qualified* name is checked against
  `MAX_QUALIFIED_NAME_LEN = MAX_NAME_LEN * 2 + 1` (= 129 characters) — see
  [`loader/mod.rs:23`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/loader/mod.rs#L23)
  and its use in
  [`loader/host.rs:321`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/loader/host.rs#L316-L325).
  This still never checks charset, case, or hyphen placement — only length — so the headline claim
  stands: **nothing in Codex's runtime loading path validates the open spec's `name` character-set
  rules.**
- `description`: must be non-empty after whitespace-collapsing, or the skill fails to load
  (`SkillParseError::MissingField("description")`). **There is no upper-length check at load
  time** — the spec's 1024-character cap is not enforced by this parser, so a longer-than-spec
  description loads without error. (A 1024-char cap *is* enforced elsewhere: on the separate
  `agents/openai.yaml` `interface.short_description` and `interface.default_prompt` fields, see
  §5; and separately again, purely for *display*, `render.rs`'s `MAX_CATALOG_SKILL_DESCRIPTION_CHARS
  = 1_024` truncates an over-length description in the compact catalog list with a `...` suffix —
  see §4.1. The practical effect: text past character 1,024 in a `description` loads fine and is
  fully present if the skill's body is later read, but is invisible to the *implicit*-invocation
  catalog match, since that match only ever sees the truncated 1,024-character version.)
- `metadata.short-description` (hyphenated key, Codex-specific): if present, becomes
  `short_description`.
  [`protocol/src/protocol.rs:3899`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/protocol/src/protocol.rs#L3899)
  documents this field with the comment `/// Legacy short_description from SKILL.md. Prefer
  SKILL.json interface.short_description.` A repo-wide `grep -rn "SKILL.json" codex-rs` finds
  **only that same comment string, duplicated in one other protocol file** — no parser, writer, or
  schema for a file named `SKILL.json` exists anywhere in the inspected commit. Treat the comment
  as a stale or forward-looking note about an interface Codex does not currently implement, not as
  evidence a `SKILL.json` format exists today.
- Malformed YAML repair: before giving up on a parse error, the parser tries a **line-oriented
  repair pass** (`repair_frontmatter_scalar_fields`) that quotes scalar values containing an
  unescaped `key: value: more text`-style colon (its own comment cites the example
  `description: Build for AWS: ECS`). This is the exact failure mode the agentskills.io
  client-implementation guide's "Lenient validation" section recommends handling — "Malformed YAML
  with unquoted colons … try a fallback that quotes or block-scalarizes it" — so this is a
  documented-recommendation-turned-implementation match between Codex and the open standard's
  client guidance, not a divergence.

### 2.2 A third, independent validator: Codex's own bundled `quick_validate.py`

Codex ships its own validation script inside the bundled `skill-creator` sample skill
([`codex-rs/skills/src/assets/samples/skill-creator/scripts/quick_validate.py`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/assets/samples/skill-creator/scripts/quick_validate.py)).
This script is
**not** what Codex's runtime loader uses to decide whether a skill loads (§2.1's Rust parser is);
it is a tool the `skill-creator` skill tells the model to run against *new* skills it authors. Its
rules are almost exactly the open spec's six-field model, minus `compatibility`:

```python
allowed_properties = {"name", "description", "license", "allowed-tools", "metadata"}
```

It also enforces, independently of the Rust loader:

- `name` must match `^[a-z0-9-]+$`, not start/end with `-`, contain no `--`, and be ≤64 chars —
  i.e., the full open-spec `name` rule set that the runtime loader (§2.1) does **not** check.
- `description` must be ≤1024 chars and **must not contain `<` or `>`** — the exact "angle bracket"
  rule the sibling research file's Gap #1 says is unverified against agentskills.io's own spec and
  `skills-ref` validator. Codex's bundled `quick_validate.py` enforces the identical rule (same
  error string) to this repo's own bundled validator. As detailed in Implications, #3 below, this
  is very likely one convention with a shared ancestor rather than two independent
  implementations converging on the same answer — but it is still real and attributable, not
  invented.
- Rejects `[TODO: …]` placeholder text left over from scaffolding, in both the description and the
  body.

So within Codex itself there are now **three different enforcement levels** for the same file
format: the hosted docs (informal), the Rust runtime loader (loosest — only checks `name` ≤64/129
and non-empty `description`), and the bundled `skill-creator`'s `quick_validate.py` (strictest —
nearly full open-spec conformance for authored skills). A skill can pass one and fail the other in
both directions:

- A skill named `My_Skill` (uppercase, underscore) would be **silently accepted** by the runtime
  loader's length-only check, but **rejected** by `quick_validate.py`'s `^[a-z0-9-]+$` regex.
- Conversely, `description: ""` (the key present, value an empty string) **passes**
  `quick_validate.py`: its code only checks the key's *presence* (`if "description" not in
  frontmatter`), then guards the length/angle-bracket checks behind `if description:` — which is
  false for an empty string, so those checks are skipped and the function returns "Skill is
  valid!". The same file **fails to load** at runtime, because the Rust parser's
  `validate_len`/non-empty check treats an empty (or whitespace-only) `description` as a hard
  `MissingField` error. A skill can therefore pass Codex's own authoring validator and still be
  refused by Codex's own loader.

---

## 3. Discovery: where Codex looks for skills

From `learn.chatgpt.com/docs/build-skills.md` (verbatim table):

| Skill Scope | Location | Suggested use |
| --- | --- | --- |
| `REPO` | `$CWD/.agents/skills` — current working directory: where you launch Codex. | Skills relevant to a working folder, e.g. one microservice. |
| `REPO` | `$CWD/../.agents/skills` — a folder above CWD when you launch Codex inside a Git repository. | Skills relevant to a shared area in a parent folder. |
| `REPO` | `$REPO_ROOT/.agents/skills` — the topmost root folder when you launch Codex inside a Git repository. | Root skills available to any subfolder in the repository. |
| `USER` | `$HOME/.agents/skills` — the user's personal folder. | Skills relevant to a user across any repository. |
| `ADMIN` | `/etc/codex/skills` — machine/container-shared system location. | SDK scripts, automation, default admin skills for everyone on the machine. |
| `SYSTEM` | Bundled with Codex by OpenAI. | Broadly useful built-ins such as `skill-creator` and plan skills. |

The doc states discovery is a walk, not a single fixed path: "For repositories, Codex scans
`.agents/skills` in every directory from your current working directory up to the repository
root." It also states explicitly: **"If two skills share the same `name`, Codex doesn't merge
them; both can appear in skill selectors."**

### 3.1 What the source code adds / confirms

[`codex-rs/ext/skills/src/host_roots.rs`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_roots.rs)
(function `roots_from_layer_stack`, lines 73-131) confirms and refines the doc's table:

- `REPO` roots come from two independent mechanisms: (a) `<project-config-folder>/skills`, where
  the project config folder is the project-local `.codex/` directory (this is why the
  `openai/codex` repository's own dev-only review/testing skills live at `.codex/skills/*`, not
  `.agents/skills/*` — confirmed by `find` over the repo, e.g.
  `.codex/skills/code-review/SKILL.md`); and (b) `.agents/skills` walked from the discovered
  project root (found via `project_root_markers`, default `[".git"]`, the same mechanism
  `agents_md.rs` uses for AGENTS.md — see §7) down to the current working directory.
- `USER` roots are **two** paths, one of them explicitly deprecated in a code comment:
  `$CODEX_HOME/skills` — the comment at
  [`host_roots.rs:96-97`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_roots.rs#L96-L97)
  reads "Deprecated user skills location (`$CODEX_HOME/skills`), kept for backward compatibility" —
  and `$HOME/.agents/skills`. Note the inconsistency this creates: the bundled `skill-creator`
  skill's own authoring instructions still tell Codex to "create discoverable skills in
  `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is unset"
  ([`skill-creator/SKILL.md:151`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md#L151)) —
  i.e., Codex's own built-in tool defaults to writing into the path its own loader code calls
  deprecated, rather than into `~/.agents/skills`.
- `SYSTEM` scope is **not just** "bundled with the binary" in the literal sense implied by the doc
  table. Codex compiles its sample skills directly into the binary via
  [`include_dir!("$CARGO_MANIFEST_DIR/src/assets/samples")`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/lib.rs#L55)
  and then, on startup, **extracts that embedded directory to disk** at
  `system_cache_root_dir(codex_home)` = `$CODEX_HOME/skills/.system`
  ([`skills/src/lib.rs:63-66`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/lib.rs#L63-L66)),
  guarded by a fingerprint marker file so it only rewrites when the embedded content changes. This
  is a separate mechanism from installed *plugin* packages, which get their own cache directory
  (`PLUGINS_CACHE_DIR`, referenced in `exec-server/src/discoverV2/capability_locations.rs`) — do
  not conflate "where bundled system skills like `skill-creator` get materialized" with "where
  downloaded plugins get cached"; they are two different directories under `$CODEX_HOME`.
- `ADMIN` maps to the parent directory of Codex's system config file, which on Unix is the literal
  path `/etc/codex/config.toml`
  ([`config/src/loader/mod.rs:79`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/config/src/loader/mod.rs#L79),
  `SYSTEM_CONFIG_TOML_FILE_UNIX`), i.e. `/etc/codex/skills` exactly as the doc states.
- **Symlinks:** the doc says "Codex supports symlinked skill folders and follows the symlink
  target when scanning these locations." The source
  ([`loader/host.rs:165-166`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/loader/host.rs#L165-L166))
  is more precise: `User | Repo | Admin` scopes follow directory symlinks; **`System` scope does
  not** (`DirectorySymlinkPolicy::Ignore`).
- **Ordering is not override precedence.** A `scope_rank` function (`Repo=0, User=1, System=2,
  Admin=3`) appears in at least two places —
  [`loader/host_merge.rs:262-269`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/loader/host_merge.rs#L262-L269)
  and
  [`host_service.rs:492-497`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_service.rs#L492-L497)
  (the latter building a config-cache key rather than sorting a list) — and is used only to *sort*
  or *key by* scope, never to resolve a naming collision; it is
  not a collision-resolution rule the way agentskills.io's client guide's "project-level skills
  override user-level skills" is. Root deduplication happens separately, by filesystem *root path*
  (`dedupe_skill_roots_by_path`,
  [`host_roots.rs:271`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_roots.rs#L271)),
  not by skill *name*. Combined with the doc's own explicit statement — **"If two skills share the
  same `name`, Codex doesn't merge them; both can appear in skill selectors"** — this means
  **same-named skills from different scopes coexist rather than one overriding the other.** This
  is a real divergence from the open standard's documented client convention of "project-level
  skills override user-level skills on collision" (sibling research file, §4): Codex does not
  implement that override rule; it has coexistence plus a display sort order instead. One
  practical consequence, confirmed in
  [`selection.rs:164-196`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/selection.rs#L164-L196):
  a bare `$skill-name` text mention only resolves to a specific skill when exactly one loaded skill
  has that name **and** no installed connector shares the same slug (case-insensitively) — if a
  name collides across scopes or with a connector, plain `$name` mentions silently fail to select
  anything, and only a full-path mention or the selector UI can disambiguate. See §9 for the
  authoring implication.

### 3.2 Enabling/disabling and config

From the doc: `[[skills.config]]` entries in `~/.codex/config.toml` disable a specific skill by
path without deleting it:

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

Confirmed in source
([`codex-rs/core/src/config/edit.rs:61-63`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/config/edit.rs#L61-L63),
`ConfigEdit::SetSkillConfig` / `SetSkillConfigByName`): entries can select by `path` or by `name`. A
separate top-level toggle, `[skills.bundled]\nenabled = false`, disables all bundled (`SYSTEM`-scope)
skills at once
([`codex-rs/config/src/skills_config_tests.rs:53-70`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/config/src/skills_config_tests.rs#L53-L70)).
Restart Codex after editing `config.toml`.

---

## 4. Invocation: explicit and implicit

From the doc:

> "1. **Explicit invocation:** Include the skill directly in your prompt. In ChatGPT, type `@` to
> select a skill. In Codex CLI or the IDE extension, run `/skills` or type `$` to mention a skill.
> 2. **Implicit invocation:** ChatGPT or Codex can choose a skill when your task matches the skill
> `description`."

And on writing descriptions for that implicit path: "Because implicit matching depends on
`description`, write concise descriptions with clear scope and boundaries. Front-load the key use
case and trigger words so a host can still match the skill if descriptions are shortened." This
last clause matters specifically because of the catalog budget documented next.

### 4.1 The catalog token/character budget

> "In Codex, the initial list also includes each skill's file path. To avoid crowding out the rest
> of the prompt, this list uses at most 2% of the model's context window, or 8,000 characters when
> the context window is unknown. If many skills are installed, Codex shortens skill descriptions
> first. For large skill sets, Codex may omit some skills from the initial list and show a
> warning. This budget applies only to the initial skills list. When Codex selects a skill, it
> still reads the full SKILL.md instructions for that skill."

This is Codex's concrete version of the "~50–100 tokens per catalog entry" tier-1 budget the open
standard's client-implementation guide describes in the abstract. Codex including each skill's
file path in that catalog line is consistent with, not a divergence from, the open client guide —
the sibling research file's §10 notes the guide's own recommended catalog shape is "`name`,
`description`, optional `location`."

Source confirms and sharpens the exact numbers
([`ext/skills/src/render.rs:19-29`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/render.rs#L19-L29)):
`SKILL_METADATA_CONTEXT_WINDOW_PERCENT = 2`, `DEFAULT_SKILL_METADATA_CHAR_BUDGET = 8_000`,
`MAX_CONFIGURED_SKILL_METADATA_TOKEN_BUDGET = 10_000`, and a fixed
`MAX_CATALOG_SKILL_DESCRIPTION_CHARS = 1_024` per individual catalog entry (past which a single
description gets truncated with a `...` suffix before the overall budget is even applied).

### 4.1.1 A second, separate byte cap: the selected skill's own body

Beyond the catalog budget above (which governs the compact name+description list before a skill is
chosen), Codex defines a **second, independent cap** on the full `SKILL.md` body of a skill *after*
it is selected: `MAX_SKILL_PROMPT_BYTES = 8_000`
([`render.rs:21`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/render.rs#L21),
a byte cap, not the same constant as the catalog's 8,000-*char* budget despite sharing the number),
applied by a `truncate_main_prompt_contents` helper. Eight thousand bytes is roughly 2,000 tokens —
**tighter than**, not a soft enforcement of, the open spec's "under 5,000 tokens" `SKILL.md` body
recommendation.

Tracing every call site of that helper surfaces **two different guard conditions in two different
code paths**, and this research could not fully resolve which one governs a given Codex
installation/session, so both are reported rather than collapsed into one claim:

- [`ext/skills/src/host_prompt.rs:79-88`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_prompt.rs#L79-L88),
  inside `HostSkillsSnapshot::load_skill_prompts` — whose own doc comment says "Core calls this
  directly, including for hosts without an installed skills extension" — truncates **only if the
  skill is bundled inside an agent plugin**
  (`is_agent_plugin_skill`, [`host_outcome.rs:84`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_outcome.rs#L84)):
  `if self.outcome().is_agent_plugin_skill(skill) { truncate_main_prompt_contents(&contents) } else
  { (contents, false) }`. This function is called from `core/src/session/turn.rs`, i.e. from
  Codex's own core turn loop, suggesting it is the baseline path for a standard local CLI session.
- [`ext/skills/src/extension.rs:488-497`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/extension.rs#L488-L497),
  inside the separate "skills extension" implementation that also handles `Executor`- and
  `Cloud`-sourced skills (per `catalog_prompt.rs`'s `SkillSourceKind`), calls
  `truncate_main_prompt_contents(read_result.contents.as_str())` **unconditionally, for every
  selected skill**, with no plugin check at all.

Tracing one level further resolves most of the ambiguity between these two paths. `core/src/session/turn.rs`
calls `load_skill_prompts` (the plugin-only-guard path) with exactly one input:
`mentioned_skills = collect_explicit_skill_mentions(...)` — i.e., core's own direct call is scoped
to **explicitly** mentioned skills (`$name` or a structured skill selection), not to implicitly
selected ones. Separately, `extension.rs` (the unconditional-truncation path) explicitly tracks
**host**-scope (filesystem/standalone) entries it has already injected, via
`InjectedHostSkillPrompts::insert_path` guarded by `entry.authority.kind == SkillSourceKind::Host`
([`extension.rs:521-522`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/extension.rs#L521-L522)),
and core's `host_prompt.rs` path checks `InjectedHostSkillPrompts::is_superseded_path` to avoid
re-injecting a skill the extension already handled. Put together: `host_prompt.rs`'s doc comment
("Core calls this directly, including for hosts **without** an installed skills extension") reads
as describing the *fallback* case, and `extension.rs` — which explicitly injects and truncates
**host**-scope skills, not only plugin ones — is the path exercised whenever the skills extension is
present, which is the normal condition for a standard Codex CLI/IDE-extension install. Under that
reading, **the 8,000-byte cap does apply to standalone `.agents/skills` skills too, in the default
configuration**, not only to plugin-bundled ones — the plugin-only guard in `host_prompt.rs` is the
behavior of a reduced/fallback host configuration, not the typical case.

One further nuance, from `catalog_prompt.rs`'s own model-facing instructions
([`SKILLS_HOW_TO_USE_WITH_HOST_ALIASES`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/catalog_prompt.rs#L28)):
for filesystem-hosted skills the model is told to itself "expand the listed short `path` … then
open and read its `SKILL.md` completely … If a read is truncated or paginated, continue until
EOF" — language that describes the model reading the file through a general tool. This document
could not fully reconcile this instruction with the `extension.rs`/`host_prompt.rs` injection paths
above within the scope of this pass (see Gaps, #6): it may describe a different invocation mode
(e.g. implicit selection, where the model reads the file itself, versus explicit/core-injected
mention, where core or the extension injects it pre-truncated), or a different execution
environment (Executor/Cloud-sourced skills, which `catalog_prompt.rs` also serves). Treat "Codex
applies an 8,000-byte cap to a selected skill's body in the default configuration" as the better-
supported reading, with the model-reads-it-itself instruction as a specific, not fully resolved,
exception.

### 4.2 Per-skill policy: disabling implicit invocation

`agents/openai.yaml`'s `policy.allow_implicit_invocation` (default `true`) turns off the implicit
path for one skill while keeping explicit `$skill-name` invocation available — see §5.

### 4.3 "Record & Replay" — a Codex-specific authoring path with no open-spec equivalent

The doc's "Create a skill" section offers a third creation path beyond manual authoring and the
`$skill-creator` conversational flow: "If you already know the workflow and it's easier to show
than describe, use Record & Replay. The recorder captures the workflow, inspects the steps, and
drafts a reusable skill from the demonstration." This is a Codex/ChatGPT product feature
(documented separately at `learn.chatgpt.com/docs/extend/record-and-replay`, not investigated
here) with no counterpart in the agentskills.io spec or client-implementation guide, which only
describes the two extraction methods (hands-on task, synthesize from existing artifacts) covered
in the sibling research file's §6.

---

## 5. `agents/openai.yaml` — Codex's skill-metadata extension

This file has no counterpart at all in the agentskills.io spec; it is a pure Codex/ChatGPT
extension, explicitly scoped that way in the bundled reference doc:
[`codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/assets/samples/skill-creator/references/openai_yaml.md)
states: "`agents/openai.yaml` is an extended, product-specific config intended for the
machine/harness to read, not the agent." Full example from that file:

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-400px.png"
  icon_large: "./assets/large-logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"

dependencies:
  tools:
    - type: "mcp"
      value: "github"
      description: "GitHub MCP server"
      transport: "streamable_http"
      url: "https://api.githubcopilot.com/mcp/"

policy:
  allow_implicit_invocation: true
```

Confirmed field-by-field against the Rust deserializer
([`codex-rs/skills/src/interface.rs`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/interface.rs),
`SkillInterfaceFile`) and the model types
([`codex-rs/skills/src/model.rs`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/model.rs)):

- `interface.display_name` — ≤64 chars (shares `MAX_NAME_LEN` with the `SKILL.md` `name` field).
- `interface.short_description` — ≤1024 chars (shares `MAX_DESCRIPTION_LEN`). This is the field
  the "Legacy short_description from SKILL.md" protocol comment (§2.1) says to prefer over
  `metadata.short-description`.
- `interface.icon_small` / `icon_large` — must resolve to a relative path under the skill's own
  `assets/` directory (or, for a skill bundled inside a plugin, under the plugin's shared
  `assets/`); an absolute path or a `..` escape outside those directories is rejected with a
  warning and the field is dropped, not a hard load failure.
- `interface.brand_color` — must match `^#[0-9a-fA-F]{6}$` (a strict 7-character `#RRGGBB` hex
  string) or it is dropped with a warning.
- `interface.default_prompt` — ≤1024 chars. The bundled `skill-creator`'s own authoring guidance
  requires this to explicitly reference the skill as `$skill-name` in the generated example
  prompt.
- `dependencies.tools[].type` — per `openai_yaml.md`: "Only `mcp` is supported for now."
- `dependencies.tools[].{value,description,transport,url}` — an MCP server reference; `command`
  and `oauth_callback_port` are also modeled in `SkillToolDependency` but not documented on the
  reference page (unverified beyond the struct's existence — treat as an in-progress/internal
  field).
- `policy.allow_implicit_invocation` — "When `false`, the skill is not injected into the model
  context by default, but can still be invoked explicitly via `$skill`. Defaults to true." A
  second, code-only field, `policy.products`, restricts which OpenAI product (Codex, ChatGPT,
  Atlas) a skill applies to, but a `TODO` comment at
  [`model.rs:65-66`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/model.rs#L65-L66)
  states: "Enforce product gating in Codex skill selection/injection instead of only parsing and
  storing this metadata" — i.e., as of the pinned commit, `products` is parsed but **not yet
  enforced** anywhere in skill selection.

**Naming-convention inconsistency worth flagging:** `agents/openai.yaml`'s `interface` block uses
`snake_case` keys (`display_name`, `short_description`, `brand_color`). The *plugin* manifest
format (§6) has its own, differently-cased `interface` block using `camelCase`
(`displayName`, `shortDescription`, `brandColor`) — confirmed by reading a real manifest,
`plugins/figma/.codex-plugin/plugin.json`, in the `openai/plugins` repo. These are two distinct,
non-interchangeable schemas that happen to share the word "interface."

---

## 6. Distributing skills: plugins have superseded the standalone skills catalog

**`openai/skills` is deprecated.** Its
[`README.md`](https://github.com/openai/skills/blob/778b0e6129cf18cbaee3bf11479f583fadae8d03/README.md),
as of commit `778b0e6` (2026-06-22), opens with:

> "**This repository is deprecated.** For current Codex skill and plugin examples, use the
> [OpenAI Plugins repository](https://github.com/openai/plugins). If you want to add your own
> skills to Codex, follow the [Build plugins](https://developers.openai.com/codex/plugins/build)
> guide, which includes instructions for creating a skill-only plugin."

Despite that, the current `learn.chatgpt.com/docs/build-skills.md` page still links to
`github.com/openai/skills/tree/main/skills/.curated/...` examples for "GitHub CI repair," "PDF,"
and "Linear" — i.e., the live docs page and the deprecated-repo notice have not been fully
reconciled as of the access date. Treat the `openai/skills` repo as a frozen historical example
set, not an actively maintained distribution channel.

The doc's own framing of the split: "Skills are the authoring format for reusable workflows.
Plugins distribute reusable skills and connectors through the universal plugin directory shared by
ChatGPT and Codex … Use skills to design the workflow itself, then package it as a plugin when you
want other people to install it." Standalone `.agents/skills`-style folders remain the right tool
for "local authoring and repo-scoped workflows"; plugins are for "distribute a reusable skill,
bundle two or more skills together, or ship a skill alongside a connector."

**There are, in fact, two documented plugin manifest layouts, at two different maturity stages —
this was only fully resolved by raw-fetching the "Package your plugin" doc page directly**
(`https://developers.openai.com/plugins/build/plugins.md`, fetched with `curl` in this pass; this
particular Codex doc URL, unlike the skills and AGENTS.md pages, does **not** redirect to
`learn.chatgpt.com`):

1. **The current default / "compatibility" layout**, at `<plugin-root>/.codex-plugin/plugin.json` —
   what both real example plugins inspected in `openai/plugins` (`plugins/figma`, `plugins/notion`)
   actually use, and what the built-in `@plugin-creator` skill scaffolds today. The doc says so in
   its own words: "The current scaffold uses the Codex compatibility layout, not the portable Agent
   Plugins layout … `.codex-plugin/plugin.json` files remain supported as a compatibility
   fallback." Confirmed by directly reading a real manifest,
   [`plugins/figma/.codex-plugin/plugin.json`](https://github.com/openai/plugins/blob/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f/plugins/figma/.codex-plugin/plugin.json):
   it contains `name`, `version`, `description`, `author`, `license`, a `skills` pointer
   (`"./skills/"`), an `apps` pointer, and an `interface` block using **`camelCase`** keys
   (`displayName`, `shortDescription`, `brandColor`, `defaultPrompt`) — a different casing
   convention from the `snake_case` `interface` block in a standalone skill's own `agents/openai.yaml`
   (§5). This manifest contains **no** `$schema` field.
2. **The "portable Agent Plugins" layout** (newer, cross-product) — a root `plugin.json` (no
   `.codex-plugin/` wrapper) declaring `"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"`,
   documented as the forward-looking format: "For a portable Agent Plugins package, add
   `plugin.json` at the plugin root and declare the Agent Plugins schema." The doc's own minimal
   worked example is exactly this:
   ```json
   {
     "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
     "name": "my-first-plugin",
     "version": "1.0.0",
     "description": "Reusable greeting workflow"
   }
   ```
   with skills discovered automatically from a root `skills/` directory (no `skills` pointer field
   needed, unlike layout 1). An analogous `mcp.json` with its own
   `agent-plugins.org/schemas/1.0.0/mcp.schema.json` exists for the MCP-server side of a portable
   plugin. `agent-plugins.org` is therefore a **real, currently-documented schema host for this
   emerging cross-product plugin format** — the earlier paraphrase this research initially flagged
   as possibly wrong was not wrong, it just described the newer of two coexisting formats, one of
   which (layout 1) is what every real example repository still actually ships. This document could
   not determine `agent-plugins.org`'s own governance or scope beyond what this one Codex doc page
   states (see Gaps, #3).

A plugin bundles a `skills/` directory of ordinary `SKILL.md` folders alongside optional
`.app.json` (ChatGPT app surface), `.mcp.json` (MCP server registration), `agents/` (plugin-level
extra config, including its own `openai.yaml`), `commands/`, and `hooks.json`.

### 6.1 A fourth acquisition path this document had not been looking for: Codex can import skills directly from Claude Code (and Cursor)

Codex ships a dedicated `external-agent-migration` crate whose entire purpose is one-way migration
of configuration from other agent tools into Codex. It currently supports exactly two source
agents, modeled as an `ExternalAgentSource` enum with variants `Cla` and `Cur`
([`migration_source.rs:52`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/migration_source.rs#L52)):

- **`Cla`** ("Claude") — source config directory `.claude`, source guidance file `CLAUDE.md`
  ([`source/cla.rs:20-21`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/source/cla.rs#L20-L21)).
- **`Cur`** ("Cursor") — its own separate config layout.

For skills specifically, `skills_dir_names` returns `["skills"]` for both sources in the general
case (i.e., `.claude/skills` and the Cursor equivalent), with a Cursor-only home-scope addition of
`skills-cursor`
([`migration_source.rs:76-80`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/migration_source.rs#L76-L80)).
The copy logic
([`utils.rs:44-86`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/utils.rs#L44-L86))
recursively copies a skill's directory tree byte-for-byte, **except** the `SKILL.md` file itself,
whose *text content* is passed through a `RewriteProfile`
([`source/cla.rs:23-32`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/source/cla.rs#L23-L32)
constructs it; [`rewrite.rs:39-49`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/rewrite.rs#L39-L49)
implements `rewrite()`). Reading `rewrite()` directly resolves exactly what it does:

- `doc_file_name` (`"CLAUDE.md"` for the `Cla` profile) is replaced with the literal string
  `"AGENTS.md"` — so a skill's own reference to `CLAUDE.md` becomes a reference to `AGENTS.md` on
  import.
- Every string in `term_variants` (`"claude code"`, `"claude-code"`, `"claude_code"`,
  `"claudecode"`, `"claude"`) is matched **case-insensitively** (the haystack and needle are both
  lowercased before matching,
  [`replace_case_insensitive_with_boundaries`, `rewrite.rs:85-122`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/external-agent-migration/src/rewrite.rs#L85-L122)),
  **at word boundaries only** (a byte before/after the match must not be alphanumeric or `_`, so
  "Claude" inside "ClaudeBot" would not match, but "Claude", "CLAUDE", or "claude" as a standalone
  word would), and replaced with the literal string `"Codex"`.
- The `Cla` profile's `REWRITE_PROFILE` is built with `RewriteProfile::new(...)`, which leaves the
  separate `case_sensitive_term_variants` list empty — so, for Claude-sourced migrations,
  **everything is matched case-insensitively**; there is no case-sensitive term list actually
  populated for this source. (An earlier draft of this section incorrectly called the term list
  "case-sensitive as written" — it is the opposite: case-insensitive by construction.)

So a phrase like "this Claude Code skill…" in an imported `SKILL.md` **would** be rewritten (the
two-word variant "claude code" matches "Claude Code" case-insensitively at word boundaries and
becomes "Codex"), yielding "this Codex skill…" — case does not save a Claude-specific mention from
being rewritten.

**Conclusion:** a skill written for Claude Code, sitting in `.claude/skills/`, is a
**first-party-supported migration source for Codex**, not merely "happens to be compatible because
both read `SKILL.md`" — OpenAI built and ships code specifically to detect and import it, rewriting
only the `SKILL.md` file's own prose (product-name mentions and its `CLAUDE.md`→`AGENTS.md`
reference) while copying every other bundled file (`scripts/`, `references/`, `assets/`) byte for
byte, unchanged. This document did not trace how this migration is actually invoked by a user (the
exact CLI command/prompt path was out of scope for this pass), only that the source-side detection
and copy logic exists and specifically targets `.claude/skills` and `CLAUDE.md`.

**This one-time migration is not the only Claude-compatibility mechanism — Codex's *plugin* loader
separately recognizes Claude Code's own plugin manifest format at runtime, on an ongoing basis, with
no import step at all.** A broader repo-wide `grep -rn '\.claude' codex-rs --include=*.rs` (not
excluding anything this time) surfaces two production, non-test constants:

- [`exec-server-protocol/src/protocol.rs:49-52`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/exec-server-protocol/src/protocol.rs#L49-L52) —
  `DISCOVERABLE_PLUGIN_MANIFEST_PATHS`, "Ordered plugin manifest paths recognized beneath a plugin
  root": `[".codex-plugin/plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"]`.
- [`core-plugins/src/marketplace.rs:19-24`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core-plugins/src/marketplace.rs#L19-L24) —
  `MARKETPLACE_MANIFEST_RELATIVE_PATHS`: `[".agents/plugins/marketplace.json",
  ".agents/plugins/api_marketplace.json", ".claude-plugin/marketplace.json",
  ".cursor-plugin/marketplace.json"]`.

So: a **plugin** (§6) that ships a `.claude-plugin/plugin.json` manifest — Claude Code's own plugin
manifest filename and location — is directly discoverable and loadable by Codex's plugin system,
with no rewrite, no migration step, and no `.codex-plugin/` equivalent required. This is a distinct
mechanism from both the `.codex-plugin/plugin.json` "compatibility layout" and the portable root
`plugin.json` (§6) — a third, cross-product manifest location Codex reads natively. It is scoped to
the **plugin manifest itself** (identity, name, version, interface metadata), not to individual
`SKILL.md` files inside `skills/` — those are still ordinary `SKILL.md` files read the normal way
once the plugin is discovered. By contrast, a **standalone** `.claude/skills/` directory sitting
outside any plugin structure is not in this discoverable-manifest list at all; for that case, the
`external-agent-migration` crate's one-time copy-and-rewrite path (above) is, as far as this
research could determine, the only route into Codex.

---

## 7. AGENTS.md for Codex

From `learn.chatgpt.com/docs/agent-configuration/agents-md.md` (fetched verbatim, 2026-09-30):

> "Codex reads `AGENTS.md` files before doing any work. By layering global guidance with
> project-specific overrides, you can start each task with consistent expectations, no matter
> which repository you open."

### 7.1 Discovery and merge algorithm (exact, doc + source-confirmed)

The doc states the precedence order explicitly:

> "Codex builds an instruction chain when it starts (once per run; in the TUI this usually means
> once per launched session). Discovery follows this precedence order:
> 1. **Global scope:** In your Codex home directory (defaults to `~/.codex`, unless you set
> `CODEX_HOME`), Codex reads `AGENTS.override.md` if it exists. Otherwise, Codex reads
> `AGENTS.md`. Codex uses only the first non-empty file at this level.
> 2. **Project scope:** Starting at the project root (typically the Git root), Codex walks down to
> your current working directory. If Codex cannot find a project root, it only checks the current
> directory. In each directory along the path, it checks for `AGENTS.override.md`, then
> `AGENTS.md`, then any fallback names in `project_doc_fallback_filenames`. Codex includes at most
> one file per directory.
> 3. **Merge order:** Codex concatenates files from the root down, joining them with blank lines.
> Files closer to your current directory override earlier guidance because they appear later in
> the combined prompt."

And: "Codex skips empty files and stops adding files once the combined size reaches the limit
defined by `project_doc_max_bytes` (32 KiB by default)."

This is confirmed to the byte in
[`codex-rs/core/src/agents_md.rs`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/agents_md.rs)
and
[`codex-rs/core/src/config/mod.rs`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/config/mod.rs):

- `DEFAULT_AGENTS_MD_FILENAME = "AGENTS.md"`, `LOCAL_AGENTS_MD_FILENAME = "AGENTS.override.md"`
  (`agents_md.rs:42-45`).
- The project-root marker defaults to `[".git"]` (`default_project_root_markers`), configurable
  via `project_root_markers`; an empty marker list disables upward traversal entirely, and Codex
  "do[es] **not** walk past the project root" (module doc comment,
  [`agents_md.rs:1-18`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/agents_md.rs#L1-L18)).
- The join separator between the user-level and project-level blocks is the literal string
  `"\n\n--- project-doc ---\n\n"`
  ([`AGENTS_MD_SEPARATOR`, `agents_md.rs:49`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/agents_md.rs#L49)) —
  not documented on the hosted page, only visible in source.
- `AGENTS_MD_MAX_BYTES` resolves to `DEFAULT_PROJECT_DOC_MAX_BYTES`, commented `// 32 KiB`
  ([`config/mod.rs:255`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/config/mod.rs#L255)),
  matching the doc's "32 KiB by default" exactly.

**Important precision the doc's file-tree example adds:** within a single directory, an
`AGENTS.override.md` does not get concatenated alongside a sibling `AGENTS.md` — it *replaces* it
for that directory. The doc's worked example shows `services/payments/AGENTS.md` annotated
"Ignored because an override exists" once `services/payments/AGENTS.override.md` is added. So
"override" here means "one file wins per directory, `.override.md` beats `.md`," not "later text
overrides earlier text via LLM instruction-following" — that second, weaker sense is what governs
different *directories'* content once concatenated (a nested file's guidance is not structurally
enforced to win, it just physically appears later in the prompt, and the doc relies on the model to
treat later text as higher-priority).

This is worth contrasting with how the generic, Codex-agnostic agents.md project describes the
same idea. Its own FAQ ([`components/FAQSection.tsx`](https://github.com/agentsmd/agents.md/blob/d001185d792eb6402a58e4cbef1c228b309ec25d/components/FAQSection.tsx)), verbatim: "What if instructions
conflict? The closest AGENTS.md to the edited file wins; explicit user chat prompts override
everything." Read literally, "wins" sounds like exclusion — as if only the closest file's content
reaches the model. Codex's actual behavior is concatenation with the closest file appearing last,
not exclusion of the farther ones — "wins" in Codex's implementation means "appears latest in the
combined prompt, which the model is expected to weight more heavily," not "is the only one
included."

### 7.2 Configuration knobs

- `project_doc_max_bytes` (TOML, default 32768) — raises or lowers the 32 KiB cap.
- `project_doc_fallback_filenames` (TOML, list of strings) — additional filenames checked after
  `AGENTS.override.md` and `AGENTS.md` in each directory, e.g.
  `["TEAM_GUIDE.md", ".agents.md"]`. Entries containing path separators for the executor's OS are
  ignored before any filesystem probe
  ([`agents_md.rs:273-288`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/agents_md.rs#L273-L288)).
- `CODEX_HOME` — relocates the "global scope" file and the deprecated user-skills directory (§3.1)
  together; the doc shows setting it per-invocation for "a project-specific automation user."

### 7.3 Where AGENTS.md content actually lands in the model's context

[`core/src/context/user_instructions.rs:24`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/context/user_instructions.rs#L24)
wraps the assembled text under the header `"# AGENTS.md instructions"`.
[`core/src/tools/handlers/multi_agents_spec.rs:733`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/core/src/tools/handlers/multi_agents_spec.rs#L733)
shows Codex's own internal sub-agent-spawning guidance explicitly treating AGENTS.md and skills as
siblings-but-distinct
sources of user intent: "Do not spawn sub-agents unless the user or applicable AGENTS.md/skill
instructions explicitly ask for sub-agents, delegation, or parallel agent work." — i.e., inside
Codex's own source, "AGENTS.md instructions" and "skill instructions" are named as two separate,
coexisting categories of guidance the model receives, not one folded into the other.

---

## 8. AGENTS.md vs. Agent Skills (SKILL.md): relationship and differences

This is the question most likely to get conflated, so stated plainly first: **these are two
separate, separately-governed, separately-invented things that Codex happens to support
together.** Nothing on `agents.md` mentions Agent Skills or `SKILL.md` at all — the entire
comparison below rests on Codex's own docs and source, not on any first-party statement from the
AGENTS.md side.

### 8.1 Origin and governance

- **AGENTS.md** is older. Its repository's first commit
  ([`ba9474a6`](https://github.com/agentsmd/agents.md/commit/ba9474a69e9a2c0c4176713843b78e8f54377941))
  is dated **2025-08-19**. Reading the site's own React source directly (not a paraphrase) —
  [`components/AboutSection.tsx`](https://github.com/agentsmd/agents.md/blob/d001185d792eb6402a58e4cbef1c228b309ec25d/components/AboutSection.tsx):

  > "AGENTS.md emerged from collaborative efforts across the AI software development ecosystem,
  > including OpenAI Codex, Amp, Jules from Google, Cursor, and Factory." … "AGENTS.md is now
  > stewarded by the Agentic AI Foundation under the Linux Foundation."

  And [`components/Hero.tsx`](https://github.com/agentsmd/agents.md/blob/d001185d792eb6402a58e4cbef1c228b309ec25d/components/Hero.tsx) /
  [`pages/_app.tsx`](https://github.com/agentsmd/agents.md/blob/d001185d792eb6402a58e4cbef1c228b309ec25d/pages/_app.tsx):
  "AGENTS.md is a simple, open format for guiding coding agents, used by over 60k open-source
  projects." So: multi-vendor from the start (OpenAI/Codex is one of five named founding
  contributors, not the sole author), now under neutral foundation governance.
- **Agent Skills / agentskills.io**, per the sibling research file, was "originally developed by
  [Anthropic], released as an open standard." That file records the `agentskills/agentskills`
  repository's own commit history as beginning **2025-12-18**, roughly four months *after*
  AGENTS.md's first commit — but the sibling document itself notes that repository was moved from
  an earlier `anthropics/agentskills` location (visible in the stray PyPI metadata it found), so
  2025-12-18 is a documented lower bound for *that specific repository's* history, not necessarily
  the true origin date of Anthropic's underlying Skills work. With that caveat, the ordering
  evidence available from both research passes still points the same way: **AGENTS.md's earliest
  recorded commit predates the open agentskills.io repository's earliest recorded commit.** This
  research could not determine when Codex itself first shipped `SKILL.md` support (see Scope &
  method), so no claim is made here about which Codex *feature* Codex itself adopted first — only
  about the relative age of the two upstream projects.

### 8.2 Purpose and content model

| | AGENTS.md | Agent Skills (`SKILL.md`) |
| --- | --- | --- |
| What it is | A single (per-directory) plain-Markdown "README for agents" | A directory bundle: `SKILL.md` + optional `scripts/`, `references/`, `assets/` |
| Required structure | None. The site's own FAQ ([`components/FAQSection.tsx`](https://github.com/agentsmd/agents.md/blob/d001185d792eb6402a58e4cbef1c228b309ec25d/components/FAQSection.tsx)), verbatim: "Are there required fields? No. AGENTS.md is just standard Markdown. Use any headings you like; the agent simply parses the text you provide." | YAML frontmatter with required `name` and `description` |
| When it's loaded | **Always**, for every task, concatenated from every applicable directory, "before doing any work" | **Progressively**: name+description always visible in a compact catalog; full body only once selected; `scripts/`/`references/`/`assets/` only as needed |
| How much can be loaded | Capped by `project_doc_max_bytes` (32 KiB default) across *all* applicable files combined | Catalog capped at ~2% of context / 8,000 chars (§4.1); a selected skill's own body is capped at 8,000 *bytes* (~2,000 tokens), applying to standalone skills as well as plugin ones whenever the skills extension is active — the normal case (§4.1.1) |
| Selection mechanism | None — there is no "matching"; whatever files are found on the discovery walk are all included | Two mechanisms: implicit (LLM judges the `description` matches the task) or explicit (`$skill-name` mention, `/skills` command) |
| Granularity | One (layered) file per project — genuinely global/ambient guidance | Many independent, individually-selectable units — task-specific, opt-in-by-relevance capabilities |
| Governance | Agentic AI Foundation (Linux Foundation), multi-vendor from inception | Originated at Anthropic, now an open spec at agentskills.io; Codex is one of the clients that implements it |

### 8.3 The naming trap: `.agents/skills/` is not AGENTS.md

Because Agent Skills' cross-client discovery convention is a directory literally named
`.agents/skills/` (§3, and confirmed as the agentskills.io client-guide's own recommended
convention in the sibling research file's §4), and because AGENTS.md's own filename also starts
with "Agents," it is easy to conflate the two. In Codex's implementation they are two unrelated
mechanisms that happen to walk **the same range of directories** by **the same shared logic**, but
combine what they find in completely different ways — this is a subtler distinction than "opposite
directions," and worth stating precisely because it is easy to get wrong:

- **They scan the same directory range, using the same project-root setting but two separate
  implementations of "find the root."** `AGENTS.md` discovery
  (`agents_md.rs`'s `load_project_instructions`) and repo-scoped skills discovery
  (`host_roots.rs`'s `repo_agents_skill_roots`) both read the same configured
  `project_root_markers` setting (default `[".git"]`) to decide what counts as a project root, and
  both fall back to treating the current working directory as the only directory considered when no
  marker is found up the ancestor chain (confirmed by reading
  [`host_roots.rs:206-247`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/ext/skills/src/host_roots.rs#L206-L247)'s
  `find_project_root`, which returns `cwd.clone()` both when the marker list is empty and when no
  ancestor probe finds a match — the same two fallback conditions the `agents_md.rs` module comment
  describes). This is, however, **two independently-implemented functions with the same
  configuration and the same fallback behavior**, not literally one shared code path — `agents_md.rs`
  uses `find_nearest_ancestor_with_markers`, while `host_roots.rs` has its own `find_project_root`.
  Given that, both mechanisms end up enumerating the same inclusive set of directories between the
  project root and the current working directory. The hosted docs describe this range in two
  different reading orders — AGENTS.md's doc says Codex "walks down" from the root to the cwd; the
  skills doc says Codex "scans … from your current working directory up to the repository root" —
  but these describe the same inclusive directory set, just narrated in opposite reading order.
  There is no actual directional divergence in what gets discovered.
- **What differs is aggregation, not direction.** For `AGENTS.md`, Codex picks **at most one file
  per directory** (`AGENTS.override.md` beats `AGENTS.md` beats any configured fallback name) and
  concatenates the *entire text* of every directory's winning file into one always-present prompt
  block, capped at 32 KiB total. For `.agents/skills/`, Codex instead treats each directory's
  `.agents/skills/` as a *container of independently-selectable units*: every subdirectory with its
  own `SKILL.md` becomes one catalog entry (name + description only, until selected), with no
  single-file-per-directory rule and no "closer one wins" rule — same-named skills from different
  directories/scopes coexist (§3.1) rather than the nearer one replacing the farther one the way a
  nearer `AGENTS.md` effectively does.
- **`AGENTS.md` is a file; `.agents/skills/` is a directory of directories.** One is a leaf; the
  other is itself a discovery root that Codex recurses into looking for `SKILL.md` files.

Codex's own hosted AGENTS.md doc treats the two as complementary rather than substitutable: its
"Next steps" section links out to `https://agents.md` for general AGENTS.md background, while the
separate `build-skills.md` page is where skills are documented — the two pages never cross-link to
explain the boundary between them, so a reader who only finds one of the two pages could easily
miss the other's existence.

### 8.4 Practical rule of thumb (synthesized from the above, not a direct quote)

Put something in **AGENTS.md** when it should shape *every* task Codex does in that
directory/repository regardless of what the task is — build commands, code style, review rules,
"always run the tests before committing." Put something in a **Skill** when it is a self-contained
procedure that only a subset of tasks need, especially one that benefits from being loaded on
demand (to save context), bundling its own scripts/reference material, or being explicitly
invoked by name (`$skill-name`) rather than inferred.

---

## 9. Best practices for authoring AGENTS.md and Skills for Codex

### 9.1 AGENTS.md, from Codex's own docs

- Put durable, cross-repo working agreements in the global file (`~/.codex/AGENTS.md`); put
  repository norms in the repo-root `AGENTS.md`; put team- or service-specific exceptions in a
  nested `AGENTS.override.md` as close as possible to the code they govern, since "Codex stops
  searching once it reaches your current directory, so place overrides as close to specialized
  work as possible."
- For Codex's GitHub code-review integration specifically, add a `## Code Review Rules` section
  "to the `AGENTS.md` closest to the code the rules govern," keep each rule "concise, explain the
  behavior to flag and any safe path or exception, and reserve formatting and lint checks for CI."
- If a repository already has a non-standard conventions file (e.g. `TEAM_GUIDE.md`), register it
  in `project_doc_fallback_filenames` rather than duplicating its content into a new `AGENTS.md`.
- Raise `project_doc_max_bytes` (or split guidance across nested directories) rather than letting
  instructions silently truncate at the 32 KiB default — the doc lists "Instructions truncated" as
  a named troubleshooting case with exactly that fix.
- To debug what Codex actually loaded, the doc recommends asking Codex directly
  (`codex --ask-for-approval never "Summarize the current instructions."`) or inspecting a TUI log
  / session JSONL file — there is no separate "list active AGENTS.md files" command.

### 9.2 Skills, from Codex's own bundled `skill-creator` (the most detailed first-party guidance
found, and effectively Codex's answer to Anthropic's `skill-creator`)

All of the following are direct paraphrases/quotes of
`codex-rs/skills/src/assets/samples/skill-creator/SKILL.md`, i.e. instructions Codex itself ships
and follows when authoring skills:

- **Assume Codex is already capable.** "Include only information that changes its decisions or
  improves its work. Remove generic advice, repeated instructions, speculative edge cases, and
  examples that do not materially clarify the task."
- **Match specificity to risk, not to thoroughness.** "Give the model room to choose an appropriate
  approach when multiple approaches are reasonable. Use detailed steps, deterministic scripts, or
  absolute language only when correctness, safety, permissions, or a genuinely fragile workflow
  requires them."
- **Keep discovery cheap and precise.** "Skill names and descriptions are available before a skill
  is loaded. Describe the actual capability and when it applies, adding exclusions only when they
  prevent likely misrouting. Avoid exhaustive capability lists and catchalls that attract unrelated
  requests." A worked example of a well-scoped description: "Create or edit Word documents when
  formatting, tracked changes, or comments require document-specific handling."
- **Disclose detail progressively**, same principle as the open standard: keep shared purpose and
  essential constraints in `SKILL.md`; move "substantial mode-specific guidance, schemas, examples,
  or procedures" into `references/`, and "read only the references relevant to the current task."
- **Naming:** "Use lowercase letters, digits, and hyphens. Keep names under 64 characters and
  prefer short action-oriented names. Namespace by tool or domain when doing so improves discovery.
  Name the skill folder after the skill." (Note this authoring guidance is stricter than what the
  Rust runtime loader actually enforces — see §2.1 — so following it produces a skill that is
  portable to `quick_validate.py` and to other agentskills.io clients even though Codex's own
  loader would tolerate a laxer name.)
- **Default to automatic (implicit) invocation.** "Automatic skill selection is allowed by default.
  Change that default only when the user explicitly requests an explicit-only skill" via
  `policy.allow_implicit_invocation: false`. Do not infer explicit-only from "sensitive operations
  or required approvals: keep the skill discoverable and require authorization immediately before
  the actual mutation" — i.e., gate the dangerous action itself, not the skill's discoverability.
- **What not to include:** "Avoid adding a `README.md`, installation guide, changelog, duplicated
  quick reference, or other auxiliary documentation unless a specific task or packaging requirement
  calls for it."
- **Validate, then forward-test.** Run `scripts/quick_validate.py <path>` — "it does not prove that
  the skill makes good decisions" — and, for complex or risky skills, do an "Independent
  Forward-Testing" pass: hand an evaluating subagent "a realistic user request, the skill, and the
  minimum raw artifacts needed," withholding the intended answer or suspected bug, then "make only
  changes supported by the observed behavior."
- **Scaffolding tools that ship with the sample:** `scripts/init_skill.py <name> --path <dir>
  [--resources scripts,references,assets] [--examples]` to create a new skill's files, and
  `scripts/generate_openai_yaml.py <path> --interface key=value` to (re)generate
  `agents/openai.yaml` — "The generator replaces the entire file. If an existing file contains
  `policy` or `dependencies`, update only the intended fields in place instead of regenerating it."

### 9.3 A source-derived best practice not stated in any doc: keep names globally unique

Because Codex does not deduplicate or override same-named skills across scopes (§3.1), and because
a bare `$skill-name` mention only resolves when the loaded skill count for that name is exactly one
**and** no installed connector shares the same slug case-insensitively
([`selection.rs:164-196`](https://github.com/openai/codex/blob/0b43721d8d1f734658e41bffe12a6ba6c9240abd/codex-rs/skills/src/selection.rs#L164-L196)),
an author who names a repo skill the same as an existing user-, admin-, or system-scope skill (or
the same as an installed connector) does not get "my copy wins" — they get a name that silently
fails to resolve via the plain `$name` shorthand from that point on, in the affected scope. Pick
names that are unlikely to collide with system-bundled skills (`skill-creator`, `skill-installer`,
etc.), other repos' `.agents/skills`, or connector/app slugs, and namespace by tool or domain when
in doubt — exactly the naming advice the bundled `skill-creator` gives (§9.2) for a different
reason (discoverability) that turns out to also be the fix for this collision behavior.

Relatedly: keep `description` at or under the spec's own 1,024-character cap even though Codex's
runtime loader does not enforce it (§2.1). A longer description still loads, but Codex's catalog
renderer silently truncates it to 1,024 characters for the purpose of implicit-invocation matching
— so anything past that point can never help (or hurt) whether the skill gets selected.

### 9.4 From the hosted docs' own "Best practices" list (`build-skills.md`)

- "Keep each skill focused on one job."
- "Prefer instructions over scripts unless you need deterministic behavior or external tooling."
- "Write imperative steps with explicit inputs and outputs."
- "Test prompts against the skill description to confirm the right trigger behavior."

---

## 10. Versioning / evolution notes specific to Codex

- Codex's skills documentation has moved at least once at the URL level: the canonical-looking
  `developers.openai.com/codex/...` paths now 308-redirect to `learn.chatgpt.com/docs/...`. Anyone
  linking to the old host should expect the redirect, not a 404, but should also expect the
  in-repo docs (`docs/skills.md`, `docs/agents_md.md`) to remain one-line stubs pointing outward
  rather than mirroring content.
- `openai/skills` (the original skills catalog repo) is deprecated in favor of `openai/plugins`,
  as of 2026-06-22 — see §6. This is a meaningful shift in how OpenAI expects third parties to
  distribute skills — bundled inside a plugin, either with the current-default
  `.codex-plugin/plugin.json` "compatibility" manifest or the newer, portable root `plugin.json`
  declaring the `agent-plugins.org` schema (§6) — versus how the earliest Codex skills tooling
  expected them to be distributed (a flat catalog of standalone skill folders installed via
  `$skill-installer`). The `$skill-installer` mechanism itself is still documented as current
  ("Use this for local setup and experimentation. For reusable distribution of your own skills,
  prefer plugins.") — it has not been removed, just de-emphasized relative to plugins. Within
  plugin manifests specifically, Codex is also mid-migration from its own
  `.codex-plugin/plugin.json` format toward the cross-product portable one — two formats
  coexist today, with real example repos still shipping the older one.
- Within `openai/codex`'s own source, `SkillPolicy.products` (product-gating for
  Codex/ChatGPT/Atlas) is parsed but explicitly not yet enforced (§5) — a concrete example of a
  schema field that exists ahead of the behavior it is meant to control.
- No changelog entries mentioning "skill" were found in `openai/codex`'s root `CHANGELOG.md` at
  the pinned commit; this repository does not appear to use that file to announce this kind of
  feature, so its absence there should not be read as evidence about when skills support shipped.

---

## Gaps / unverified

1. **Exact commit/date Codex first added Skills or AGENTS.md support.** Not determinable from a
   shallow clone; not asserted anywhere in this document.
2. **`dependencies.tools[].command` and `.oauth_callback_port`** (`SkillToolDependency` in
   `model.rs`) exist in the Rust struct but are not documented on
   `references/openai_yaml.md` or the hosted docs page. Their intended use is unverified.
3. ~~The `agent-plugins.org` plugin schema~~ — **resolved during verification, see §6**: it is a
   real, currently-documented schema host for Codex/ChatGPT's newer "portable Agent Plugins"
   manifest format, confirmed by a raw fetch of `developers.openai.com/plugins/build/plugins.md`.
   What remains unverified is `agent-plugins.org`'s own governance, scope, and relationship (if
   any) to other agent-tooling standards efforts — this document did not fetch `agent-plugins.org`
   itself, only the one Codex doc page that references it.
4. **Whether `SKILL.json` is a real, planned, or abandoned format.** The only evidence is the
   single stale-looking code comment in §2.1; no schema, parser, or writer for a file by that name
   was found anywhere in the inspected `openai/codex` commit.
5. **ChatGPT-side behavior** (as opposed to Codex CLI/IDE-extension behavior) for skills — the
   `@skill` mention syntax, the "Skills" sidebar, and Record & Replay were only confirmed via the
   shared documentation page, not by inspecting any ChatGPT-specific source, which is outside this
   repository's reach.
6. **Reconciling `catalog_prompt.rs`'s "the model reads `SKILL.md` itself" instruction with the
   `extension.rs`/`host_prompt.rs` injection paths that apply the 8,000-byte cap.** §4.1.1 traced
   enough of the call graph to conclude, with reasonable confidence, that the 8,000-byte
   (`MAX_SKILL_PROMPT_BYTES`) truncation applies to standalone `.agents/skills` skills too whenever
   the skills extension is active (the normal case), not only to plugin-bundled skills. What remains
   unresolved is how that squares with `catalog_prompt.rs`'s model-facing text telling the model to
   read a filesystem-hosted skill's `SKILL.md` itself via a general file tool — whether that
   describes a different invocation mode, a different execution environment, or is read *after* an
   already-truncated version was injected. This document does not have a fully reconciled account
   of all skill-body-delivery paths in Codex.

---

## Implications for this repo

`skill-maker`'s existing references (`spec-reference.md`, `spec-provenance.md`,
`authoring-guide.md`) document the open agentskills.io standard and this repo's own hardening
choices. This repo's own validator's `ALLOWED_PROPERTIES` set is
`{name, description, license, allowed-tools, metadata, compatibility}` — i.e. all six open-spec
fields (confirmed by reading
`skills/skill-maker/scripts/quick_validate.py` directly in this pass). None of the existing
references currently distinguish "what agentskills.io says" from "what Codex's own runtime, or
Codex's own bundled authoring validator, actually does with a skill built by this tool." Concrete,
verified points worth carrying into that guidance if `skill-maker` wants to claim Codex
compatibility explicitly:

1. **Codex's own bundled authoring validator is narrower than this repo's, in one specific way
   this repo should know about: it has no `compatibility` field in its allow-list.** Codex ships
   its own version of this kind of script,
   `codex-rs/skills/src/assets/samples/skill-creator/scripts/quick_validate.py`, whose
   `allowed_properties` is `{"name", "description", "license", "allowed-tools", "metadata"}` —
   missing `compatibility`. A skill this repo produces that legitimately uses the spec's
   `compatibility` field (which this repo's own validator explicitly allows and the open spec
   defines) would be flagged as an "Unexpected key" failure by Codex's own bundled
   `quick_validate.py`, even though it would load without issue in Codex's actual runtime (§2.1,
   which ignores unrecognized frontmatter keys entirely rather than rejecting them). If this repo
   ever documents Codex compatibility, note this specific gap rather than assuming "Codex's
   validator" and "this repo's validator" check the same six fields.
2. **A skill that is valid by this repo's own validator should load fine in Codex's runtime, with
   one Unicode-length exception.** Codex's Rust loader (§2.1) reads only `name`, `description`, and
   `metadata.short-description` from frontmatter — it silently ignores every other key, *including*
   `license`, `compatibility`, and `allowed-tools`, which are spec fields this repo's own validator
   explicitly *allows* (not forbids). The exception: this repo's validator length-checks the
   **NFKC-normalized** name (64-char limit applied after `unicodedata.normalize('NFKC', name)`),
   while Codex's Rust parser length-checks the **raw**, unnormalized `chars().count()` (§2.1). A
   name written with decomposed Unicode (a base letter plus a separate combining accent mark,
   rather than one precomposed character) can have 64 or fewer characters *after* NFKC
   normalization — passing this repo's validator — while still exceeding 64 *raw* code points,
   which Codex's loader would refuse to load with "exceeds maximum length of 64 characters." NFKC
   composition only ever shortens or preserves length, so this failure runs in one direction only:
   a name skill-maker accepts can be one Codex's loader rejects, never the reverse.
3. **The angle-bracket rejection this repo's own validator applies is not independent, convergent
   evidence of an ecosystem convention — it is very likely the same rule, copied.** A direct `diff`
   between this repo's `skills/skill-maker/scripts/quick_validate.py` and Codex's
   `skill-creator/scripts/quick_validate.py`, performed in this pass, shows the two scripts share
   the same function name (`validate_skill`), the same overall control flow, and near-identical
   error-message wording — including the exact string "cannot start/end with hyphen or contain
   consecutive hyphens" and "Description cannot contain angle brackets (< or >)". This is strong
   evidence of a **shared ancestor** (plausibly Anthropic's own `skill-creator` reference tooling,
   which the sibling research file's §6 already cites as the tool the agentskills.io best-practices
   guide points to), independently adapted by both OpenAI and this repo — not two unrelated
   implementations independently arriving at the same rule. It is therefore still fair to say the
   angle-bracket rule is a real, attributable convention rather than an invented one, but the
   correct attribution is "a convention inherited from a shared lineage of `skill-creator`-style
   tooling," not "two independent clients converged on the same answer." It is also worth being
   precise about *which part* of Codex enforces it: Codex's **runtime loader accepts angle
   brackets** in `description` without complaint (§2.1); only Codex's own **authoring tool**
   (`quick_validate.py`, run by the `skill-creator` skill against skills it writes) rejects them.
   "Codex rejects angle brackets" would overstate what is actually true only of one specific
   bundled script.
4. **`agents/openai.yaml` is now a verified, sourced schema**, not an unverified claim. The sibling
   research file's Gap #10 and `spec-provenance.md`'s "Client extension fields" list both flag
   client-specific extension fields (naming `agents/openai.yaml` among them) as unverifiable
   without reading each client's own docs. This document verifies that schema directly against
   Codex's Rust deserializer and reference doc (§5): `interface.{display_name, short_description,
   icon_small, icon_large, brand_color, default_prompt}`, `dependencies.tools[].{type, value,
   description, transport, url}`, and `policy.{allow_implicit_invocation, products}`, with exact
   length limits and validation behavior for each.
5. **`~/.agent/skills/` (singular) still does not appear anywhere in Codex.** The sibling research
   file's Gap #3 already flags this path (from this repo's own `spec-reference.md`) as unverified
   against agentskills.io's own client guide, which lists only the plural `~/.agents/skills/`.
   Codex's discovery code (§3, §3.1) also only ever uses the plural `.agents/skills` — confirmed
   directly in `AGENTS_DIR_NAME`/`SKILLS_DIR_NAME` constants in `host_roots.rs`. This is a second,
   independent client confirming the plural form and never using the singular one; nothing found in
   this pass supports keeping `~/.agent/skills/` in this repo's reference material.
6. **This repo's own body-length warning threshold (~5,000 tokens / ~20 KB, soft) sits well above
   Codex's 8,000-byte (~2,000-token) hard truncation cap found in §4.1.1.** `skill-maker`'s
   `quick_validate.py` only *warns* once a `SKILL.md` body exceeds `BODY_TOKEN_BUDGET = 5000`
   (approximated as chars/4) or `BODY_LINE_BUDGET = 500` lines, matching the open spec's own
   recommendation. A body that passes that warning-free (e.g. 3,000–4,000 tokens, comfortably under
   this repo's own budget) can still be **more than twice** what at least one Codex code path will
   inject before truncating it (§4.1.1), with Codex silently cutting it off mid-instruction rather
   than erroring. If this repo wants a Codex-safe body budget, note that Codex's own hard limit is
   materially tighter than this repo's soft one. This is worth connecting to this repo's own
   multiple-`SKILL.md` validation error, which tells an author to "build a plugin" as one resolution
   path for separate skills bundled together — plugins are exactly the distribution path this
   document confirms is truncated at 8,000 bytes (§4.1.1), so that suggested fix does not exempt an
   author from the tighter budget.
7. Codex's catalog-description truncation limit, `MAX_CATALOG_SKILL_DESCRIPTION_CHARS = 1_024`
   (§4.1), numerically matches the open spec's own `description` ceiling that this repo's validator
   already enforces — so a spec-conformant description is never catalog-truncated by Codex. No
   action needed; noted for completeness.
8. `skill-maker`'s references were checked (`grep -rn "codex/skills\|CODEX_HOME"
   skills/skill-maker/references/`) and currently contain **no** Codex-specific install-path
   guidance at all, so there is nothing existing to correct on that front — but if this repo ever
   adds instructions telling a user where to put a skill for Codex specifically, `~/.codex/skills`
   is explicitly called "deprecated … kept for backward compatibility" in Codex's own source
   (§3.1); prefer `~/.agents/skills` or a repo-local `.agents/skills`.
9. **A skill built by this repo and placed under `.claude/skills/` is a supported, first-party
   Codex import source, not just an accidentally-compatible file (§6.1).** If this repo ever adds
   Codex-specific packaging or install guidance, it's worth knowing OpenAI ships code that
   specifically detects `.claude/skills/*/SKILL.md` and copies it into Codex, rewriting only the
   literal strings `claude`, `claude code`, `claude-code`, `claude_code`, and `claudecode` inside
   `SKILL.md`'s own text. A skill whose `SKILL.md` prose says something like "this Claude Code
   skill…" would have that phrase mechanically rewritten on import in a way this repo cannot
   control or preview; a skill that avoids naming the host product by name in its own body (already
   good practice for a cross-platform tool) sidesteps this rewrite entirely.

Beyond validation, if this repo ever wants to author Codex-specific guidance (e.g. a "Codex"
section in `authoring-guide.md`, or a Codex-targeted variant of `agents/openai.yaml` scaffolding),
§5 and §9.2 of this document are the sourced starting points: the exact `agents/openai.yaml` schema
and length limits, and Codex's own `skill-creator`'s authoring philosophy, both confirmed against
the pinned `openai/codex` commit's source rather than against the hosted docs alone.
