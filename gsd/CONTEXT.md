# GSD Context

Updated: 2026-07-03

## Purpose

This folder gives Codex and future contributors a stable planning baseline for AppGenesis without changing runtime behavior.

## Current Stack

- Backend: Python 3.12
- Web framework: FastAPI
- Templating/UI shell: Jinja templates plus server-rendered HTML
- Frontend assets: static CSS and JavaScript loaded from `static/`
- ORM and data access: SQLAlchemy 2.x
- Database migrations: Alembic
- Main database: PostgreSQL via `psycopg`
- Runtime orchestration: Docker and `docker compose`
- App server: Uvicorn

## Current Application Shape

- Main application package: `appgenesis/`
- App factory: `appgenesis/app.py`
- Legacy/shared runtime entrypoints still exist through `web_app.py` and `appgenesis/core.py`
- Route groups are organized by domain under `appgenesis/routes/`
- Shared business logic lives mainly in `appgenesis/services/`
- Reusable data access helpers live in `appgenesis/repositories/`
- SQLAlchemy models live in `appgenesis/models/`
- Server-rendered templates live in `templates/`
- Static assets live in `static/`
- Tests live in `tests/`
- Existing project documentation already lives in `docs/`

## Authentication And Session Model

- Session-based web authentication is active through `SessionMiddleware`
- The project supports local login and signup flows
- There is an admin login path in addition to the regular login path
- User invitation and activation flows exist
- OAuth providers currently referenced in the project:
  - Google
  - Microsoft
  - GitHub
- SMTP-backed email flows are already part of the current system
- WhatsApp verification is also part of the current authentication/profile ecosystem

## Entities, Profiles And Permissions

- The project is entity-aware and already stores an active entity context in session
- `Entity` uses profile scope concepts such as `owner` and `legado`
- Current permission logic is centralized around service-layer checks
- Current permission vocabulary observed in the codebase includes:
  - `can_manage_tenant_structure`
  - `can_manage_all_entities`
  - `allowed_structure_entity_ids`
  - `allowed_data_entity_ids`
- Multi-tenant safety already depends on validating the active entity, user scope, and allowed entity ids before reading or mutating data

## Modules And Menu Direction

- A future modular architecture is already present in the data model through:
  - `app_modules`
  - `sidebar_menu_items`
  - `entity_module_entitlements`
- At the same time, the current menu/configuration runtime still relies heavily on `sidebar_menu_settings`
- This means the project currently carries both:
  - a legacy/configuration-driven sidebar path
  - a newer module-entitlement direction

## Current UI Direction

- The current frontend is still primarily server-rendered
- The main administrative shell is Jinja-based and enhanced with shared JavaScript modules
- A significant amount of workflow logic is still coupled to the current FastAPI + Jinja runtime

## Web And Mobile Direction

- The current production-facing web application remains the main delivery surface
- A directory named `appverbo-mobile/` exists in the repository, but it is not the primary application runtime in this phase
- The long-term direction is to support both web and mobile, but the current source of truth remains the existing web stack

## Why GSD Core Is Being Added

- To capture architectural context in one predictable place
- To preserve decisions between AI-assisted implementation sessions
- To separate planning state from runtime code
- To support future work such as:
  - login internationalization
  - stronger multi-tenant boundaries
  - API separation
  - managed Postgres evaluation
  - future web/mobile expansion
