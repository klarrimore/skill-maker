# skill-maker failure modes

The concrete ways skill-maker's instructions fail in practice, and which eval catches each.
This is the error-analysis record behind `evals.json`: expectations are written against these
failure modes, not borrowed generic qualities.

**Provenance.** These modes were derived from the skill's own instructions and known agent
failure patterns, not yet from a trace-review pass over real skill-maker sessions. Treat them
as a seed: when real sessions exist, sample them (see `references/evaluation.md` and the
audit's sampling strategies), confirm or add modes, and mark each covered/gap honestly.

| ID | Failure mode | Caught by |
| --- | --- | --- |
| FM-1 | Emits platform-locked frontmatter — a client-specific field (`context`, `model`, `user-invocable`, scripts sidecar) instead of the six standard fields | Eval 1 (recognized-fields assertion); `grade_artifacts.py` |
| FM-2 | Invalid frontmatter — non-lowercase/kebab name, name ≠ directory, or description over 1024 chars (spec violations); plus angle brackets, which the bundled validator rejects as a skill-maker hardening measure (the spec is silent and `skills-ref` does not check them) | Eval 1, Eval 2; `grade_artifacts.py`; `quick_validate` |
| FM-3 | Bloats `SKILL.md` with depth that belongs in `references/` instead of disclosing it behind a read-this-when pointer | Eval 1 (body-budget assertion) |
| FM-4 | Skips validation before handoff | Eval 1 (runs validator), Eval 4 (re-validates) |
| FM-5 | Invents a generic procedure from general knowledge ("handle errors appropriately") instead of extracting real expertise | Eval 1 (task-specific guidance assertion) — **partial** |
| FM-6 | Writes a description that will not trigger — vague, missing the when-to-use half, not pushy about indirect contexts | Eval 3; trigger set |
| FM-7 | Overfits the description to the queries it was tuned on (no held-out selection) | Eval 3 (held-out selection assertion) |
| FM-8 | Updates an installed skill by renaming it (`-v2`) or editing a read-only install in place | Eval 4 |
| FM-9 | Ships a skill whose behavior surprises a description-only reader (hidden access or exfiltration behind a benign description) | Eval 5 |
| FM-10 | Overfits the skill itself to the few test prompts with fiducial MUSTs | **Gap** — judged qualitatively per `references/evaluation.md` |
| FM-11 | Damages the eval suite itself: fixes the broken fixture in place, disarming the negative test | Eval 2 (copy-first assertion); `smoke.sh` fixture-integrity check |
| FM-12 | Forces the eval loop on a user who declined it, instead of adapting | Eval 6 |
| FM-13 | Ignores environment limits (no subagents, no display, no packager) and fails instead of substituting the manual path | **Gap** — process-verified only; `references/environment-adaptations.md` |

## Keeping this current

- Re-run the task evals and trigger loop after any change to `SKILL.md` frontmatter or body,
  and after model switches. A mode that was covered can regress silently.
- When a new failure appears in a real session, add it here first, then add or sharpen the
  expectation that catches it. Evaluators follow error analysis, never the reverse.
- Close the **Gap** rows when a mode becomes testable, or mark them permanently qualitative
  (FM-10) rather than inventing a brittle assertion.
