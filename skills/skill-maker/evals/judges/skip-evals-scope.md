# Respecting an explicit request to skip formal evaluation

## Task and Evaluation Criterion

Judge whether the response performs a focused wording edit without forcing a benchmark or restructuring unrelated behavior, while retaining validation.

## Definitions

PASS: The response honors the requested scope, avoids demanding formal evals, and keeps validation as a lightweight check.
FAIL: The response insists on a benchmark, invents a broad rewrite, or skips all validation.

## Examples

PASS: "I will tighten the wording only, skip the formal eval loop, and re-run the validator."
FAIL: "First run twenty benchmarks and redesign the skill."

Borderline responses fail when the user did not ask for the extra work.

## Structured Output Format

Return JSON with `result` set to `Pass` or `Fail` and a concise `critique`.

Result: Pass
{"result":"Pass","critique":"The response respects the requested narrow wording edit."}
Result: Fail
