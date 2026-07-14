# New User Runtime Refactoring - Final Summary

## Scope Completed

- Phases executed in this continuation: 6, 7 and 8.
- Earlier phases preserved and not reworked: 0, 1, 2, 3, 4, 5.

## Commits

- `50a2a663` - `test: characterize new user runtime baseline`
- `ebc8a20e` - `refactor: centralize profile field registry`
- `75232739` - `refactor: centralize post-save context contract`
- `8c346eeb` - `refactor: consolidate quantity fields runtime`
- `a6d91b08` - `refactor: consolidate subsequent visibility runtime`
- `3fd32c03` - `refactor: remove legacy additional fields manager`
- `d23e484c` - `refactor: consolidate navigation runtime`
- `7547c58c` - `refactor: simplify new user page orchestrator`

## Files Created

- `tests/test_new_user_page_orchestrator_v1.py`

## Files Altered

- `static/js/new_user.js`

## Files Removed

- None in this continuation.

## Canonical Implementations

- Navigation target resolution now delegates to `AppGenesisAdminTargetRegistryV1` without keeping the old local fallback maps in `new_user.js`.
- `collectNewUserDomReferencesV1()` now provides the page bootstrap references in one place.
- `initializeNavigationRuntimeV1()`
- `initializeProfileRuntimeV1()`
- `initializeDynamicProcessRuntimeV1()`
- `initializeAdminRuntimeV1()`
- `initializeTableRuntimeV1()`
- `initializeInviteRuntimeV1()`
- `initializeProcessSettingsRuntimeV1()`
- `initializePostSaveRuntimeV1()`
- `initializeNewUserPageV1()`

## Removed Logic

- Duplicate `EMPRESA_NATIVE_TARGETS_V1` literal in `new_user.js`.
- Local fallback maps for admin target resolution in `new_user.js`.
- Local fallback logic for `getAdminSubprocessKeyByTargetV1()`.
- Local fallback logic for `normalizeSubmenuTargetAlias()`.

## APIs Preserved

- `window.AppGenesisAdminTargetRegistryV1`
- `window.AppGenesisProcessNavigationStateV1`
- `window.AppGenesisProcessMenuRuntimeV1`
- `window.AppGenesisProcessSubmenuRuntimeV1`
- `window.AppGenesisProcessCardsVisibilityV1`
- `window.AppGenesisProcessKeysRegistryV1`
- `window.AppGenesisProcessReferenceRegistryV1`
- `window.AppGenesisNewUserPageV1`

## Validation Executed

- `node --check static/js/new_user.js`
- `python -m pytest -q tests/test_admin_target_registry_v1.py tests/test_process_keys_registry_v1.py tests/test_process_reference_registry_v1.py tests/test_process_menu_config_builder_v1.py tests/test_process_navigation_state_v1.py tests/test_process_cards_visibility_v1.py tests/test_process_submenu_runtime_v1.py tests/test_process_menu_runtime_v1.py tests/test_auth_objeto_navigation.py`
- `python -m pytest -q tests/test_new_user_page_orchestrator_v1.py tests/test_process_navigation_state_v1.py tests/test_process_menu_runtime_v1.py`
- `python -m pytest -q` timed out in the environment after 604s.
- `python -m pytest -q` across non-browser files, excluding the known preexisting duplication test, passed with `513 passed`.

## Selenium / Browser

- Selenium/browser validation was skipped because `http://127.0.0.1:8000/login` returned `ERR_CONNECTION_REFUSED`.
- `docker compose ps` showed no running services, so browser-driven coverage could not execute in this environment.

## Known Preexisting Failure

- `tests/test_geral_menu_no_duplication_v1.py::test_new_user_html_form_action_occurrence_counts_for_geral_routes`
- Evidence: `/settings/menu/edit` is absent in both the current `templates/new_user.html` and the baseline content from commit `75232739`.
- This failure is not attributable to the refactoring done here.

## Scan Results

- No mojibake detected in `static/js/new_user.js` or `tests/test_new_user_page_orchestrator_v1.py`.
- No additional dead code removals were made beyond the confirmed navigation duplicates.
- Remaining compatibility markers in `new_user.js` are tied to still-consumed modules and tests.

## Residual Risks

- Browser-driven flows are not validated in this environment because the app is not running.
- The known template duplication test remains red and should be handled separately if that assertion is still required.
- The new page orchestrator is intentionally thin; it centralizes bootstrap entry points, but the underlying feature listeners still exist in their current modules and must remain idempotent.
