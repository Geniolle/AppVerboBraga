# New User Runtime Functional Completion Assessment

Data: 2026-07-14

## Summary

O `new_user.js` passou a orquestrar os runtimes canónicos reais para quantity, subsequentes, pós-save e navegação. Os blocos legados mais problemáticos foram removidos do bootstrap direto e a execução real ficou concentrada nos módulos canónicos.

## Quantity

### Implementação canónica pretendida

`static/js/modules/process_quantity_runtime_v1.js`

### Implementação realmente ativa

- `initialize(context)` instancia um runtime por formulário e evita listeners por control.
- `render(context)` cria hosts, itens repetidos, readonly e payload hidden.
- `sync(context)` reconstrói o JSON a partir do DOM atual.
- `getValues(context)` lê os valores atuais.
- `destroy(context)` remove listeners e nós gerados.
- Os adaptadores `createMeuPerfilQuantityAdapterV1()` e `createDynamicProcessQuantityAdapterV1()` estão ativos.

### Implementação antiga ainda ativa

- Não há mais o bloco histórico de quantity/subsequentes/pós-save a executar diretamente no `new_user.js`.
- O bootstrap mantém apenas a ligação ao runtime canónico.

### Compatibilidade necessária

- `process_quantity_payload__<rule_key>`
- `max_items`
- `item_label`
- `header_key`
- `repeated_field_keys`
- tipos `text`, `number`, `email`, `phone`, `date`, `time`, `flag`, `list`

## Subsequentes

### Implementação canónica pretendida

`static/js/modules/process_subsequent_visibility_runtime_v1.js`

### Implementação realmente ativa

- `initialize(context)` liga listeners por formulário.
- `evaluate(context)` normaliza regras e valores.
- `apply(context)` oculta/exibe wrappers e tabs.
- `refresh(context)` reaplica o estado.
- `destroy(context)` limpa listeners.

### Compatibilidade necessária

- Operadores `equals`, `not_equals`, `is_empty`, `is_not_empty`.
- Preservação de controls originalmente desativados.
- Funcionamento em `Meu Perfil` e em processos dinâmicos.

## Pós-save

### Implementação canónica pretendida

- `static/js/modules/post_save_context_contract_v1.js`
- `static/js/modules/post_save_context_capture_v1.js`
- `static/js/modules/navigation_reload_guard_v1.js`

### Implementação realmente ativa

- O contrato mantém e expira o contexto em `sessionStorage`.
- O capture canónico expõe `initialize`, `bindForm`, `captureForm` e `destroy`.
- O reload guard consome o contrato antes de navegar.

### Compatibilidade necessária

- `appgenesis_after_save=1`
- prioridade de URL, target e menu existente
- expiração do contexto

## Campos adicionais

### Estado atual

- `static/js/modules/process_additional_fields_manager_v3.js` permanece como a única implementação ativa.

## Navegação

### Estado atual

- `static/js/modules/navigation_reload_guard_v1.js` continua carregado no `head`.
- O guard continua a depender do contrato partilhado de pós-save.

## Orquestração

### Estado atual

- `new_user.js` continua como orquestrador, mas agora só chama runtimes canónicos e módulos utilitários.
- O evento `appgenesis:new-user-page-ready` é emitido depois da inicialização real.

## Meu Perfil

### Estado atual

- O registry canónico `profile_field_registry_v1.js` continua ativo.
- O runtime de quantity e o runtime de subsequentes usam o registry real.
- A lógica legada de dedup e filtro de secção foi removida do bootstrap direto.

## Processos dinâmicos

### Estado atual

- O runtime de quantity já atua também no contexto dinâmico.
- O runtime de subsequentes aplica regras em formulários dinâmicos quando o contexto fornece `setting` e `root`.

## Sessões

### Estado atual

- A navegação de sessões continua ligada ao resolver canónico de targets.
- O browser real ainda mantém um xfail isolado para o card de secções em `admin_tab=sessoes`.

## Validação executada

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

## Resultados observados

- Os testes sintéticos principais passaram.
- Os browser suites reais passaram, com xfail explícitos apenas nos casos de wrapper de autorização e no card de secções com `admin_tab=sessoes`.
- O `ui_text_cleanup.js` deixou de lançar o `createTreeWalker` error em páginas reais.

## Residual risks

- Os três xfails atuais continuam a refletir um desfasamento entre o target wrapper esperado e a montagem real do DOM nos fluxos de autorização e secções.
- O bootstrap ficou funcional, mas ainda depende de módulos canónicos já existentes no lado do backend.
