# Task 011: Objeto de Autorização Entity Scope

Status: completed
Updated: 2026-07-06

## Objective

Close a confirmed cross-entity data leak: `Objeto de Autorização` rows were tagged with
`__numero_entidade` on save but never filtered by it on read, so every entity could see
every other entity's authorization objects. Also close the related latent write-side bug
that let two entities collide on the same generated row key.

## Scope

- Add entity filtering to `ObjetoAutorizacaoAdminRepository.list_rows` (and therefore
  `get_for_edit`, which reuses it), mirroring the filter already shipped for
  `AuthProfileAdminRepository` (`_row_matches_entity_context_v1`, see Task 010 /
  Decision 016).
- Fix `record_index_by_key` in both `ObjetoAutorizacaoAdminRepository.save_row` and
  `AuthProfileAdminRepository.save_row` so duplicate/edit-key detection is scoped per
  entity instead of colliding globally, while preserving positional-index correctness
  against the raw (unfiltered) records list.
- Thread the already-resolved, backend-derived `selected_entity_number` into the
  `auth_objeto_repo_v1.list_rows(...)` call in `page_handler.py`, which was previously
  missing `entity_number` from its context entirely (the repository fix alone would
  have been a no-op without this).
- Add focused automated tests for both repositories.

## Out Of Scope

- `sidebar_menu_settings` entity scope (tracked separately, see Task 012 — the
  underlying table is global and needs a schema migration, not a filter fix).
- `resolve_field_list_options_v1`'s discarded `active_entity_id` (blocked on Task 012).
- Changes to Docker, OAuth/login, or unrelated processes.
- Frontend redesign.

## Checklist

- [x] Confirmed the leak by tracing write path (`profile_handlers.py`) vs read path
      (`objeto_autorizacao_repository.py`, `page_handler.py`)
- [x] Read path filtered by entity, with legacy/untagged rows staying globally visible
      (backward compatible, no silent hardcoded entity fallback)
- [x] Write-side key collision fixed in both Objetos and Perfis repositories
- [x] Missing `entity_number` in context added at the `page_handler.py` call site
- [x] Focused automated tests added (`tests/test_objeto_autorizacao_repository.py`,
      `tests/test_auth_profile_repository.py`)
- [x] Full related test suite passes
- [x] `gsd/STATE.md` was updated
- [x] `gsd/DECISIONS.md` was updated

## Completion Criteria

This task is complete when:

- Objetos de Autorização are only visible to the entity that created them (plus
  untagged legacy rows, visible to all until explicitly re-scoped)
- Two different entities can independently save an object using the same label/key
  without a false "duplicate key" rejection or accidental overwrite
- the change stays localized and does not alter unrelated application behavior
