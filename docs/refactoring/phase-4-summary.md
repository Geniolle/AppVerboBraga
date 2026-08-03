# Fase 4 — Decomposição do god-function `get_page_data` (`services/page.py`)

## Objetivo

Reduzir o tamanho e a complexidade da função `get_page_data` em
`appgenesis/services/page.py` (a maior função do módulo, ~740 linhas antes desta
fase), extraindo blocos coesos para funções privadas nomeadas, sem alterar
nenhum comportamento observável (respostas HTTP, dados de contexto passados aos
templates, ordem de resolução, mensagens de erro).

## Técnica de validação usada

Mesma validação tripla das fases anteriores, aplicada após cada alteração:
1. `python -m pyflakes appgenesis/services/page.py` — zero `undefined name`.
2. `python -c "import appgenesis.services.page"` — import limpo em runtime.
3. `pytest -q` completo — 190/190 aprovados.

## Correção de bug pré-existente: função duplicada

Durante a Fase 2 já tinha sido sinalizado (ver `phase-2-summary.md`) que
`_apply_meu_perfil_subsequent_visibility_v2` estava definida duas vezes no
módulo. Confirmado nesta fase que a primeira definição (bloco `V1`, linhas
originais 59-164, com os helpers `_format_profile_visibility_date_v1`,
`_collect_meu_perfil_subsequent_rules_v1`, `_build_meu_perfil_visibility_values_v1`)
era código morto: por semântica de vinculação de nomes do Python, uma segunda
`def` com o mesmo nome sobrepõe sempre a primeira — a definição `V1` nunca era
executada. Confirmado por grep que os três helpers do bloco `V1` não eram
usados em mais nenhum ponto do código.

Removido o bloco `V1` completo (107 linhas). Validado com pyflakes (zero erros
de nome indefinido) e `pytest -q` (190/190) antes de prosseguir com a
decomposição.

Commit: `0207a6f4` "refactor: remove dead duplicate
_apply_meu_perfil_subsequent_visibility_v2".

## Decomposição de `get_page_data`

Extraídas seis funções privadas nomeadas, cada uma correspondendo a um bloco
coeso identificado por leitura completa da função original:

- `_resolve_actor_page_context(session, actor_user_id, actor_login_email, selected_entity_id)`
  — permissões do ator (`get_user_entity_permissions`), entidade primária do
  ator, formulários de seleção de entidade, `current_entity_scope`.
- `_resolve_sidebar_menu_context(session, current_user_is_admin, current_entity_scope)`
  — `sidebar_menu_settings`, linhas de menu ativas/inativas, chaves de menu
  visíveis, opções de secção da sidebar.
- `_resolve_actor_menu_process_maps(session, actor_user_id, sidebar_menu_settings, visible_sidebar_menu_keys, selected_entity_id)`
  — mapas de valores/histórico/quantidade de campos de processo por menu
  (genérico, não específico de nenhum domínio).
- `_resolve_scoped_entities(session, allowed_entity_ids)` — consulta de
  entidades ativas/recentes/inativas, já filtrada por `allowed_entity_ids`.
- `_resolve_scoped_users(session, permissions, apply_scope_filter, scoped_entity_ids)`
  — consulta de utilizadores filtrada por `allowed_data_entity_ids`,
  categorização por estado de conta (`pending`, `created`, `active_created`,
  `inactive`, `recent`), `account_status_summary`.
- `_resolve_company_profile_data(session, selected_entity_id, permissions)` —
  perfil institucional da entidade ativa (processo Empresa), restrito a
  `allowed_data_entity_ids`.

A closure local `serialize_entity_row` (definida dentro de `get_page_data`, sem
capturar nenhuma variável do escopo envolvente) foi elevada a função de módulo
`_serialize_entity_row_v1`, reutilizada por `_resolve_scoped_entities`
(indiretamente, no return de `get_page_data`) e por
`_resolve_company_profile_data`.

`get_page_data` passou a ser um orquestrador que chama as seis funções acima em
sequência e monta o dicionário de retorno final — de ~740 linhas para ~430
linhas.

### Bloco explicitamente fora desta fase: motor de campos dinâmicos do Meu Perfil

O bloco de resolução de visibilidade de campos do Meu Perfil (cálculo de
`profile_personal_visible_fields`, `profile_personal_field_labels`,
`profile_personal_custom_field_meta`, `profile_personal_sections`,
`profile_personal_field_section_map`, chamada a
`_apply_meu_perfil_subsequent_visibility_v2`, e os sub-blocos marcados
`APPGENESIS_MEU_PERFIL_HEADER_TABS_ONLY_V1` e
`APPGENESIS_MEU_PERFIL_REQUIRED_SECTION_MAP_V1`) foi deixado **completamente
intacto**, na mesma posição dentro de `get_page_data`, sem extração.

Motivo: é o lado de leitura do mesmo motor genérico de campos
dinâmicos/quantidade/regras subsequentes cujo lado de escrita
(`update_personal_profile`, `update_dynamic_process_profile`/`process-data`,
em `routes/profile/profile_handlers.py`) já tinha sido deliberadamente deixado
intacto na Fase 3, por ser território da Fase 6 (motor de processos
dinâmicos) e não específico de um domínio. Extrair apenas o lado de leitura
agora, sem o lado de escrita, criaria uma decomposição assimétrica e
prematura da arquitetura da Fase 6. **Decisão de fronteira consistente com a
já registada em `phase-3-summary.md`.**

### Limpeza natural: variável morta pré-existente

Ao mover o bloco de resolução de utilizadores para `_resolve_scoped_users`,
foi removida a variável local `user_ids = [int(row.id) for row in user_rows]`,
que o pyflakes já assinalava como "assigned to but never used" antes desta
fase (nunca lida em nenhum ponto posterior da função original). Como o bloco
inteiro estava a ser reescrito, a remoção foi feita como parte natural da
extração, não como limpeza avulsa fora de escopo.

## Ficheiros alterados

- `appgenesis/services/page.py` — único ficheiro alterado nesta fase.

## Validação final

- `python -m pyflakes appgenesis/services/page.py` — zero `undefined name`
  (mantém-se apenas o ruído pré-existente de
  `appgenesis.services.profile.filter_process_fields_by_hidden_targets`
  "imported but unused", confirmado via `git show HEAD` que já existia antes
  de qualquer alteração desta fase).
- `python -c "import appgenesis.services.page"` — import limpo.
- `pytest -q` completo — 190/190 aprovados.

## Riscos

Nenhum risco novo introduzido: a decomposição preserva a ordem de execução, os
nomes e valores de todas as chaves do dicionário de retorno, e as regras de
filtragem por `allowed_entity_ids`/`allowed_data_entity_ids`. O bloco de
campos dinâmicos do Meu Perfil permanece com o mesmo nível de fragilidade que
tinha antes desta fase (múltiplos marcadores de correção de incidentes
versionados), a aguardar tratamento conjunto com o lado de escrita na Fase 6.
