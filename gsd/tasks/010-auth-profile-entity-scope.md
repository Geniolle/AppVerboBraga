# Task 010: Authorization Profile Entity Scope

Status: completed
Updated: 2026-07-04

## Objective

Add the `Entidade` field to the authorization-profile flow and enforce, on both UI and server, that only an active owner entity can create global profiles.

## Scope

- Inspect how the current profile flow resolves active entity, owner/legacy entity scope, and user permissions
- Add the `Entidade` field to the authorization-profile technical form
- Persist the chosen entity scope together with the existing profile payload
- Validate on the server that legacy entities cannot force global scope
- Keep profile rows separated by active entity context, while preserving global rows
- Update GSD planning state and any durable technical decision if needed
- Add focused automated tests for repository behavior

## Out Of Scope

- Changes to Docker
- Database migrations
- Changes to OAuth or the broader login flow
- Changes to unrelated processes
- Changes to object-authorization storage
- Frontend redesign

## Checklist

- [x] Active-entity and permission flow was inspected
- [x] `Entidade` was added to the authorization-profile form contract
- [x] Owner context can choose between own entity and whole system
- [x] Legacy context cannot create or edit profiles as global through the server
- [x] Profile rows are filtered by active entity context, with global rows preserved
- [x] Existing generic form rendering was reused
- [x] Focused automated tests were added or updated
- [x] `gsd/STATE.md` was updated
- [x] `gsd/DECISIONS.md` was updated

## Completion Criteria

This task is complete when:

- the authorization-profile form exposes `Entidade`
- the backend rejects invalid global submissions from legacy context
- owner context can still create both entity-scoped and global profiles
- the change stays localized and does not alter unrelated application behavior
