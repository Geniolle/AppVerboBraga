# ADR-001: Legacy Authorization Granularity

Status: proposed
Updated: 2026-07-03

## Context

`process_view_authorization_rules` is no longer used by the current runtime, but its 2 remaining rows still preserve older authorization semantics for Tesouraria and Extrato.

Current runtime behavior is broader:

- profiles are stored in `process_records__perfil_de_autorizacao`
- authorization objects are stored in `process_records__objeto_de_autorizacao`
- process and subprocess options are resolved from current `sidebar_menu_settings`

The reconciliation work showed partial, not complete, correspondence.

## Questions

### Is the profile `Tesouraria` still necessary?

- Technical answer:
  - no exact current equivalent was found
  - the closest live equivalent is `Gestor de Tesouraria`
- Decision:
  - pending human validation

### Do `Importar extrato` and `Dados de extrato` still need separate permissions?

- Technical answer:
  - the current contract does not preserve them as separate live authorization rows
  - the current runtime appears to use broader authorization semantics
- Decision:
  - pending human validation

### Is legacy `entity` scope still necessary?

- Technical answer:
  - the wider application is still entity-aware
  - but the current auth-profile/auth-object storage does not preserve the old `entity` authorization scope explicitly
- Decision:
  - pending human validation

### Should `department_name` still be part of the rule?

- Technical answer:
  - no active equivalent was found in current authorization-object storage
- Decision:
  - pending human validation

### Is the current behavior correct, or was there semantic loss?

- Technical answer:
  - there was semantic loss relative to the legacy row-per-subprocess model
  - but the codebase alone does not prove whether that loss was intentional and accepted
- Decision:
  - pending human validation

## Decision Recommendation

Recommended decision:

- `pendente de validação humana`

Interim technical recommendation:

- treat the current runtime contract as valid for ongoing operation
- treat the remaining legacy rows as preserved audit evidence
- do not drop the table
- do not create a complementary migration until a human confirms whether the old granularity still matters

## Consequences

### If human validation chooses archive

- the legacy table can later be exported and removed safely
- current broader behavior becomes the accepted source of truth
- old subprocess, department, and `entity` scope granularity is intentionally abandoned

### If human validation chooses migration

- a complementary migration must preserve the missing semantics explicitly
- the team must decide whether to:
  - extend the current JSON-backed contract
  - or introduce a cleaner first-class authorization contract
- the legacy table remains in place until that migration is designed and validated
