# Legacy Authorization Migration Or Archive Plan

Updated: 2026-07-03

## Scope

This report compares two future paths for the remaining legacy authorization semantics in `process_view_authorization_rules`:

- Scenario A: archive legacy and later remove the table
- Scenario B: perform a complementary migration before any removal

The report is documentary only. It does not alter data, schema, or runtime behavior.

## Current Technical Baseline

### Legacy semantics still present

The 2 remaining legacy rows still express these dimensions:

- profile name
- process label
- subprocess label
- department name
- status
- entity-oriented scope

### Current runtime contract

The current runtime instead uses:

- `process_records__perfil_de_autorizacao`
- `process_records__objeto_de_autorizacao`
- `sidebar_menu_settings`

Current equivalents observed:

- profile
  - current equivalent exists, but labels are not identical
  - closest current example: `Gestor de Tesouraria`
- process
  - current equivalent exists
  - `Extrato` is still an active current process/menu
- subprocess
  - current equivalent exists only in broader form
  - current `Extrato` tab/options do not preserve separate legacy rows for `Importar extrato` and `Dados de extrato`
- department
  - no active equivalent was found in current authorization-object storage
- entity scope
  - the broader application is entity-aware
  - but the current auth-profile/auth-object storage does not preserve the legacy `entity` scope in the same way

## Key Decision Questions

These questions remain the decision boundary:

1. Does the product still need a distinct profile concept equivalent to legacy `Tesouraria`?
2. Does the product still need separate permissions for:
   - `Importar extrato`
   - `Dados de extrato`
3. Does authorization still need to vary by department?
4. Does authorization still need a scope equivalent to legacy `entity` for this use case?

Technical evidence alone does not answer those as a business decision.

## Scenario A: Archive Legacy

### When to apply

Apply Scenario A when:

- the current broader authorization behavior is acceptable
- separate permissions for `Importar extrato` and `Dados de extrato` are no longer required
- `department_name` is no longer part of the authorization contract
- entity-specific scope for these rows is no longer required

### What to export

Before any future drop, export at minimum:

- the 2 raw rows from `process_view_authorization_rules`
- related metadata:
  - `entity_id`
  - `created_by_user_id`
  - `updated_by_user_id`
  - `created_at`
  - `updated_at`
- a reconciliation note linking:
  - legacy `Tesouraria`
  - current `Gestor de Tesouraria`
  - current `extrato`
  - current broader object record

### What to document

Document:

- that the old granularity was intentionally abandoned
- that department-specific semantics were intentionally dropped
- that `entity` scope was intentionally not carried forward
- that the current broader contract is the accepted replacement

### Risks

- accepted semantic loss
- weaker audit fidelity than the old row-per-subprocess model
- future requests for subprocess-level authorization may require rework from scratch

### Future steps before table removal

1. export the raw legacy rows
2. attach the export location to GSD/ADR documentation
3. confirm human acceptance of lost granularity
4. only then plan the destructive cleanup migration

## Scenario B: Complementary Migration

### When to apply

Apply Scenario B when:

- `Tesouraria` still matters as a distinct authorization concept
- `Importar extrato` and `Dados de extrato` still need separate permissions
- `department_name` still matters to the rule
- entity-specific scope still matters for authorization behavior

### Data that would need migration

At minimum:

- `profile_name`
- `process_label`
- `subprocess_label`
- `department_name`
- `status`
- `visibility_scope_mode`
- optional audit metadata if the new contract should retain lineage

### Proposed mapping concerns

#### Profile `Tesouraria`

- No exact current equivalent exists
- Closest current live label is `Gestor de Tesouraria`
- Human validation is required before treating those as equivalent

#### `Importar extrato`

- No exact current object-row equivalent exists
- Current runtime still knows the concept at menu/module level
- A complementary migration would need to decide whether this becomes:
  - a distinct current authorization object
  - a distinct subprocess-level permission flag
  - or a normalized child rule under a broader object

#### `Dados de extrato`

- Same issue as above
- Not preserved as an independent current storage row

#### `department_name`

- No active equivalent was found in current auth-object storage
- A migration would need to decide whether department becomes:
  - a field inside object values
  - a child rule
  - or a separate normalized contract

#### `visibility_scope_mode`

- Legacy value is `entity`
- Current auth-profile/auth-object UI/storage uses values like `all`, `owner`, and `legado`
- A migration would need an explicit mapping rule instead of guessing:
  - preserve as a new current value
  - map to a different existing scope
  - or model it separately from current menu visibility scope

### Risks

- introducing semantics that current runtime no longer expects
- inventing equivalences that are not business-approved
- reviving normalized authorization complexity without a clear product need
- future mismatch if migration chooses the wrong target shape

### Future steps

1. validate business meaning of:
   - `Tesouraria`
   - subprocess-level permissions
   - department-aware authorization
   - `entity` scope
2. choose the target contract
3. only then design a data migration
4. validate with runtime read paths before any cleanup of the legacy table

### Need for model/service/repository

Not necessarily in the first step.

If the chosen target remains the current JSON-backed contract, a complementary migration could write into the existing `profile_custom_fields` structure without restoring the legacy table as active runtime state.

If the business wants durable subprocess- and department-level authorization as a first-class feature again, then a new explicit model/service/repository would likely be cleaner than further stretching the JSON contract.

## Recommended Position

Recommended position:

- `pendente de validação humana`

Operationally, the safer default is to behave as if Scenario A is more likely, because the current runtime already works with broader authorization objects and does not read the legacy table.

However, that is not enough evidence to finalize Scenario A yet, because:

- the legacy data still contains semantics not preserved in current storage
- no business validation was found proving those semantics are intentionally obsolete

## Recommendation Summary

- Do not remove the table now
- Do not create a data migration now
- Keep the final decision pending human validation
- Prepare to choose:
  - Scenario A if the old granularity is intentionally obsolete
  - Scenario B if subprocess, department, or entity-scope semantics still matter

## Recommended Next Task

`Task 010 — Validação humana da granularidade legada de autorização`

Goal:

- confirm whether the legacy semantics are still product-relevant
- choose Scenario A or Scenario B explicitly
- define the exact future implementation path without yet mutating data
