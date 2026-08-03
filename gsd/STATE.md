# GSD State

Updated: 2026-07-06

## Current Known State

- AppGenesis is currently a FastAPI web application with Jinja templates and shared frontend JavaScript
- PostgreSQL is the main database in the Docker-first runtime
- SQLAlchemy and Alembic are already part of the stack
- The repository already has a meaningful `docs/` area, but did not yet have a dedicated GSD Core planning area
- The main application code is centered in `appgenesis/`
- The repository also contains `tests/`, Docker files, bootstrap/init scripts, and a mobile-related directory
- Initial login multi-language support now exists for `pt`, `en`, `es`, and `fr` using JSON translations plus cookie/session persistence
- Authenticated users can now persist `preferred_language` on `users`, while pre-login language selection still uses session/cookie as bootstrap
- Alembic baseline drift has now been documented; `users.system_type` metadata drift was normalized, while legacy table drift remains for `songs`, `admin_definitions`, and `process_view_authorization_rules`
- Legacy-table classification is now documented: `admin_definitions` and `process_view_authorization_rules` are currently treated as `legada`; `songs` remains `indefinida`
- Focused review of `process_view_authorization_rules` is now documented; the table is treated as `legada`, with the current runtime contract living in `sidebar_menu_settings` plus `members.profile_custom_fields`
- Reconciliation of legacy authorization rows is now documented; the 2 remaining `process_view_authorization_rules` rows are only `Parcial` in relation to current auth storage
- Migration-versus-archive planning for legacy authorization semantics is now documented; the final path remains pending human validation
- Authorization-profile creation/editing now includes `Entidade`, with owner-only global scope and active-entity filtering for profile rows
- Objeto de Autorização rows are now filtered by active entity on read, and save-time key-collision checks are scoped per entity for both Objetos and Perfis (Decision 017, Task 011); confirmed as a real cross-entity leak fix, not a hardening measure
- `sidebar_menu_settings` is confirmed as the next multi-tenant gap: it is a fully global table (no entity column) shared by every entity today; the target architecture is per-entity duplication, and a ready-to-execute plan is written up in Task 012, but implementation is deliberately deferred as its own atomic unit (Decision 018)

## Existing Functional Areas Observed In The Repository

- Authentication and session flows
- User administration
- Entity administration
- Profile and settings flows
- Webhooks
- Dynamic/admin subprocess infrastructure
- Sidebar/menu configuration flows
- Modular architecture tables for future entitlement-based navigation

## Existing Product Areas Visible In Current Defaults And Structure

- Home
- Administrativo
- Empresa
- Meus dados
- Funcionários
- Financeiro
- Relatórios
- Links
- Contato
- Tutorial

## What Is In Progress At A Planning Level

- Formalizing project context for AI-assisted implementation
- Formalizing the workflow for how GSD should be used across future agent sessions
- Keeping the current web stack stable while preparing clearer architectural separation
- Preserving the current Jinja/FastAPI runtime until API boundaries are mature
- Extending the new login i18n baseline carefully before broader UI translation work
- Deciding how future authenticated UI surfaces should expose language changes safely without inventing ad hoc routes
- Deciding the explicit fate of legacy Alembic tables that still exist in PostgreSQL but are no longer represented in active metadata
- Determining whether `process_view_authorization_rules` and `songs` should regain explicit runtime contracts or be retired later
- Reconciling legacy authorization rows against the current auth-profile/auth-object storage before any destructive cleanup
- Defining whether missing legacy authorization granularity should be migrated forward or only archived before cleanup
- Preparing a human validation step for whether subprocess, department, and entity-scope semantics still matter
- Reviewing how current entity, owner, legacy, and permission rules should evolve into a cleaner multi-tenant model
- Preparing the project for future web and mobile delivery paths without forcing that migration now
- Executing Task 012 (sidebar_menu_settings entity scope): schema migration, ~44-site raw-SQL rewrite, and rewiring of 6 caller files, as one atomic reviewable unit

## Known Risks

- The current web runtime still mixes backend, templates, and shared JavaScript concerns closely
- The legacy sidebar configuration path and the newer module-entitlement path coexist, which increases architectural drift risk
- Multi-tenant rules are already important and easy to break if entity scope, owner rules, or data boundaries are not checked consistently
- Mobile direction is not yet the main implementation path, so premature frontend rewrites would create additional fragmentation
- Documentation and planning context can drift quickly across AI sessions if not centralized

## Near-Term Priorities

- Adopt GSD Core as the default planning layer for future work
- Formalize the usage workflow for GSD across Codex, Claude, and similar agents
- Keep documenting the current architecture before large changes
- Validate and extend multilingual support from the login surface to adjacent auth entry flows when appropriate
- Reuse `users.preferred_language` as the canonical personal language source for future authenticated i18n work
- Resolve the remaining Alembic baseline drift through an explicit keep-or-retire decision for `songs`, `admin_definitions`, and `process_view_authorization_rules`
- Reconcile the remaining `process_view_authorization_rules` rows with current auth storage before any destructive cleanup of legacy tables
- Decide whether legacy authorization details such as subprocess granularity, department, and scope must survive in the current contract
- Validate with a human owner whether the project accepts archive-only cleanup or requires complementary migration of legacy authorization semantics
- Revisit multi-tenant boundaries with explicit entity, owner, permission, and data-separation rules
- Implement Task 012 (`sidebar_menu_settings` entity scope) as a dedicated, atomic migration + rewrite
- Prepare for later evaluation of:
  - Supabase as managed Postgres
  - a more explicit API layer
  - Next.js only after backend/API separation is mature
  - React Native in a later phase

## Explicit Non-Goals Of The Current Auth I18n Phase

- No full-application translation yet
- No Docker changes
- No Supabase changes
- No Next.js migration
- No entity-level language storage
- No unsafe authenticated language-change endpoint without a clear profile/settings contract
