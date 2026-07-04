# Task 005: Alembic Baseline Drift

Status: completed
Updated: 2026-07-03

## Objective

Analyze and document the pre-existing drift between the current SQLAlchemy metadata and the Alembic/database baseline, without destructive database changes and without altering application behavior.

## Scope

- Create the task record for Alembic baseline drift
- Inspect `migrations/`, `alembic.ini`, `migrations/env.py`, models, and bootstrap scripts
- Identify the remaining Alembic drift after Task 004
- Classify each drift item by probable origin and risk
- Create a technical report under `gsd/reports/`
- Apply only very small safe metadata alignment if it does not mutate existing data
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` if a durable migration-policy decision is needed

## Out Of Scope

- Dropping tables
- Dropping columns
- Destructive downgrade work
- Functional application changes
- Docker changes
- Login/auth flow changes
- Supabase changes
- Next.js migration
- Reconstructing removed product features without explicit scope

## Checklist

- [x] `gsd/tasks/005-alembic-baseline-drift.md` exists
- [x] `gsd/reports/alembic-baseline-drift.md` exists
- [x] `alembic current` was inspected
- [x] `alembic heads` was inspected
- [x] `alembic check` was inspected
- [x] The drift items were classified individually
- [x] `users.system_type` metadata drift was normalized safely
- [x] No destructive migration was created
- [x] Remaining legacy drift was documented clearly for human decision

## Completion Criteria

This task is complete when:

- the remaining Alembic drift is explained in a durable report
- safe metadata-only alignment has been applied where low risk
- destructive cleanup is explicitly deferred instead of guessed
- future sessions can distinguish resolved metadata drift from unresolved legacy schema drift
