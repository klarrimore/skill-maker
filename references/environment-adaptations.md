# Environment Adaptations

The create, test, evaluate, improve, optimize loop is the same everywhere, but the
mechanics depend on what your runtime can do. Adapt by capability rather than by product
name, since the goal is a skill that ports across many agents. Find the capabilities your
environment is missing and apply the matching adaptation.

## No subagents (cannot run independent parallel agents)

- Running test cases: run them yourself, one at a time. For each case, read the skill's
  `SKILL.md`, then follow its instructions to do the task. This is less rigorous than
  independent agents (you wrote the skill and you are running it, so you have full
  context), but it is a useful sanity check, and the human review step compensates.
- Skip the baseline runs; just use the skill to do the task.
- Skip quantitative benchmarking that relies on baseline comparison, and the blind
  comparison in `evaluation.md`; they are not meaningful without independent agents.
- Focus on qualitative feedback from the user, still organized into iteration directories
  if you have a filesystem.

## No display (headless VM or remote server, no browser)

- Skip the browser review view. Present results directly in the conversation: for each
  case, show the prompt and the output. If an output is a file the user must see (a
  `.docx`, an `.xlsx`), save it to the filesystem and tell them where so they can download
  and inspect it. Ask for feedback inline ("How does this look? Anything you would
  change?").
- If you still want the structured viewer, generate it as a standalone file with
  `eval-viewer/generate_review.py --static <output_path>` and hand the user a link to open
  in their own browser. Feedback downloads as a `feedback.json` file when they submit;
  copy it into the workspace so the next iteration can read it.

## No model CLI (no claude-style command-line agent)

- The automated description-optimization loop (`scripts/run_loop.py`, `scripts/run_eval.py`)
  calls a model CLI via subprocess. Without it, use the manual optimization path in
  `description-optimization.md`; it produces the same result by hand.

## Packaging

`scripts/package_skill.py` and `scripts/quick_validate.py` need only Python and a
filesystem, so they run anywhere. Packaging is only relevant for hosts that accept a
zipped `.skill` upload; for folder-based agents, distribute the folder itself.

## Updating an installed skill in a read-only path

Installed skill directories are often read-only.

- Preserve the name: keep the directory name and the `name` frontmatter field unchanged.
  If the installed skill is `research-helper`, the output stays `research-helper`, not
  `research-helper-v2`.
- Copy to a writable location before editing: copy to `/tmp/<name>/`, edit there, and
  validate and package from the copy.
- If packaging manually, stage in `/tmp/` first, then copy to the output directory; direct
  writes may fail on permissions.

## One rule that holds in every environment

When you run test cases, get the outputs in front of the human to review before you start
critiquing and rewriting them yourself. Generate the review view (or present results
inline) first. Put it on your task list so it does not get skipped.
