# GSD Decisions

Updated: 2026-07-03

## Decision 001

Backend remains on FastAPI in the current phase.

Reason:
- It is already the active runtime
- Routes, services, auth, permissions, and templates are built around it
- Replacing the backend now would add migration risk without first improving architecture boundaries

## Decision 002

The current Jinja frontend remains in place for now.

Reason:
- It is the live administrative shell today
- A large amount of current workflow behavior depends on server-rendered templates plus shared JavaScript
- Replacing it before separating the API would increase coupling and migration cost

## Decision 003

PostgreSQL remains the primary database in this phase.

Reason:
- It is already the main Docker runtime database
- The application already depends on SQLAlchemy, Alembic, and PostgreSQL behavior
- This phase is documentation-first, not persistence redesign

## Decision 004

Supabase should be evaluated first as managed Postgres, not as an immediate replacement for the whole architecture.

Reason:
- The lowest-risk evaluation path is infrastructure first
- The current app already speaks Postgres
- Broader Supabase adoption should only be considered after API, auth, and multi-tenant boundaries are clearer

## Decision 005

Next.js should only be introduced after the backend/API surface is better separated from the current Jinja runtime.

Reason:
- A new web frontend without clean API boundaries would duplicate business logic and create drift
- The project should avoid running two competing frontend contracts too early

## Decision 006

React Native is a future-phase concern, not a current implementation target.

Reason:
- Mobile is part of the long-term direction
- The project still needs stronger backend and multi-tenant boundaries before mobile becomes the main delivery focus

## Decision 007

Any future multi-tenant implementation must validate:

- active entity
- owner rules
- permissions
- data separation

Reason:
- The current codebase already depends on entity-aware permission checks
- Tenant isolation failures would be high-risk defects
- Future API, web, and mobile work must inherit the same safety rules

## Decision 008

GSD files are planning artifacts only and must not drive runtime behavior directly.

Reason:
- This keeps planning separate from application logic
- It reduces the risk of accidental behavioral change during documentation phases

## Decision 009

Initial language preference should be stored in session and cookie, with `pt` as fallback, before any user-profile-level persistence is introduced.

Reason:
- This adds low-risk language persistence without requiring a database migration
- It keeps the current authentication model stable in this phase
- It remains compatible with future web and mobile language-preference evolution

## Decision 010

The canonical personal language preference now lives on `users.preferred_language`, while session/cookie remain synchronization and pre-auth bootstrap layers.

Reason:
- Language is a personal user preference, not an entity-level setting
- The login flow already has access to the authenticated user record safely
- This keeps future web and mobile clients aligned on one durable source of truth

## Decision 011

Legacy tables that still exist in PostgreSQL but are no longer present in active metadata must not be silently dropped or silently reintroduced just to satisfy `alembic check`.

Reason:
- These tables may still contain real data
- A green `alembic check` is not worth accidental data loss or accidental feature resurrection
- Each such table needs an explicit keep-or-retire decision before corrective schema work

## Decision 012

Authorization-related legacy tables should default to `indefinida` unless the codebase proves an explicit replacement or explicit retirement path.

Reason:
- Authorization data has higher semantic risk than generic legacy persistence
- Missing code references alone are not enough evidence that authorization records are safe to remove
- This avoids treating sensitive permission data as disposable schema noise

## Decision 013

The current runtime contract for authorization-profile/process visibility flows is `sidebar_menu_settings` plus `members.profile_custom_fields`, not `process_view_authorization_rules`.

Reason:
- Current code reads and writes auth-profile and auth-object records through admin subprocess repositories backed by `profile_custom_fields`
- Current process and subprocess visibility options are resolved dynamically from `sidebar_menu_settings`
- The remaining rows in `process_view_authorization_rules` still have audit value, but the table is no longer the active source of truth

## Decision 014

Legacy authorization rows must not be dropped until their missing semantics are either migrated into the current contract or explicitly archived as accepted loss.

Reason:
- The remaining legacy rows are only partially represented in current auth storage
- Current storage does not yet prove preservation of legacy subprocess granularity, department information, or `entity` scope semantics
- Removing the table before that decision would create avoidable authorization-data loss

## Decision 015

No complementary migration of legacy authorization semantics should be implemented until a human validates whether subprocess, department, and `entity`-scope granularity are still required.

Reason:
- The current codebase proves semantic mismatch, but not the intended business outcome
- A migration designed without that validation would guess at profile equivalence and scope behavior
- Deferring implementation is safer than encoding the wrong authorization model
