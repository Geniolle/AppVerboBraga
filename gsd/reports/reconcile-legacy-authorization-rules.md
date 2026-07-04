# Reconcile Legacy Authorization Rules Report

Updated: 2026-07-03

## Scope

This report reconciles the 2 legacy rows in `process_view_authorization_rules` against the current authorization storage in `members.profile_custom_fields`.

Current storage keys analyzed:

- `process_records__perfil_de_autorizacao`
- `process_records__objeto_de_autorizacao`

## Commands Executed

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec db psql -U postgres -d app_igreja -c "select id, entity_id, profile_name, process_label, subprocess_label, department_name, status, visibility_scope_mode, created_by_user_id, updated_by_user_id from process_view_authorization_rules order by id;"
docker compose exec db psql -U postgres -d app_igreja -c "select count(*) as legacy_rows from process_view_authorization_rules; select count(*) as profile_json_rows from members where coalesce(profile_custom_fields,'') like '%process_records__perfil_de_autorizacao%'; select count(*) as object_json_rows from members where coalesce(profile_custom_fields,'') like '%process_records__objeto_de_autorizacao%';"
docker compose exec db psql -U postgres -d app_igreja -c "with src as (select u.id as user_id, u.login_email, m.profile_custom_fields::jsonb as fields from users u join members m on m.id = u.member_id where coalesce(m.profile_custom_fields,'') like '%process_records__perfil_de_autorizacao%') select src.user_id, src.login_email, rec->>'record_id' as record_id, rec->>'section_key' as section_key, rec->'values'->>'__menu_key' as menu_key, rec->'values'->>'custom_perfil' as custom_perfil, rec->'values'->>'custom_nome_do_perfil' as custom_nome_do_perfil, rec->'values'->>'custom_perfil_2' as custom_perfil_2, rec->'values'->>'__estado' as estado, rec->'values'->>'__scope_mode' as scope_mode from src cross join lateral jsonb_array_elements(((src.fields ->> 'process_records__perfil_de_autorizacao')::jsonb)) rec order by src.user_id, rec->>'record_id';"
docker compose exec db psql -U postgres -d app_igreja -c "with src as (select u.id as user_id, u.login_email, m.profile_custom_fields::jsonb as fields from users u join members m on m.id = u.member_id where coalesce(m.profile_custom_fields,'') like '%process_records__objeto_de_autorizacao%') select src.user_id, src.login_email, rec->>'record_id' as record_id, rec->>'section_key' as section_key, rec->'values'->>'__key' as object_key, rec->'values'->>'objeto_de_autorizacao' as objeto_de_autorizacao, rec->'values'->>'custom_objeto_label' as custom_objeto_label, rec->'values'->>'custom_nome_do_perfil' as custom_nome_do_perfil, rec->'values'->>'custom_processo' as custom_processo, rec->'values'->>'processo_label' as processo_label, rec->'values'->>'custom_subprocesso' as custom_subprocesso, rec->'values'->>'autorizacao_label' as autorizacao_label, rec->'values'->>'custom_autorizacao' as custom_autorizacao, rec->'values'->>'__estado' as estado, rec->'values'->>'__scope_mode' as scope_mode from src cross join lateral jsonb_array_elements(((src.fields ->> 'process_records__objeto_de_autorizacao')::jsonb)) rec order by src.user_id, rec->>'record_id';"
docker compose exec db psql -U postgres -d app_igreja -c "with profiles as (select u.id as user_id, u.login_email, rec->'values' as v from users u join members m on m.id = u.member_id cross join lateral jsonb_array_elements(((m.profile_custom_fields::jsonb ->> 'process_records__perfil_de_autorizacao')::jsonb)) rec where coalesce(m.profile_custom_fields,'') like '%process_records__perfil_de_autorizacao%'), objects as (select u.id as user_id, u.login_email, rec->'values' as v from users u join members m on m.id = u.member_id cross join lateral jsonb_array_elements(((m.profile_custom_fields::jsonb ->> 'process_records__objeto_de_autorizacao')::jsonb)) rec where coalesce(m.profile_custom_fields,'') like '%process_records__objeto_de_autorizacao%') select 'profile_exact_tesouraria' as check_name, count(*) from profiles where coalesce(v->>'custom_perfil','') = 'Tesouraria' or coalesce(v->>'custom_nome_do_perfil','') = 'Tesouraria' union all select 'object_exact_tesouraria', count(*) from objects where coalesce(v->>'objeto_de_autorizacao','') = 'Tesouraria' or coalesce(v->>'custom_objeto_label','') = 'Tesouraria' or coalesce(v->>'custom_nome_do_perfil','') = 'Tesouraria' union all select 'object_process_extrato', count(*) from objects where lower(coalesce(v->>'custom_processo','')) = 'extrato' or lower(coalesce(v->>'processo_label','')) = 'extrato' union all select 'object_subprocess_importar_extrato', count(*) from objects where coalesce(v->>'custom_subprocesso','') in ('Importar extrato','custom_importar_extrato_header') or coalesce(v->>'autorizacao_label','') = 'Importar extrato' union all select 'object_subprocess_dados_extrato', count(*) from objects where coalesce(v->>'custom_subprocesso','') in ('Dados de extrato','custom_dados_de_extrato') or coalesce(v->>'autorizacao_label','') = 'Dados de extrato';"
docker compose exec web python -c "from appverbo.db import SessionLocal; from appverbo.menu_settings import get_sidebar_menu_settings; from appverbo.services.process_tabs import resolve_process_tab_options_v1; s=SessionLocal(); rows=get_sidebar_menu_settings(s); print(resolve_process_tab_options_v1('extrato', rows, visible_sidebar_menu_keys={'extrato','perfil_de_autorizacao','tesouraria','home','administrativo','empresa','meu_perfil','sessoes','calendario'})); s.close()"
docker compose exec web python -c "from fastapi.testclient import TestClient; from appverbo.app import create_app; client=TestClient(create_app()); resp=client.get('/login'); print(resp.status_code)"
```

## Current Runtime Contract Recap

The current authorization flow no longer reads `process_view_authorization_rules`.

Current persistence lives in:

- auth-profile records:
  - `process_records__perfil_de_autorizacao`
- auth-object records:
  - `process_records__objeto_de_autorizacao`

Current runtime resolution lives in:

- `appverbo/admin_subprocesses/repositories/auth_profile_repository.py`
- `appverbo/admin_subprocesses/repositories/objeto_autorizacao_repository.py`
- `appverbo/services/profile.py`
- `appverbo/services/process_tabs.py`
- `appverbo/services/page.py`

## Legacy Rows

### Legacy row 11

- `id = 11`
- `entity_id = 8`
- `profile_name = Tesouraria`
- `process_label = Extrato`
- `subprocess_label = Importar extrato`
- `department_name = Todos os departamentos`
- `status = active`
- `visibility_scope_mode = entity`

### Legacy row 12

- `id = 12`
- `entity_id = 8`
- `profile_name = Tesouraria`
- `process_label = Extrato`
- `subprocess_label = Dados de extrato`
- `department_name = ""`
- `status = active`
- `visibility_scope_mode = entity`

## Current Storage Found

### `process_records__perfil_de_autorizacao`

Current rows found:

- `admin@appverbo.local`
  - `Gestor de Tesouraria`
  - `Calendario Geral`
- `verbodavidabraga@gmail.com`
  - `Músicas`

Important observations:

- there is no current auth-profile row with exact label `Tesouraria`
- current live row closest to the legacy domain is `Gestor de Tesouraria`
- the current stored profile rows do not carry an exact legacy menu/profile name match

### `process_records__objeto_de_autorizacao`

Current rows found:

- `admin@appverbo.local`
  - object key: `gestor_de_tesouraria`
  - object label: `Gestor de Tesouraria`
  - linked profile label: `Gestor de Tesouraria`
  - process: `extrato`
  - subprocess: `custom_extratos_bancarios`
  - authorization: `Todas autorizações`
  - state: `ativo`
  - scope: `all`

Important observations:

- there is no current object row with exact label `Tesouraria`
- there is one current object row with `process = extrato`
- there are no current object rows matching:
  - `Importar extrato`
  - `Dados de extrato`

## Structure Differences

The legacy table stores one row per authorization target:

- profile name
- process label
- subprocess label
- department name
- status
- visibility scope

The current object storage is structurally different:

- one object row can represent a broader authorization
- subprocess is stored as a single field inside record `values`
- current object row stores `custom_autorizacao = Todas autorizações`
- department is not present in the current object row found
- current scope is `all`, not `entity`

This means the current storage is not a 1:1 row-model replacement for the legacy table.

## Reconciliation Matrix

### Legacy row 11

Registo legado  
`Tesouraria` -> `Extrato` -> `Importar extrato`

Destino atual  
Closest current destination:

- auth-profile row:
  - `Gestor de Tesouraria`
- auth-object row:
  - object label `Gestor de Tesouraria`
  - process `extrato`
  - subprocess `custom_extratos_bancarios`
  - authorization `Todas autorizações`

Estado  
- `Parcial`

Why:

- process domain matches only partially (`Extrato` -> `extrato`)
- there is no exact profile label match (`Tesouraria` is missing)
- there is no exact subprocess match for `Importar extrato`
- `department_name = Todos os departamentos` is not present in current storage
- scope changed from `entity` to `all`
- the current object row is broader than the legacy row

### Legacy row 12

Registo legado  
`Tesouraria` -> `Extrato` -> `Dados de extrato`

Destino atual  
Closest current destination:

- auth-profile row:
  - `Gestor de Tesouraria`
- auth-object row:
  - object label `Gestor de Tesouraria`
  - process `extrato`
  - subprocess `custom_extratos_bancarios`
  - authorization `Todas autorizações`

Estado  
- `Parcial`

Why:

- process domain matches only partially (`Extrato` -> `extrato`)
- there is no exact profile label match (`Tesouraria` is missing)
- there is no exact subprocess match for `Dados de extrato`
- current storage keeps a single broader object row rather than one row per subprocess
- scope changed from `entity` to `all`

## Was Migration Complete?

No.

The legacy information was not fully reconciled into the current storage.

## What Appears To Be Missing Or Transformed

- exact legacy profile name `Tesouraria`
- exact subprocess granularity:
  - `Importar extrato`
  - `Dados de extrato`
- exact department value:
  - `Todos os departamentos`
- exact legacy scope:
  - `entity`
- exact 2-row shape of the old authorization rules

What exists instead:

- one broader current object record
- one broader current authorization mode:
  - `Todas autorizações`
- one broader current subprocess value:
  - `custom_extratos_bancarios`

## Additional Read-Only Evidence

The current generic tab resolver probe for `Extrato` returned:

- `custom_extratos_bancarios`
  - label: `Extratos bancários`

It did not return separate current options for:

- `Importar extrato`
- `Dados de extrato`

That supports the conclusion that current storage/configuration is broader than the legacy row model.

## Risk Assessment

Risk of dropping `process_view_authorization_rules` now:

- high

Reason:

- the table is not used in runtime
- but its remaining data is only partially represented in current storage
- dropping it now would discard:
  - exact subprocess-level legacy intent
  - department-level information
  - legacy scope semantics

## Is Complementary Data Migration Needed?

Yes, if the project wants to preserve the business meaning before future removal.

A future complementary data migration should decide whether to:

1. split current broader object records into finer-grained modern records
2. preserve legacy subprocess and department details in a new normalized current contract
3. export the 2 legacy rows as audit/archive evidence if the finer granularity is intentionally being abandoned

This task does not implement that migration.

## Final Recommendation

Do not remove `process_view_authorization_rules` yet.

Current status of the 2 legacy rows:

- row 11: `Parcial`
- row 12: `Parcial`

The safe next step is a focused design task to choose one of these paths:

1. migrate missing legacy semantics into the current storage model
2. explicitly accept loss of old granularity and archive/export the 2 rows before removal

## What Was Not Changed

- No table was altered
- No column was altered
- No row was altered
- No migration was created
- No functional code was changed

## Recommended Next Task

`Task 009 — Plano de migração complementar ou arquivo para regras legadas de autorização`

Goal:

- decide whether legacy subprocess and department semantics must survive
- define the exact target contract for those fields
- prepare a safe migration/export plan before any destructive cleanup
