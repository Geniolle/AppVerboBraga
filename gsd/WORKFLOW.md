# GSD Workflow

Updated: 2026-07-03

## Purpose

This document defines how GSD Core should be used in future AppGenesis sessions with Codex, Claude, or another agent.

## Reading Order

Use this order when starting work:

1. Read `gsd/WORKFLOW.md`
2. Read `gsd/CONTEXT.md`
3. Read `gsd/STATE.md`
4. Read `gsd/DECISIONS.md`
5. Read the active phase in `gsd/phases/`
6. Read the relevant task in `gsd/tasks/`, if one already exists

## When To Read `CONTEXT.md`

Read `gsd/CONTEXT.md` when:

- starting a new session in the repository
- the task touches architecture, stack, auth, permissions, modules, or runtime boundaries
- the agent does not yet know the current web stack
- there is any risk of inventing architecture that the repo does not currently use

## When To Update `STATE.md`

Update `gsd/STATE.md` when:

- a planning milestone changes
- a new near-term priority becomes explicit
- a risk becomes more important
- a relevant piece of current project status changes
- a completed documentation step changes what future sessions should assume

Do not update `STATE.md` for every minor code edit.

## When To Create A Task In `gsd/tasks/`

Create a new task when:

- the work has a clear objective
- the work should be traceable across one or more sessions
- the task has boundaries that can be stated as scope and out-of-scope
- completion should be validated with explicit criteria

Use one file per task.

Suggested naming:

- `gsd/tasks/003-short-kebab-name.md`

## When To Update `DECISIONS.md`

Update `gsd/DECISIONS.md` when:

- a technical direction is intentionally chosen
- the team wants future sessions to stop reopening the same architectural question
- a strategic constraint should survive beyond the current task

Do not use `DECISIONS.md` for:

- transient implementation notes
- unresolved ideas
- temporary debugging details

## When To Create Or Close A Phase

Create a phase file in `gsd/phases/` when:

- a group of related tasks belongs to the same broader stage
- the work has a shared goal and shared non-goals
- multiple sessions should align around the same roadmap step

Close or update a phase when:

- the phase goal is achieved
- the scope changes materially
- the next phase becomes the new active focus

Only one phase should normally be marked `active`.

## How To Use GSD With Codex

At the start of a Codex session:

1. Ask Codex to read `gsd/WORKFLOW.md`, `gsd/CONTEXT.md`, `gsd/STATE.md`, and `gsd/DECISIONS.md`
2. Point Codex to the relevant phase and task, if they already exist
3. Ask Codex to keep new work aligned with current decisions before editing code

During the session:

- ask Codex to create a new task file before large work if one does not exist
- ask Codex to update `STATE.md` only when the project-level state truly changes
- ask Codex to update `DECISIONS.md` only when a decision should persist across future sessions

At the end of the session:

- confirm whether the task should remain active or be marked completed
- record new planning outcomes if they matter beyond the current turn

## How To Use GSD With Claude

At the start of a Claude session:

1. Ask Claude to read the same GSD files first
2. State which phase and task the work belongs to
3. Ask Claude not to reopen settled decisions unless there is new evidence

During the session:

- use the task file to keep scope tight
- use `STATE.md` to track meaningful planning changes
- use `DECISIONS.md` only for durable technical direction

At the end of the session:

- ask Claude to summarize whether the task changed project state
- update GSD files only if the change is durable and useful for future sessions

## Before Changing Code

Checklist:

- [ ] Read `gsd/WORKFLOW.md`
- [ ] Read `gsd/CONTEXT.md`
- [ ] Read `gsd/STATE.md`
- [ ] Read `gsd/DECISIONS.md`
- [ ] Identify the active phase
- [ ] Identify the current task or create a new one if needed
- [ ] Confirm the work does not conflict with existing decisions
- [ ] Confirm the scope and non-goals before editing runtime code

## After Changing Code

Checklist:

- [ ] Confirm whether the task should be marked completed
- [ ] Update `STATE.md` only if project-level status changed
- [ ] Update `DECISIONS.md` only if a durable decision was made
- [ ] Update the active phase only if the phase status or scope changed
- [ ] Keep planning notes separate from runtime code
- [ ] Record validation evidence in the task or final session summary

## Small Rules

- Keep GSD files simple and readable
- Prefer short durable statements over long narrative logs
- Do not mix planning records with runtime implementation
- Do not let GSD replace code comments, tests, or normal technical documentation
- Treat GSD as the planning layer, not the application layer
