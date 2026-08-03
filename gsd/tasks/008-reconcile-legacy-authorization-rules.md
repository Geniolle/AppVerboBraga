# Task 008: Reconcile Legacy Authorization Rules

Status: completed
Updated: 2026-07-03

## Objective

Confirm whether the 2 legacy rows in `process_view_authorization_rules` were already migrated or meaningfully replaced by the current authorization storage in:

- `process_records__perfil_de_autorizacao`
- `process_records__objeto_de_autorizacao`

## Scope

- Create the task record for legacy authorization reconciliation
- Inspect current authorization/profile storage contracts in code
- Inspect live legacy rows in `process_view_authorization_rules`
- Inspect live current authorization/profile records stored in `members.profile_custom_fields`
- Build a reconciliation matrix for the 2 legacy rows
- Identify any missing or transformed data
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` if a durable data-reconciliation rule becomes clear

## Out Of Scope

- Dropping tables
- Dropping columns
- Altering data
- Creating migrations
- Reintroducing runtime models or services
- Changing login/auth behavior
- Docker changes
- Supabase changes
- Next.js migration

## Checklist

- [x] `gsd/tasks/008-reconcile-legacy-authorization-rules.md` exists
- [x] `gsd/reports/reconcile-legacy-authorization-rules.md` exists
- [x] Static repository analysis was executed
- [x] Read-only database queries were executed
- [x] The 2 legacy rows were compared against current storage
- [x] A reconciliation matrix was produced
- [x] No schema or data was changed
- [x] `GET /login` still responds `200`
- [x] `alembic current` and `alembic heads` remain unchanged
- [x] `alembic check` did not gain new drift

## Completion Criteria

This task is complete when:

- each legacy row has a documented reconciliation status
- the report states whether migration is complete, partial, or missing
- any missing business information is listed explicitly
- future data migration or retirement work can start from a documented baseline
