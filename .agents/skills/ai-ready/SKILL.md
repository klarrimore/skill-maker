---
name: ai-ready
description: 'Make any repo AI-ready — analyzes your codebase and generates AGENTS.md, copilot-instructions.md, CI workflows, issue templates, and more. Mines your PR review patterns and creates files customized to your stack. USE THIS SKILL when the user asks to "make this repo ai-ready", "set up AI config", or "prepare this repo for AI contributions".'
compatibility: 'Points the user at an external skill (johnpapa/ai-ready) and installs it through the agent''s own skill-install mechanism, which is client-specific. The example install commands target GitHub Copilot CLI; other clients install the skill folder differently.'
---

# AI Ready

This skill points the user to the latest [ai-ready](https://github.com/johnpapa/ai-ready) skill by [John Papa](https://github.com/johnpapa). That skill analyzes a codebase and generates AGENTS.md, copilot-instructions.md, CI workflows, issue templates, and more — customized to the project's stack and mined from its PR review patterns.

*Why a pointer instead of the full skill?*: The full ai-ready skill is ~600 lines of detailed instructions that evolve frequently. This wrapper keeps it discoverable here while the source of truth stays in [johnpapa/ai-ready](https://github.com/johnpapa/ai-ready) — always up to date.

## How it is installed

The ai-ready skill is distributed as a folder in the `johnpapa/ai-ready` repository. The user installs it with their agent's skill-install mechanism, then invokes it. The exact command is client-specific:

- **GitHub Copilot CLI**: `/skills add johnpapa/ai-ready`, then `/skills reload`.
- **Other clients**: clone or copy the skill folder into the skills directory the client reads (commonly `.agents/skills/` for cross-client use, or the client's native skills path).

## Steps

1. Give the user the install command for their client (the Copilot CLI example above is the common case). Re-running it updates to the latest version.
2. Remind the user to review the skill before loading it. They can inspect the SKILL.md first, e.g.:
   ```bash
   head -20 <skills-dir>/ai-ready/SKILL.md   # e.g. ~/.copilot/skills/ai-ready/SKILL.md on Copilot CLI
   ```
3. After the user confirms they've reviewed and installed it, have them reload skills and then say `make this repo ai-ready`.
4. Do **not** run the install command on the user's behalf. The user must run it themselves.
