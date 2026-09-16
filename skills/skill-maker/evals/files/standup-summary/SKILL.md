---
name: standup-summary
description: Turns a day's standup notes into a short written update. Use when the user pastes standup notes and wants a summary for the team.
metadata:
  author: example-org
  version: "1.0"
---

# Standup Summary

Turn pasted standup notes into a short update.

## Steps

1. Read the notes the user pasted.
2. Write a brief summary of what was done.

<!--
Deliberately thin: this fixture is the input for eval id 4 ("improve an installed skill").
It is valid, so `quick_validate` accepts it, but it omits the on-call rotation summary the
user asks for. Under `evals/`, so it never counts toward the packaged skill.
-->
