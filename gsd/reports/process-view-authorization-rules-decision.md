# Process View Authorization Rules Decision Report

Updated: 2026-07-03

## Scope

This report determines whether `process_view_authorization_rules` is still part of the active AppGenesis runtime or whether it has already been replaced by another authorization/profile configuration path.

## Commands Executed

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec db psql -U postgres -d app_igreja -c "select column_name, data_type, is_nullable, column_default from information_schema.columns where table_name = 'process_view_authorization_rules' order by ordinal_position;"
docker compose exec db psql -U postgres -d app_igreja -c "select id, entity_id, profile_name, process_key, process_label, subprocess_key, subprocess_label, department_name, status, visibility_scope_mode, legacy_record_id, created_by_user_id, updated_by_user_id, created_at, updated_at from process_view_authorization_rules order by id;"
docker compose exec db psql -U postgres -d app_igreja -c "select count(*) as matching_users from users u join members m on m.id = u.member_id where coalesce(m.profile_custom_fields,'') ilike '%Gestor de Tesouraria%' or coalesce(m.profile_custom_fields,'') ilike '%Extrato%' or coalesce(m.profile_custom_fields,'') ilike '%Importar extrato%' or coalesce(m.profile_custom_fields,'') ilike '%Dados de extrato%';"
docker compose exec db psql -U postgres -d app_igreja -c "select id, menu_label, is_active, is_deleted from sidebar_menu_settings where lower(menu_label) in ('extrato','tesouraria','perfil de autorização') or lower(menu_key) in ('extrato','tesouraria','perfil_de_autorizacao') order by id;"
docker compose exec web python -c "from appgenesis.db import SessionLocal; from appgenesis.services.page import get_page_data; s=SessionLocal(); data=get_page_data(s, actor_user_id=1, actor_login_email='admin@appverbo.local', selected_entity_id=8); item=next(row for row in data['sidebar_menu_settings'] if str(row.get('key') or '').strip().lower()=='perfil_de_autorizacao'); print(item.get('process_additional_fields')); s.close()"
docker compose exec web python -c "from appgenesis.db import SessionLocal; from appgenesis.models import Member, User; from sqlalchemy import select; from appgenesis.services.profile import parse_member_profile_fields, parse_menu_process_records, build_menu_process_records_storage_key; s=SessionLocal(); row=s.execute(select(User.login_email, Member.profile_custom_fields).join(Member, Member.id==User.member_id).where(User.id==1)).one(); fields=parse_member_profile_fields(row.profile_custom_fields); print(parse_menu_process_records(fields.get(build_menu_process_records_storage_key('perfil_de_autorizacao')))); print(parse_menu_process_records(fields.get(build_menu_process_records_storage_key('objeto_de_autorizacao')))); s.close()"
docker compose exec web python -c "from fastapi.testclient import TestClient; from appgenesis.app import create_app; client=TestClient(create_app()); resp=client.get('/login'); print(resp.status_code)"
```

## Static Repository Findings

### 1. Direct usage of the table

- No current model exists for `process_view_authorization_rules`
- No current repository, service, route, or template reads the table directly
- Current direct references are limited to Alembic migrations

### 2. Current runtime contract that replaced it

The active authorization/profile configuration flow now lives in:

- `sidebar_menu_settings`
  - current process and tab metadata
  - current visibility-scope metadata for menus and sections
- `members.profile_custom_fields`
  - persisted history records under keys like:
    - `process_records__perfil_de_autorizacao`
    - `process_records__objeto_de_autorizacao`
- admin subprocess repositories
  - `appgenesis/admin_subprocesses/repositories/auth_profile_repository.py`
  - `appgenesis/admin_subprocesses/repositories/objeto_autorizacao_repository.py`
- list and tab resolvers
  - `appgenesis/services/profile.py`
  - `appgenesis/services/page.py`
  - `appgenesis/services/process_tabs.py`

### 3. Evidence of substitution in code

- `auth_profile_repository.py`
  - reads and writes authorization-profile records from `member.profile_custom_fields`
  - persists them with `build_menu_process_records_storage_key('perfil_de_autorizacao')`
- `objeto_autorizacao_repository.py`
  - reads and writes authorization-object records from `member.profile_custom_fields`
  - derives `process_label` and `authorization_label` from stored record `values`
- `services/profile.py`
  - `resolve_field_list_options_v1()` resolves:
    - `active_menus`
    - `profile_menu_tabs`
  - `_resolve_profile_menu_tabs_list_options_v1()` maps the selected process/profile to current tabs via `resolve_process_tab_options_v1()`
- `services/page.py`
  - builds `menu_process_history_map` from `profile_custom_fields`
  - decorates current sidebar/menu field definitions with resolved list options at runtime

### 4. What the old migration shows

`authview01_create_process_view_authorization_rules.py` proves the table was originally introduced as a bridge away from `members.profile_custom_fields`, not as a completely independent domain model.

The migration:

- created `process_view_authorization_rules`
- then backfilled it from `members.profile_custom_fields`
- extracted:
  - `custom_perfil`
  - `custom_processo`
  - `custom_subprocesso`
  - `custom_departamento`
  - `__estado`

That matters because the present codebase has effectively moved back to a `profile_custom_fields`-centric contract for these admin authorization flows.

## Database Findings

### Table structure

Current columns:

- `entity_id`
- `profile_name`
- `process_key`
- `process_label`
- `subprocess_key`
- `subprocess_label`
- `department_name`
- `status`
- `visibility_scope_mode`
- `legacy_record_id`
- audit columns and user references

### Current rows

There are 2 rows:

1. `Tesouraria` / `Extrato` / `Importar extrato`
2. `Tesouraria` / `Extrato` / `Dados de extrato`

Shared properties:

- `entity_id = 8`
- `status = active`
- `visibility_scope_mode = entity`
- `created_by_user_id = 1`
- `updated_by_user_id = 1`

### Do the rows still make semantic sense?

Yes.

The referenced process still exists:

- `sidebar_menu_settings` still contains active `Perfil de autorização`
- `sidebar_menu_settings` still contains active `Extrato`

The referenced subprocess labels also still correspond to current process-tab concepts:

- `Importar extrato`
- `Dados de extrato`

Current `Extrato` menu configuration for entity `8` still exposes header/tab keys equivalent to those labels:

- `custom_importar_extrato_header`
- `custom_dados_de_extrato`

## Comparison With Current Runtime Data

### Current active storage found

For `admin@appverbo.local`, current profile storage already contains:

- `process_records__perfil_de_autorizacao`
  - examples:
    - `Calendario Geral`
    - `Gestor de Tesouraria`
- `process_records__objeto_de_autorizacao`
  - example:
    - profile label: `Gestor de Tesouraria`
    - process: `extrato`
    - authorization: `Todas autorizações`
    - subprocess: `custom_extratos_bancarios`

### Important mismatch

The legacy table rows are not mirrored 1:1 in current active storage.

Examples:

- legacy table uses `profile_name = Tesouraria`
- current active profile storage uses labels such as `Gestor de Tesouraria`
- legacy table stores two subprocess labels:
  - `Importar extrato`
  - `Dados de extrato`
- current active authorization-object sample stores:
  - `custom_subprocesso = custom_extratos_bancarios`

This strongly suggests:

- the table is not active runtime storage anymore
- but its remaining rows cannot be assumed to be fully migrated into the new contract

## Answers To The Decision Questions

### Is the table still used by current code?

No.

No active runtime path reads `process_view_authorization_rules` directly.

### Is there substitute logic?

Yes.

The current replacement contract is:

- menu/process/tab definitions from `sidebar_menu_settings`
- authorization/profile records stored in `members.profile_custom_fields`
- runtime list resolution in `appgenesis/services/profile.py`
- admin subprocess repositories for `perfil_de_autorizacao` and `objeto_de_autorizacao`

### Do the existing rows still make sense?

Yes.

They still point to an existing process (`Extrato`) and to tab concepts that still exist in current menu configuration.

### Is there removal risk?

High.

The table is unused by code, but it still contains authorization data that was not proven to be migrated exactly into the current contract.

### Should it regain a model?

Not now.

There is not enough evidence that the current runtime wants this table back as its source of truth.

### Should it regain a service/repository?

Not now.

A read-only reconciliation script or report would be safer than reactivating it as live runtime state.

### Should it remain documented as legacy?

Yes.

That is the safest current classification.

## Final Classification

- `process_view_authorization_rules`
  - `legada`

## Final Recommendation

Treat `process_view_authorization_rules` as a legacy authorization snapshot that was superseded by the current `sidebar_menu_settings` + `members.profile_custom_fields` runtime contract.

Do not:

- drop it now
- reintroduce it as active metadata now
- assume its remaining rows are already reconciled with current auth-profile/auth-object storage

Instead:

1. Keep it documented as legacy
2. Compare its 2 rows against current `perfil_de_autorizacao` and `objeto_de_autorizacao` records
3. Decide whether the remaining information should be:
   - migrated into current storage
   - exported as audit evidence
   - or retired later by planned destructive migration

## If Reintroduction Were Ever Chosen Later

The likely files would be:

- `appgenesis/models/process_view_authorization_rule.py`
- `appgenesis/repositories/process_view_authorization_rule_repository.py`
- `appgenesis/services/process_view_authorization_rules.py`
- integration points in admin/profile routes or services

This is not recommended in the current task because it would revive a table that the current runtime has already replaced.

## What Was Not Changed

- No table was altered
- No row was altered
- No migration was created
- No functional code was changed
- No login/auth behavior was changed

## Recommended Next Task

`Task 008 — Reconciliar regras legadas de autorização com o storage atual`

Goal:

- compare the 2 legacy rows against current `process_records__perfil_de_autorizacao` and `process_records__objeto_de_autorizacao`
- determine whether any business meaning is still missing from current storage
- prepare an export/migration/retirement plan before any future drop
