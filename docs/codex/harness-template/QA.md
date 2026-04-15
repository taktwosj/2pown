# Harness QA (Template)

## Core checks

- Q1: The current sprint's acceptance criteria are each tested explicitly.
- Q2: No unrelated behavior regressed in the touched area.
- Q3: The user-visible state after the change is understandable.
- Q4: Any validation, proof, or rollback path required by the sprint is exercised.

## Regression notes

- Re-run the immediate user flow around the touched feature.
- Re-check any touched labels, dates, status text, and save/apply flows.
- Record both success and failure expectations when relevant.
