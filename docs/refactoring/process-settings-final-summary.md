# Resumo final — Refatoração das 6 abas de configuração de processo (Fases 0-10)

## Contexto

Este documento fecha a sequência autónoma de refatoração das 6 abas de configuração de processo
(Geral, Configuração dos campos, Campos Adicionais, Campos Quantidade, Listas, Campos Subsequentes),
iniciada com o levantamento `docs/refactoring/process-settings-phase-0-assessment.md` e concluída
com a auditoria de legado `docs/refactoring/process-settings-phase-10-legacy-audit.md`.

Esta sequência é **distinta** da refatoração anterior de 11 fases
(`refactor/appgenesis-process-architecture`, já mergeada, ver `docs/refactoring/final-summary.md`),
que mapeou esta mesma área e decidiu, de forma explícita, **não a tocar autonomamente** (ver
`risk-map.md` Risco #4: 30 regras de incidente documentadas em `AGENTS.md`,
`APPGENESIS_SESSOES_V4`-`V30`). Esta sequência trabalhou especificamente dentro dessa área,
com um plano revisado (secção 10 do assessment da Fase 0) mais estreito do que o pedido original de
18 fases: consolidar duplicação de gerações já existente por aba, extrair para módulos de
serviço/handler por domínio, e documentar o que resta — **sem** reescrever
`settings_handlers.py`/`menu_settings.py` do zero, sem migrar para repositórios reais de escrita, e
sem tocar em Sessões/Menu (que continuam em `settings_handlers.py`/`menu_settings.py`, fora do
escopo das 6 abas).

13 commits, um por unidade coerente de consolidação/extração/documentação, com a suite de testes das
6 abas corrida entre cada um.

## O que mudou, fase a fase

- **Fase 0** (`335454a5`): levantamento isolado, sem alteração de código — mapeou as 6 abas, os
  ficheiros JS ativos/órfãos, a duplicação de gerações por aba, e propôs a sequência revisada A-F
  (secção 10 do assessment), depois executada como Fases 1-10 numeradas.
- **Fase 1** (`e861a79a`, `2e76b54c`, `985a78b2`): testes de proteção para as células ⬜ da matriz
  de regressão da Fase 0 (criar/editar/remover/permissões por aba), sem alterar nenhum código de
  produção. Base que tornou seguras todas as consolidações seguintes.
- **Fase 2** (`e6bf7d1d`, Geral): consolidado `create_sidebar_menu_setting` numa única
  implementação; corrigido um bug real de `entity_id NOT NULL` na criação genuína; garantido bump de
  `sidebar_global_refresh_version` na criação/reativação; removido `menu_section_form.js` (órfão,
  confirmado sem formulário real a apontar para ele).
- **Fase 3** (`20a4cec6`, Campos Subsequentes): removidas 2 gerações mortas de
  `normalize_menu_process_subsequent_fields` e o helper exclusivo `_normalize_subsequent_field_operator_v2`,
  mantendo só a implementação canónica ativa.
- **Campos Adicionais** (`c9b8b36c`, etapa de consolidação entre as Fases 3 e 4): removidas 6 gerações mortas do normalizador (incluindo
  uma com bug latente `raw_fields=raw_fields`) e 2 definições mortas sem sufixo de
  `update_sidebar_menu_additional_fields`; removido import órfão em `profile_handlers.py`/
  `page_handler.py`; preservadas as 2 gerações genuinamente distintas e vivas (sem sufixo e `_v1`) e
  a cadeia de persistência ativa (`_v1 → _v4`).
- **Fase 4** (`737856b8`, Configuração dos campos): investigação por grep exaustivo **disprovou** a
  especulação de código morto do assessment da Fase 0 — `update_sidebar_menu_process_fields_v4` e
  `normalize_menu_process_visible_fields_v4` são as implementações reais, únicas chamadoras dos
  wrappers sem sufixo. Nenhuma alteração de código necessária; só correção de documentação.
- **Fase 5** (`e62d89ca`, Campos Quantidade): confirmado que esta aba já estava no estado mínimo
  consolidado (1 geração de normalizador, 1 de persistência), sem gerações órfãs, sem script JS
  paralelo. Nenhuma alteração de código necessária; só correção de contagem de testes na
  documentação (71 testes em 4 ficheiros, não 1).
- **Fase 6** (`7c70b578`, Listas): removidos os 3 ficheiros JS órfãos (`force_lista_tab_v1.js`,
  `process_lists_v1.js`, `process_lists_runtime_v3.js`) — a única razão de preservação
  (`scripts/restore_template.py`) já tinha sido removida antes desta sequência começar. Confirmado
  por grep exaustivo que `normalize_menu_process_lists_v1`/`_v2` e `get_menu_process_lists_v1`/`_v2`
  não são código morto, apesar de redundantes (cadeia de decoradores encadeados, ver Fase 10).
- **Fase 7** (`ba56d67d`, Geral, revisão): confirmado que não há código morto residual na aba Geral
  (create/update/move/delete/visibility já numa única geração cada). Único achado: documentação
  desatualizada sobre `menu_section_form.js` (já removido na Fase 2) — corrigida.
- **Fase 8** (`c84a33d6`): `settings_handlers.py` (então 3071 linhas) separado por domínio em
  `appgenesis/routes/profile/process_settings/` (`common.py`, `general_handlers.py`,
  `field_handlers.py`, `additional_field_handlers.py`, `quantity_field_handlers.py`,
  `list_handlers.py`, `subsequent_field_handlers.py`), sem alterar rotas, decorators, nomes públicos
  ou comportamento. Helpers partilhados movidos para `common.py`, reexportados em
  `settings_handlers.py` para compatibilidade. 506 testes passando, 1 falha externa pré-existente
  não relacionada.
- **Fase 9** (`ec2f3a4f`): `menu_settings.py` (então ~2900 linhas) separado por domínio em
  `appgenesis/services/process_settings/` (`normalizers.py`, `additional_field_service.py`,
  `field_service.py`, `quantity_field_service.py`, `subsequent_field_service.py`,
  `list_service.py`), reexportado integralmente em `menu_settings.py` para preservar todos os
  chamadores existentes. A cadeia de wrappers puro/impuro de Listas
  (`get_sidebar_menu_settings_v2/_v3/_v4`, com guardas de monkeypatch) foi deixada intocada em
  `menu_settings.py` por depender da ordem de carregamento do módulo. `general_service.py` foi
  avaliado e **intencionalmente não criado**: o código remanescente em `menu_settings.py` é o hub de
  orquestração (base de `get_sidebar_menu_settings` + cadeia de wrappers + CRUD de menu) que liga
  todos os domínios extraídos — extraí-lo acrescentaria indireção sem reduzir acoplamento.
  `menu_settings.py`: ~2900 → 1594 linhas.
- **Fase 10** (`29374e9a`): auditoria final de legado, sem remoção de código. Catalogou todos os
  wrappers/aliases/reexports/monkeypatches/chamadas indiretas confirmados como vivos e deliberados,
  e dois achados novos: `static/js/process_settings/adminProcessTabs_v1.js` é órfão confirmado (zero
  consumidor); `scripts/apply_member_country.py` falha silenciosamente hoje porque o seu alvo de
  edição por regex (constantes `MENU_MEU_PERFIL_FIELD_*`) já não está em `menu_settings.py` desde a
  Fase 9. Ver detalhe completo em `process-settings-phase-10-legacy-audit.md`.

## Arquitetura final

```
appgenesis/menu_settings.py (1594 linhas — hub de orquestração + reexports)
  - Reexporta a superfície pública completa de services/process_settings/*.py (secção "imports",
    linhas 1-154) para preservar os ~32 ficheiros consumidores existentes.
  - Mantém: get_sidebar_menu_settings (+ cadeia _v2/_v3/_v4, monkeypatch de wrapper puro/impuro),
    CRUD de menu (create/update/move/delete_sidebar_menu_setting), refresh global do sidebar,
    helpers de secção da sidebar.
  - NÃO contém mais: normalização/persistência por aba (movido para services/process_settings/).

appgenesis/services/process_settings/  (lógica de negócio por domínio, sem FastAPI/routing)
  - normalizers.py (927 linhas): constantes partilhadas + normalização de menu_key, visibility
    scope, sidebar sections, alias legado (_resolve_legacy_menu_alias / resolve_menu_key_alias),
    ensure_sidebar_menu_settings_defaults.
  - field_service.py (637 linhas): domínio "Configuração dos campos" — opções/tipos de campo,
    normalização e persistência de campos visíveis (update_sidebar_menu_process_fields).
  - additional_field_service.py (785 linhas): domínio "Campos Adicionais" — normalização,
    persistência (_v1 → _v4), reconstrução de hierarquia de menu a partir de campos adicionais.
  - quantity_field_service.py (263 linhas): domínio "Campos Quantidade".
  - subsequent_field_service.py (242 linhas): domínio "Campos Subsequentes".
  - list_service.py (344 linhas): domínio "Listas" — inclui as 3 gerações vivas mas redundantes
    (v1/v2/v3) consumidas pela cadeia de wrappers de menu_settings.py (ver Fase 10, secção 10).

appgenesis/routes/profile/process_settings/  (camada HTTP, 1 handler por domínio)
  - common.py (234 linhas): helpers partilhados (_build_settings_redirect_url,
    _build_settings_editor_stay_redirect_url_v1, _require_menu_settings_owner_v1,
    debug/log de fluxo do editor de processo), reexportados em settings_handlers.py.
  - general_handlers.py (313 linhas): Geral (edit/create/move/delete de menu).
  - field_handlers.py (214 linhas): Configuração dos campos.
  - additional_field_handlers.py (557 linhas): Campos Adicionais (o maior — inclui preservação de
    cabeçalhos de menu ao editar campos adicionais).
  - quantity_field_handlers.py (120 linhas): Campos Quantidade.
  - list_handlers.py (204 linhas): Listas.
  - subsequent_field_handlers.py (149 linhas): Campos Subsequentes.
  - __init__.py: importa todos os módulos acima para registar as rotas @router por efeito
    colateral; settings_handlers.py importa este pacote com `# noqa: F401` para o mesmo efeito.

appgenesis/routes/profile/settings_handlers.py (1472 linhas — RESIDUAL, fora do escopo das 6 abas)
  - Contém apenas Sessões (sidebar sections v19/v25) e Menu (menu_subprocess_save/move/delete_v1) —
    área de maior histórico de incidentes do projeto (AGENTS.md, APPGENESIS_SESSOES_V4-V30),
    deliberadamente não tocada por esta sequência (mesma decisão de fronteira da refatoração
    anterior, Fase 3/7 de `final-summary.md`).
  - Reexporta helpers de process_settings/common.py para compatibilidade com testes/handlers ainda
    não migrados.

appgenesis/process_settings/  (pacote pré-existente, NÃO duplicado por esta sequência)
  - admin_tabs.py: ADMIN_PROCESS_SETTINGS_TABS (fonte de verdade de rótulo/ordem/chave normalizada
    das 6 abas).
  - menu_origin.py: is_admin_menu_process_v1 (decide se as 6 abas aparecem para um processo).
  - context_builder.py: build_admin_process_settings_context_v1 (contexto para o template).
```

### Fluxo de escrita (uma aba, exemplo Listas — inalterado desde a Fase 0)

```
templates/new_user.html (form data-process-lists-manager-v1='1')
  → static/js/modules/process_lists_manager_v1.js
  → POST /settings/menu/process-lists
  → appgenesis/routes/profile/process_settings/list_handlers.edit_sidebar_menu_process_lists_handler
  → appgenesis/services/process_settings/list_service ou menu_settings (via reexport)
      .update_sidebar_menu_process_lists → normalize_menu_process_lists_v3
  → SidebarMenuSetting.menu_config (JSON) via sessão SQLAlchemy direta
  → _build_settings_editor_stay_redirect_url_v1 (redirect 303, card aberto, settings_tab=lista)
  → GET /users/new?...&settings_tab=lista
  → services/page.py monta sidebar_menu_settings/menuProcessValuesMap via
    menu_settings.get_sidebar_menu_settings (cadeia _v4, ver "Comportamentos legado preservados")
  → window.__APPGENESIS_BOOTSTRAP__
  → static/js/modules/process_lists_runtime_v5.js relê o processo/listas do bootstrap
```

## Funções canónicas por aba (o que chamar numa alteração futura)

| Aba | Normalização (chamar) | Persistência (chamar) | Handler HTTP |
|---|---|---|---|
| Geral | inline em `update_sidebar_menu_label` (`menu_settings.py`) | `update_sidebar_menu_label`, `set_sidebar_menu_visibility`, `create_sidebar_menu_setting`, `move_sidebar_menu_setting`, `delete_sidebar_menu_setting` (`menu_settings.py`) | `general_handlers.py` |
| Configuração dos campos | `normalize_menu_process_visible_fields` (`field_service.py`) | `update_sidebar_menu_process_fields` (`field_service.py`) | `field_handlers.py` |
| Campos Adicionais | `normalize_menu_process_additional_fields` (`additional_field_service.py:574`) | `update_sidebar_menu_additional_fields_v1` (`additional_field_service.py:377`) | `additional_field_handlers.py` |
| Campos Quantidade | `normalize_menu_process_quantity_fields` (`quantity_field_service.py`) | `update_sidebar_menu_process_quantity_fields_v1` (`quantity_field_service.py`) | `quantity_field_handlers.py` |
| Listas | `normalize_menu_process_lists_v3` (`list_service.py`) | `update_sidebar_menu_process_lists` (`menu_settings.py`) | `list_handlers.py` |
| Campos Subsequentes | `normalize_menu_process_subsequent_fields` (`subsequent_field_service.py`) | `update_sidebar_menu_subsequent_fields` (`subsequent_field_service.py`) | `subsequent_field_handlers.py` |

**Nunca chamar diretamente** as variantes com sufixo (`_v1`, `_v4`, etc.) a partir de código novo —
são implementações internas da cadeia wrapper→implementação (secção 2 de
`process-settings-phase-10-legacy-audit.md`); chamar sempre o nome sem sufixo/canónico da tabela
acima, exceto onde a tabela já indica que o nome canónico exposto tem sufixo (ex.: Campos Adicionais
e Campos Quantidade, cujo nome vivo já inclui `_v1`).

## Reexports mantidos (não remover sem migrar todos os consumidores)

- `appgenesis/menu_settings.py` reexporta toda a superfície pública movida para
  `services/process_settings/*.py` — consumida por ~32 ficheiros (`settings_handlers.py`, os 7
  módulos de `routes/profile/process_settings/`, `page_handler.py`, `profile_handlers.py`,
  `admin_subprocesses/repositories/{auth_profile,objeto_autorizacao,sidebar_section,menu}_repository.py`,
  `services/{profile.py,page.py}`, `scripts/{diagnose_meu_perfil_header_tabs_v1.py,
  backfill_menu_hierarchy_v1.py}`, e ~15 ficheiros de teste).
- `settings_handlers.py` reexporta de `process_settings/common.py`:
  `_debug_process_editor_flow_enabled_v1`, `_log_process_editor_flow_v1`,
  `_sanitize_users_new_settings_return_url_v1`, `_SETTINGS_MENU_EDITOR_STAY_TARGET_V1`,
  `_build_settings_redirect_url`, `_build_settings_editor_stay_redirect_url_v1`,
  `_require_menu_settings_owner_v1` — comentário explícito no código diz que é "para compatibilidade
  com os handlers ainda nao migrados e com testes que importam diretamente deste modulo".

## Scripts ativos relacionados

- `scripts/backfill_menu_hierarchy_v1.py`, `scripts/diagnose_meu_perfil_header_tabs_v1.py`: importam
  nomes reexportados de `menu_settings` — continuam funcionais sem alteração.
- `scripts/apply_member_country.py`: **risco residual confirmado na Fase 10** — o seu alvo de edição
  por regex (`MENU_MEU_PERFIL_FIELDS_DEFAULT`/`_FIELD_LABELS`/`_FIELD_OPTIONS`) já não existe em
  `appgenesis/menu_settings.py` desde a Fase 9 (movido para `services/process_settings/normalizers.py`).
  O script não falha ao correr — apenas não edita nada, silenciosamente. Não corrigido nesta
  sequência (fora do âmbito de uma fase de auditoria); precisa de correção do caminho-alvo antes da
  próxima vez que for necessário adicionar um país por este mecanismo.
- Demais scripts que fazem SQL direto sobre a tabela `sidebar_menu_settings` (ver
  `process-settings-phase-10-legacy-audit.md` secção 6) não são afetados pela relocação de código
  Python.

## Comportamentos legado preservados (não "corrigir" sem decisão de negócio)

- **Cadeia de wrappers `get_sidebar_menu_settings_v2 → _v3 → _v4`** em `menu_settings.py`
  (monkeypatch com guardas `if "_original_..." not in globals()`): 3 camadas, cada uma reexecuta a
  mesma query SQL e recalcula `process_lists` com um normalizador diferente, sendo o resultado das
  duas primeiras sempre sobrescrito pela última. Redundante mas não morto — afeta a leitura das 6
  abas via `services/page.py`. Consolidar isto é trabalho de uma fase futura aprovada
  explicitamente, não desta sequência.
- **`update_sidebar_menu_additional_fields_v1 → _v4`** e **`update_sidebar_menu_process_fields →
  _v4`**, **`normalize_menu_process_visible_fields → _v4`**: pares wrapper→implementação
  confirmados vivos e testados — não são duplicação pendente, são a arquitetura final.
- **Verificação de permissão inconsistente entre handlers**: `general_handlers.py` usa o helper
  partilhado `_require_menu_settings_owner_v1`; `list_handlers.py` duplica a mesma lógica inline
  (achado da Fase 0, não resolvido por nenhuma fase 1-10 — permanece risco de drift se uma regra de
  permissão for corrigida só no helper partilhado).
- **Tradução hífen↔underscore de chave de aba** entre HTML (`campos-config`) e backend
  (`configuracao_campos`) — normalização não totalmente mapeada (ver auditoria da Fase 10, secção 11).

## Modelo atual de `entity_id`

`SidebarMenuSetting` tem uma coluna `entity_id` (FK obrigatória para `entities.id`, com
`UniqueConstraint("entity_id", "menu_key")`), mas **não é usada para particionar configuração por
entidade**. `ensure_sidebar_menu_settings_defaults` (`normalizers.py:758`) cria uma única linha por
`menu_key`, preenchendo `entity_id` com a primeira entidade por `id` ascendente
(`_resolve_sidebar_menu_settings_entity_id`, `normalizers.py:338`) apenas para satisfazer a FK
`NOT NULL`. Todas as funções de leitura/escrita filtram exclusivamente por
`lower(trim(menu_key))`, nunca por `entity_id`. A configuração de processo é **global**; o
particionamento por entidade acontece dentro do JSON (`visibility_scope`/`profile_scope`), não ao
nível da tabela. **Isto é comportamento correto por desenho, não um bug** — protegido por
`tests/test_process_lists_persistence_isolation_v1.py::test_update_process_lists_ignores_entity_id_column_by_design`.
Qualquer tentativa futura de "aproveitar" a coluna `entity_id` para filtrar consultas introduziria
uma regressão de segregação que não existe hoje por design.

## Testes existentes

337 testes cobrem as 6 abas (medido na Fase 10, suite completa):
`test_geral_menu_handler_edit_permissions_v1.py`, `test_geral_menu_no_duplication_v1.py`,
`test_geral_menu_persistence_isolation_v1.py`, `test_menu_settings.py`,
`test_menu_settings_process_lists_v1.py`,
`test_process_additional_fields_{handler_edit_permissions_v1,manager_v3,no_duplication_v1,persistence_isolation_v1}.py`,
`test_process_fields_config_{handler_edit_permissions_v1,manager_v7,no_duplication_v1,persistence_isolation_v1}.py`,
`test_process_lists_{handler_edit_permissions_v1,manager_v1,persistence_isolation_v1}.py`
(+ `test_process_lists_{columns_editor,reusable_create}.py`, browser/Selenium, excluídos do CI),
`test_process_quantity_fields_{handler_edit_permissions_v1,manager_v1,no_duplication_v1,persistence_isolation_v1}.py`,
`test_process_subsequent_fields_{handler_edit_permissions_v1,manager_v1,no_duplication_v1,persistence_isolation_v1}.py`,
`test_process_editor_redirect_url.py`, `tests/process_settings/test_admin_process_tabs_v1.py`.

Todos os `test_*_no_duplication_v1.py` são testes estruturais (leem o código-fonte via
`inspect.getsource`/contagem de `def nome(` no ficheiro) — falham se uma nova geração duplicada for
introduzida ou se um wrapper deixar de delegar para a implementação nomeada. **Ao adicionar código
novo a qualquer um dos 6 domínios, correr estes testes primeiro** — são o mecanismo de proteção mais
sensível a regressão de arquitetura desta área.

## Decisões da Fase 10

- Nenhuma remoção de código executável — só documentação (ver
  `process-settings-phase-10-legacy-audit.md`).
- `adminProcessTabs_v1.js` confirmado órfão, mas não removido (decisão de não remover sem aprovação
  explícita, mesma régua usada para os 3 ficheiros da Fase 6, que só foram removidos depois de
  confirmação exaustiva de zero consumidor E aprovação implícita da sequência de fases já em curso).
- `scripts/apply_member_country.py` identificado como quebrado silenciosamente, não corrigido (fora
  do âmbito de uma fase de auditoria; risco residual documentado abaixo).

## Riscos residuais

1. `scripts/apply_member_country.py` faz no-op silencioso contra `menu_settings.py` desde a Fase 9 —
   precisa de correção de `MENU_SETTINGS_PATH`/regex-alvo antes do próximo uso.
2. Cadeia de wrappers `get_sidebar_menu_settings_v2/_v3/_v4` continua a executar a mesma query SQL 3
   vezes por chamada de leitura das 6 abas — não é bug, é ineficiência conhecida e documentada,
   candidata a consolidação futura aprovada.
3. Verificação de permissão duplicada inline em `list_handlers.py` (e presumivelmente nas outras
   abas exceto Geral, não confirmado individualmente) em vez de reutilizar
   `_require_menu_settings_owner_v1` — risco de drift de regra de negócio.
4. `adminProcessTabs_v1.js` órfão — zero risco de execução, risco de confusão para quem procurar "o"
   controlador de abas.
5. Sobreposição de responsabilidade não confirmada entre `process_lists_runtime_v5.js` e
   `process_field_options_resolver_v1.js`, e entre `settings_process_tabs.js` e
   `settings_default_tab.js` — nenhuma fase 0-10 leu estes ficheiros até ao fim.
6. `settings_handlers.py` (1472 linhas, Sessões + Menu) e a parte residual de `menu_settings.py`
   (1594 linhas, hub + cadeia de wrappers) continuam grandes e multi-responsabilidade — aceite como
   estado final desta sequência, não um defeito a corrigir sem pedido de negócio explícito.

## Instruções para criar ou alterar novas abas

Para adicionar uma **nova aba** de configuração de processo:

1. Adicionar a entrada em `appgenesis/process_settings/admin_tabs.py`
   (`ADMIN_PROCESS_SETTINGS_TABS`) — fonte de verdade única de rótulo/ordem/chave.
2. Criar um novo módulo em `appgenesis/services/process_settings/<dominio>_service.py` com
   `normalize_menu_process_<dominio>_fields` e `update_sidebar_menu_<dominio>_fields` — seguir o
   padrão de `quantity_field_service.py` (o mais simples, 263 linhas, sem gerações duplicadas) como
   modelo de arquitetura mínima, não `additional_field_service.py` (785 linhas, o mais complexo).
3. Criar um novo módulo em `appgenesis/routes/profile/process_settings/<dominio>_handlers.py` com o
   handler `POST /settings/menu/process-<dominio>`, reutilizando
   `_require_menu_settings_owner_v1` de `common.py` para a verificação de permissão (não duplicar
   inline — ver risco residual #3 acima) e `_build_settings_editor_stay_redirect_url_v1` para o
   redirect pós-guardar.
4. Registar o import do novo módulo em
   `appgenesis/routes/profile/process_settings/__init__.py` (efeito colateral de registo de rota).
5. Adicionar o painel no template `templates/new_user.html` com
   `data-process-edit-tab="<chave-com-hifen>"` e o manager JS dedicado em
   `static/js/modules/process_<dominio>_manager_v1.js` (seguir o padrão de
   `process_quantity_fields_manager_v1.js`).
6. Criar testes seguindo o padrão de 4 ficheiros por aba: `test_process_<dominio>_manager_v1.py`,
   `test_process_<dominio>_no_duplication_v1.py`, `test_process_<dominio>_handler_edit_permissions_v1.py`,
   `test_process_<dominio>_persistence_isolation_v1.py` — o último deve incluir explicitamente um
   teste que confirme que `entity_id` **não** é usado para filtrar/particionar (mesma regra do
   modelo atual, secção acima), a menos que uma decisão de negócio explícita mude esse modelo.
7. **Não** adicionar lógica de particionamento por `entity_id` na tabela `sidebar_menu_settings` sem
   decisão de negócio explícita — isso seria uma mudança de modelo, não uma extensão aditiva.
8. Correr a suite completa das 6(+1) abas antes de commitar (ver comando na secção "Testes
   existentes" acima) e `python -m py_compile` sobre os novos ficheiros.

Para **alterar** uma aba existente: identificar a função canónica na tabela "Funções canónicas por
aba" acima, ler o corpo completo antes de editar (nenhuma fase 0-10 leu os corpos de
`update_sidebar_menu_*` linha a linha — ver item inconclusivo #4 da auditoria da Fase 10), e correr
o teste `_no_duplication_v1` da aba antes e depois da alteração para confirmar que nenhuma nova
geração duplicada foi introduzida acidentalmente.

## Ficheiros de referência desta sequência

- `docs/refactoring/process-settings-phase-0-assessment.md` — levantamento inicial e plano revisado
  (secção 10, Fases A-F mapeadas para as Fases 1-10 numeradas efetivamente executadas).
- `docs/refactoring/process-settings-phase-10-legacy-audit.md` — catálogo detalhado de
  wrappers/aliases/reexports/monkeypatches/chamadas indiretas/itens inconclusivos.
- Este ficheiro (`process-settings-final-summary.md`) — síntese de fecho desta sequência.
- `docs/refactoring/final-summary.md` — síntese da refatoração arquitetural anterior (11 fases,
  já mergeada), que mapeou esta mesma área e decidiu deliberadamente não a tocar — ponto de partida
  desta sequência.
