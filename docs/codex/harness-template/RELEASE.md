# Release Sprint (Template)

## Preconditions

- All planned sprints for this release are PASS.
- QA checklist has been executed and recorded.
- Rollback plan is written.
- The user explicitly issued: `RELEASE`.

## Steps

1. Run full QA from `QA.md` and the active sprint criteria in `PLAN.md`
2. Update `Documentation.md`:
   - What changed
   - How it was verified locally
   - Remaining risks
   - Release notes
3. Prepare release-ready git state locally
   - Understand the working tree state
   - Do not violate the no-commit-before-release rule
4. Deploy to runtime only through the project's allowed non-FTP path
5. Verify the runtime using the same core scenarios
6. Push / merge only after runtime verification passes and the project workflow allows it

## Output

Create a final `RELEASE REPORT` in `Documentation.md` including:

- Commit hash(es), if any were created during release
- Deploy evidence
- Verification results
- Rollback instructions
