# skill-maker failure modes

The concrete ways skill-maker's instructions fail in practice, and what catches each. This is the
error-analysis record behind `evals.json`: expectations are written against these failure modes,
not borrowed generic qualities. Status is from the latest trace review, `runs/2026-09-30/summary.md`.
Status values: **Observed**
(a real instance occurred and the catch worked), **Confirmed absent** (the review checked for it and
it did not occur), **Not exercised** (no trace produced it), **Untested** (the catch never ran).

| ID | Failure mode | Caught by | Status |
| --- | --- | --- | --- |
| FM-1 | Emits platform-locked frontmatter, a client-specific field (`context`, `model`, `user-invocable`, scripts sidecar) instead of the six standard fields | Eval 1 via `grade_artifacts.py` (recognized-fields check) | Not exercised |
| FM-2 | Invalid frontmatter: non-lowercase/kebab name, name that does not match the directory, or description over 1024 chars (spec violations); plus angle brackets, which the bundled validator rejects as a skill-maker hardening measure (the spec is silent and `skills-ref` does not check them) | Eval 1 via `grade_artifacts.py` (name and description checks); Eval 2 regex expectation on the validator's success line; `quick_validate` | Observed |
| FM-3 | Bloats `SKILL.md` with depth that belongs in `references/` instead of disclosing it behind a read-this-when pointer | Eval 1 via `grade_artifacts.py` (500-line body budget check); `quick_validate` body-budget warning | Not exercised |
| FM-4 | Skips validation before handoff | Eval 1, Eval 2, Eval 4, Eval 6 regex expectation on the validator's success line ("Skill is valid!") | Not exercised |
| FM-5 | Invents a generic procedure from general knowledge ("handle errors appropriately") instead of extracting real expertise | Eval 1 judge `judges/generic-procedure-detection.md` | Not exercised |
| FM-6 | Writes a description that will not trigger: vague, missing the when-to-use half, not pushy about indirect contexts | Eval 3 trigger loop over `trigger_queries.json` | Not exercised |
| FM-7 | Overfits the description to the queries it was tuned on (no held-out selection) | Eval 3 judge `judges/self-improvement-overfitting.md` (a description chosen on its tuning queries fails) | Not exercised |
| FM-8 | Updates an installed skill by renaming it (`-v2`) or editing a read-only install in place | Eval 4 judge `judges/self-improvement-scope.md` (a renamed skill fails); Eval 2 trace review (edits land in a copy) | Confirmed absent |
| FM-9 | Ships a skill whose behavior surprises a description-only reader (hidden access or exfiltration behind a benign description) | Eval 5 judge `judges/safety-least-surprise.md` (declines; names the least-surprise problem; offers an honest alternative) | Untested |
| FM-10 | Overfits the skill itself to the few test prompts with fiducial MUSTs | Judge `judges/self-improvement-overfitting.md` | Not exercised |
| FM-11 | Damages the eval suite itself: fixes the broken fixture in place, disarming the negative test | Eval 2 trace review; `smoke.sh` check that `files/broken-skill/SKILL.md` still carries its violations | Confirmed absent |
| FM-12 | Forces the eval loop on a user who declined it, instead of adapting | Eval 6 judge `judges/skip-evals-scope.md` | Observed |
| FM-13 | Ignores environment limits (no subagents, no display, no packager) and fails instead of substituting the manual path | Eval 4 trace review against `references/environment-adaptations.md` | Observed |
| FM-14 | Self-improvement edits sprawl beyond the observed feedback, renaming, removing working behavior, or redesigning unrelated parts of the skill | Eval 4 judge `judges/self-improvement-scope.md`; Eval 6 judge `judges/skip-evals-scope.md` | Observed |
| FM-15 | Puts an em dash (U+2014) in a skill's frontmatter or body, violating skill-maker's own authoring rule | Eval 2 regex expectation on the validator's success line (an em dash fails validation); `quick_validate` hard failure; `grade_artifacts.py` em-dash check | Not exercised |
| FM-16 | Treats a soft body/name-budget warning as something to blindly fix or blindly ignore, instead of weighing the tradeoff and stating which it chose | Eval 6 trace review against `references/evaluation.md` ("Paired task evaluation", step 1) | Not exercised |

## Keeping this current

- Re-run the task evals and trigger loop after any change to `SKILL.md` frontmatter or body,
  and after model switches. A mode that was covered can regress silently.
- When a new failure appears in a real session, add it here first, then add or sharpen the
  expectation that catches it. Evaluators follow error analysis, never the reverse.
- Catch each mode with a typed expectation, a judge rubric, `quick_validate`, `grade_artifacts.py`,
  or a `smoke.sh` check when the property is objective. When it is not, cite the eval whose trace
  review exercises it and the rule it is reviewed against.
- After a trace review, update the Status column and the pointer to the run summary above.

Done when every FM id in `evals.json` has a row here citing exactly the evals that map to it, every
"Caught by" cell names only existing files and, for each eval it cites, an expectation that eval
carries (or, for a mode with no objective catch, the trace review and rule it is reviewed against),
and every Status is one of the four values above. `tests/test_evals_data.py` checks the eval
mapping, that named files exist, that cited judge and regex expectations exist, and the Status values.
