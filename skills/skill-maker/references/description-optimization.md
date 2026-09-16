# Optimizing the Description for Triggering

The `description` field is the primary and essentially only mechanism an agent uses to decide
whether to load a skill. An under-specified description means the skill will not trigger when
it should; an over-broad one means it triggers when it should not. After the skill works, tune
the description with a small eval-driven loop.

## How triggering actually works

A skill appears in the agent's available-skills list as its `name` plus `description`, and the
agent decides whether to consult it from that text alone. Two consequences:

- Agents only consult a skill for a task they cannot already handle trivially. A one-step
  request like "read this PDF" may not trigger a PDF skill even with a perfect description,
  because the agent can just do it. So eval queries must be substantive enough that consulting
  a skill is worthwhile; "read file X" is a poor test case.
- Agents tend to under-trigger. Counter it by making the description a little pushy: list the
  contexts where the skill applies, including ones where the user does not name the domain
  ("even if they do not explicitly mention CSV or analysis").

## Principles for a good description

- Imperative phrasing. "Use this skill when..." rather than "This skill does...".
- Focus on user intent, not implementation.
- Be pushy: enumerate applicable contexts, including indirect ones.
- Stay concise. Aim for 256 characters or fewer and treat 512 as the working ceiling; 1024 is
  a hard limit, not a target. Do not approach it by keyword-stuffing.

Before and after:

```yaml
# Before
description: Process CSV files.

# After
description: >
  Analyze CSV and tabular data files: compute summary statistics, add derived
  columns, generate charts, and clean messy data. Use this skill when the user
  has a CSV, TSV, or Excel file and wants to explore, transform, or visualize the
  data, even if they do not explicitly mention "CSV" or "analysis."
```

## Step 1: Generate trigger eval queries

Create about 20 queries, split should-trigger and should-not-trigger:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Make them realistic: concrete and specific, with file paths, job or situation context, column
names and values, company names, URLs, a little backstory. Vary length and register; some
lowercase, some with abbreviations, typos, or casual speech. Favor edge cases over clear-cut
ones.

Weak: "Format this data", "Extract text from PDF", "Create a chart".

Strong: "ok so my boss just sent me this xlsx file (its in my downloads, called something
like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the
profit margin as a percentage. revenue is in column C and costs are in column D i think".

For should-trigger (8 to 10): cover different phrasings of the same intent, some formal and
some casual, including cases where the user names neither the skill nor the file type but
clearly needs it. Throw in uncommon use cases and cases where this skill competes with another
but should win.

For should-not-trigger (8 to 10): the valuable ones are near-misses, queries that share
keywords or concepts with the skill but need something different. Adjacent domains, ambiguous
phrasing where a naive keyword match would trigger, contexts where another tool fits better. Do
not make negatives obviously irrelevant; "write a fibonacci function" as a negative for a PDF
skill tests nothing.

## Step 2: Review the eval set with the user

Bad eval queries produce bad descriptions, so get sign-off. If you have a display, render
`assets/eval_review.html`: replace `__EVAL_DATA_PLACEHOLDER__` with the JSON array (no
surrounding quotes; it is a JS assignment), `__SKILL_NAME_PLACEHOLDER__` with the name, and
`__SKILL_DESCRIPTION_PLACEHOLDER__` with the current description. Write to a temp file and open
it. The user can edit queries, toggle should-trigger, add or remove entries, then export the
set. With no display, present the queries inline and let the user edit them in the
conversation.

## Step 3: Run the optimization loop

Split the eval set into roughly 60 percent train and 40 percent held-out test. Run each query
at least 3 times to get a reliable trigger rate, with a pass threshold of 0.5. Propose an
improved description from the train failures only, re-evaluate on both splits, and iterate up
to about 5 times. Select the best iteration by the held-out score, not the train score, to
avoid overfitting.

Run the loop by hand with the model that powers the current session, so the test matches what
the user experiences. Record whether the skill would trigger for each query. Store the split,
per-query trigger rates, and scores as `trigger_results.json` (schema in `schemas.md`) so the
selection is auditable.

## Step 4: Apply the result

Take the winning description, update the `SKILL.md` frontmatter, and re-check the length
budget. Angle brackets are not a format constraint: the spec is silent and the official
`skills-ref` validator does not check them. The bundled validator rejects them as a hardening
measure, since some clients may sanitize markup. Then sanity-check the winner with 5 to 10
fresh queries, and show the user the before and after with the scores.