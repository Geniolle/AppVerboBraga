# Task 007: Process View Authorization Rules Decision

Status: completed
Updated: 2026-07-03

## Objective

Confirm whether `process_view_authorization_rules` is still required by the current application, has already been replaced by another runtime contract, or should regain explicit ownership in code.

## Scope

- Create the task record for the focused `process_view_authorization_rules` decision
- Inspect current permission, profile, menu, and admin-subprocess code paths
- Inspect the related Alembic migrations
- Inspect the live PostgreSQL table in read-only mode
- Compare the legacy table with the current runtime storage used by authorization/profile flows
- Classify the table as `ativa`, `legada`, `obsoleta`, or `indefinida`
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` if the replacement contract is now clear

## Out Of Scope

- Dropping the table
- Dropping columns
- Removing data
- Creating migrations
- Reintroducing models or services with runtime impact
- Changing login/auth behavior
- Docker changes
- Supabase changes
- Next.js migration

## Checklist

- [x] `gsd/tasks/007-process-view-authorization-rules-decision.md` exists
- [x] `gsd/reports/process-view-authorization-rules-decision.md` exists
- [x] Static repository analysis was executed
- [x] Read-only database queries were executed
- [x] Current runtime replacement logic was identified
- [x] The table received a final classification
- [x] No schema or data was changed
- [x] `GET /login` still responds `200`
- [x] `alembic current` and `alembic heads` remain unchanged
- [x] `alembic check` did not gain new drift

## Completion Criteria

This task is complete when:

- the table has an evidence-based classification
- the report explains whether the table is still used
- any replacement runtime contract is identified explicitly
- future cleanup or restoration work can start from a documented decision baseline
