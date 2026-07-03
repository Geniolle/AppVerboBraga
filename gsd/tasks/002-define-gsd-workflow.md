# Task 002: Define GSD Workflow

Status: completed
Updated: 2026-07-03

## Objective

Define a clear workflow for how GSD Core should be used in future AppVerboBraga sessions with Codex, Claude, or another agent.

## Scope

- Create `gsd/WORKFLOW.md`
- Define when each core GSD file should be read or updated
- Define when to create new tasks
- Define when to update decisions
- Define when to create or close phases
- Add before-code and after-code checklists
- Reflect the workflow priority in `gsd/STATE.md` if useful

## Out Of Scope

- Changing application behavior
- Changing backend code
- Changing frontend code
- Changing templates
- Changing routes
- Changing services
- Changing models
- Changing database structure
- Changing Docker
- Installing dependencies

## Checklist

- [x] `gsd/WORKFLOW.md` exists
- [x] The workflow explains when to read `CONTEXT.md`
- [x] The workflow explains when to update `STATE.md`
- [x] The workflow explains when to create tasks
- [x] The workflow explains when to update `DECISIONS.md`
- [x] The workflow explains when to create or close phases
- [x] The workflow includes Codex usage guidance
- [x] The workflow includes Claude usage guidance
- [x] The workflow includes a checklist before changing code
- [x] The workflow includes a checklist after changing code
- [x] No functional application files were changed

## Completion Criteria

This task is complete when:

- future agent sessions have one obvious workflow document to follow
- the relation between context, state, decisions, phases, and tasks is explicit
- the guidance remains purely documental
- the application runtime remains unaffected
