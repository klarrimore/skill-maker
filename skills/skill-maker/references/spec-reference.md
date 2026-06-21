# Agent Skills Spec Reference

The exact, current constraints of the open Agent Skills standard (agentskills.io). Read
this before writing any frontmatter. The standard is intentionally minimal and
unversioned; conformance is defined by the current spec text, which can change. This file
reflects the standard as published at the December 18, 2025 open-standard release.

## What a skill is

A skill is a directory containing, at minimum, a `SKILL.md` file. `SKILL.md` must contain
YAML frontmatter followed by Markdown content. Everything else is optional.

```
skill-name/
|-- SKILL.md          # Required: metadata + instructions
|-- scripts/          # Optional: executable code
|-- references/       # Optional: documentation loaded on demand
|-- assets/           # Optional: templates, resources used in output
\-- ...               # Any additional files or directories
```

- `scripts/` holds executable code the agent can run. Scripts should be self-contained or
  clearly document dependencies, include helpful error messages, and handle edge cases.
  Supported languages depend on the agent; Python, Bash, and JavaScript are common.
- `references/` holds documentation the agent reads when needed (for example
  `REFERENCE.md`, `FORMS.md`, or domain files like `finance.md`). Keep each reference file
  focused: agents load them on demand, so smaller files cost less context.
- `assets/` holds static resources used in output: templates, images, data files.

## Frontmatter schema (the full field set)

There are exactly six recognized fields. Two are required.

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | Yes | 1 to 64 characters. Lowercase letters, digits, and hyphens only. No leading or trailing hyphen, no consecutive hyphens. Must match the parent directory name. |
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
- Lowercase alphanumeric (`a-z`, `0-9`) and hyphens (`-`) only.
- Must not start or end with a hyphen.
- Must not contain consecutive hyphens (`--`).
- Must match the parent directory name.
- Some clients reserve certain words (often their own product or vendor name) in skill names
  and reject a name that contains one on upload. The standard does not define a reserved-word
  list, so check the constraints of the client you are targeting. As a portable default, avoid
  vendor or brand names in skill names entirely.

Valid: `pdf-processing`, `data-analysis`, `code-review`.
Invalid: `PDF-Processing` (uppercase), `-pdf` (leading hyphen), `pdf--processing` (double
hyphen).

## description rules

- 1 to 1024 characters.
- State both what the skill does and when to use it.
- Include specific keywords that help an agent recognize relevant tasks.
- The bundled validator also rejects angle brackets (`<`, `>`) for safety against markup
  injection into the system prompt; avoid them.
- Stay clear of the 1024 ceiling. A description within about 5% of the limit (roughly 973+
  characters) is a maintenance trap: the next trigger-phrase addition silently breaches it.
  Re-check the length after every edit, not just at first authoring. An edit that grows the
  description is the most common way a previously compliant skill goes over.

Good: "Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs.
Use when working with PDF documents or when the user mentions PDFs, forms, or document
extraction." Poor: "Helps with PDFs."

## compatibility rules

- 1 to 500 characters if present.
- Include only when there are real environment requirements.

Examples: "Requires a non-interactive shell and network access"; "Requires git, docker, jq, and
access to the internet"; "Requires Python 3.14+ and uv".

## Body content

The Markdown body after the frontmatter holds the instructions. There are no format
restrictions; write whatever helps the agent perform the task. The agent loads the entire
body once it activates the skill, so keep it under 500 lines and roughly 5000 tokens, and
split longer material into referenced files. Recommended ingredients: step-by-step
instructions, examples of inputs and outputs, and common edge cases.

When referencing other files, use relative paths from the skill root, and keep references
one level deep. Avoid deeply nested reference chains. Tell the agent when to read each
file (for example, "Read references/api-errors.md if the API returns a non-200 status"),
not just that the file exists.

## Progressive disclosure (how loading works)

Agents pull in detail only as a task calls for it, in three tiers:

| Tier | What loads | When | Cost |
| --- | --- | --- | --- |
| 1. Metadata | `name` + `description` | At session start, for every skill | ~50 to 100 tokens per skill |
| 2. Instructions | The full `SKILL.md` body | When the skill activates | <5000 tokens recommended |
| 3. Resources | Files under `scripts/`, `references/`, `assets/` | Only when the instructions reference them | Varies |

Design consequence: the `description` is the only thing that decides whether tier 2 ever
loads, so it carries the entire triggering burden. Bundled resources are effectively
unlimited because they load lazily; do not fear large reference files, fear a bloated
`SKILL.md`.

## Portable vs platform-locked

A conformant, portable skill uses only the core format: `SKILL.md` with the standard
frontmatter and a Markdown body. Such a skill runs unchanged across skills-compatible
agents.

A skill becomes platform-locked when it relies on client-specific extensions. Known
examples to avoid if you want portability:

- `context: fork`: runs the skill in a forked subagent context; recognized by some clients only.
- `user-invocable`, `model`, `disable-model-invocation`: invocation controls some clients
  honor and others do not recognize.
- An `agents/openai.yaml` policy file (for example `allow_implicit_invocation: false`):
  honored by one client, ignored by the rest.
- Heavy reliance on `allowed-tools` enforcement, which is experimental and varies by
  agent.

Rule of thumb: if you need cross-agent compatibility, stick to `name`, `description`, and
the Markdown body, and put any environment dependency in `compatibility` rather than in a
nonstandard field. Note any deliberate platform-lock in `compatibility` so users are not
surprised.

## Portability operations

The `SKILL.md` format is identical across skills-compatible clients. What differs is runtime,
distribution, and where files live. Keep a skill portable by assuming the least-capable runtime
and avoiding client-specific machinery.

- Runtime varies. Some agent runtimes have no network access and cannot install packages at run
  time. Do not assume either is available. Prefer inline dependency declarations for scripts
  (see authoring-guide.md) and have scripts degrade gracefully when a capability is absent.
- The folder is the portable unit of distribution. Plugin and marketplace packaging formats are
  client-specific and mutually incompatible. To reach more than one client, ship the skill as a
  folder in a skills directory the target clients read, not only as a plugin.
- Always-on instruction files are client-specific. If the better mechanism is an always-on
  instruction rather than a skill, note that its file format is not portable the way `SKILL.md`
  is; `AGENTS.md` is the cross-tool convention, and some clients read their own equivalent
  instead. A skill is portable to every skills-compatible client; an always-on file is not.
- Any frontmatter field outside the six in the schema above is client-specific and breaks
  portability, as are client-specific sidecar files. Avoid them unless you intend single-client
  behavior, and if you use one, state it in `compatibility`.

## Directory placement (convention, not spec)

The spec defines what goes inside a skill directory, not where the directory lives. The
emerging cross-client convention:

| Scope | Path | Purpose |
| --- | --- | --- |
| Project | `<project>/.<client>/skills/` | The client's native location |
| Project | `<project>/.agents/skills/` | Cross-client interoperability |
| User | `~/.<client>/skills/` | The client's native location |
| User | `~/.agent/skills/` | User-global Agent CLI location |
| User | `~/.agents/skills/` | Cross-client interoperability |

Many clients also read one or more shared compatibility paths in addition to their own native
location. On a name collision,
project-level skills override user-level skills.

## Validation and distribution

- Canonical validator: `skills-ref validate ./your-skill` (the standard's Python reference
  library, also on PyPI; exposes `validate`, `read-properties`, and `to-prompt`).
- The folder is the unit of distribution; source-control it. Ecosystem tools operate on
  folders or repos (for example `gh skill`, `npx skills add <owner/repo>`).
- A zipped `.skill` upload is a host convenience offered by some hosts (a hosted skills app
  or a skills API), not part of the open standard.

## Security posture

The spec is silent on security, but skills execute bundled scripts with the agent's
permissions and their instructions are processed at operator level. Treat any third-party
skill like an unaudited dependency: inspect before installing, prefer trusted sources, and
sandbox script execution. Never ship a skill whose real behavior differs from what its
description implies.
