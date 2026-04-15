# Harness Prompts (Template)

## Planner prompt

Read `CHARTER.md`, `PLAN.md`, `RUNBOOK.md`, and `Documentation.md`.
Refine only the current sprint.
Do not write code.
Update planning and documentation only.
End with a STATUS REPORT and STOP.

## Builder prompt

Read `CHARTER.md`, `PLAN.md`, `RUNBOOK.md`, `QA.md`, and `Documentation.md`.
Implement ONLY the current sprint.
Keep diffs minimal.
Run the sprint's manual checks.
Update `Documentation.md`.
End with a STATUS REPORT and STOP.

## Evaluator prompt

Read `PLAN.md`, `QA.md`, and `Documentation.md`.
Do NOT implement.
Verify the current sprint against its acceptance criteria.
Return PASS or FAIL with exact repro steps if failed.
Update `Documentation.md`.
End with a STATUS REPORT and STOP.
