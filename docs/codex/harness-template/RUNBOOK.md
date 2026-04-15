# Harness Runbook (Template)

## Roles

- Planner: refine plan and documentation only
- Builder: implement the current sprint only
- Evaluator: verify the current sprint and return PASS / FAIL only

## Core rules

1. Work only on the current sprint.
2. Keep diffs small and local.
3. Do not change APIs unless the sprint explicitly allows it.
4. Update `Documentation.md` after each sprint.

## Approval gate

After EACH sprint, output a STATUS REPORT and STOP.
Do not proceed until the user replies with one of:
`CONTINUE` / `HOLD` / `REPLAN` / `RELEASE` / `STOP`.
Harness Mode remains active until `STOP`.

## QA execution

- Run the manual checklist from `QA.md`
- Record the outcome in `Documentation.md`
- If verification is incomplete, say why explicitly
