# .agents

Local reusable agent assets for this repository.

- `agents/`: prompt fragments and subagent-specific guidance
- `commands/`: reusable command templates and workflow snippets
- `instructions/`: canonical reusable instruction documents loaded via `AGENTS.md`

Add new reusable agent material here instead of bloating `CLAUDE.md` or `.github/copilot-instructions.md`.
Install reusable skills globally under `~/.agent/skills/` instead of keeping project-local copies here.
