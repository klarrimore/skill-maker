# Writing and Bundling Scripts

A skill can bundle executable code under `scripts/`. Scripts suit deterministic, repetitive
work. The agent runs them without loading their source into context, so they cost no tokens.
This file owns the script guidance; other references point here.

## Choose a one-off command or a bundled script

Prefer an existing package runner when one command finishes the job. Reference the runner
directly. Do not add a `scripts/` directory for a single command.

- Python: `uvx` or `pipx`.
- Node: `npx`, `bunx`, or `deno run`.
- Go: `go run`.

Pin the tool version in the command. A pinned command reproduces the same result later.

State the prerequisite in `SKILL.md` or in the `compatibility` field. Name the tool and the
minimum version.

Move the command into a script when it grows. A script is easier to test, reuse, and read.
Bundle a script once traces show the agent reinventing the same logic on every run.

## Reference scripts from the skill root

The agent runs commands from the skill directory root. Write every script path relative to
that root.

List each script in `SKILL.md` with a one-line purpose. The agent runs only the scripts it
knows exist. The offline audit (`skill_eval audit`) warns about packaged scripts not named in
the body; the audit requires the full skill-relative path (e.g. `scripts/run.py`), not just
a basename that could match a file in a different directory. It also warns when `SKILL.md`
or a reference names a `scripts/`, `references/`, or `assets/` path that does not exist
(lines marked "e.g." or "for example" count as illustrations), and enforces the large-reference
table-of-contents rule in `references/authoring-guide.md`.

```bash
python -m scripts.quick_validate ./your-skill
```

Run Python scripts as modules. Package-relative imports then resolve correctly.

## Bundled script inspection checklist

Agents run scripts in non-interactive shells. Every executable file under `scripts/` (except
`__init__.py`) must pass this checklist before the skill is packaged:

- [ ] Listed in `SKILL.md` with a one-line purpose and invocation example.
- [ ] Non-interactive: no blocking prompts (a blocking prompt hangs forever); reads input from
      flags, env vars, or stdin.
- [ ] `--help` documents usage, arguments, and exit codes.
- [ ] `--dry-run` available for every destructive operation.
- [ ] Input constraints validated up front, failing early with a clear message.
- [ ] Errors state what went wrong, what was expected, and what to try.
- [ ] Documented exit codes: `0` for success, distinct nonzero codes for distinct failures, so
      the agent can branch on the code without parsing text.
- [ ] Structured output (JSON, CSV, TSV) on stdout; diagnostics on stderr, so stdout stays
      machine-parseable while logs stay visible.
- [ ] Idempotent: rerunning does not corrupt state or duplicate side effects.
- [ ] Safe defaults: read-only unless the user opts in to writes.
- [ ] Dependencies declared inline (PEP 723, npm:, bundler/inline) or documented in
      `compatibility`.
- [ ] Output size kept predictable: harnesses often truncate around 10K-30K chars, so summarize
      or paginate large results.

## Make scripts self-contained

A script should run with no separate install step. Declare its dependencies inline and pin
their versions. This satisfies the spec rule: self-contained, or dependencies clearly
documented.

Python uses a PEP 723 block. Run the file with `uv run`.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests==2.32.3",
# ]
# ///
```

Deno resolves imports with `npm:` and `jsr:` specifiers.

```typescript
import { z } from "npm:zod@3.23.8";
```

Bun installs pinned imports automatically.

```typescript
import { z } from "zod@3.23.8";
```

Ruby uses `bundler/inline`.

```ruby
require "bundler/inline"
gemfile do
  source "https://rubygems.org"
  gem "json", "2.7.2"
end
```

Treat an external manifest as the fallback, not the default.

## Supported languages

Supported languages depend on the agent implementation. Python, Bash, and JavaScript are
common. Prefer a language the target agents already support. Check `compatibility` when a
script needs a language the skill cannot assume.
