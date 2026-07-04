# Alembic Baseline Drift Report

Updated: 2026-07-03

## Scope

This report documents the pre-existing drift between the current SQLAlchemy metadata (`Base.metadata`) and the live PostgreSQL schema tracked by Alembic.

It does not introduce destructive schema cleanup.

## Configuration Notes

- `alembic.ini` points Alembic to `migrations/`
- `migrations/env.py` uses `appverbo.models.Base.metadata` as `target_metadata`
- `scripts/init_db.py` upgrades the database to Alembic `head`
- The runtime is Docker-first, so validation was executed through `docker compose exec web`

## Commands Executed

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic history
docker compose exec db psql -U postgres -d app_igreja -c "select column_name, data_type, is_nullable, column_default from information_schema.columns where table_name in ('process_view_authorization_rules','admin_definitions','songs','users') order by table_name, ordinal_position;"
docker compose exec db psql -U postgres -d app_igreja -c "select tablename, indexname, indexdef from pg_indexes where schemaname = 'public' and tablename in ('process_view_authorization_rules','admin_definitions','songs') order by tablename, indexname;"
docker compose exec db psql -U postgres -d app_igreja -c "select 'process_view_authorization_rules' as table_name, count(*) from process_view_authorization_rules union all select 'admin_definitions', count(*) from admin_definitions union all select 'songs', count(*) from songs;"
docker compose exec web python -c "from fastapi.testclient import TestClient; from appverbo.app import create_app; client=TestClient(create_app()); resp=client.get('/login'); print('GET /login', resp.status_code)"
```

## Alembic Baseline

### `alembic current`

```text
userlang01 (head)
```

### `alembic heads`

```text
userlang01 (head)
```

### `alembic history`

The current repository history is linear through the affected revisions:

```text
... -> admindefs01 -> songs01 -> authview01 -> authview02 -> admindefscope01 -> authview03 -> profilescope01 -> memberuser01 -> memberuser02 -> memberuser03 -> entitynum01 -> systemtype01 -> userlang01
```

This matters because the drift is not caused by an unreachable Alembic branch.  
The affected tables are part of the historical migration chain, but are no longer represented in current metadata.

## `alembic check` Result

Current result after this task:

```text
FAILED: New upgrade operations detected:
- remove_index / remove_table for `songs`
- remove_index / remove_table for `admin_definitions`
- remove_index / remove_table for `process_view_authorization_rules`
```

The previous `users.system_type` default drift is no longer present after metadata alignment in `appverbo/models/user.py`.

## Differences Found

### 1. `process_view_authorization_rules`

- Live DB state:
  - table exists
  - 2 rows
  - 3 secondary indexes
  - foreign keys to `entities` and `users`
  - `visibility_scope_mode` column exists
- Migration origin:
  - `authview01_create_process_view_authorization_rules.py`
  - `authview03_add_visibility_scope_to_authorization_rules.py`
- Metadata state:
  - no active model under `appverbo/models/`
  - repo search found references only in migrations, not in current runtime code
- Probable origin:
  - feature/schema was introduced historically, then removed from metadata/runtime without a cleanup migration
- Risk:
  - medium
  - table contains data, so blind drop would lose records
- Recommendation:
  - do not auto-drop
  - decide explicitly whether this feature is still needed
  - if needed, reintroduce a maintained model/repository/service contract
  - if not needed, export/back up data and create a planned destructive cleanup migration later

### 2. `admin_definitions`

- Live DB state:
  - table exists
  - 57 rows
  - 4 secondary indexes
  - nullable `entity_id` foreign key to `entities`
- Migration origin:
  - `admindefs01_add_admin_definitions_table.py`
  - `admindefscope01_add_entity_scope_to_admin_definitions.py`
- Metadata state:
  - no active model under `appverbo/models/`
  - repo search found references only in migrations, not in current runtime code
- Probable origin:
  - historical admin/config storage persisted in schema after metadata/runtime stopped declaring it
- Risk:
  - high
  - highest row count among the drifted tables
- Recommendation:
  - treat as legacy data until explicit human decision
  - do not recreate active runtime contracts implicitly
  - map ownership/product need first, then choose between feature restoration or archived cleanup

### 3. `songs`

- Live DB state:
  - table exists
  - 1 row
  - 2 secondary indexes
  - check constraints on `lyrics_source` and `lyrics_status`
- Migration origin:
  - `songs01_create_songs_table.py`
- Metadata state:
  - no active model under `appverbo/models/`
  - repo search found references only in migrations, not in current runtime code
- Probable origin:
  - abandoned or not-yet-finished feature removed from active metadata without schema retirement
- Risk:
  - low to medium
  - only 1 row, but still existing user data
- Recommendation:
  - same pattern as above: document, decide, then either restore intentionally or retire with backup and explicit migration

### 4. `users.system_type`

- Live DB state:
  - `users.system_type` exists
  - database default is `'default'`
- Migration origin:
  - `systemtype01_add_system_type_to_users.py`
- Metadata state before this task:
  - model declared Python-side `default="default"` but not `server_default="default"`
- Probable origin:
  - metadata drift, not schema drift
- Risk:
  - low
- Recommendation:
  - resolved safely by aligning the model with the historical migration/database default

## Safe Alignment Applied In This Task

One small non-destructive metadata alignment was applied:

- `appverbo/models/user.py`
  - `system_type` now declares `server_default="default"` to match:
    - migration `systemtype01`
    - live PostgreSQL schema

This change does not mutate existing data and does not change runtime behavior.

## What Was Not Altered

- No table was dropped
- No column was dropped
- No destructive downgrade was created
- No legacy data was deleted
- No login/auth behavior was changed
- No Docker config was changed
- No migration was created for destructive cleanup

## Why No Corrective Migration Was Created

The remaining drift is not a simple missing-column case.

It reflects three legacy tables that:

- still exist in the live database
- still contain data
- are still part of historical Alembic revisions
- are no longer represented in active metadata/runtime code

Creating a “fix” without product intent would force one of two risky paths:

- silently reintroducing legacy tables into active metadata as if they were current features
- or dropping real tables/data to satisfy `alembic check`

Neither is safe to do automatically in this task.

## Risks

- `alembic check` remains red until the three legacy tables get an explicit disposition
- future developers may misread the red `alembic check` as a regression unless this baseline is documented
- the legacy tables still hold real data, especially `admin_definitions`
- if these tables are actually still needed, the current codebase has already lost an explicit model/runtime contract for them

## Recommended Next Step

Run a focused follow-up decision task with one explicit goal:

1. Decide table-by-table whether each legacy table is:
   - an active feature to be restored into maintained metadata/code
   - or a retired feature to be archived and removed deliberately
2. Only then:
   - add maintained models for the surviving tables
   - or create a planned destructive cleanup migration with backup/export steps
