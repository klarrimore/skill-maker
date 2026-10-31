# Agent Skills Spec Reference

The exact, current constraints of the open Agent Skills standard (agentskills.io). Read this
before writing any frontmatter. The spec publishes no version number; conformance is the
current spec text, which can change.

For spec-mandated, documented, and de-facto status, and for spec-versus-reference-validator
divergences, read `references/spec-provenance.md`.

## What a skill is

A skill is a directory containing at minimum a `SKILL.md` file. `SKILL.md` must contain YAML
frontmatter followed by Markdown content. Everything else is optional.

```
skill-name/
|-- SKILL.md          # Required: metadata + instructions
|-- scripts/          # Optional: executable code
|-- references/       # Optional: documentation loaded on demand
|-- assets/           # Optional: templates, resources used in output
\-- ...               # Any additional files or directories
```

- `scripts/` holds executable code the agent can run; `references/scripts.md` owns how to
  write it.
- `references/` holds documentation the agent reads when needed (for example `REFERENCE.md`,
  `FORMS.md`, or domain files like `finance.md`). Keep each reference file focused: agents load
  them on demand, so smaller files cost less context.
- `assets/` holds static resources used in output: templates, images, data files.

## Frontmatter schema (the full field set)

The spec defines six fields; two are required.

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | Yes | 1 to 64 characters. Lowercase alphanumeric and hyphens (see `name rules` for the Unicode nuance). No leading or trailing hyphen, no consecutive hyphens. Must match the parent directory name. |
| `description` | Yes | 1 to 1024 characters, non-empty. States what the skill does and when to use it. |
| `license` | No | A license name or a reference to a bundled license file. Keep it short. |
| `compatibility` | No | 1 to 500 characters. Environment requirements (intended product, system packages, network access). Include only if the skill has specific requirements; most skills do not. |
| `metadata` | No | A map of string keys to string values for properties outside the spec. Use reasonably unique key names to avoid collisions. |
| `allowed-tools` | No | A space-separated string of pre-approved tools. Experimental; support varies by agent. |

Minimal valid frontmatter:

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

## name rules

- 1 to 64 characters.
- Lowercase alphanumeric and hyphens (`-`). The spec is ambiguous: the prose says "unicode
  lowercase alphanumeric characters", but its parenthetical says `a-z, 0-9`. The reference
  validator normalizes NFKC and accepts any lowercase `isalnum()` character, so `技能`,
  `мой-навык`, and `café` are valid there. For maximum
  cross-client portability, **prefer ASCII-only names** regardless: at least one major client's
  own authoring validator accepts only `^[a-z0-9-]+$` and will reject a Unicode name this
  skill's own validator (and `skills-ref`) accepts. The bundled validator's strict mode emits a
  non-ASCII warning; ASCII names are the generated default. A decomposed-Unicode name (a base
  letter plus a separate combining accent mark) can pass an NFKC-normalized 64-character
  check while exceeding a client that counts raw, unnormalized code points.
- Must not start or end with a hyphen.
- Must not contain consecutive hyphens (`--`).
- Must match the parent directory name. This is enforced by the reference validator
  (`skills-ref`) and by this skill's own validator, but at least one major client does not
  check it as a per-upload rule at all, and another checks it only as a fallback used when
  `name` is absent from frontmatter. Keep matching it regardless: it is the strictly stricter
  rule, and it is what keeps a skill portable to the reference validator and to clients that
  do enforce it.
- Some clients reserve certain words (often their own product or vendor name) and reject a name
  containing one on upload. This is a client upload convention, not part of the standard. The
  standard defines no reserved-word list, so check the client you target. Claude's platform
  documentation states that `name` cannot contain the substrings "anthropic" or "claude",
  and Claude Code separately reserves the skill-folder names `synced` and `anthropic-skills`
  for its own synced-skills mechanism. As a portable default, keep vendor and brand names out
  of `name` (see also `references/authoring-guide.md` for the same rule applied to a skill's
  body text).

Valid: `pdf-processing`, `data-analysis`, `code-review`.
Invalid: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing` (double
hyphen).

## description rules

- 1 to 1024 characters. The 1024 ceiling is a hard limit enforced by the validator, not a
  target.
- Aim for 256 characters or fewer, and treat 512 as the working ceiling. A description past 512
  should earn every extra character: its length is paid on every skill the agent weighs for a
  task.
- State both what the skill does and when to use it.
- Include specific keywords that help an agent recognize relevant tasks.
- Keep angle brackets (`<`, `>`) out of the description. The bundled validator rejects them
  as hardening because some clients may sanitize markup; the spec and `skills-ref` accept
  them (lineage: `references/spec-provenance.md`).
- Keep the description well clear of the 1024 ceiling, with keywords chosen, not stuffed. A
  description within about 5% of it (roughly 973+ characters) is a maintenance trap: the next
  trigger-phrase addition silently breaches it. Re-check the length after every edit, not only
  at first authoring. An edit that grows the description is the most common way a previously
  compliant skill goes over.

Good: "Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs.
Use when working with PDF documents or when the user mentions PDFs, forms, or document
extraction." Poor: "Helps with PDFs."

## compatibility rules

- 1 to 500 characters if present.
- Omit the field rather than leaving it empty: both `skills-ref` and the bundled validator
  enforce only the upper bound, so an empty string passes them.
- Include only when real environment requirements exist.
- A portability gotcha specific to Codex: its own bundled skill-authoring validator (not its
  runtime loader, which ignores unrecognized frontmatter keys entirely) allow-lists only five
  of the standard's six fields and omits `compatibility`. A skill that legitimately uses
  `compatibility` (spec-legal, accepted by this skill's own validator, and loads fine on
  Codex's actual runtime) will still be flagged as an "Unexpected key" failure by Codex's own
  authoring tool. If you hit this while targeting Codex specifically, it is that tool's gap,
  not a sign your skill is wrong.

Examples: "Requires a non-interactive shell and network access"; "Requires git, docker, jq, and
access to the internet"; "Requires Python 3.14+ and uv".

## Body content

The Markdown body after the frontmatter holds the instructions. There are no format
restrictions; write what helps the agent perform the task. The agent loads the entire body once
it activates the skill, so keep it under 500 lines and roughly 5000 tokens, and split longer
material into referenced files. Recommended ingredients: step-by-step instructions, examples of
inputs and outputs, and common edge cases. Treat the 5000-token figure as an upper bound, not a
target: as of 2026-09-30, Codex hard-truncates a selected skill's body at roughly 8000 bytes
(about 2000 tokens) in its default configuration, well under half the spec's own
recommendation, silently cutting the body off mid-instruction rather than erroring.

Point to other files as the **Draft** step of `SKILL.md` "Create a new skill" describes: one
line per file with its purpose and when to read it, one level deep.

## Progressive disclosure (how loading works)

Agents pull in detail only as a task calls for it, in three tiers:

| Tier | What loads | When | Cost |
| --- | --- | --- | --- |
| 1. Metadata | `name` + `description` | At session start, for every skill | ~50 to 100 tokens per skill |
| 2. Instructions | The full `SKILL.md` body | When the skill activates | <5000 tokens recommended |
| 3. Resources | Files under `scripts/`, `references/`, `assets/` | Only when the instructions reference them | Varies |

Design consequence: the `description` alone decides whether tier 2 ever loads, so it carries the
entire triggering burden. Tier 3 costs nothing until the agent reads a file, so keep
`SKILL.md` lean and move detail into focused reference files, structured as
`references/authoring-guide.md` describes.

## Portable vs platform-locked

A conformant, portable skill uses only the core format: `SKILL.md` with the standard frontmatter
and a Markdown body. Such a skill runs unchanged across skills-compatible agents.

A skill becomes platform-locked when it relies on client-specific extensions. A field outside
the six defined fields is a client extension, not a spec violation, but it locks the skill to
the clients that read it. Known examples to avoid for portability:

- `context: fork`: runs the skill in a forked subagent context; recognized by some clients only.
- `user-invocable`, `model`, `disable-model-invocation`: invocation controls some clients
  honor and others do not recognize.
- An `agents/openai.yaml` policy file (for example `allow_implicit_invocation: false`):
  honored by one client, ignored by the rest.
- Heavy reliance on `allowed-tools` enforcement, which is experimental and varies by agent.

Rule of thumb: for cross-agent compatibility, stick to `name`, `description`, and the Markdown
body. Put any environment dependency in `compatibility`, not in a nonstandard field. Note any
deliberate platform-lock in `compatibility` so users are not surprised.

Host extensions (client-specific frontmatter fields, install paths, plugin manifests, hosted
skill IDs, marketplace metadata) are adapter concerns, not portable schema. They belong in
target-specific contracts outside the canonical artifact. Add one only when a target was
requested.

## Portability operations

The `SKILL.md` format is identical across skills-compatible clients. Runtime, distribution, and
file locations differ. Keep a skill portable by assuming the least-capable runtime and avoiding
client-specific machinery.

- Runtime varies. Some agent runtimes have no network access and cannot install packages at run
  time. Write for a runtime with neither: prefer inline dependency declarations for scripts
  (see `references/scripts.md`), and make scripts degrade gracefully when a capability is absent.
- The folder is the portable unit of distribution. Plugin and marketplace packaging formats are
  client-specific and mutually incompatible. To reach more than one client, ship the skill as a
  folder in a skills directory the target clients read, not only as a plugin.
- Always-on instruction files are client-specific. If an always-on instruction is the better
  mechanism, note that its file format is not portable the way `SKILL.md` is; `AGENTS.md` is the
  cross-tool convention, and some clients read their own equivalent instead. A skill is portable
  to every skills-compatible client; an always-on file is not.

## Directory placement (convention, not spec)

The spec defines what goes inside a skill directory, not where it lives. The emerging
cross-client convention:

| Scope | Path | Purpose |
| --- | --- | --- |
| Project | `<project>/.<client>/skills/` | The client's native location |
| Project | `<project>/.agents/skills/` | Cross-client interoperability |
| User | `~/.<client>/skills/` | The client's native location |
| User | `~/.agents/skills/` | Cross-client interoperability |

`~/.agents/skills/` and a repo-local `.agents/skills/` are this skill's own installer
defaults (`scripts/install_skill.py`).

Discovery scans both project and user scope. `.agents/skills/` is the cross-client convention;
some clients also read `.claude/skills/` and other paths. The client guide calls
"project-level skills override user-level skills on a collision" the universal convention
across existing implementations, but at least two major clients do not actually follow it:
one reverses the precedence for the personal/project pair (and adds tiers, such as an
enterprise scope, the standard does not define), and another does not override at all:
same-named skills from different scopes coexist, and a bare by-name mention only resolves
when the name is unambiguous, silently failing to select anything otherwise. Choose a name
unlikely to collide with a system-bundled skill or another author's skill, and expect a
collision to surface as ambiguity, not a predictable winner. The client guide recommends
gating project-level loading on a trust check, because project skills may be untrusted.

## Validation: strict versus import

The bundled validator (`scripts/quick_validate.py`) has two modes. Each check and its
authority tier is in `references/spec-provenance.md` "Bundled validator checks by tier".

- **Strict** (default): conformance validation used by packaging and installation. The
  body-budget, description-margin, and ASCII-name checks are warnings; every other check is
  an error. A skill must pass strict mode to be packaged or installed.
- **Import**: read-only inspection of an existing client-specific skill. Errors are a missing
  or unreadable SKILL.md, frontmatter that is not a YAML mapping, and a `description` that is
  missing, not a string, empty, or over 1024 characters. Every other strict-mode error is a
  warning, so the skill can be examined before conversion. An import pass asserts no
  authority tier: it is triage for whether the skill is worth converting.

A skill that passes import mode but fails strict mode must be explicitly converted before it can
be packaged: copy the skill, resolve warnings, and pass strict validation. Import-mode validity
never authorizes packaging or installation.

## Validation and distribution tooling

- Reference validator: `skills-ref validate ./your-skill` (status: `references/spec-provenance.md`).
- The folder is the unit of distribution; source-control it.
- The `.skill` zip, `gh skill`, and `npx skills add <owner/repo>` are tool-specific (sources:
  `references/spec-provenance.md`).
- The spec is silent on security, and validation is not a safety review: see
  "Format validation is not a safety review" in `references/authoring-guide.md`.
