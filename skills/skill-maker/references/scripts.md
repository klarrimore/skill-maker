# Writing and Bundling Scripts

A skill can bundle executable code under `scripts/`. Scripts suit deterministic, repetitive
work. The agent runs them without loading their source into context, so they cost no tokens.
This file expands the script guidance in `authoring-guide.md`.

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
knows exist.

```bash
python -m scripts.quick_validate ./your-skill
```

Run Python scripts as modules. Package-relative imports then resolve correctly.

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

## Design scripts for agentic use

Agents run scripts in non-interactive shells. Design for that environment.

- Never prompt interactively. A blocking prompt hangs forever.
- Accept input through flags, environment variables, or stdin.
- Document usage with `--help`.
- Write errors that state what went wrong, what was expected, and what to try.
- Emit structured output: JSON, CSV, or TSV. Send data to stdout and diagnostics to stderr.
  The split keeps stdout machine-parseable while logs stay visible.
- Be idempotent. A rerun must not corrupt state or duplicate side effects.
- Validate input constraints and fail early with a clear message.
- Offer `--dry-run` for every destructive operation.
- Use documented exit codes. Reserve `0` for success and nonzero codes for distinct failures.
  The agent can branch on the code without parsing text.
- Choose safe defaults. Stay read-only unless the user opts in to writes.
- Keep output size predictable. Harnesses often truncate around 10-30K characters.
  Summarize or paginate large results instead of printing them whole.

## Supported languages

Supported languages depend on the agent implementation. Python, Bash, and JavaScript are
common. Prefer a language the target agents already support. Check `compatibility` when a
script needs a language the skill cannot assume.
