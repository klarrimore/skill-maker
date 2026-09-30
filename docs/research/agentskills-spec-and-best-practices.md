# Agent Skills Open Standard — Specification and Best Practices

## Scope & method

**This refresh was performed 2026-09-30**, redoing the 2026-09-17 investigation from scratch
against primary sources. **Bottom line: nothing material changed.** The
[`agentskills/agentskills`](https://github.com/agentskills/agentskills) repository's `main`
branch is at the exact same commit today as it was on 2026-09-17 —
[`69ef37e9424c0a7ea9dd2293b559e43ec8176379`](https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379)
— confirmed via a fresh `git clone` and `git fetch origin` on 2026-09-30, which reported no new
commits past that hash. There have been zero commits to `main` for 52 days (last activity
2026-08-09).

The remote also carries eight `jh/*` feature branches. Checked with
`git log --oneline origin/main..<branch>` on 2026-09-30: six of them (`jh/evolve-landing-page`,
`jh/add-clients-page`, `jh/add-quickstart-guide`, `jh/add-best-practices-guide`,
`jh/add-optimizing-descriptions-guide`, `jh/add-evaluating-skills-guide`) have zero commits ahead
of `main` — they are stale refs left over from already-merged (likely squash-merged) work, not
pending changes. Two carry unmerged commits, and both are stale in a different way — abandoned,
not active:
- `jh/add-client-how-to-guide` (3 commits, last dated 2026-03-04) is an early draft of what
  became the current `adding-skills-support.mdx`; it diverged from `main` on 2026-03-02 and was
  superseded by a different, already-merged PR under the final "Adding skills support" title.
- `jh/well-known-uri` (2 commits, last dated 2026-03-23) is a genuinely separate, still-unmerged
  proposal: a spec-adjacent `docs/well-known-uri.mdx` for discovering skills at a predictable
  `https://example.com/.well-known/agent-skills/index.json` endpoint (RFC 8615 style), "distilled
  from Cloudflare's Agent Skills Discovery RFC," with SHA-256 digest verification and archive
  (`.tar.gz`/`.zip`) distribution. It has not been touched since 2026-03-23 and is not linked
  from `docs/docs.json` on `main`. It is **not part of the current spec or docs site** — flagged
  here only because it is the one piece of primary-source evidence that spec-adjacent work has
  been drafted (and then stalled) since the last research pass, not because it has any normative
  weight today.

The `skills-ref` PyPI package is likewise unchanged: still version `0.1.1`, uploaded 2026-01-10,
same ownership and repository-URL discrepancies noted below. The live `agentskills.io` site was
spot-checked against the repo — `specification.md` and `home.md` were fetched and their content
matches `docs/specification.mdx` and `README.md` line-for-line on the sections read — consistent
with the site serving the same commit, though this was an eyeball comparison of two pages, not an
exhaustive diff of the whole site.

Two corrections to the prior version, found while re-verifying line-by-line:

1. **Commit-history date range was slightly off.** The prior version said the repo's history
   runs "2025-12-18 through 2026-08-09." The actual first commit (`init`) is dated **2025-12-16**;
   `2025-12-18` is the date of the second commit ("Add documentation"). Corrected below.
2. **`disable-model-invocation` is not purely an outside/de-facto term.** The prior version's
   Gaps list stated flatly that this flag "is not on agentskills.io." That is not quite right: the
   first-party client-implementation guide names it verbatim, as a worked example of a flag "some
   clients" might use to let a skill opt out of model-driven activation
   ([adding-skills-support.mdx, line 226](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/client-implementation/adding-skills-support.mdx#L226)).
   It is still true that the spec does not define this as a recognized frontmatter field and that
   no first-party source specifies its syntax or which clients implement it — so "client
   extension, not a spec field" still holds — but the term itself does appear on agentskills.io,
   unlike `user-invocable`, `context: fork`, `agents/openai.yaml`, angle-bracket rejection, `.skill`
   zips, `gh skill`, `npx skills add`, or `~/.agent/skills/` (singular), none of which appear
   anywhere in the docs or repo (`grep -rn` over `docs/`, `AGENTS.md`, `CONTRIBUTING.md`,
   `README.md` on the 2026-09-30 clone found none of these).

Everything else below was independently re-read from the primary sources on 2026-09-30 (every
doc page under `docs/`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `docs/docs.json`,
`validator.py`, `parser.py`, `cli.py`, `pyproject.toml`, and the relevant `test_validator.py`
cases were opened fresh, not assumed from the prior write-up). Because the repository is at the
identical commit hash as the 2026-09-17 pass, "re-read and confirmed identical" is the accurate
description for repo-sourced content — the files are the same bytes, so agreement with the prior
version is expected, not independent corroboration of a possibly-changed fact. Two prior claims
about *older* history (predating both research passes) were re-verified against their actual
diffs rather than taken on faith: see the `6868401`/`6f92fcd`/`3f3bbec` commit diffs and the
frontmatter-field-history check in §11.

Sources used, and how:

- The documentation site at agentskills.io (rendered pages and their `.md` twins listed in
  [`/llms.txt`](https://agentskills.io/llms.txt), fetched 2026-09-30).
- The repository [`agentskills/agentskills`](https://github.com/agentskills/agentskills),
  freshly cloned 2026-09-30 (`git clone` + `git fetch origin`) and confirmed at HEAD commit
  [`69ef37e9424c0a7ea9dd2293b559e43ec8176379`](https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379)
  ("docs: add OpenClaw to client showcase (#492)", committed 2026-08-09 13:36:04 -0700; 145
  commits total, first commit 2025-12-16). The specification source file is
  [`docs/specification.mdx`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx).
- The reference validator source under
  [`skills-ref/src/skills_ref/`](https://github.com/agentskills/agentskills/tree/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref)
  (`validator.py`, `parser.py`, `cli.py`) and its tests
  ([`skills-ref/tests/test_validator.py`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/tests/test_validator.py)),
  read in full.
- `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, and `docs/docs.json` at repo root, read in full.
- The PyPI metadata for the `skills-ref` package, re-fetched 2026-09-30:
  [`https://pypi.org/pypi/skills-ref/json`](https://pypi.org/pypi/skills-ref/json).

**Accessed:** 2026-09-30 (prior version accessed 2026-09-17; both read the identical repo
commit).

A note on authority, because it shapes how to read everything else. The repository's
[`AGENTS.md`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/AGENTS.md) states plainly:
"`docs/specification.mdx` is authoritative for format requirements. Explanatory documentation,
examples, tests, and implementations do not add requirements to the format." It adds that
`skills-ref/` is "a demonstration artifact, not a production SDK or a source of additional
format requirements." This text is byte-identical to what it said on 2026-09-17 (same commit).
So there are three distinct tiers throughout this document:

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
alphanumeric characters" but then parenthesizes the ASCII range `a-z, 0-9`. This exact wording
is unchanged from the 2026-09-17 version and remains unresolved as of 2026-09-30. The reference
validator resolves this in favor of *Unicode*: it normalizes with NFKC and accepts any
`str.isalnum()` character, then rejects uppercase via `name != name.lower()`
([`validator.py:37-58`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/validator.py#L37-L58)).
Its tests explicitly assert that Chinese (`技能`), Russian (`мой-навык`, `навык`), and
decomposed-accent (`café`) names are valid
([`test_validator.py`, e.g. `test_i18n_chinese_name`, `test_i18n_russian_name_with_hyphens`,
`test_nfkc_normalization`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/tests/test_validator.py)).
The parenthetical `a-z, 0-9` was in fact *corrected* in an earlier commit ("fix name field
character range to include digits") to match the table's "letters, numbers," wording, but the
word "unicode" and the ASCII parenthetical still coexist
([commit `6868401`, 2026-05-16](https://github.com/agentskills/agentskills/commit/6868401b64f791e9ff565f29beb6338826b73a2b)).
Treat the character set as an unresolved ambiguity in the spec text.

The git history also shows the spec originally read `(a-z and -)` and was changed to
`(a-z, 0-9)` — see the same commit. This is the closest thing to a documented spec
clarification, and no further clarification has landed since.

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
([`AGENTS.md`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/AGENTS.md)).

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
  > — [`parser.py:12-27`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/parser.py#L12-L27)

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

There is no first-party list of "platform-locked" fields. One concrete client-extension example
*is* named in the client-implementation guide, though only as an illustrative aside, not as a
defined convention: a skill can opt out of model-driven activation "e.g., via a
`disable-model-invocation` flag"
([adding-skills-support, "Filtering"](https://agentskills.io/client-implementation/adding-skills-support)).
No agentskills.io page defines this flag's syntax, scope, or which clients implement it — it is
named only as an example of the *kind* of thing a client might do, not standardized. Other
concrete client extensions (e.g. `context: fork`, `disable-model-invocation`'s exact contract,
`agents/openai.yaml`) are **not** described on agentskills.io beyond that one example; those
come from individual client docs (not investigated here) and should be treated as tier-(c)
de-facto knowledge. The repo's own portability list should be read with that caveat.

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
  [`pyproject.toml`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/pyproject.toml),
  requires Python `>=3.11`, deps `click` and `strictyaml`. Console script is
  `skills-ref = "skills_ref.cli:main"`. The `pyproject.toml` author is listed as "Keith Lazuka
  <klazuka@anthropic.com>."
- The README carries an explicit disclaimer:
  > "This library is intended for demonstration purposes only. It is not meant to be used in
  > production."
  > — [`skills-ref/README.md`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/README.md)
- `CONTRIBUTING.md` says: "We're still determining the direction for the reference library and
  are not accepting code contributions to it at this time."
  ([CONTRIBUTING.md](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/CONTRIBUTING.md))

### CLI commands

From [`cli.py`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/cli.py):

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
[`validator.py:118-147`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/validator.py#L118-L147)
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
([`validator.py:10-12`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/validator.py#L10-L12)).

The parser additionally requires the file to *start with* `---` and to be closed with `---`,
and requires the frontmatter to parse as a YAML mapping
([`parser.py:42-59`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/parser.py#L42-L59)).
It coerces `metadata` values to strings: `{str(k): str(v) …}`
([`parser.py:61-62`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/parser.py#L61-L62)).

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

The package is published on PyPI as `skills-ref` (version `0.1.1`, unchanged since a
2026-01-10 upload — re-confirmed 2026-09-30, no newer release exists), so "also on PyPI" is
true. Several discrepancies are worth recording, re-verified this pass:

- The PyPI long description advertises the console command as `agentskills validate …`, not
  `skills-ref validate …` as in the repo's own `pyproject.toml` and README.
  ([PyPI JSON](https://pypi.org/pypi/skills-ref/json))
- The PyPI project's `project_urls` still point at `github.com/anthropics/agentskills` (the
  pre-move org), and the JSON `ownership.roles[].user` is `BjoernBethge`, not an Anthropic
  account.
- A nuance not previously checked: the PyPI package's own `author_email` field reads "Keith
  Lazuka <klazuka@anthropic.com>" — matching the repo's `pyproject.toml` author exactly. So the
  package metadata is a faithful mirror of what an Anthropic engineer put in the source
  `pyproject.toml`, even though the account that owns/uploads the PyPI listing itself
  (`BjoernBethge`) is not an Anthropic account. This somewhat softens (but does not resolve) the
  provenance concern: the *content* traces back to the official repo; the *distribution
  channel* (who can publish new versions under this name on PyPI) does not appear to be
  Anthropic-controlled.
- The official install instructions in the repo README remain local (`pip install -e .` or
  `uv sync`). Treat the PyPI artifact as convenience distribution rather than the canonical
  installation path.

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
  skills entirely; omit the catalog entirely when no skills exist. The guide's worked example of
  a filtering reason is a skill that "has opted out of model-driven activation (e.g., via a
  `disable-model-invocation` flag)" — named as an illustrative example of client behavior, not
  as a spec-defined field.
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
  repository has no git tags at all (`git tag -l` returned nothing on both 2026-09-17 and
  2026-09-30 clones). The spec is therefore effectively unversioned; conformance is defined by
  the current spec text. This is an inference from the absence of any versioning artifact, not a
  statement the docs make.
- The format was "originally developed by [Anthropic], released as an open standard, and has been
  adopted by a growing number of agent products"
  ([home, "Open development"](https://agentskills.io/home); same text in the repo README).
- `CONTRIBUTING.md` frames the project as early-stage and deliberately conservative: "We maintain
  a high bar for additions to the spec — it is much easier to add things to a specification than
  to remove them." It is "not accepting … major architectural changes" and not accepting skill
  submissions.
- `AGENTS.md` sets the design bar: "new requirements impose costs on every implementation and
  should address demonstrated interoperability needs, not hypothetical completeness."
- The repository's history (145 commits, **2025-12-16** through 2026-08-09, unchanged as of
  2026-09-30 — corrected from the prior version's "2025-12-18," which was the date of the
  *second* commit, "Add documentation," not the first, "init") shows only clarifications to
  wording, examples, and the field table — no added or removed frontmatter fields. This was
  checked directly, not inferred: `git log --follow -p -- docs/specification.mdx | grep -E
  '^[-+]\| \`'` over the full history lists every field-table row ever added or removed, and the
  same six field names (`name`, `description`, `license`, `compatibility`, `metadata`,
  `allowed-tools`) are the only ones that ever appear — each row was reworded in place at most
  once, never added or dropped. The three specific wording changes were confirmed by reading
  their actual diffs to `docs/specification.mdx` (not just their commit subject lines):
  - [`6868401`](https://github.com/agentskills/agentskills/commit/6868401b64f791e9ff565f29beb6338826b73a2b)
    (2026-05-16, "docs: fix name field character range to include digits") changed the `name`
    field bullet from `` `a-z` `` to `` `a-z`, `0-9` `` — confirmed via `git show`.
  - [`6f92fcd`](https://github.com/agentskills/agentskills/commit/6f92fcdb78af119d41544ce667e16eb20e94de8e)
    (2026-03-30, "Use precise type name for `allowed-tools` field") changed both the table row
    and the field-detail bullet from "Space-delimited list" to "Space-separated string" —
    confirmed via `git show`.
  - [`3f3bbec`](https://github.com/agentskills/agentskills/commit/3f3bbec8133ce7fcde5aa9fc42556cd15cab8646)
    (2026-08-03, "Clarify `metadata` in the frontmatter overview") added "(a map from string keys
    to string values)" to the `metadata` table row, matching wording already present in the
    detailed field section — confirmed via `git show`.

  No commit since 2026-08-09 has touched the spec, since there have been no commits to `main` at
  all since then.
- The site navigation groups content into "For skill creators" and "For client implementors,"
  with redirects from older routes (`/integrate-skills` → adding-skills-support,
  `/what-are-skills` → `/`) — evidence the docs were reorganized at some point in the past, though
  no further reorganization has occurred since 2026-08-09
  ([`docs/docs.json`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/docs.json)).

---

## Gaps / unverified

Things the first-party sources are silent on, or where this repo's claims could **not** be
confirmed. These are explicitly *not* claims; they are open items. Re-checked 2026-09-30 by
grepping the fresh clone (`docs/`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`) for each term;
none of items 1–10 below turned up any first-party hits beyond what's noted.

1. **"The bundled validator also rejects angle brackets (`<`, `>`)."**
   This repo's `spec-reference.md` asserts (as a repo-specific hardening choice, not a spec
   claim) that the bundled validator rejects them; the primary `skills-ref` validator does not
   check for angle brackets. `grep` over `skills-ref/src/` finds no such rule;
   `_validate_description` only checks non-empty and ≤1024
   ([`validator.py:70-84`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/skills-ref/src/skills_ref/validator.py#L70-L84)).
   The spec does not mention angle brackets either. This remains **unverified against the
   agentskills.io primary sources** as a standard behavior — it is fine as a documented
   skill-maker-specific hardening measure, but should not be presented as spec or reference-
   validator behavior.

2. **Reserved words in skill names.** Some clients are said to reserve certain words and reject a
   name that contains one on upload; the standard defines no reserved-word list. The "no list"
   half matches the sources. The existence and behavior of client-side reserved words is not
   described anywhere on agentskills.io. Unverified.

3. **`~/.agent/skills/` (singular "agent").** No first-party source mentions this path. The
   client guide lists `~/.agents/skills/` (plural) and `.claude/skills/` only. Unverified against
   primary sources.

4. **`.skill` zip uploads.** No agentskills.io page mentions `.skill`, packaging, or zip
   distribution. The spec defines folders, not archives, so "not part of the standard" is
   defensible, but the existence/convention of `.skill` zips is unverified from first-party
   sources.

5. **Ecosystem commands (`gh skill`, `npx skills add <owner/repo>`).** Neither appears in the
   agentskills.io docs or the official repo. Unverified.

6. **`metadata.version`.** The spec's examples use `metadata: { version: "1.0" }`, but the spec
   does **not** define a `version` field for the skill itself, nor any versioning scheme.
   `metadata` is "arbitrary key-value mapping." Do not treat `version` as a spec field.

7. **Skill-to-skill composition.** The first-party docs never discuss composition at all, so any
   claim that "the standard does not support skill-to-skill composition" is an inference from
   silence rather than a documented prohibition.

8. **Security.** The spec is silent on security. The only first-party security-adjacent guidance
   is the client guide's project-level trust check and the warning in `AGENTS.md` to distinguish
   format from implementation choices. Framing third-party skills as "an unaudited dependency" is
   sound practice but is not a spec statement.

9. **Token-count precision.** Tier 1 is "~100 tokens" in the spec and "~50-100" in the client
   guide; tier 2 is "< 5000 tokens recommended." Exact tokenization is model-dependent and the
   spec does not specify a tokenizer.

10. **Client extension fields.** Only `disable-model-invocation` is named on agentskills.io (as a
    filtering example, not a defined field — see the Scope & method note above). `context: fork`,
    `user-invocable`, `model`, and `agents/openai.yaml` do not appear anywhere in the docs or
    repo. They may be accurate per individual clients, but are not verifiable from agentskills.io
    without reading each client's own docs (out of scope).

11. **`skills-ref` production use.** The README says demonstration-only; `CONTRIBUTING.md` says
    the library's direction is undecided and code contributions are closed right now, unchanged
    as of 2026-09-30. Any plan that depends on `skills-ref` as a stable dependency should account
    for this.

12. **PyPI ownership / entry point.** The PyPI `skills-ref` package's advertised CLI is
    `agentskills`, its `project_urls` point to the old `anthropics/agentskills` org, and its PyPI
    ownership role is an individual account (`BjoernBethge`) rather than Anthropic — all
    unchanged as of 2026-09-30. The package's `author_email` field does match the repo's
    `pyproject.toml` ("Keith Lazuka <klazuka@anthropic.com>"), so the *metadata content* traces
    to the official repo even though the *publishing account* does not appear to be
    Anthropic-controlled. The canonical install path in the repo README remains a local editable
    install. Verify provenance before relying on the PyPI artifact for anything beyond casual use.

---

## Implications for this repo

Where the primary sources refine or contradict what `skill-maker` currently claims. As of
2026-09-30, `skills/skill-maker/references/spec-reference.md` and
`skills/skill-maker/references/description-optimization.md` already reflect essentially all of
the corrections raised by the 2026-09-17 version of this research (the angle-bracket caveat is
correctly scoped as a skill-maker hardening choice, the "exactly six fields" framing is correctly
split into "spec-conformant but not portable," the `name` Unicode ambiguity is stated accurately,
`~/.agent/skills/` no longer appears, the `compatibility` minimum-not-enforced caveat is present,
the validator is called a "reference validator... not a production SDK" rather than "canonical,"
and `spec-reference.md`'s own mention of `disable-model-invocation` (in its "Portable vs
platform-locked" section) is phrased carefully as "invocation controls some clients honor and
others do not recognize" — it never claims the term is absent from agentskills.io, so it needed
no change). Checked
`skills/skill-maker/references/spec-provenance.md` as well this pass (not checked in the prior
research), since `spec-reference.md` points to it for the spec-vs-de-facto authority framing.
That file **does** repeat the now-corrected claim and is the one that needs a fix:

1. **Fix needed: `spec-provenance.md` line 107.** Its "Client extension fields" bullet reads:
   "`context: fork`, `user-invocable`, `model`, `disable-model-invocation`, and `agents/openai.yaml`
   do not appear on agentskills.io." That is no longer accurate for one of the five —
   `disable-model-invocation` is named, verbatim, in the first-party
   [adding-skills-support guide](https://agentskills.io/client-implementation/adding-skills-support)
   as a worked example of a flag a client *might* use for activation opt-out (filtering reasons:
   "The skill has opted out of model-driven activation (e.g., via a `disable-model-invocation`
   flag)"). It is still true that no agentskills.io page defines this flag's syntax or says which
   clients implement it, and the file's closing advice ("They may be real per client, but verify
   each against that client's docs") still holds for all five terms — but the blanket "do not
   appear on agentskills.io" is now wrong for this one. Suggested fix: split the bullet, e.g.
   "`context: fork`, `user-invocable`, `model`, and `agents/openai.yaml` do not appear on
   agentskills.io. `disable-model-invocation` is named once, as a worked example in the
   client-implementation guide, but its syntax and semantics are not specified there — verify it
   against the client you target." This file was not part of the 2026-09-17 research's file list,
   so this is a newly surfaced finding, not a change since that version.

2. **Nothing else needs correction.** The repo's field table and exact limits (64 / 1024 / 500
   with the correct `compatibility` lower-bound caveat), the name rules including directory match
   and `--` prohibition, the three-tier progressive-disclosure model, the 500-line / 5000-token
   body budget, the "one level deep" reference rule, the "tell the agent when to load each file"
   rule, the `description`-carries-triggering framing, the pushy-imperative description guidance,
   the 20-query / 3-runs / 0.5-threshold / 60-40 train-validation loop, the eval workspace layout,
   and the agentic script-design rules all remain accurate, faithful paraphrases of the primary
   sources as re-verified on 2026-09-30.

3. **Nothing in the primary sources contradicts** the repo's core authoring guidance (ground in
   real expertise, refine with traces, add only what the agent lacks, calibrate specificity to
   fragility, prefer defaults over menus, gotchas, templates, checklists, validation loops,
   plan-validate-execute, bundle repeated scripts). Those sections remain well-aligned with
   [best-practices](https://agentskills.io/skill-creation/best-practices) and
   [evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills), both re-read in
   full on 2026-09-30. Their content is guaranteed identical to what the 2026-09-17 pass saw,
   since the repository is at the same commit hash both times (see Scope & method); this was
   confirmed by reading the files fresh, not by diffing against an archived copy of the prior
   text.
