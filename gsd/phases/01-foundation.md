# Phase 01: Foundation

Status: active
Updated: 2026-07-03

## Goal

Create a stable planning foundation for AppGenesis before deeper architectural changes.

## Scope

- Adopt GSD Core inside the repository
- Document the current application architecture
- Establish initial architectural decisions
- Create a shared planning baseline for future AI-assisted work

## Workstreams

### 1. GSD Core Adoption

- Create the base `gsd/` structure
- Standardize where context, state, decisions, phases, and tasks will live

### 2. Current Architecture Documentation

- Capture the current FastAPI + Jinja + SQLAlchemy + PostgreSQL + Docker stack
- Document the current auth, entity, profile, and permission model
- Record the coexistence of legacy sidebar configuration and newer modular tables

### 3. Login Multi-Idioma Planning

- Keep the current login behavior unchanged in this phase
- Prepare a future plan for multilingual login and entry flows
- Treat localization as a planned improvement, not a current rewrite

### 4. Future Multi-Tenant Review

- Revisit the current entity, owner, legacy, and permission boundaries
- Make future work explicitly validate active entity, permission scope, and data separation
- Avoid redesigning multi-tenant behavior before the current runtime is better documented

### 5. Future Platform Preparation

- Prepare the project for later evaluation of Supabase as managed Postgres
- Prepare the project for later API separation
- Keep Next.js and React Native as later-phase consumers, not current runtime replacements

## Non-Goals

- No replacement of FastAPI
- No replacement of Jinja
- No database migration
- No Docker restructuring
- No route, model, template, or service rewrite

## Exit Criteria

- GSD directory structure exists in the repository
- Current architecture is documented well enough to guide future implementation sessions
- Initial strategic decisions are captured
- The repository gains planning context without altering application behavior
