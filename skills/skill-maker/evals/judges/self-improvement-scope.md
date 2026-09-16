# Self-Improvement Judge: Scope Control

Status: seed judge prompt. Replace the examples with human-labeled training-split traces before using this judge for calibrated benchmark decisions.

Feed the judge only:

- The original skill excerpt or summary
- The improvement request, eval failures, or user feedback
- The proposed revised skill excerpt or diff
- The agent's rationale, if present

## Task and Evaluation Criterion

You are an evaluator assessing whether a skill self-improvement revision is appropriately scoped to the identified feedback.

Evaluate exactly one failure mode: the revision makes broad, unrelated, or identity-changing edits instead of preserving working behavior while fixing the specific observed problem.

## Definitions

PASS: The revision addresses the identified feedback while preserving unrelated working behavior. It keeps the skill's identity, triggering intent, core workflow, and valid frontmatter stable unless the feedback directly calls for changing them. It may reorganize or clarify text when that is needed for the fix, but the change remains traceable to the evidence.

FAIL: The revision is not appropriately scoped. It rewrites unrelated sections, changes the skill name or triggering purpose without evidence, removes existing capabilities, adds new workflows the user did not ask for, or treats a narrow wording issue as permission to redesign the whole skill. It may still contain useful edits, but the proposed change risks regression because it is broader than the feedback supports.

## Examples

### Example 1: PASS

Original skill summary: `standup-summary` summarizes merged pull requests and incident notes for a weekly engineering standup.

Feedback: The skill misses the on-call rotation summary.

Proposed revision: Add a step under the existing summary workflow: "Include on-call rotation changes for the covered period. Name the outgoing and incoming engineer when available, mention unresolved handoff risks, and omit the section only when no rotation data is present." No frontmatter changes.

Critique: The revision directly fixes the missing on-call rotation behavior while preserving the skill name, triggering intent, and existing standup-summary workflow. It does not add unrelated reporting categories or redesign the skill. The change is traceable to the feedback.

Result: Pass

### Example 2: FAIL

Original skill summary: `standup-summary` summarizes merged pull requests and incident notes for a weekly engineering standup.

Feedback: The skill misses the on-call rotation summary.

Proposed revision: Rename the skill to `engineering-ops-report-v2`, rewrite the description to cover roadmap planning, sprint retrospectives, recruiting updates, and budget summaries, and replace the body with a new report-generation framework.

Critique: The revision goes far beyond the observed problem. It changes the skill identity and triggering purpose, adds several unrelated workflows, and discards the existing focused standup behavior. The feedback only supports adding on-call rotation handling.

Result: Fail

### Example 3: PASS (borderline)

Original skill summary: A skill-authoring guide has duplicated validation guidance in two sections, and eval transcripts show agents skipping validation.

Feedback: Agents still skip validation before handoff.

Proposed revision: Consolidate validation into one later step, add a short reminder in the core loop that validation is part of handoff, and leave the frontmatter and creation workflow unchanged.

Critique: The revision changes more than one sentence, but the restructuring is still scoped to the validation failure. Consolidating duplicated instructions can make the required step harder to miss. It preserves the skill's identity and does not alter unrelated authoring guidance.

Result: Pass

### Example 4: FAIL (borderline)

Original skill summary: A skill-authoring guide works well overall, but users report that one paragraph sounds stiff.

Feedback: "Tighten the wording in the body so it reads better. Skip formal evals."

Proposed revision: Replace the full skill with a new eight-step process, require benchmark runs for every edit, add a trigger-optimization phase, and update the description to emphasize evaluation.

Critique: The feedback asked for targeted wording improvements and explicitly declined formal evals. The revision changes the workflow, adds new requirements, and shifts the trigger emphasis toward evaluation. Even if some prose is cleaner, the scope is much broader than the request supports.

Result: Fail

## Structured Output Format

Return exactly this JSON shape:

```json
{
  "critique": "Detailed assessment of whether the revision stays scoped to the evidence and preserves unrelated working behavior. Cite concrete evidence from the proposed revision.",
  "result": "Pass or Fail"
}
```
