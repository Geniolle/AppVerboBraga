# Task 012: Sidebar Menu Settings Entity Scope

Status: planned (not started)
Updated: 2026-07-06

## Objective

`sidebar_menu_settings` (menus, process field config, dynamic lists, custom fields,
display order, visibility scopes — the whole "configurable layer" driving Menu,
Sessões, and process forms) is currently one **global, unscoped table shared by every
entity**. This is the root cause of several open gaps:

- `resolve_field_list_options_v1` in `services/profile.py` discards `active_entity_id`
  (`del active_entity_id`) because none of its data sources carry an entity dimension.
- Any entity editing a menu's fields, lists, additional fields, or display order changes
  it for every other entity too — there is no isolation at all today, by design of the
  current schema (not a bug in the filtering logic, unlike Task 011 — there is no
  filtering logic to fix, because there is no entity column to filter on).

Decision (confirmed by user 2026-07-06): duplicate configuration per entity now,
rather than continue sharing one global config or defer indefinitely.

## Why this is a separate task, not part of the same pass as Task 011

Task 011 fixed a filtering gap in JSON-blob repositories that already stored a
per-row entity tag. This task requires an actual schema change plus a rewrite of a
different order of magnitude:

- `appgenesis/menu_settings.py` (172KB) contains **~44 raw `text()` SQL statements**
  directly referencing `sidebar_menu_settings`, spread across ~20 functions/helpers
  (including low-level helpers reused everywhere: `_menu_exists`, `_load_menu_config`,
  `_persist_sidebar_menu_display_order`, `ensure_sidebar_menu_settings_defaults`,
  `get_sidebar_menu_settings`).
- None of these statements currently take an entity parameter at all — this is a
  signature change rippling outward, not a WHERE-clause patch.
- 11 live call sites read via `get_sidebar_menu_settings(session)` and ~14 live write
  functions are called from at least 6 other files (`auth_profile_repository.py`,
  `menu_repository.py`, `objeto_autorizacao_repository.py`, `profile_handlers.py`,
  `page_handler.py`, `services/page.py`), none of which currently pass entity context
  into this table's functions.
- A partially-migrated state (some queries filtered, others not) would be a silent
  cross-tenant leak — the exact failure mode this whole effort exists to prevent —
  so the schema change and the full read/write rewiring must land as one atomic,
  carefully reviewed unit, not staged incrementally across unrelated commits.

This matches the project's own stop criteria for irreversible/high-blast-radius
changes: rushing a ~44-site raw-SQL rewrite inside an already large mixed-scope pass
carries a materially higher risk of an overlooked filter than doing it as a dedicated,
reviewable unit — consistent with how this project already splits large refactors into
focused `post-refactor/issue-NN` branches instead of one mega-commit.

## Scope (ready to execute)

1. **Model**: add `entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"),
   nullable=False)` to `SidebarMenuSetting` (matches the `Department`/`Role` FK
   convention — a real FK, not a JSON `__numero_entidade` tag, since this is a real
   table). Replace `UniqueConstraint("menu_key", ...)` with
   `UniqueConstraint("entity_id", "menu_key", ...)`.
2. **Migration** (new Alembic revision, `down_revision = "userlang01"`):
   - Add `entity_id` nullable.
   - For each active `Entity`, clone every existing `sidebar_menu_settings` row
     (all 27 today) into a copy tagged with that entity's id, preserving
     `menu_label`, `is_active`, `is_deleted`, `menu_config` as-is (2 active entities
     today → 27 global rows become 54 entity-owned rows).
   - Delete the original untagged rows.
   - Alter `entity_id` to `NOT NULL`, add the FK, drop the old unique constraint on
     `menu_key` alone, add `uq_sidebar_menu_settings_entity_menu_key` on
     `(entity_id, menu_key)`.
   - Downgrade: drop the new constraint/column (standard lossy downgrade).
3. **`appgenesis/menu_settings.py` rewrite** — add an `entity_id: int` parameter
   (no default, no silent fallback) to every function that touches
   `sidebar_menu_settings`, and add `AND entity_id = :entity_id` (or
   `WHERE entity_id = :entity_id AND ...`) to every one of the ~44 raw SQL
   statements. Functions confirmed dead (`create_sidebar_menu_setting_v2`,
   `update_sidebar_menu_sidebar_sections`, `update_sidebar_menu_additional_fields`,
   `get_sidebar_menu_settings_v2/_v3/_v4`) should be deleted rather than migrated,
   since they have zero callers.
4. **Call-site rewiring** — thread `entity_id` from `get_session_entity_id(request)`
   (already the established backend-derived, non-trusted-client source used by the
   Objetos save path) down through:
   - `auth_profile_repository.py` (`_build_sidebar_menu_lookup`,
     `_resolve_auth_profile_field_keys`, `_resolve_menu_scope_defaults`, `list_rows`)
   - `menu_repository.py` (`list_rows`)
   - `objeto_autorizacao_repository.py` (its `get_sidebar_menu_settings` caller)
   - `profile_handlers.py` (2 call sites), `page_handler.py`, `services/page.py`
   All of these already receive or can receive a `context`/`request` object today —
   this is signature threading, not new plumbing infrastructure.
5. **New-entity bootstrap** — when a new `Entity` is created, seed its 27 default
   rows from `SIDEBAR_MENU_DEFAULTS` (the same template `ensure_sidebar_menu_settings_defaults`
   already uses), scoped to the new `entity_id`. Investigate reusing
   `ensure_sidebar_menu_settings_defaults` itself (once entity-scoped) as the hook,
   since it already has "insert if missing" semantics per key.
6. Once this lands, revisit `resolve_field_list_options_v1` in `services/profile.py`
   to actually use `active_entity_id` instead of discarding it.

## Out Of Scope

- `admin_definitions` (preserved per ADR-002, no ORM model, not touched).
- `profiles`/`user_profiles` tables (confirmed dead code, zero live callers — separate
  decision, not blocking this task).
- Docker, OAuth/login changes.
- Mobile-specific work.

## Checklist

- [ ] Model + migration written and applied against a scratch DB copy
- [ ] `ensure_sidebar_menu_settings_defaults` and `get_sidebar_menu_settings`
      entity-scoped
- [ ] All ~14 live write functions entity-scoped
- [ ] All 6 caller files rewired to pass backend-derived `entity_id`
- [ ] Dead v2/v3/v4 variants removed
- [ ] New-entity seeding implemented and tested
- [ ] `resolve_field_list_options_v1` uses `active_entity_id`
- [ ] Full pytest suite passes; manual smoke test with 2 entities confirms no
      cross-entity menu/field/list bleed
- [ ] `gsd/STATE.md` and `gsd/DECISIONS.md` updated

## Completion Criteria

This task is complete when each entity has its own independent menu/process/field/list
configuration, edits in one entity never affect another, new entities are seeded with
the default template automatically, and no call site can read or write another
entity's `sidebar_menu_settings` rows without an explicit, backend-derived
`entity_id`.
