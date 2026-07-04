# Task 006: Legacy Tables Decision

Status: completed
Updated: 2026-07-03

## Objective

Analyze and classify the legacy PostgreSQL tables that still exist in the Alembic history and live database, but no longer have an active contract in `appverbo/models/`.

## Scope

- Create the task record for legacy-table classification
- Inspect repository usage for `songs`, `admin_definitions`, and `process_view_authorization_rules`
- Inspect the live PostgreSQL structure and data for those tables
- Classify each table as `ativa`, `legada`, `obsoleta`, or `indefinida`
- Record risk, recommendation, and next action for each table
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` if a durable classification policy becomes clear

## Out Of Scope

- Dropping tables
- Dropping columns
- Removing data
- Creating destructive migrations
- Restoring feature code
- Changing login/auth behavior
- Docker changes
- Supabase changes
- Next.js migration

## Checklist

- [x] `gsd/tasks/006-legacy-tables-decision.md` exists
- [x] `gsd/reports/legacy-tables-decision.md` exists
- [x] Static repository usage was inspected
- [x] Read-only database queries were executed
- [x] Each table received a classification
- [x] No schema or data was changed
- [x] `GET /login` still responds `200`
- [x] The result stays documentary only

## Completion Criteria

This task is complete when:

- each target table has a documented classification
- the classification is evidence-based
- any uncertainty is made explicit instead of guessed away
- future sessions can decide keep/restore/retire from a documented baseline
