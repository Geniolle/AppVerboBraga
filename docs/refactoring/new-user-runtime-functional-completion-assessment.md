# New User Runtime Functional Completion Assessment

Data: 2026-07-14

## Summary

O runtime do `new_user.js` foi consolidado para os módulos canónicos carregados no template, com execução real para quantidade, campos subsequentes e pós-save. Os blocos históricos grandes foram removidos do `new_user.js` e substituídos por delegação ou por helpers curtos de compatibilidade.

## Quantity

### Implementação canónica pretendida

`static/js/modules/process_quantity_runtime_v1.js`

### Implementação realmente ativa

- `initialize(context)` cria estado por formulário, liga listeners e renderiza.
- `render(context)` monta hosts, itens repetidos, render readonly e payload hidden.
- `sync(context)` reconstrói o JSON com base no DOM atual.
- `getValues(context)` lê valores atuais do formulário.
- `destroy(context)` remove listeners e nós gerados.
- Os adaptadores `createMeuPerfilQuantityAdapterV1()` e `createDynamicProcessQuantityAdapterV1()` estão expostos.

### Implementação antiga ainda ativa

- Não há mais o bloco histórico grande de pós-save/quantity/subsequent no `new_user.js`.
- Ainda existem helpers de integração no `new_user.js`, mas o fluxo real passa pelo runtime canónico.

### Stub

- Não há stubs principais restantes no módulo.

### Consumers

- `new_user.js` inicia o runtime para `Meu Perfil` e para o processo dinâmico.
- Testes browser sintéticos validam render e sync.

### Código morto

- Os blocos históricos de pós-save e subsequentes foram removidos do `new_user.js`.

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

### Implementação antiga ainda ativa

- O bloco legado grande foi removido.
- `new_user.js` apenas conserva o bootstrap mínimo para chamar o runtime.

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

- O contrato grava, lê e limpa o contexto com `sessionStorage`.
- O capture canonical expõe `initialize`, `bindForm`, `captureForm` e `destroy`.
- O reload guard consome o contrato antes de navegar.

### Implementação antiga ainda ativa

- Os blocos históricos grandes de `KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1`, `POST_SAVE_CONTEXT_CAPTURE_V3`, `RETURN_URL_POST_SAVE_CAPTURE_V4`, `FRONTEND_RETURN_URL_POST_SAVE_V6` e `INITIAL_PROFILE_SECTION_FROM_URL_V1` foram removidos do `new_user.js`.
- A reativação inicial da secção do perfil foi preservada num helper curto de compatibilidade.

### Compatibilidade necessária

- `appgenesis_after_save=1`
- prioridade de URL, target e menu existente
- expiração do contexto

## Campos adicionais

### Estado atual

- `static/js/modules/process_additional_fields_manager_v3.js` continua como implementação canónica ativa.
- Não houve duplicação nova neste ciclo.

## Navegação

### Estado atual

- `static/js/modules/navigation_reload_guard_v1.js` continua carregado no `head`.
- O guard continua a depender do contrato partilhado de pós-save.

## Orquestração

### Estado atual

- `new_user.js` continua como orquestrador, mas agora chama os runtimes canónicos.
- A execução principal não está mais ancorada nos blocos históricos grandes.

## Meu Perfil

### Estado atual

- O registry canónico `profile_field_registry_v1.js` permanece ativo.
- O runtime de quantidade e o runtime de subsequentes já usam o registry.
- A secção inicial do perfil ainda é reativada via helper curto.

## Processos dinâmicos

### Estado atual

- O runtime de quantidade passa a renderizar e sincronizar também no contexto dinâmico.
- O runtime de subsequentes aplica regras em formulários dinâmicos quando o contexto fornece `setting` e `root`.

## Sessões

### Estado atual

- Não houve alteração estrutural a sessões neste ciclo.
- A validação de sessão/menu continua a depender da infraestrutura existente.

## Validação executada

- `node --check static/js/new_user.js`
- `node --check static/js/modules/process_quantity_runtime_v1.js`
- `node --check static/js/modules/process_subsequent_visibility_runtime_v1.js`
- `node --check static/js/modules/post_save_context_capture_v1.js`
- `pytest -q tests/test_new_user_runtime_functional_v1.py tests/test_process_quantity_runtime_v1.py tests/test_process_subsequent_visibility_runtime_v1.py tests/test_post_save_context_contract_v1.py tests/test_new_user_runtime_phase0_characterization_v1.py tests/test_profile_field_registry_v1.py`

## Residual risks

- O fluxo de restauração inicial da secção do perfil foi compactado e mantido no `new_user.js`; deve ser revisto se surgir uma migração dedicada futura.
- A cobertura browser atual valida o comportamento principal em página sintética, mas não substitui totalmente uma execução completa no app real.
