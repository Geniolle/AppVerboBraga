# ADR-002: Legacy Tables Preservation

Status: proposed
Updated: 2026-07-05

## Context

The repository contains three legacy tables: `songs`, `admin_definitions`, and `process_view_authorization_rules`. 
These tables exist in the historical database schema and Alembic migrations, but they are no longer defined in `appgenesis/models/`.

Running `alembic check` failed because Alembic detected these tables in the live database but not in the code models, triggering automatic table removal suggestions.

Reconciliation and analysis shows:
- `songs` contains active song transcription records.
- `process_view_authorization_rules` contains active authorization rule records with legacy semantics.
- `admin_definitions` contains 57 rows of active layout/style settings.

Silent deletion or modification of these tables poses a high risk of data loss.

## Decision

We will preserve these tables in the live PostgreSQL database for audit and potential future use. 

To resolve the autogenerate baseline drift, we configure Alembic's `include_object` context callback in `migrations/env.py` to explicitly ignore these three tables. This maintains schema validation integrity without destructive modifications.

## Consequences

- `alembic check` passes successfully with `No new upgrade operations detected`.
- No active metadata or code runtime is affected.
- Legacy table rows remain fully preserved and queryable.
