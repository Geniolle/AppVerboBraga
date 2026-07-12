# AGENT_HANDOFF

## Estado atual

Implementação da evolução das listas automáticas em curso/concluída para o fluxo de processo:

- `source_subprocess_key` passou a ser persistido, validado e renderizado.
- O editor de listas passou a mostrar o campo `Subprocesso` quando o tipo é `Automático` e existe menu selecionado.
- O backend usa o resolver central de tabs para montar as opções de subprocesso por menu.
- A tabela de listas foi atualizada para expor a coluna `Subprocesso`.
- O comportamento legado de listas automáticas sem subprocesso foi preservado como `Todos os subprocessos`.

## O que já foi alterado

- `appgenesis/services/process_settings/list_service.py`
- `appgenesis/menu_settings.py`
- `appgenesis/routes/profile/page_handler.py`
- `appgenesis/routes/profile/process_settings/list_handlers.py`
- `static/js/modules/process_lists_manager_v1.js`
- `static/css/modules/configurable_items_manager_v1.css`
- `templates/new_user.html`
- testes atualizados em:
  - `tests/test_process_lists_manager_v1.py`
  - `tests/test_process_lists_persistence_isolation_v1.py`
  - `tests/test_process_lists_handler_edit_permissions_v1.py`
  - `tests/test_process_lists_reusable_create.py`
  - `tests/test_menu_settings_process_lists_v1.py`
  - `tests/process_settings/test_admin_process_tabs_v1.py`

## Validações já executadas

- `node --check static/js/modules/process_lists_manager_v1.js`
- `python -m py_compile` nos ficheiros Python/t testes alterados
- `git diff --check`
- `python -m pytest tests/test_process_lists_manager_v1.py tests/test_menu_settings_process_lists_v1.py tests/test_process_lists_persistence_isolation_v1.py tests/test_process_lists_handler_edit_permissions_v1.py tests/process_settings/test_admin_process_tabs_v1.py -q`
  - resultado: `33 passed`
- `python -m pytest tests/test_process_lists_reusable_create.py::test_automatic_list_source_menu_real_flow -q`
  - resultado: passou após reiniciar o serviço `web`
- Revisão final do diff: `git diff --name-only` confirma apenas os ficheiros esperados no trabalho atual.
- Validação final de whitespace/patch: `git diff --check` sem erros.

## Estado funcional confirmado

- Manual:
  - conteúdo visível
  - menu oculto
  - subprocesso oculto
- Automático:
  - menu visível
  - subprocesso aparece após selecionar menu
- `Perfil de autorização`:
  - opções resolvidas corretamente:
    - `Todos os subprocessos`
    - `Perfis`
    - `Objeto de autorização`
- Cancelar/editar/guardar no fluxo de listas está funcional.

## Observações e riscos

- O mapa de subprocessos passou a ser fornecido pela página através de `get_sidebar_menu_settings(session)` para evitar mapa vazio no contexto do editor.
- Existem ficheiros de cache local `.tokensave/tokensave.db-shm` e `.tokensave/tokensave.db-wal` marcados no worktree.
- Não foi encontrado `AGENT_HANDOFF.md` pré-existente no repositório; este ficheiro foi criado agora para continuidade.

## Próxima ação exata

1. Rever o diff final dos ficheiros alterados.
2. Se necessário, executar a bateria restante de testes/validações de regressão visual.
3. Atualizar este handoff novamente antes de mudar de agente ou antes de uma bateria longa adicional.
