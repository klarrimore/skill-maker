# Environment Adaptations

The create, test, evaluate, improve, optimize loop is the same everywhere, but the mechanics
depend on what your runtime can do. Adapt by capability, not by product name, since the goal is
a skill that ports across many agents. Find the capabilities your environment lacks and apply
the matching adaptation.

## No subagents (cannot run independent parallel agents)

- Running test cases: run them yourself, one at a time. For each case, read the skill's
  `SKILL.md`, then follow its instructions to do the task. This is less rigorous than
  independent agents (you wrote the skill and you are running it, so you have full context),
  but it is a useful sanity check, and the human review step compensates.
- Skip the baseline runs; use the skill to do the task.
- Skip quantitative benchmarking that relies on baseline comparison, and the blind comparison
  in `evaluation.md`; they are not meaningful without independent agents.
- Focus on qualitative feedback from the user, still organized into iteration directories if
  you have a filesystem.

## No display (headless VM or remote server, no browser)

- Present results directly in the conversation: for each case, show the prompt and the output.
  If an output is a file the user must see (a `.docx`, an `.xlsx`), save it to the filesystem
  and tell them where, so they can download and inspect it. Ask for feedback inline ("How does
  this look? Anything you would change?").
- For the description-optimization trigger eval, the `assets/eval_review.html` template still
  works without a display: fill its placeholders, write it to a file, and hand the user a link
  to open in their own browser, or present the queries inline and edit them in the
  conversation.

## No agent CLI (no non-interactive command-line agent runner)

- Nothing in the bundled flow requires one. The validation and packaging scripts need only
  Python and a filesystem. Both the evaluation loop (`evaluation.md`) and the
  description-optimization loop (`description-optimization.md`) are run by hand, so they work
  the same whether or not your environment can invoke an agent non-interactively.

## Packaging

`scripts/package_skill.py` and `scripts/quick_validate.py` need only Python and a filesystem,
so they run anywhere. Packaging is only relevant for hosts that accept a zipped `.skill`
upload; for folder-based agents, distribute the folder itself.

For a folder install, `scripts/install_skill.py` builds a clean copy (dev-only
`tests/`/`evals/` and caches stripped) and drops it into a skills directory. It defaults to
`~/.agents/skills/`, takes any directory via `--target`, and refuses to replace an existing
install unless passed `--force`. Use `--dry-run` to see the destination without writing.

## Updating an installed skill in a read-only path

Installed skill directories are often read-only.

- Preserve the name: keep the directory name and the `name` frontmatter field unchanged. If the
  installed skill is `research-helper`, the output stays `research-helper`, not
  `research-helper-v2`.
- Copy to a writable location before editing: copy to `/tmp/<name>/`, edit there, and validate
  and package from the copy.
- If packaging manually, stage in `/tmp/` first, then copy to the output directory; direct
  writes may fail on permissions.

## One rule that holds in every environment

When you run test cases, get the outputs in front of the human to review before you critique
and rewrite them yourself. Present the results for review first - inline, or saved to a file
the user can open. Put it on your task list so it does not get skipped.