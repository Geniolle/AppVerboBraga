# Fase 0 — Mapeamento e linha de base: abas de configuração dos processos

Documento isolado de análise. Nenhum ficheiro funcional foi alterado para o produzir — apenas
leitura (`Read`/`Grep`/`Glob`/`git status`/`git diff`, sem escrita fora deste ficheiro).

## 0. Contexto obrigatório: o que já foi decidido antes deste documento

Antes de qualquer leitura de código, este levantamento consultou `docs/refactoring/final-summary.md`
e os documentos de fase da refatoração anterior (`refactor/appgenesis-process-architecture`, 51
commits, já mergeada em `master`). Essa refatoração **excluiu deliberadamente** a área exata que
este documento mapeia agora:

- `docs/refactoring/risk-map.md` (Risco #4): a aba **Sessões** sozinha acumulou 30 regras de
  incidente (`APPGENESIS_SESSOES_V4`–`V30`) no `AGENTS.md`. Qualquer alteração a
  `menu_settings.py`/`settings_handlers.py`/`admin_subprocesses/service.py` "tem de ser validada
  manualmente contra o fluxo completo de Sessões... não basta o pytest".
- `docs/refactoring/phase-3-summary.md`: `page_handler.py` e `settings_handlers.py` foram
  analisados e conscientemente não tocados — "sinalizando fragilidade extrema".
- `docs/refactoring/phase-7-summary.md` e `docs/refactoring/issue-27-handlers-migration-report.md`:
  confirmam que `settings_handlers.py` não usa repositórios reais (`create`/`update`/`move`/`delete`
  continuam por implementar em `BaseAdminSubprocessRepository`), e que migrar isso "seria reescrever
  ~5000 linhas do código mais historicamente instável do repositório... fora do âmbito de uma fase
  autónoma".
- `docs/refactoring/phase-8-summary.md`: confirma que 25 ficheiros JS mortos foram removidos, mas
  **3 ficheiros relacionados com Listas foram deliberadamente preservados sem remoção**
  (`force_lista_tab_v1.js`, `process_lists_v1.js`, `process_lists_runtime_v3.js`) por estarem
  citados por nome num script dormente (`scripts/restore_template.py`), apesar de zero referências
  em templates vivos.
- `docs/refactoring/current-architecture.md`: já documenta que `menu_settings.py` (então 4848
  linhas, hoje 5307) tem "gerações paralelas (`_v1/_v2/_v3/_v4`) de quase todas as funções centrais,
  com nomes redefinidos múltiplas vezes no mesmo módulo".

**Conclusão desta secção**: nada do que se segue é uma descoberta nova de arquitetura — é a
extensão, com detalhe específico às 6 abas de configuração de processo, de riscos já identificados
e conscientemente adiados pela refatoração anterior. Este documento não recria nenhuma estrutura já
existente (`appgenesis/process_settings/` já existe e é preservado — ver secção 5).

---

## 1. Inventário das abas de configuração existentes

Confirmado em `templates/new_user.html` (linhas 1358–1364, links da barra de abas) e
`appgenesis/process_settings/admin_tabs.py` (`ADMIN_PROCESS_SETTINGS_TABS`, fonte de verdade dos
rótulos/ordem):

| # | Chave (`data-process-edit-tab`) | Rótulo | Pane DOM (`id`) |
|---|---|---|---|
| 1 | `geral` | Geral | `#settings-tab-geral` |
| 2 | `campos-config` (backend: `configuracao_campos`) | Configuração dos campos | `#settings-tab-campos-config` |
| 3 | `campos-adicionais` (backend: `campos_adicionais`) | Campos Adicionais | `#settings-tab-campos-adicionais` |
| 4 | `campos-quantidade` (backend: `campos_quantidade`) | Campos Quantidade | `#settings-tab-campos-quantidade` |
| 5 | `lista` (backend: `lista`) | Listas | `#settings-tab-lista` |
| 6 | `campos-subsequentes` (backend: `campos_subsequentes`) | Campos Subsequentes | `#settings-tab-campos-subsequentes` |

**Nota de inconsistência confirmada**: a chave usada no `href`/`data-process-edit-tab` do HTML
(`campos-config`, `campos-adicionais`, `campos-quantidade`, `campos-subsequentes`, com hífen) é
**diferente** da chave usada em `ADMIN_PROCESS_SETTINGS_TABS` e no parâmetro `settings_tab` do
backend (`configuracao_campos`, `campos_adicionais`, `campos_quantidade`, `campos_subsequentes`,
com underscore — exceto `campos_adicionais`/`campos_quantidade`/`campos_subsequentes` que coincidem
com underscore em ambos os lados menos o hífen do HTML). Existe portanto **tradução implícita
hífen↔underscore** em algum ponto do JavaScript de navegação de abas (`settings_process_tabs.js`)
que não foi lida em detalhe nesta fase — candidato a teste de proteção explícito na Fase 1, porque
qualquer normalização futura que assuma as chaves iguais nos dois lados quebra silenciosamente a
navegação de abas.

Nenhuma sétima aba foi encontrada. `appgenesis/process_settings/menu_origin.py` confirma que estas
6 abas só ficam ativas (`settings_tabs_enabled=True`) quando o processo tem origem
`administrativo_menu` (criado a partir de Administrativo → Menu) — processos criados por outra via
não mostram esta barra de abas.

---

## 2. Detalhe por aba

Nota metodológica: "função de persistência" e "função de normalização" foram confirmadas por
`grep` de definição + `grep` de chamadores (para resolver qual das várias versões `_v1`/`_v2`/`_v3`
é a que está realmente ligada ao handler, dado que em Python a última definição de um nome no
módulo é a que vale). Corpos de função não foram lidos linha a linha na sua totalidade — ver
secção 9 para o que fica pendente de leitura mais profunda antes da Fase 1.

### 2.1 Geral

- **Frontend**: painel `#settings-tab-geral` (`new_user.html:1368-1538`, campos de label, estado,
  âmbito de visibilidade, secção da sidebar). Nenhum manager JS dedicado — navegação de aba tratada
  por `settings_process_tabs.js`/`settings_default_tab.js`. `menu_section_form.js` já não existe —
  foi removido numa fase anterior a esta sequência (confirmado por
  `tests/test_geral_menu_no_duplication_v1.py`, que documenta a sua ausência: não havia formulário
  real em `new_user.html` a apontar para `/settings/menu/create`, tornando o script morto na
  prática). A referência a este ficheiro neste documento e na tabela da secção 3 estava
  desatualizada e foi corrigida na Fase 7.
- **Backend**: `POST /settings/menu/edit` → `edit_sidebar_menu_setting_handler_v1`
  (`settings_handlers.py:1514`).
- **Permissão**: usa o gate partilhado `_require_menu_settings_owner_v1` (login + admin + Owner via
  `can_manage_tenant_structure`) — **este é o único handler dos 6 confirmado a reutilizar o helper
  partilhado em vez de duplicar a lógica inline** (ver 2.5 e secção 9, risco de duplicação).
- **Persistência**: `update_sidebar_menu_label` + `set_sidebar_menu_visibility` (ambas em
  `menu_settings.py`, sem sufixo de versão — não há duplicação confirmada para estas duas).
- **Normalização**: inline no próprio `menu_settings.update_sidebar_menu_label`.
- **Bootstrap**: `sidebarMenuSettings`, `settingsEditKey`, `settingsTab`, `settingsAction` (todos em
  `window.__APPGENESIS_BOOTSTRAP__`, `new_user.html:2799-2801`).
- **Runtime**: nenhum runtime operacional dedicado (aba estática, sem transformação de campo).
- **Testes**: cobertos indiretamente por `tests/test_menu_settings.py` (60 testes, ficheiro
  genérico) e `tests/test_process_editor_redirect_url.py` (11 testes, foco em redirect). Nenhum
  ficheiro de teste dedicado só à aba Geral foi encontrado.
- **Redirect/card/aba após guardar**: `_build_settings_editor_stay_redirect_url_v1` →
  `redirect_target="settings-menu-edit-card"` — o card **permanece aberto** e a aba ativa é
  reafirmada via `settings_tab="geral"` no URL de retorno.

### 2.2 Configuração dos campos

- **Frontend ativo**: `process_fields_config_manager_v7.js` (`new_user.html:2841`, versão de
  cache-bust `20260629-edit-mode-options-v1`).
- **Backend**: `POST /settings/menu/process-fields` → `edit_sidebar_menu_process_fields_handler`
  (`settings_handlers.py:2317`).
- **Persistência**: `update_sidebar_menu_process_fields` (`menu_settings.py:2367`) — **Fase 4
  confirmou por grep exaustivo de chamadores**: `update_sidebar_menu_process_fields_v4`
  (`menu_settings.py:2164`) NÃO é código morto — é a implementação real (escreve no DB via SQL
  bruto), chamada exclusivamente pelo wrapper sem sufixo, que por sua vez é o único chamado por
  `settings_handlers.py`. Duas gerações vivas por desenho (wrapper → `_v4`), já no estado mínimo
  consolidado; sem alteração necessária. Ver `tests/test_process_fields_config_no_duplication_v1.py`.
- **Normalização**: `normalize_menu_process_visible_fields` (`menu_settings.py:1009`) delega para
  `normalize_menu_process_visible_fields_v4` (`menu_settings.py:930`) — mesmo padrão wrapper→`_v4`,
  também confirmado sem chamador direto do `_v4` fora do wrapper (Fase 4).
- **Bootstrap**: `menuProcessValuesMap`, `menuProcessHistoryMap`, `sidebarMenuSettings`.
- **Testes**: `tests/test_process_fields_config_manager_v7.py`,
  `tests/test_process_fields_config_no_duplication_v1.py`,
  `tests/test_process_fields_config_handler_edit_permissions_v1.py`,
  `tests/test_process_fields_config_persistence_isolation_v1.py` (45 testes no total, Fase 4).
- **Redirect/card/aba**: mesmo padrão do 2.1 (`settings_tab="configuracao_campos"`, card
  permanece aberto).

### 2.3 Campos Adicionais

- **Frontend ativo**: `process_additional_fields_manager_v3.js` (`new_user.html:2812`) +
  `process_field_options_resolver_v1.js` (`new_user.html:2810`, runtime que resolve opções de campo
  do tipo `list` — `SUPPORTED_TYPES` inclui `"list"`, seletor raiz
  `[data-process-additional-fields-manager-v3='1']`) + `configurable_items_manager_core_v1.js`
  (núcleo partilhado, `window.AppGenesisConfigurableItems`, também consumido por Listas — ver 2.5).
- **Backend**: `POST /settings/menu/process-additional-fields` →
  `edit_sidebar_menu_process_additional_fields_v1` (`settings_handlers.py:2142`).
- **Persistência**: `update_sidebar_menu_additional_fields` (`menu_settings.py:4240`).
  **Duplicação confirmada por grep**: `update_sidebar_menu_additional_fields_v4` (linha 4177) e
  `update_sidebar_menu_additional_fields_v1` (linha 4228) existem no mesmo ficheiro, antes da
  versão sem sufixo (linha 4240, a que vale por último-vence). Precisa confirmação de chamadores
  antes de qualquer remoção.
- **Normalização**: `normalize_menu_process_additional_fields` — **a versão realmente ativa é a
  definida em último lugar no ficheiro, linha 4880**, não a de linha 795 nem a de linha 4044 (ambas
  também sem sufixo, mas sobrepostas pela de 4880 por semântica de último-vence do Python). Existem
  ainda `_v1` (3940), `_v2` (3079), `_v3` (3142 **e** 3408, definida duas vezes), `_v4` (3608) — 7
  definições no total para o mesmo conceito.
  **Achado relevante para o plano de refatoração**: a versão viva (linha 4880) **já suporta**
  `item_list_source_type` (`"manual"` por default) e campos
  `item_automatic_source_process_key/section_key/field_key` — ou seja, o suporte a "lista
  automática" mencionado como trabalho futuro no pedido original **já existe, pelo menos
  parcialmente, no normalizador live**. Isto precisa de validação de até onde vai (se é só
  normalizado e nunca lido/resolvido em runtime, ou se já é consumido) antes de qualquer fase que
  assuma que "listas automáticas" é greenfield.
- **Associação com listas**: por `item_list_key`/chave, não por índice (mitiga um dos riscos que o
  pedido original queria evitar na Fase 7) — a confirmar com leitura mais profunda do runtime de
  associação antes de declarar isto como garantido em produção.
- **Bootstrap**: `menuProcessValuesMap`, `sidebarMenuSettings` (para resolver `process_lists`
  disponíveis como fonte).
- **Testes**: `tests/test_process_additional_fields_manager_v3.py` (2 testes).
- **Redirect/card/aba**: mesmo padrão (`settings_tab="campos_adicionais"`).

### 2.4 Campos Quantidade

- **Frontend ativo**: `process_quantity_fields_manager_v1.js` (`new_user.html:2814`).
- **Backend**: `POST /settings/menu/process-quantity-fields` →
  `edit_sidebar_menu_process_quantity_fields_handler` (`settings_handlers.py:2509`).
- **Persistência**: `update_sidebar_menu_process_quantity_fields_v1` (`menu_settings.py:3277`) —
  **Fase 5 confirmou**: única versão, sem duplicação, sem chamador direto fora de
  `settings_handlers.py`.
- **Normalização**: `normalize_menu_process_quantity_fields` (`menu_settings.py:3185`) — única
  versão, sem sufixo duplicado. Depende do normalizador de Campos Adicionais via nome sem sufixo
  (resolve para a geração ativa por last-definition-wins); validação cruzada só ocorre na gravação,
  não na leitura (comportamento estranho documentado e preservado).
- **Bootstrap**: `menuProcessValuesMap`, `sidebarMenuSettings`.
- **Testes**: `tests/test_process_quantity_fields_manager_v1.py`,
  `tests/test_process_quantity_fields_no_duplication_v1.py`,
  `tests/test_process_quantity_fields_handler_edit_permissions_v1.py`,
  `tests/test_process_quantity_fields_persistence_isolation_v1.py` (71 testes no total, Fase 5).
- **Redirect/card/aba**: mesmo padrão (`settings_tab="campos_quantidade"`).
- **Observação**: esta é, das 6 abas, a que tem menor sinal de duplicação de gerações no backend —
  candidata natural a ser a primeira aba a migrar para uma arquitetura nova, se/quando essa decisão
  for tomada, por ser a de menor risco de regressão.

### 2.5 Listas

Esta é a aba citada explicitamente no pedido original como tendo concorrência de scripts. O
levantamento confirma uma situação **mais específica e menos caótica** do que "5 ficheiros
concorrentes fazendo a mesma coisa" — ver secções 3 e 4 para o detalhe completo. Resumo:

- **Fase 6 confirmou e removeu** os 3 ficheiros órfãos citados abaixo (2.6.1): a única razão
  documentada para preservá-los (`scripts/restore_template.py`) já não existe — esse script foi
  removido em `b15df9b5` ("docs: audit one-off scripts in scripts/, remove dead/duplicate ones"),
  antes mesmo desta sequência de fases começar. Zero referências remanescentes em templates,
  JS, Python ou testes, confirmado por grep exaustivo.
- **Frontend ativo (2 ficheiros, papéis distintos, ambos carregados)**:
  - `process_lists_manager_v1.js` (`new_user.html:2813`, versão
    `20260710-list-editor-scope-v3`) — **editor**: manipula
    `form[data-process-lists-manager-v1='1']`, cria/edita/remove linhas de lista no formulário,
    usa o núcleo partilhado `window.AppGenesisConfigurableItems`.
  - `process_lists_runtime_v5.js` (`new_user.html:2830`, carregado numa secção posterior e
    separada do bloco principal de managers) — **runtime**: lê
    `window.__APPGENESIS_BOOTSTRAP__.sidebarMenuSettings`, resolve o processo atual por
    `settings_edit_key`, e obtém as listas configuradas do processo (`obterListasProcesso_v5`) —
    presumivelmente para alimentar campos do tipo lista fora do editor da própria aba Listas (ex.:
    transformar inputs noutras abas em selects). Não lido até ao fim do ficheiro (573 linhas) nesta
    fase — confirmar escopo exato de runtime vs. `process_field_options_resolver_v1.js` (2.3) antes
    da Fase 1, porque pode haver sobreposição de responsabilidade entre os dois.
- **Backend**: `POST /settings/menu/process-lists` → `edit_sidebar_menu_process_lists_handler`
  (`settings_handlers.py:2613`). **Este handler duplica inline o bloco de verificação de permissão
  (login + admin + Owner) em vez de chamar `_require_menu_settings_owner_v1`** — confirmado por
  leitura direta do corpo (linhas 2630-2679), diferente do padrão usado por 2.1 (Geral). Risco de
  drift: uma correção de regra de permissão feita só no helper partilhado não propaga
  automaticamente para este handler.
- **Persistência**: `update_sidebar_menu_process_lists` (`menu_settings.py:2381`).
- **Normalização**: `normalize_menu_process_lists_v3` (`menu_settings.py:3041`) — confirmado por
  grep de chamadores como a versão realmente usada tanto pelo handler de escrita (via
  `update_sidebar_menu_process_lists`) como por `get_sidebar_menu_settings_v4` (leitura, chamada
  direta, sem passar por `get_menu_process_lists_v2`).
- **Fase 6 corrigiu esta especulação**: `normalize_menu_process_lists_v1`/`_v2` e
  `get_menu_process_lists_v1`/`_v2` NÃO são código morto — são executadas em todas as chamadas a
  `get_sidebar_menu_settings` (que resolve para `_v4`, que chama `_v3` internamente via
  `_original_get_sidebar_menu_settings_for_lists_v3`, que por sua vez chama `_v2`, que chama o
  original). É uma cadeia de decoradores encadeados (last-definition-wins) em que `_v4` sobrescreve
  o resultado de `process_lists`/`process_list_options` calculado por `_v2`/`_v3` antes de devolver
  — ou seja, o trabalho de `_v1`/`_v2` (incluindo uma query SQL repetida 3x por chamada) é real mas
  redundante, não morto. Colapsar esta cadeia teria impacto nas 6 abas (não só Listas) e fica
  documentado como risco residual para a Fase 9/10, não tratado nesta fase.
- **Bootstrap**: `sidebarMenuSettings` (contém `process_lists` por processo).
- **Testes**: `tests/test_menu_settings_process_lists_v1.py`, `tests/test_process_lists_columns_editor.py`,
  `tests/test_process_lists_reusable_create.py`, `tests/test_process_lists_manager_v1.py`,
  `tests/test_process_lists_persistence_isolation_v1.py`,
  `tests/test_process_lists_handler_edit_permissions_v1.py` — 20 testes ao todo (Fase 6),
  espalhados por 6 ficheiros com convenções de nome diferentes; sem ficheiro canónico único.
- **Redirect/card/aba**: mesmo padrão (`settings_tab="lista"`).
- **Suporte a Tipo de campo Manual/Automático**: o formulário submete `process_list_field_type`
  (lista, `Form(default=[])`) por linha — confirma que a distinção manual/automático já existe pelo
  menos ao nível do payload aceite pelo handler.

#### 2.5.1 Ficheiros órfãos removidos na Fase 6

`force_lista_tab_v1.js`, `process_lists_v1.js` e `process_lists_runtime_v3.js` foram removidos:
zero `<script src>` em qualquer template, zero imports/referências em outro JS, zero uso em
Python ou testes. A única justificação registada para os preservar (citação por nome em
`scripts/restore_template.py`, um script dormente) deixou de existir — esse script foi removido em
`b15df9b5`, antes desta sequência de fases começar.

### 2.6 Campos Subsequentes

- **Frontend ativo**: `process_subsequent_fields_manager_v1.js` (`new_user.html:2815`).
- **Backend**: `POST /settings/menu/process-subsequent-fields` →
  `edit_sidebar_menu_process_subsequent_fields_handler` (`settings_handlers.py:2804`).
- **Persistência**: `update_sidebar_menu_subsequent_fields` (`menu_settings.py:4315`).
- **Normalização**: `normalize_menu_process_subsequent_fields` — **3 definições do mesmo nome no
  ficheiro** (linhas 4257, 4589, 4741); a de 4741 é a que vale (última). Cada uma tem uma família
  de helpers próxima (`_normalize_subsequent_field_operator_v2` junto à de 4589,
  `_normalize_subsequent_field_operator_v3`/`_build_subsequent_field_key_v3` junto à de 4741) — não
  são apenas renomeações triviais, parecem gerações reais com lógica diferente. Precisa leitura
  completa antes de qualquer alteração, para não perder regras de operador entretanto corrigidas
  entre gerações.
- **Bootstrap**: `menuProcessValuesMap`, `sidebarMenuSettings`.
- **Testes**: `tests/test_process_subsequent_fields_manager_v1.py` (1 teste) — cobertura visivelmente
  fina para a aba com a lógica condicional mais complexa das 6.
- **Redirect/card/aba**: mesmo padrão (`settings_tab="campos_subsequentes"`).

---

## 3. Inventário de scripts JavaScript relacionados

| Ficheiro | Linhas | `<script src>` em template vivo? | Importado por outro script? | Ativo? | Legado? | Duplica lógica? | Risco de remoção | Recomendação |
|---|---|---|---|---|---|---|---|---|
| `static/js/modules/process_lists_manager_v1.js` | 706 | Sim (`new_user.html:2813`) | Consome núcleo `configurable_items_manager_core_v1.js` via `window.AppGenesisConfigurableItems` | **Sim** | Não | Não (é o editor ativo da aba Listas) | Alto se removido sem substituto | Manter; candidato natural a extrair para `tabs/lists_tab.js` numa fase futura, mantendo contrato |
| `static/js/modules/process_lists_runtime_v5.js` | 573 | Sim (`new_user.html:2830`) | Lê `window.__APPGENESIS_BOOTSTRAP__` diretamente | **Sim** | Não | Sobreposição a confirmar com `process_field_options_resolver_v1.js` | Alto se removido sem substituto | Manter; ler por completo antes de decidir se é runtime genérico ou específico de Listas |
| `static/js/modules/process_lists_v1.js` | 406 | **Removido na Fase 6** | — | — | — | — | — | `scripts/restore_template.py` (única razão de preservação) já não existe desde `b15df9b5` |
| `static/js/modules/process_lists_runtime_v3.js` | 202 | **Removido na Fase 6** | — | — | — | — | — | idem |
| `static/js/modules/force_lista_tab_v1.js` | 264 | **Removido na Fase 6** | — | — | — | — | — | idem |
| `static/js/process_settings/adminProcessTabs_v1.js` | 105 | Não confirmado nesta leitura (fora do bloco de `<script src>` da secção principal analisada) | — | A confirmar | Não (recente, par de `appgenesis/process_settings/`) | Não | — | Investigar propósito exato antes da Fase 1 — pode já ser parte de um controlador de abas embrionário |
| `static/js/modules/process_additional_fields_manager_v3.js` | não medido | Sim (`new_user.html:2812`) | Usa `configurable_items_manager_core_v1.js` | Sim | Não | Não | — | Manter |
| `static/js/modules/process_field_options_resolver_v1.js` | não medido | Sim (`new_user.html:2810`) | Alvo `[data-process-additional-fields-manager-v3='1']` | Sim | Não | Sobreposição a confirmar com `process_lists_runtime_v5.js` (ambos resolvem opções de campo tipo lista) | — | Investigar sobreposição antes de qualquer runtime unificado |
| `static/js/modules/configurable_items_manager_core_v1.js` | não medido | Sim (`new_user.html:2811`) | Núcleo partilhado por Listas e Campos Adicionais | Sim | Não | Não — é o ponto de reutilização que já existe | — | Manter; é a base a partir da qual um `process_editor_form_utils.js` futuro poderia generalizar |
| `static/js/modules/process_quantity_fields_manager_v1.js` | não medido | Sim (`new_user.html:2814`) | — | Sim | Não | Não | — | Manter |
| `static/js/modules/process_subsequent_fields_manager_v1.js` | não medido | Sim (`new_user.html:2815`) | — | Sim | Não | Não | — | Manter |
| `static/js/modules/process_fields_config_manager_v7.js` | não medido | Sim (`new_user.html:2841`) | — | Sim | Não (v1-v6 já removidos na Fase 8 anterior) | Não | — | Manter |
| `static/js/modules/settings_process_tabs.js` | não medido | Sim (`new_user.html:2834`) | — | Sim | Não | A confirmar sobreposição com `settings_default_tab.js` | — | Ambos parecem ter responsabilidades distintas (normalização de aba vs. regra de aba default ao editar) — confirmar antes de fundir num controlador único |
| `static/js/modules/settings_default_tab.js` | não medido | Sim (`new_user.html:2835`) | — | Sim | Não | Ver acima | — | Ver acima |
| `static/js/modules/menu_section_form.js` | — | **Removido antes desta sequência** | — | — | — | — | — | Já não existe no repositório; a linha anterior (que dizia "Sim, `new_user.html:2835`, Manter") estava desatualizada — o número de linha citado corresponde hoje a `settings_default_tab.js`. Corrigido na Fase 7. |

**Nota de correção de registo**: no início desta investigação (turno anterior desta conversa) foi
afirmado, por leitura apressada de um `grep` agregado, que "só `force_lista_tab_v1.js` está
referenciado" nos templates. Uma leitura direta e específica de `force_lista_tab` em
`new_user.html` nesta fase **não encontrou nenhuma ocorrência** — essa afirmação anterior estava
errada e fica corrigida aqui. Os dois ficheiros de facto ativos da família "listas" são
`process_lists_manager_v1.js` e `process_lists_runtime_v5.js`, não `force_lista_tab_v1.js`.

---

## 4. Qual implementação da aba Listas está realmente ativa

- **Editor**: `process_lists_manager_v1.js` — confirmado pela tag `<script src="/static/js/modules/process_lists_manager_v1.js?v=20260710-list-editor-scope-v3">`, a versão de cache-bust mais recente de toda a área (10 de julho, mesma data do levantamento), e pelo seletor de formulário `form[data-process-lists-manager-v1='1']` que só faz sentido se o template renderizar esse atributo (não confirmado por leitura do HTML do painel `#settings-tab-lista`, linhas 1828+, mas consistente com o padrão dos outros managers).
- **Runtime**: `process_lists_runtime_v5.js` — carregado numa secção do template fisicamente separada do bloco principal de managers (linha 2830 vs. bloco 2808-2826), o que sugere que foi adicionado numa fase de trabalho diferente e nunca consolidado na mesma zona de scripts, mas ambos executam na mesma página e não há sinal de exclusão mútua.
- **Órfãos confirmados (zero `<script src>`)**: `process_lists_v1.js`, `process_lists_runtime_v3.js`, `force_lista_tab_v1.js` — três ficheiros que existem no repositório e foram deliberadamente preservados numa fase de limpeza anterior por estarem citados em `scripts/restore_template.py` (script dormente), não por estarem em uso.
- **Conflitos de inicialização / `setTimeout` / listeners duplicados**: não confirmados nem descartados nesta fase — os dois ficheiros ativos (`_manager_v1`, 706 linhas; `_runtime_v5`, 573 linhas) não foram lidos até ao fim. Este é o item de maior prioridade para leitura completa antes de escrever qualquer teste de proteção para a aba Listas na Fase 1, porque a resposta a "há duas inicializações concorrentes do mesmo formulário?" determina se a separação editor/runtime já existente é segura para servir de modelo (como o pedido original imaginava para uma futura Fase 5) ou se já esconde uma condição de corrida.
- **Fonte real da funcionalidade hoje**: `process_lists_manager_v1.js` (criação/edição/remoção de listas no formulário) + `process_lists_runtime_v5.js` (leitura das listas configuradas a partir do bootstrap) + `configurable_items_manager_core_v1.js` (núcleo partilhado de UI) + backend `edit_sidebar_menu_process_lists_handler` → `update_sidebar_menu_process_lists` → `normalize_menu_process_lists_v3`.

---

## 5. Arquitetura existente mapeada

```
templates/new_user.html (2843 linhas)
  - Barra de abas do editor de processo: linhas 1358-1364
  - Panes das 6 abas: linhas 1368-2201 (Geral, Campos config, Campos Quantidade, Listas,
    Campos Subsequentes, Campos Adicionais — ordem física no HTML não coincide com a ordem
    visual da barra de abas, que segue ADMIN_PROCESS_SETTINGS_TABS)
  - Bootstrap window.__APPGENESIS_BOOTSTRAP__: linhas 2775+
  - Bloco de scripts do editor de processo: linhas 2808-2842

appgenesis/routes/profile/settings_handlers.py (3071 linhas)
  - Helpers partilhados: _build_settings_redirect_url, _build_settings_editor_stay_redirect_url_v1,
    _require_menu_settings_owner_v1 (usado de forma inconsistente — ver secção 9)
  - 1 handler por aba de configuração + handlers de Sessões/Menu (fora do escopo das 6 abas, mas
    no mesmo ficheiro, mesma área de risco documentada como Sessões V4-V30)

appgenesis/menu_settings.py (5307 linhas, o maior ficheiro do projeto)
  - Normalização e persistência de todas as 6 abas, mais Sessões, mais listas/campos partilhados
  - Duplicação de gerações confirmada e detalhada por aba na secção 2

appgenesis/process_settings/ (pacote pequeno, ~120 linhas, já existente, NÃO duplicar)
  - admin_tabs.py: ADMIN_PROCESS_SETTINGS_TABS (fonte de verdade de rótulo/ordem/chave normalizada)
  - menu_origin.py: is_admin_menu_process_v1 (decide se as 6 abas aparecem para este processo)
  - context_builder.py: build_admin_process_settings_context_v1 (monta o contexto para o template)
  - Não toca normalização, persistência, nem runtime — é só "quais abas existem e estão ativas".
  - Testado por tests/process_settings/test_admin_process_tabs_v1.py (5 testes).

appgenesis/routes/profile/page_handler.py
  - Não lido em detalhe nesta fase; current-architecture.md (refatoração anterior) já confirma que
    consome admin_subprocesses/ para Sessões/Menu/Perfil/Objeto, e separadamente
    process_settings/context_builder.py para as 6 abas aqui mapeadas (via services/page.py,
    responsável por montar sidebar_menu_settings, menu_process_values_map, etc., que alimentam o
    bootstrap consumido pelas 6 abas).
```

### Fluxo de escrita (uma aba, exemplo Listas)

```
templates/new_user.html (form data-process-lists-manager-v1='1')
  → static/js/modules/process_lists_manager_v1.js (serializa e submete)
  → POST /settings/menu/process-lists
  → settings_handlers.edit_sidebar_menu_process_lists_handler
      (permissão inline duplicada, não via _require_menu_settings_owner_v1)
  → menu_settings.update_sidebar_menu_process_lists
      → menu_settings.normalize_menu_process_lists_v3
      → grava menu_config["process_lists"] em SidebarMenuSetting
  → _build_settings_editor_stay_redirect_url_v1 (redirect 303, card fica aberto, settings_tab=lista)
  → GET /users/new?...&settings_tab=lista
  → services/page.py monta sidebar_menu_settings/menuProcessValuesMap novamente
  → window.__APPGENESIS_BOOTSTRAP__
  → static/js/modules/process_lists_runtime_v5.js relê o processo/listas do bootstrap
```

---

## 6. Documentação da refatoração anterior — já lida e considerada

Ver secção 0. Ficheiros lidos integralmente nesta fase:
`docs/refactoring/final-summary.md`, `risk-map.md`, `current-architecture.md`, `phase-3-summary.md`,
`phase-7-summary.md`, `phase-8-summary.md`, `issue-27-handlers-migration-report.md`. Não foram
lidos nesta fase (não pareceram relevantes ao escopo das 6 abas por título/resumo em
`final-summary.md`): `phase-1-summary.md`, `phase-2-summary.md`, `phase-4-summary.md`,
`phase-5-summary.md`, `phase-6-summary.md`, `phase-9-summary.md`, `phase-10-summary.md`,
`inventory.md`, `validation-plan.md`, `walkthrough.md`, `issue-26-*.md`, `issue-28-*.md`. Se uma
fase futura tocar Meu Perfil ou o motor de campos dinâmicos genérico partilhado com Meu Perfil
(`update_dynamic_process_profile`), esses documentos devem ser lidos antes.

---

## 7. Matriz de regressão por aba

Legenda: ✅ = comportamento confirmado por leitura de código nesta fase; 🟡 = inferido por padrão
consistente entre abas mas não confirmado individualmente; ⬜ = não verificado nesta fase, requer
teste manual/E2E antes da Fase 1.

| Cenário | Geral | Config. campos | Campos Adic. | Campos Qtd. | Listas | Campos Subseq. |
|---|---|---|---|---|---|---|
| Abrir | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| Carregar dados existentes | ✅ (bootstrap) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Criar | ⬜ | ⬜ | ⬜ | ⬜ | ✅ (payload por linha confirmado) | ⬜ |
| Editar | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ |
| Remover | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Guardar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cancelar | ⬜ (via `appgenesis_cancel_controller_v1.js`, não lido) | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Reabrir | 🟡 (via `settings_tab` no redirect) | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| Atualizar a página | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Trocar de aba | 🟡 (`settings_process_tabs.js`, não lido em detalhe) | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| Trocar de processo | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Trocar de entidade | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Como administrador (não Owner) | ✅ bloqueado | 🟡 | 🟡 | 🟡 | ✅ bloqueado (verificação duplicada) | 🟡 |
| Como Owner | ✅ permitido | 🟡 | 🟡 | 🟡 | ✅ permitido | 🟡 |
| Sem permissão nenhuma | ✅ redirect com erro | 🟡 | 🟡 | 🟡 | ✅ redirect com erro | 🟡 |
| Redirect após guardar | ✅ `settings-menu-edit-card`, `settings_tab` preservado | ✅ (mesmo padrão) | ✅ | ✅ | ✅ | ✅ |
| Estado do card após guardar | ✅ permanece aberto | ✅ | ✅ | ✅ | ✅ | ✅ |
| Persistência correta | ✅ | ✅ | ✅ (com ressalva de 7 gerações do normalizador) | ✅ | ✅ (com ressalva de 3 gerações do normalizador) | ✅ (com ressalva de 3 gerações do normalizador) |
| Isolamento entre processos | 🟡 (por `menu_key`, chave de partição confirmada em todos os handlers) | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| Isolamento entre entidades | ⬜ — `SidebarMenuSetting` é **global, não por entidade** (Risco #6 do `risk-map.md` anterior); o escopo de entidade vive dentro do próprio `menu_config` (`visibility_scope`), não como filtro de tabela | idem | idem | idem | idem | idem |

**Achado que deve ser tratado como crítico de design, não de bug**: `SidebarMenuSetting` (e portanto
todas as 6 abas) **tem** uma coluna `entity_id` (FK obrigatória para `entities.id`, com
`UniqueConstraint("entity_id", "menu_key")`) — correção face a uma leitura anterior desta secção,
que afirmava a ausência da coluna. Na prática, porém, essa coluna não é usada para particionar
configuração por entidade: `ensure_sidebar_menu_settings_defaults` cria uma única linha por
`menu_key`, preenchendo `entity_id` com um valor arbitrário resolvido por
`_resolve_sidebar_menu_settings_entity_id` (a primeira entidade por `id` ascendente, apenas para
satisfazer a FK `NOT NULL`); e todas as funções de leitura/escrita confirmadas nesta fase
(`_menu_exists`, `_load_menu_config`, `update_sidebar_menu_process_lists`) filtram exclusivamente
por `lower(trim(menu_key))`, nunca por `entity_id`. Ou seja, o comportamento funcional já descrito
permanece correto: "Isolamento entre entidades" para estas abas não significa "cada entidade tem a
sua cópia da configuração" — significa "a mesma configuração de processo é global, e o campo
`visibility_scope`/`profile_scope` dentro do JSON decide que entidades a veem". Qualquer fase futura
de refatoração que assuma erradamente particionamento por entidade ao nível do repositório (como o
`risk-map.md` da refatoração anterior já avisou para `domains/modules/menu_provider.py`), incluindo
uma tentativa de "aproveitar" a coluna `entity_id` já existente para filtrar consultas, introduziria
uma regressão de segregação que não existe hoje por design. Isto tem de ser preservado exatamente
como está, não "corrigido". Protegido por
`tests/test_process_lists_persistence_isolation_v1.py::test_update_process_lists_ignores_entity_id_column_by_design`.

Todas as linhas ⬜ requerem validação manual em browser (ou um novo teste Selenium/E2E) antes da
Fase 1 poder declarar "testes de proteção completos" para essa aba — não é seguro assumir o
comportamento por analogia com as abas já confirmadas.

---

## 8. Mapa de dependências (consolidado)

```
Template (new_user.html, painel + bootstrap)
  → JavaScript do editor (1 manager por aba, ver secção 3)
    → [Listas e Campos Adicionais também passam por configurable_items_manager_core_v1.js]
  → endpoint POST /settings/menu/process-<aba> (ou /settings/menu/edit para Geral)
  → handler em settings_handlers.py
    → _require_menu_settings_owner_v1 (só Geral) OU verificação inline duplicada (as outras 5 —
      não confirmado individualmente para config-campos/campos-adicionais/quantidade/subsequentes,
      só confirmado para Listas; assumir duplicação até prova em contrário é a postura segura)
  → serviço/função de negócio em menu_settings.py (update_sidebar_menu_*)
    → normalização (normalize_menu_process_*, com o problema de múltiplas gerações descrito)
  → persistência: menu_config (JSON) dentro de SidebarMenuSetting, via sessão SQLAlchemy direta
    (sem repositório dedicado — confirma issue-27-handlers-migration-report.md)
  → bootstrap: services/page.py (não lido em detalhe) monta sidebar_menu_settings/
    menuProcessValuesMap/menuProcessHistoryMap a partir do mesmo SidebarMenuSetting, injetado em
    window.__APPGENESIS_BOOTSTRAP__ no próximo GET
  → runtime: só Listas (process_lists_runtime_v5.js) e Campos Adicionais
    (process_field_options_resolver_v1.js) têm um runtime dedicado lendo o bootstrap para
    transformar campos; as outras 4 abas não têm runtime operacional identificado além de
    apresentar os dados já carregados no próprio painel.
```

---

## 9. Riscos concretos identificados

### Crítico

- **Nenhum risco novo de nível crítico foi introduzido ou descoberto nesta fase que já não
  estivesse classificado como tal (ou equivalente) pela refatoração anterior.** O risco mais sério
  aplicável aqui é herdado: qualquer reescrita de `settings_handlers.py`/`menu_settings.py` sem
  validação manual completa reabre uma classe de incidente com 27-30 ocorrências documentadas
  (`AGENTS.md`, `APPGENESIS_SESSOES_V4`-`V30`), mesmo que os incidentes documentados sejam
  nominalmente de "Sessões" — o ficheiro é partilhado com as 6 abas aqui mapeadas.

### Alto

1. **Duplicação de geração do normalizador de Campos Adicionais** (`normalize_menu_process_additional_fields`,
   7 definições, `menu_settings.py`) — maior densidade de duplicação das 6 abas. A versão viva
   (linha 4880) já contém lógica de `list_source_type` automático/manual não presente nas gerações
   anteriores — uma reversão acidental para uma versão antiga (ex.: um merge malfeito) perderia essa
   funcionalidade silenciosamente, sem erro de sintaxe.
2. **Duplicação de geração do normalizador de Campos Subsequentes** (3 definições com helpers
   próprios de operador, `_v2` vs `_v3` — parecem lógica diferente, não só rename).
3. **Verificação de permissão duplicada e inconsistente entre handlers**: `Geral` usa o helper
   partilhado `_require_menu_settings_owner_v1`; `Listas` duplica a mesma lógica inline. Uma
   correção de regra de negócio (ex.: adicionar um novo perfil autorizado) aplicada só ao helper
   não propaga para `Listas` (e presumivelmente não propaga para as outras 4 abas, não confirmadas
   individualmente).
4. **Ausência de repositório real de escrita**: confirmado por `issue-27-handlers-migration-report.md`
   e por leitura direta — todas as 6 abas persistem via manipulação direta de JSON dentro de
   `SidebarMenuSetting.menu_config`, sem `create`/`update`/`delete` de um repositório dedicado. Isto
   é uma escolha de arquitetura já avaliada e conscientemente adiada, não um bug — mas qualquer
   fase futura que assuma "basta trocar para o repositório X" subestima o esforço.
5. **Ficheiros muito grandes com múltiplas responsabilidades**: `menu_settings.py` (5307 linhas,
   cobre as 6 abas + Sessões + aliases + refresh global) e `settings_handlers.py` (3071 linhas,
   mesma mistura). Nenhuma das duas é exclusiva das 6 abas de configuração de processo — separar
   por domínio implica necessariamente tocar também código de Sessões que vive no mesmo ficheiro.

### Médio

6. **Sobreposição de responsabilidade não confirmada entre runtimes**: `process_lists_runtime_v5.js`
   e `process_field_options_resolver_v1.js` podem estar resolvendo o mesmo problema (opções de
   campo tipo lista) por caminhos diferentes — precisa leitura completa antes de decidir se há
   consolidação segura.
7. **Tradução hífen↔underscore de chave de aba** entre HTML (`campos-config`) e backend
   (`configuracao_campos`) — ponto de fragilidade silenciosa se um novo código assumir que as duas
   convenções são intercambiáveis sem passar pela normalização existente.
8. **Cobertura de teste desigual entre abas**: Campos Subsequentes (lógica condicional, a mais
   complexa das 6) tem apenas 1 teste dedicado; Listas tem 20 testes (Fase 6) espalhados por 6
   ficheiros com convenções de nome diferentes (`test_menu_settings_process_lists_v1.py`,
   `test_process_lists_columns_editor.py`, `test_process_lists_reusable_create.py`,
   `test_process_lists_manager_v1.py`, `test_process_lists_persistence_isolation_v1.py`,
   `test_process_lists_handler_edit_permissions_v1.py`) sem um ficheiro canónico único.
9. ~~`update_sidebar_menu_process_fields_v4` (`menu_settings.py:2164`) e
   `update_sidebar_menu_additional_fields_v4`/`_v1` (linhas 4177/4228) não confirmadas como
   chamadas por nenhum handler ativo — candidatas a código morto~~ — **resolvido**: grep exaustivo
   de chamadores confirmou que ambas são vivas (wrapper→`_v4`, sem chamador direto do `_v4` fora do
   próprio wrapper). `update_sidebar_menu_additional_fields_v4`/`_v1` consolidada na Fase 3
   (commits `985a78b2`..`c9b8b36c`); `update_sidebar_menu_process_fields_v4` confirmada na Fase 4
   sem necessidade de alteração de código.

### Baixo

10. ~~3 ficheiros JS órfãos de Listas (`process_lists_v1.js`, `process_lists_runtime_v3.js`,
    `force_lista_tab_v1.js`) — zero risco de execução (não carregados), risco de confusão para
    quem procura "a" implementação de Listas. Já avaliados e preservados por decisão da Fase 8
    anterior~~ — **resolvido na Fase 6**: `scripts/restore_template.py` (a única razão de
    preservação) foi removido em `b15df9b5`, antes desta sequência de fases começar. Confirmado
    por grep exaustivo (templates, JS, Python, testes) que os 3 ficheiros não tinham nenhum
    consumidor; removidos.
10b. **(Novo, Fase 6) Cadeia de decoradores redundante em `get_sidebar_menu_settings`**:
    `_v2`→`_v3`→`_v4` encadeiam-se via `_original_get_sidebar_menu_settings_for_lists_vN`, cada
    uma reexecutando a mesma query SQL (`SELECT menu_key, menu_config FROM
    sidebar_menu_settings`) e recalculando `process_lists` com um normalizador diferente
    (`_v1`/`_v2`/`_v3`), sendo os dois primeiros resultados sempre sobrescritos por `_v4`. Não é
    código morto (todas as camadas executam), mas é trabalho redundante (3x a mesma query por
    chamada) com potencial de consolidação segura. Afeta as 6 abas (função central de leitura),
    não só Listas — fora do âmbito da Fase 6; documentado para avaliação na Fase 9/10.
11. **`static/js/process_settings/adminProcessTabs_v1.js`** não teve o seu propósito confirmado
    nesta fase — baixo risco por ser pequeno (105 linhas) e recente, mas deve ser lido antes de
    criar qualquer controlador de abas novo, para não duplicar algo que já pode existir.

### Riscos do pedido original não confirmados como aplicáveis

- **"Listeners duplicados"/"MutationObserver duplicando render"**: padrão documentado para Sessões
  (V9 do `AGENTS.md`), não confirmado (nem descartado) para nenhuma das 6 abas nesta fase — os
  ficheiros JS de manager não foram lidos até ao fim.
- **"Dependência por índice"**: não confirmada para Campos Adicionais↔Listas — a associação parece
  ser por `item_list_key` (chave), não por posição de array, o que é mais seguro do que o pedido
  original presumia. Precisa confirmação final por leitura do runtime completo antes de ser dada
  como resolvida.
- **"Atualizações amplas de JSON" (substituir a secção toda em vez de fazer merge parcial)**: não
  confirmado nem descartado — depende do corpo completo de `update_sidebar_menu_*`, não lido linha
  a linha nesta fase.

---

## 10. Proposta revisada de sequência de refatoração

O plano original de 18 fases foi desenhado sem visibilidade sobre: (a) a refatoração anterior já
mergeada e as suas exclusões deliberadas; (b) que a separação editor/runtime já existe
organicamente para Listas; (c) que o pacote `appgenesis/process_settings/` já existe e já resolve
parte da Fase 2/3 originais (contexto comum de abas); (d) a escala real dos ficheiros
(`menu_settings.py` 5307 linhas, não uma estimativa). A proposta abaixo substitui o plano de 18
fases por uma sequência menor, ancorada no código real.

| Fase revisada | Objetivo | Depende de | Risco | Ficheiros principais | Testes necessários | Critério de entrada | Critério de saída | Rollback | Tamanho estimado | Automatizável? |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** | Testes de proteção: fechar as 22 células ⬜ da matriz da secção 7 (criar/remover/cancelar/reabrir/refresh/troca de processo/entidade, por aba) | Este documento aprovado | Baixo (só adiciona testes) | `tests/*` (novos, um por célula ⬜ confirmada em falta) | `pytest -q` completo antes/depois, sem alterar nenhum teste existente | Fase 0 aprovada pelo utilizador | 0 testes removidos, todos os novos e antigos verdes, `AGENTS.md`/regras de Sessões não tocadas | `git revert` do commit de testes | Médio (só ficheiros de teste) | **Sim, com revisão humana da matriz de cobertura no fim** |
| **B** | Ler por completo e documentar (sem alterar) os 4 pontos "não confirmado" de maior risco: `process_lists_manager_v1.js` + `process_lists_runtime_v5.js` na íntegra (concorrência/listeners), corpo completo de `update_sidebar_menu_*` das 6 abas (merge parcial vs. substituição total de JSON), sobreposição `process_lists_runtime_v5.js`/`process_field_options_resolver_v1.js`, e confirmação de chamadores de `update_sidebar_menu_process_fields_v4`/`update_sidebar_menu_additional_fields_v4`/`_v1` | A (mesma sessão pode correr em paralelo, é só leitura) | Nulo (zero escrita) | leitura apenas | Nenhum (documentação) | — | Documento de achados anexo a este, sem código alterado | — | Pequeno (documentação) | **Sim, integralmente automatizável** |
| **C** | Remover as 3 definições mortas confirmadas de código duplicado (ex.: `get_sidebar_menu_settings_v1`/`_v2`/`_v3` se B confirmar zero chamadores externos; idem para `update_sidebar_menu_process_fields_v4` se aplicável) | B (precisa da confirmação de chamadores) | Médio (remoção de código, mesmo que morto) | `menu_settings.py` | `pytest -q` completo + `python -m pyflakes appgenesis/menu_settings.py` antes/depois de cada remoção individual, um commit por função removida | B concluída com confirmação individual por função | Nenhum chamador quebrado, contagem de testes inalterada | 1 commit por função — revert pontual trivial | Pequeno por commit, vários commits | Sim, mas **cada remoção individual deve ser revista por humano antes do commit**, dado o histórico de "última definição vale" já ter mascarado bugs antes |
| **D** | Unificar a verificação de permissão: fazer os 5 handlers que hoje duplicam a lógica inline passarem a chamar `_require_menu_settings_owner_v1` (sem alterar a regra de negócio, só remover duplicação) | B | Alto (toca os 6 handlers de escrita, área com histórico de incidentes) | `settings_handlers.py` | Testes de permissão explícitos por aba (parte da Fase A) correndo antes e depois de cada handler migrado, um commit por handler | A e B concluídas | Comportamento de bloqueio idêntico ao atual para os 3 perfis (sem permissão, admin não-Owner, Owner) em todas as 6 abas | 1 commit por handler | Pequeno por commit | **Não — exige validação manual em browser por aba após cada handler migrado, dado o Risco #4 herdado (30 incidentes documentados na área)** |
| **E** | Consolidar cobertura de teste desigual (Campos Subsequentes com 1 teste; Listas com 9 testes espalhados por 4 ficheiros) num ficheiro canónico por aba, sem remover nenhum teste existente | A | Baixo | `tests/*` | `pytest -q` | A concluída | Nenhum teste perdido, apenas reorganizado/complementado | trivial | Médio | Sim |
| **F** (só se houver pedido de negócio explícito e isolado) | Extrair `menu_settings.py`/`settings_handlers.py` por domínio de aba (ex.: `process_settings/lists/`, `process_settings/additional_fields/`) preservando rotas e comportamento — versão com escopo reduzido da Fase 5-12 do plano original | A, B, C, D, E todas concluídas e validadas em produção | **Crítico** (é exatamente a reescrita que a refatoração anterior classificou como "fora do âmbito de uma fase autónoma") | `menu_settings.py`, `settings_handlers.py`, templates, JS | Suite completa + validação manual completa de todas as 6 abas × 3 perfis × múltiplas entidades/processos (a matriz da secção 7 na íntegra) | Pedido de negócio explícito do utilizador, não decisão unilateral | Zero regressão confirmada manualmente, não só por pytest | Reversão de branch completa, não só de commit | Grande (semanas, não uma sessão) | **Não — precisa decisão e acompanhamento humano constante, tal como a refatoração anterior tratou Sessões/Menu** |

**Fases explicitamente removidas do plano original e porquê**: as Fases 13 ("remover legado") e 14
("otimização de performance") do pedido de 18 fases ficam subsumidas em C e numa futura fase pós-F,
respetivamente — criá-las como fases autónomas antes de F seria prematuro, porque não há ainda
arquitetura nova para a qual "migrar" o legado. As Fases 2-4 do plano original (contexto comum,
controlador único de abas, utilitários de formulário) já estão parcialmente resolvidas por
`appgenesis/process_settings/` (contexto/abas) e `configurable_items_manager_core_v1.js`
(utilitários de formulário partilhados por Listas e Campos Adicionais) — uma fase F com escopo
reduzido deve generalizar essas duas peças já existentes, não recriá-las do zero.

---

## 11. Documento criado

- `docs/refactoring/process-settings-phase-0-assessment.md` (este ficheiro).
- Referência adicionada em `docs/refactoring/final-summary.md` (ver secção 13) — uma linha, sem
  alterar nenhum conteúdo existente.

---

## 12. Restrições desta fase — confirmação de cumprimento

- Lógica funcional: não alterada (zero edição em `.py`/`.js`/`.html`).
- Ficheiros: nenhum movido, nenhum renomeado, nenhum removido.
- Rotas, persistência, templates: não tocados.
- Nenhum campo novo adicionado.
- Fase 1 não iniciada.
- Sem PowerShell, sem scripts `.ps1`, sem scripts temporários de patch.
- Sem commits de refatoração funcional (nenhum commit criado nesta fase até este ponto — commit,
  se desejado, fica a critério do utilizador após revisão deste documento).

---

## 13. Validação final da Fase 0

Comandos executados para confirmar o cumprimento das restrições (ver secção seguinte para os
resultados reais, capturados no momento da entrega):

- `git status` — confirmar que só ficheiros de documentação novos aparecem como untracked/modified.
- `git diff` — confirmar zero diferenças em ficheiros funcionais.

### Ficheiros analisados nesta fase (leitura apenas)

`docs/refactoring/final-summary.md`, `risk-map.md`, `current-architecture.md`,
`phase-3-summary.md`, `phase-7-summary.md`, `phase-8-summary.md`,
`issue-27-handlers-migration-report.md`; `templates/new_user.html`;
`appgenesis/routes/profile/settings_handlers.py`; `appgenesis/menu_settings.py`;
`appgenesis/process_settings/{__init__.py,admin_tabs.py,context_builder.py,menu_origin.py}`;
`static/js/modules/process_lists_manager_v1.js` (parcial, 40 linhas);
`static/js/modules/process_lists_runtime_v5.js` (parcial, 40 linhas);
`static/js/modules/settings_process_tabs.js` (parcial);
`static/js/modules/settings_default_tab.js` (parcial);
`static/js/modules/process_field_options_resolver_v1.js` (parcial); listagem de
`tests/*.py` relevantes por `grep`/`glob` (conteúdo dos ficheiros de teste não lido linha a linha,
só contados os `def test_`).

### Ficheiros alterados/criados nesta fase

- Criado: `docs/refactoring/process-settings-phase-0-assessment.md` (este ficheiro).
- Alterado: `docs/refactoring/final-summary.md` (uma linha de referência, ver secção 11).
- Nenhum outro ficheiro do repositório foi alterado.

### Resumo executivo

As 6 abas de configuração de processo (Geral, Configuração dos campos, Campos Adicionais, Campos
Quantidade, Listas, Campos Subsequentes) partilham dois ficheiros gigantes
(`menu_settings.py`, 5307 linhas; `settings_handlers.py`, 3071 linhas) que também servem Sessões —
a área com o histórico de incidentes documentado mais denso do projeto (30 regras
`APPGENESIS_SESSOES_V4`-`V30`). Uma refatoração anterior de 11 fases já mapeou esta zona e decidiu,
de forma explícita e documentada, não a tocar autonomamente. A concorrência de scripts citada no
pedido original existe, mas é menos grave do que descrito: apenas 2 dos 5 ficheiros "Listas" citados
estão realmente ativos hoje (`process_lists_manager_v1.js` como editor,
`process_lists_runtime_v5.js` como runtime — uma separação editor/runtime que já existe
organicamente); os outros 3 são órfãos confirmados, já avaliados e preservados por decisão anterior.
O risco real mais concreto encontrado nesta fase, não documentado anteriormente com este nível de
detalhe, é a duplicação de gerações dos normalizadores de Campos Adicionais (7 definições) e Campos
Subsequentes (3 definições, com lógica de operador diferente entre gerações) e a inconsistência de
verificação de permissão entre handlers (Geral usa o helper partilhado; Listas duplica a lógica
inline).

### Recomendação para a próxima fase

Aprovar este documento e avançar apenas para a **Fase A** (testes de proteção fechando as células
⬜ da matriz da secção 7) e **Fase B** (leitura completa dos pontos de risco ainda não confirmados —
concorrência real nos JS de Listas, merge parcial vs. substituição total de JSON) da sequência
revisada da secção 10 — ambas de risco baixo/nulo e sem escrita de código funcional. **Não
recomendo** avançar diretamente para qualquer fase que edite `menu_settings.py` ou
`settings_handlers.py` (fases C, D, F da secção 10) sem essas duas fases prévias e sem confirmação
explícita e isolada do utilizador para cada uma, dado o histórico de incidentes desta área.
