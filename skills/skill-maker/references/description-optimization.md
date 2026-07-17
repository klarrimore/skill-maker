# Optimizing the Description for Triggering

The `description` field is the primary and essentially only mechanism an agent uses to
decide whether to load a skill. An under-specified description means the skill will not
trigger when it should; an over-broad one means it triggers when it should not. After the
skill works, tune the description with a small eval-driven loop.

## How triggering actually works

A skill appears in the agent's available-skills list as its `name` plus `description`, and
the agent decides whether to consult it from that text alone. Two consequences:

- Agents only consult a skill for a task they cannot already handle trivially. A one-step
  request like "read this PDF" may not trigger a PDF skill even with a perfect
  description, because the agent can just do it. So eval queries must be substantive
  enough that consulting a skill is actually worthwhile; "read file X" is a poor test
  case.
- Agents tend to under-trigger. Counter it by making the description a little pushy: list
  the contexts where the skill applies, including ones where the user does not name the
  domain ("even if they do not explicitly mention CSV or analysis").

## Principles for a good description

- Imperative phrasing. "Use this skill when..." rather than "This skill does...".
- Focus on user intent, not implementation.
- Be pushy: enumerate applicable contexts, including indirect ones.
- Stay concise. The hard limit is 1024 characters; aim for 256 characters, be very frugal over 512 characters, and do not approach it by keyword-stuffing.

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

Make them realistic: concrete and specific, with file paths, job or situation context,
column names and values, company names, URLs, a little backstory. Vary length and
register; some lowercase, some with abbreviations, typos, or casual speech. Favor edge
cases over clear-cut ones.

Weak: "Format this data", "Extract text from PDF", "Create a chart".

Strong: "ok so my boss just sent me this xlsx file (its in my downloads, called something
like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the
profit margin as a percentage. revenue is in column C and costs are in column D i think".

For should-trigger (8 to 10): cover different phrasings of the same intent, some formal
some casual, including cases where the user names neither the skill nor the file type but
clearly needs it. Throw in uncommon use cases and cases where this skill competes with
another but should win.

For should-not-trigger (8 to 10): the valuable ones are near-misses, queries that share
keywords or concepts with the skill but need something different. Adjacent domains,
ambiguous phrasing where a naive keyword match would trigger, contexts where another tool
fits better. Do not make negatives obviously irrelevant; "write a fibonacci function" as a
negative for a PDF skill tests nothing.

## Step 2: Review the eval set with the user

Bad eval queries produce bad descriptions, so get sign-off. If you have a display, render
`assets/eval_review.html`: replace `__EVAL_DATA_PLACEHOLDER__` with the JSON array (no
surrounding quotes; it is a JS assignment), `__SKILL_NAME_PLACEHOLDER__` with the name,
and `__SKILL_DESCRIPTION_PLACEHOLDER__` with the current description; write to a temp file
and open it. The user can edit queries, toggle should-trigger, add or remove entries, then
export the set. If you have no display, present the queries inline and let the user edit
them in the conversation.

## Step 3: Run the optimization loop

Split the eval set into roughly 60 percent train and 40 percent held-out test. Evaluate the
current description by running each query several times (at least 3) to get a reliable
trigger rate, with a pass threshold of 0.5. Propose an improved description based on what
failed, re-evaluate on both splits, and iterate up to about 5 times. Select the best
iteration by the held-out test score, not the train score, to avoid overfitting.

Run the loop by hand: for each candidate description, run each eval query yourself a few
times, record whether the skill would trigger, compute the trigger rate against the
threshold on the train split, revise, then confirm on the held-out split. Keep the candidate
with the best held-out result. Use the model that powers the current session for the runs so
the test matches what the user actually experiences.

## Step 4: Apply the result

Take the winning description, update the `SKILL.md` frontmatter, re-validate (the 1024
character limit and no angle brackets still apply), and show the user the before and after
with the scores.
