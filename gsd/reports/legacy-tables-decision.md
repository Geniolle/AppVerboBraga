# Legacy Tables Decision Report

Updated: 2026-07-03

## Scope

This report classifies the legacy tables that:

- still exist in PostgreSQL
- still exist in historical Alembic revisions
- do not currently have active metadata in `appgenesis/models/`

Tables analyzed:

- `songs`
- `admin_definitions`
- `process_view_authorization_rules`

## Commands Executed

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic history
docker compose exec db psql -U postgres -d app_igreja -c "select 'songs' as table_name, count(*) as total_rows, min(created_at) as min_created_at, max(created_at) as max_created_at, min(updated_at) as min_updated_at, max(updated_at) as max_updated_at from songs union all select 'admin_definitions', count(*), min(created_at), max(created_at), min(updated_at), max(updated_at) from admin_definitions union all select 'process_view_authorization_rules', count(*), min(created_at), max(created_at), min(updated_at), max(updated_at) from process_view_authorization_rules;"
docker compose exec db psql -U postgres -d app_igreja -c "select tablename, indexname, indexdef from pg_indexes where schemaname = 'public' and tablename in ('process_view_authorization_rules','admin_definitions','songs') order by tablename, indexname;"
docker compose exec db psql -U postgres -d app_igreja -c "select table_name, column_name, data_type, is_nullable, column_default from information_schema.columns where table_name in ('process_view_authorization_rules','admin_definitions','songs') order by table_name, ordinal_position;"
docker compose exec db psql -U postgres -d app_igreja -c "select e.id, e.name, e.profile_scope, e.is_active from entities e where e.id in (select distinct entity_id from songs where entity_id is not null union select distinct entity_id from admin_definitions where entity_id is not null union select distinct entity_id from process_view_authorization_rules where entity_id is not null) order by e.id;"
docker compose exec db psql -U postgres -d app_igreja -c "select id, entity_id, name, version, lyrics_source, lyrics_status, is_active, created_at, updated_at from songs order by id limit 10;"
docker compose exec db psql -U postgres -d app_igreja -c "select id, entity_id, parameter_name, parameter_type, process_name, subprocess_name, status, created_at, updated_at from admin_definitions order by id limit 20;"
docker compose exec db psql -U postgres -d app_igreja -c "select id, entity_id, profile_name, process_key, process_label, subprocess_key, subprocess_label, department_name, status, visibility_scope_mode, created_at, updated_at from process_view_authorization_rules order by id limit 20;"
docker compose exec web python -c "from fastapi.testclient import TestClient; from appgenesis.app import create_app; client=TestClient(create_app()); resp=client.get('/login'); print('GET /login', resp.status_code)"
```

## Repository Search Summary

### Direct table-name usage

- `songs`
  - found only in Alembic migration files
- `admin_definitions`
  - found only in Alembic migration files
- `process_view_authorization_rules`
  - found only in Alembic migration files

### Indirect functional clues

- `tesouraria` and `Importar extrato`
  - current seed/module direction still includes a Tesouraria module and route placeholders in `scripts/modules/seed_app_modules.py`
- `musicas`
  - current tests still mention the menu key `musicas`
- `Perfil de autorização`
  - the product/runtime still has active profile-authorization flows, but not backed by `process_view_authorization_rules` in current metadata
- `admin_definitions` sample values
  - data looks like visual/admin configuration tokens such as `ABA GERAL`, `BARRA LATERAL`, menu icons, colors, sizes, and fonts

## Database Summary

### Row counts and dates

| table | rows | created_at range | updated_at range |
|---|---:|---|---|
| `songs` | 1 | 2026-06-02 11:50:27 UTC | 2026-06-02 11:50:27 UTC |
| `admin_definitions` | 57 | 2026-05-18 09:35:07 UTC to 2026-06-11 16:32:18 UTC | 2026-05-18 20:37:29 UTC to 2026-06-11 16:53:15 UTC |
| `process_view_authorization_rules` | 2 | 2026-06-16 12:06:29 UTC to 2026-06-16 13:38:34 UTC | 2026-06-16 12:06:29 UTC to 2026-06-16 13:39:27 UTC |

### Entity linkage

- `songs`
  - all rows linked to `entity_id = 8`
- `process_view_authorization_rules`
  - all rows linked to `entity_id = 8`
- `admin_definitions`
  - all 57 rows have `entity_id = NULL`

Referenced entity:

- `entity_id = 8`
  - name: `Deixa Estar Tech`
  - `profile_scope = owner`
  - active

## Classification

### 1. `songs`

- Classification:
  - `indefinida`
- Why:
  - there is no active model/repository/service/route using the table directly
  - the table still contains real data
  - the broader concept `musicas` still appears in current tests and old admin-definition data
  - the feature may be abandoned, paused, or partially migrated, but that is not provable from current code alone
- Current DB structure:
  - entity-scoped
  - has lifecycle-ish fields (`is_active`, timestamps)
  - has domain-specific check constraints for lyrics source/status
- Data snapshot:
  - 1 active row
  - `lyrics_source = audio_transcription`
  - `lyrics_status = rascunho`
- Removal risk:
  - medium
  - low volume, but definitely real data
- Recommendation:
  - do not remove now
  - treat as unresolved feature storage until product intent is explicit
- Next action:
  - decide whether `Músicas` is still a planned module
  - if yes, reintroduce model/runtime intentionally
  - if not, archive and later retire via planned destructive migration

### 2. `admin_definitions`

- Classification:
  - `legada`
- Why:
  - direct table usage disappeared from active code
  - sample rows look like historic visual/admin configuration storage
  - the current project now has other configuration directions (`sidebar_menu_settings`, module seeds, templates, CSS, shared JS)
  - `entity_id` was added historically but never populated in current data, which suggests the legacy design stopped evolving
- Current DB structure:
  - global-style config table
  - 57 rows
  - all rows `status = active`
  - all rows `entity_id = NULL`
- Data snapshot:
  - parameters like `ABA GERAL`, `BARRA LATERAL`, icon entries for menu/process items, colors, fonts, sizes
- Removal risk:
  - medium to high
  - the data volume is significant enough that silent deletion would be reckless
  - but the absence of runtime readers strongly suggests legacy persistence
- Recommendation:
  - keep only as documented legacy until an owner confirms it is no longer needed
  - do not reintroduce as active metadata by default
- Next action:
  - confirm with product/owner whether any current screen still depends on these values indirectly
  - if confirmed unused, export and schedule retirement

### 3. `process_view_authorization_rules`

- Classification:
  - `indefinida`
- Why:
  - there is no active model/runtime contract for the table today
  - the table name and rows are directly related to authorization and visibility, which is a high-risk domain
  - the current product still has active `Perfil de autorização` flows and a current Tesouraria direction
  - the sample rows look like real business rules, not generic noise
- Current DB structure:
  - entity-scoped
  - status-controlled
  - audit timestamps
  - foreign keys to `entities` and `users`
  - `visibility_scope_mode`
- Data snapshot:
  - 2 active rows
  - entity 8
  - profile `Tesouraria`
  - process label `Extrato`
  - subprocess labels `Importar extrato` and `Dados de extrato`
- Removal risk:
  - high
  - the table touches authorization semantics and live business labels
- Recommendation:
  - do not remove
  - do not call it obsolete
  - require a focused authorization-design decision first
- Next action:
  - trace whether these rules were superseded by another authorization mechanism or simply abandoned in code
  - if the feature is still valid, restore explicit metadata/service ownership

## What Was Not Changed

- No table was altered
- No row was altered
- No migration was created
- No functional code was changed
- No login/auth flow was changed

## Decision Summary

- `songs`
  - keep for now
  - classification: `indefinida`
- `admin_definitions`
  - keep for now as documented legacy
  - classification: `legada`
- `process_view_authorization_rules`
  - keep for now
  - classification: `indefinida`

No table is safe to remove in this task.

## Recommended Next Task

Create a follow-up decision task focused on one of these two paths:

1. `Task 007 — Restore explicit contracts for legacy tables that are still strategically needed`
2. `Task 007 — Archive and retire confirmed-unused legacy tables with backup/export plan`

The first candidate for a human decision is `process_view_authorization_rules`, because it has the highest semantic risk.
