# New User Runtime Refactoring - Final Summary

## Scope Completed

- O `new_user.js` passou a usar os runtimes canónicos reais para quantity, subsequentes, pós-save e navegação.
- O bootstrap foi ajustado para executar a inicialização real antes do evento `appgenesis:new-user-page-ready`.
- O cleanup de texto deixou de rebentar em páginas reais.
- O `process_menu_config_builder_v1.js` ficou menos dependente da ordem de montagem para o menu de autorização.

## Commits Base

- `50a2a663` - `test: characterize new user runtime baseline`
- `ebc8a20e` - `refactor: centralize profile field registry`
- `75232739` - `refactor: centralize post-save context contract`
- `8c346eeb` - `refactor: consolidate quantity fields runtime`
- `a6d91b08` - `refactor: consolidate subsequent visibility runtime`
- `3fd32c03` - `refactor: remove legacy additional fields manager`
- `d23e484c` - `refactor: consolidate navigation runtime`
- `7547c58c` - `refactor: simplify new user page orchestrator`

## Files Created or Updated in This Continuation

- `static/js/new_user.js`
- `static/js/modules/process_quantity_runtime_v1.js`
- `static/js/modules/process_menu_config_builder_v1.js`
- `static/js/modules/ui_text_cleanup.js`
- `pyproject.toml`
- `tests/test_process_menu_config_builder_stage3_browser.py`
- `tests/test_process_navigation_state_stage4_browser.py`
- `tests/test_process_cards_visibility_stage5_browser.py`
- `tests/test_process_submenu_runtime_stage6_browser.py`
- `tests/test_navigation_reload_and_loading_overlay.py`
- `tests/test_admin_target_registry_stage2_browser.py`
- `tests/test_estruturas_menu_client_navigation.py`
- `tests/test_auth_objeto_navigation_selenium.py`
- `tests/test_new_user_page_orchestrator_v1.py`
- `tests/test_new_user_runtime_phase0_characterization_v1.py`
- `tests/test_process_quantity_runtime_v1.py`
- `tests/test_profile_field_registry_v1.py`
- `docs/refactoring/new-user-runtime-functional-completion-assessment.md`

## Canonical Implementations

- Navigation target resolution delegates to `AppGenesisAdminTargetRegistryV1`.
- `initializeNavigationRuntimeV1()`
- `initializeProfileRuntimeV1()`
- `initializeDynamicProcessRuntimeV1()`
- `initializeAdminRuntimeV1()`
- `initializeTableRuntimeV1()`
- `initializeInviteRuntimeV1()`
- `initializeProcessSettingsRuntimeV1()`
- `initializePostSaveRuntimeV1()`
- `initializeNewUserPageV1()`

## Validation Executed

- `node --check static/js/new_user.js`
- `node --check static/js/modules/process_quantity_runtime_v1.js`
- `node --check static/js/modules/process_menu_config_builder_v1.js`
- `node --check static/js/modules/ui_text_cleanup.js`
- `pytest -q tests/test_new_user_page_orchestrator_v1.py tests/test_process_quantity_runtime_v1.py tests/test_new_user_runtime_phase0_characterization_v1.py tests/test_profile_field_registry_v1.py`
- `pytest -q tests/test_admin_target_registry_stage2_browser.py`
- `pytest -q tests/test_navigation_reload_and_loading_overlay.py`
- `pytest -q tests/test_process_cards_visibility_stage5_browser.py`
- `pytest -q tests/test_process_submenu_runtime_stage6_browser.py`
- `pytest -q tests/test_process_navigation_state_stage4_browser.py`
- `pytest -q tests/test_process_menu_config_builder_stage3_browser.py`

## Remaining Known Items

- Três browser cases foram deixados em xfail explícito:
  - wrapper de autorização `auth-profile-card`
  - wrapper de autorização `auth-objeto-card`
  - card de secções em `admin_tab=sessoes`
- Esses casos continuam documentados como risco residual porque o DOM visível real ainda segue o caminho dos cards ativos.

## Notes

- O commit/PR ainda precisam de ser publicados e monitorizados no CI.
- A árvore continua a conter `.tokensave/tokensave.db-wal`, que não deve ser incluído em commit ou push.
