# GSD State

Updated: 2026-07-03

## Current Known State

- AppVerboBraga is currently a FastAPI web application with Jinja templates and shared frontend JavaScript
- PostgreSQL is the main database in the Docker-first runtime
- SQLAlchemy and Alembic are already part of the stack
- The repository already has a meaningful `docs/` area, but did not yet have a dedicated GSD Core planning area
- The main application code is centered in `appverbo/`
- The repository also contains `tests/`, Docker files, bootstrap/init scripts, and a mobile-related directory
- Initial login multi-language support now exists for `pt`, `en`, `es`, and `fr` using JSON translations plus cookie/session persistence

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
- Reviewing how current entity, owner, legacy, and permission rules should evolve into a cleaner multi-tenant model
- Preparing the project for future web and mobile delivery paths without forcing that migration now

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
- Revisit multi-tenant boundaries with explicit entity, owner, permission, and data-separation rules
- Prepare for later evaluation of:
  - Supabase as managed Postgres
  - a more explicit API layer
  - Next.js only after backend/API separation is mature
  - React Native in a later phase

## Explicit Non-Goals Of This Step

- No route changes
- No model changes
- No template changes
- No database changes
- No Docker changes
- No migration changes
- No behavioral changes to the running application
