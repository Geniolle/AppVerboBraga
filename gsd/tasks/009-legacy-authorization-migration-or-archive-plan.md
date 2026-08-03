# Task 009: Legacy Authorization Migration Or Archive Plan

Status: completed
Updated: 2026-07-03

## Objective

Decide, without changing data or runtime behavior, whether the remaining legacy semantics from `process_view_authorization_rules` should be migrated into the current contract or only archived before a future removal.

## Scope

- Create the task record for the migration-or-archive decision
- Inspect the current profile and authorization-object contracts
- Inspect current Tesouraria and Extrato process/menu concepts
- Compare legacy semantics with current equivalents for:
  - profile
  - process
  - subprocess
  - department
  - entity scope
- Produce a report with Scenario A and Scenario B
- Produce an ADR for the granularity decision
- Update `gsd/STATE.md`
- Update `gsd/DECISIONS.md` if a durable technical constraint becomes clear

## Out Of Scope

- Altering data
- Creating migrations
- Dropping tables
- Dropping columns
- Reintroducing runtime models or services
- Changing login/auth behavior
- Docker changes
- Supabase changes
- Next.js migration

## Checklist

- [x] `gsd/tasks/009-legacy-authorization-migration-or-archive-plan.md` exists
- [x] `gsd/reports/legacy-authorization-migration-or-archive-plan.md` exists
- [x] `gsd/adr/ADR-001-legacy-authorization-granularity.md` exists
- [x] Static repository analysis was executed
- [x] Read-only evidence was reviewed
- [x] Scenario A was documented
- [x] Scenario B was documented
- [x] A recommendation was recorded
- [x] Human-validation dependency was made explicit where required
- [x] No schema or data was changed
- [x] `GET /login` still responds `200`

## Completion Criteria

This task is complete when:

- both archive and migration scenarios are documented
- the ADR states what is still uncertain
- the recommendation is explicit about whether human validation is still required
- future implementation work can start from a stable decision document
