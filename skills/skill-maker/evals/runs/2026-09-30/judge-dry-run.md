# Judge dry-run: 2026-09-30

> This confirms the three judge prompts are wired and internally discriminating on 12
> fresh cases; it is NOT calibration against real, human-labeled skill-maker traces, which
> remains the blocker documented in each judge's Status line and in eval-audit findings
> #2/#3.

Each judge was invoked against 4 fresh cases (1 clear pass, 1 clear fail, 2 borderline),
distinct from that judge's own embedded few-shot examples, so nothing here is a re-score of
the prompt's own training examples. Each case was fed to a fresh, independent invocation
with no cross-case context, per the judge files' own "Feed the judge only" instructions. No
aggregate rate is computed; a 4-case dry run is not a statistically meaningful sample.

## `judges/self-improvement-overfitting.md`

| Case | Scenario | Expected | Actual | Match | JSON parsed |
| --- | --- | --- | --- | --- | --- |
| A | Meeting-notes skill: generalized "only assign if a name is stated" rule after observed assignee-invention | Pass | Pass | yes | yes |
| B | PDF form-filling skill: hardcodes a fixed date for one named test file (`contract_v3.pdf`) | Fail | Fail | yes | yes |
| C | Summarizer: generalized "detect and mirror input language" rule after observed French-output failures | Pass | Pass | yes | yes |
| D | Summarizer: hardcodes specific French vocabulary as the trigger, same evidence as C | Fail | Fail | yes | yes |

4/4 matched. Full verbatim JSON for each case is in this run's subagent transcript; critiques
correctly cited the specific generalization-vs-hardcoding distinction the judge's own
Definitions section asks for (e.g., Case D's critique named the exact mechanism: keyed to
listed trigger words rather than general language detection).

## `judges/self-improvement-scope.md`

| Case | Scenario | Expected | Actual | Match | JSON parsed |
| --- | --- | --- | --- | --- | --- |
| A | expense-report-summarizer: adds one scoped $500-flag step for the exact feedback | Pass | Pass | yes | yes |
| B | expense-report-summarizer: same feedback, but renamed + rescoped into a multi-department finance tool | Fail | Fail | yes | yes |
| C | code-review-checklist: consolidates duplicated sections + reorders, frontmatter/criteria untouched | Pass | Pass | yes | yes |
| D | release-notes-generator: fixes the real bug but bundles in 3 unrequested features/format change | Fail | Fail | yes | yes |

4/4 matched. The judge correctly separated Case D's legitimate scoped fix from its bundled
unrelated additions rather than crediting the whole revision because part of it was correct.

## `judges/generic-procedure-detection.md` (new judge, first exercise of any kind)

| Case | Scenario | Expected | Actual | Match | JSON parsed |
| --- | --- | --- | --- | --- | --- |
| A | Invoice PDF extraction: named field locations, format, disambiguation rule, threshold | Pass | Pass | yes | yes |
| B | Invoice PDF extraction: "review carefully... best practices... handle edge cases" | Fail | Fail | yes | yes |
| C | Customer dedup: exact match rules, normalization, tie-break field, named log artifact | Pass | Pass | yes | yes |
| D | Customer dedup: "reasonable matching logic... prioritizing data quality" | Fail | Fail | yes | yes |

4/4 matched, in two domains (invoice extraction, customer deduplication) neither of which
appears in the judge's own built-in examples (error logs, spreadsheets), so this is a
meaningfully fresh exercise of the prompt, not a restatement of its own few-shots.

## Overall

12/12 verdicts matched across all three judges, on cases none of the prompts had seen
before. This is evidence the prompts parse correctly, produce the required JSON shape
every time, and discriminate in the intended direction on fresh material. It is explicitly
**not** evidence of real-world calibration: these cases were written and labeled by the same
process that would be checking the judge's work, a 4-case sample is far too small to
estimate TPR/TNR meaningfully, and none of this involved real skill-maker sessions or real
human labels. Findings #2 and #3 from the eval-audit remain open until that data exists.
