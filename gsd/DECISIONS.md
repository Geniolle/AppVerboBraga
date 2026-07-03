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
