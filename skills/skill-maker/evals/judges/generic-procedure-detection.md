# Generic Procedure Detection Judge

Status: seed judge prompt. Replace the examples with human-labeled training-split traces before using this judge for calibrated benchmark decisions. A 4-case dry run (2026-09-30) confirmed this prompt parses and discriminates on fresh cases; see evals/runs/2026-09-30/judge-dry-run.md. This is not calibration.

Feed the judge only:

- The skill excerpt or full body being evaluated
- The domain or workflow the skill claims to cover
- Any source material the author had available (transcripts, runbooks, APIs), if present

## Task and Evaluation Criterion

You are an evaluator assessing whether a skill's instructions were extracted from real expertise or invented as generic procedure.

Evaluate exactly one failure mode: the skill body relies on vague, domain-agnostic filler instead of concrete, task-specific guidance a model could not have produced without real knowledge of the task.

## Definitions

PASS: The instructions name concrete operational detail specific to the domain: data sources, file formats, tools, named thresholds, decision rules, edge cases, or sequencing that reflects hands-on knowledge of the task. Generic connective language ("then confirm with the user") is fine when the surrounding steps carry real substance. A short skill can still pass if every step is concrete for its scope.

FAIL: The instructions are interchangeable with a completely different domain without rewriting: phrases like "handle errors appropriately," "follow best practices," "ensure high quality output," or "review carefully for issues" stand in for steps that should name what an error looks like, what the standard is, or what to check. No named tool, format, threshold, or example appears where the domain clearly could supply one.

## Examples

### Example 1: PASS

Skill excerpt: "Pull the last 7 days of backend error logs from the configured log source. Group by the `service` field, count occurrences per distinct error signature (exception type plus top stack frame), and rank the top 10 by count. Write the summary as a table: service, error signature, count, first-seen timestamp. Flag any signature that did not appear in the prior week's summary as 'new'."

Critique: Every step names a concrete operation: a fixed time window, a grouping key, a specific ranking method, an exact output shape, and a specific edge case (new signatures). This could only have been written by someone who has actually done this task.

Result: Pass

### Example 2: FAIL

Skill excerpt: "Gather the relevant logs. Analyze them for problems. Summarize the findings for the team and make sure to handle any errors appropriately. Present the results in a clear and professional format."

Critique: Nothing here is specific to backend error-log analysis. "Gather," "analyze," "handle appropriately," and "clear and professional format" would read identically for a skill about sales reports or meeting notes. No grouping key, time window, ranking method, or output shape is named.

Result: Fail

### Example 3: PASS (borderline)

Skill excerpt: "Read the uploaded spreadsheet and validate it before use: every row must have a non-empty `id` column, dates must parse as ISO 8601, and numeric columns must not contain currency symbols. Reject the file and tell the user which rows failed if any check fails."

Critique: "Validate it" alone would be generic, but the skill immediately cashes it out into three concrete, checkable rules and a specific failure behavior (reject and name the rows). This is short but not vague: a model without domain knowledge would not have picked these exact three checks.

Result: Pass

### Example 4: FAIL (borderline)

Skill excerpt: "When processing the spreadsheet, apply appropriate data validation rules to catch common data quality issues, then proceed with the standard analysis workflow, adjusting your approach based on the specific characteristics of the dataset."

Critique: This sounds domain-aware because it mentions "the spreadsheet" and "the standard analysis workflow," but it never says what an appropriate rule is, what a common issue looks like, or what "adjusting your approach" means in practice. Swap in any other file type and the sentence is unchanged. The specificity is only surface-level.

Result: Fail

## Structured Output Format

Return exactly this JSON shape:

```json
{
  "critique": "Detailed assessment of whether the skill body carries concrete, extracted domain expertise or generic filler. Cite concrete evidence from the skill excerpt.",
  "result": "Pass or Fail"
}
```
