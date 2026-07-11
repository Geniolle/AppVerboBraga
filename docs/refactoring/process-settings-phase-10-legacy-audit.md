# Fase 10 — Auditoria final de legado: abas de configuração dos processos

Documento isolado de auditoria. **Nenhum código executável foi alterado ou removido para o
produzir** — apenas leitura (`Read`/`Grep`/`Glob`/`git log`/`git show`) e execução de testes já
existentes. Esta fase cataloga o que resta de wrapper/alias/reexport/compatibilidade/chamada
indireta após as Fases 1–9 (`ba56d67d`..`ec2f3a4f`), sem julgar se deve ser removido — essa decisão
fica para uma fase futura com aprovação explícita do utilizador, conforme a Fase F do plano revisado
em `process-settings-phase-0-assessment.md` secção 10.

Estado de partida: Fase 9 concluída em `ec2f3a4f` (`refactor(process-settings): separate process
settings services`), que moveu a maior parte de `menu_settings.py` (então ~2900 linhas) para
`appgenesis/services/process_settings/` (`normalizers.py`, `additional_field_service.py`,
`field_service.py`, `quantity_field_service.py`, `subsequent_field_service.py`, `list_service.py`),
reduzindo `menu_settings.py` para 1594 linhas — um hub de orquestração (`get_sidebar_menu_settings`
+ cadeia de wrappers de Listas, CRUD de menu) mais reexports.

---

## 1. Funções aparentemente mortas

**Nenhuma função morta nova foi encontrada nesta fase.** As Fases 2–6 (`e6bf7d1d`, `20a4cec6`,
`c9b8b36c`, `737856b8`/`e62d89ca`, `7c70b578`) já removeram, com confirmação de zero chamadores por
grep exaustivo, todas as gerações mortas conhecidas até esta sequência começar:

| Item removido | Fase/commit | Confirmação |
|---|---|---|
| `normalize_menu_process_subsequent_fields` (2 gerações antigas) + `_normalize_subsequent_field_operator_v2` | `20a4cec6` | Teste estrutural atualizado para exigir exatamente 1 definição |
| `normalize_menu_process_additional_fields` (6 gerações antigas) + 2 `update_sidebar_menu_additional_fields` sem sufixo (incluindo bug latente `raw_fields=raw_fields`) | `c9b8b36c` | Teste estrutural + import órfão removido de `profile_handlers.py`/`page_handler.py` |
| `menu_section_form.js` (órfão) | `e6bf7d1d` | Zero `<script src>`, zero import |
| `force_lista_tab_v1.js`, `process_lists_v1.js`, `process_lists_runtime_v3.js` | `7c70b578` | Zero referência em templates/JS/Python/testes; razão de preservação (`scripts/restore_template.py`) já removida em `b15df9b5` |

Duas suspeitas de código morto do assessment original (`update_sidebar_menu_process_fields_v4`,
`normalize_menu_process_visible_fields_v4`, `update_sidebar_menu_additional_fields_v4`) foram
**disprovadas** (Fase 3/4, `737856b8`): são as implementações reais, únicas chamadoras dos
wrappers sem sufixo — ver secção 2.

## 2. Wrappers confirmados (arquitetura deliberada, não legado a remover)

Cada par abaixo é um wrapper fino → implementação real, confirmado por leitura direta do corpo e
por grep exaustivo de chamadores. É a arquitetura final, não uma duplicação pendente:

| Wrapper (nome público) | Implementação real | Ficheiro | Chamador externo único |
|---|---|---|---|
| `update_sidebar_menu_process_fields` | `update_sidebar_menu_process_fields_v4` | `field_service.py:626,423` | `settings_handlers.py`/`field_handlers.py` |
| `normalize_menu_process_visible_fields` | `normalize_menu_process_visible_fields_v4` | `field_service.py:231,152` | idem |
| `get_menu_process_default_visible_fields` | `get_menu_process_default_visible_fields_v4` | `field_service.py:142,89` | idem |
| `update_sidebar_menu_additional_fields_v1` | `update_sidebar_menu_additional_fields_v4` | `additional_field_service.py:377,326` | `additional_field_handlers.py:364` |
| `resolve_menu_key_alias` | `_resolve_legacy_menu_alias` | `normalizers.py:207,202` | usado em todos os 6 módulos de handler + `settings_handlers.py` |

Todos protegidos por teste estrutural dedicado (`test_process_*_no_duplication_v1.py`), que falha se
uma nova geração for introduzida ou se o wrapper deixar de delegar para a implementação nomeada.

## 3. Aliases

- **`resolve_menu_key_alias` / `_resolve_legacy_menu_alias`** (`normalizers.py:202-208`) — mesmo
  corpo, dois nomes: o prefixado `_` é a convenção interna do pacote `services/process_settings/`,
  o nome público é o usado por todo o código fora desse pacote (handlers, `menu_settings.py`). Não é
  duplicação de lógica, é fachada pública/privada intencional.
- **`get_sidebar_menu_settings`** (`menu_settings.py:1289,1326,1373`) — não é bem um "alias" no
  sentido de nome alternativo permanente: é reatribuição sequencial do mesmo nome de módulo
  (`get_sidebar_menu_settings = get_sidebar_menu_settings_vN`), documentada em detalhe na secção 6
  (Monkeypatches).

## 4. Reexports

`appgenesis/menu_settings.py:1-154` reexporta (via `import ... from appgenesis.services.process_settings.*`
sem uso local de todos os nomes) o conjunto completo de constantes/funções movidas nas Fases 1–9,
para preservar os chamadores externos existentes sem alterar `settings_handlers.py`,
`page_handler.py`, `profile_handlers.py`, `scripts/*.py` e os repositórios em
`admin_subprocesses/repositories/`. Confirmado por grep: 32 ficheiros fazem
`from appgenesis.menu_settings import ...` (ver secção 7 dos testes/scripts). Isto é o mecanismo
central que tornou a Fase 9 "sem alteração de comportamento" possível — remover qualquer um destes
reexports sem migrar todos os 32 ficheiros simultaneamente quebra imports em produção.

Reexport explícito e documentado por comentário (não uma descoberta desta fase, já anotado no
código): `settings_handlers.py:66-78` reexporta `_debug_process_editor_flow_enabled_v1`,
`_log_process_editor_flow_v1`, `_sanitize_users_new_settings_return_url_v1`,
`_SETTINGS_MENU_EDITOR_STAY_TARGET_V1`, `_build_settings_redirect_url`,
`_build_settings_editor_stay_redirect_url_v1`, `_require_menu_settings_owner_v1` de
`process_settings/common.py`, com o comentário: "mantidos importaveis aqui para compatibilidade com
os handlers ainda nao migrados e com testes que importam diretamente deste modulo."

## 5. Imports

- Todos os imports em `menu_settings.py:1-154` foram confirmados como usados (diretamente no corpo
  do ficheiro ou reexportados para consumo externo) — nenhum import órfão novo introduzido pela
  Fase 9. `python -m pyflakes` não foi corrido nesta fase isoladamente sobre estes ficheiros (ver
  secção 12, item pendente), mas o CI já corre `pyflakes` de forma informativa sobre `appgenesis/` e
  não bloqueia por causa dele (ruído pré-existente em `appgenesis/models/*.py`).
- `from appgenesis.routes.profile import process_settings  # noqa: F401`
  (`settings_handlers.py:37`) é um import por efeito colateral (registo de rotas `@router` dos 6
  módulos de handler da Fase 8) — o `# noqa: F401` já documenta que o linter consideraria isto um
  import não utilizado sem o supressor, mas é intencional.

## 6. Scripts

- **`scripts/apply_member_country.py`** — **achado novo desta fase, risco residual não
  documentado antes**: este script (não coberto por nenhum teste, confirmado por
  `grep -rl apply_member_country tests/` sem resultados) localiza e edita, via regex sobre o texto
  bruto do ficheiro, três blocos que presumia estarem em `appgenesis/menu_settings.py`:
  `MENU_MEU_PERFIL_FIELDS_DEFAULT`, `MENU_MEU_PERFIL_FIELD_LABELS`, `MENU_MEU_PERFIL_FIELD_OPTIONS`
  (linhas 217-281). Desde a Fase 9, estas três constantes **já não estão definidas em
  `menu_settings.py`** — foram movidas para `appgenesis/services/process_settings/normalizers.py`
  (`menu_settings.py` apenas as importa, ver secção 4). O regex de `apply_member_country.py`
  (`re.search(r"MENU_MEU_PERFIL_FIELDS_DEFAULT\s*=\s*...", menu_settings)`) já não encontra a
  atribuição no ficheiro-alvo. Como o script trata "bloco não encontrado" como no-op silencioso
  (`if default_block_match and ...`, sem `else: raise`) em vez de erro, executá-lo hoje contra
  `menu_settings.py` **não falha, mas também não faz nada** — reescreve o ficheiro com o conteúdo
  inalterado e imprime `"OK: appgenesis/menu_settings.py atualizado."`, mascarando o facto de que a
  edição pretendida não ocorreu. Não é código morto (o script corre), é um script cujo alvo foi
  deslocado pela refatoração e que falha silenciosamente — candidato a correção (apontar
  `MENU_SETTINGS_PATH` para `normalizers.py`) numa fase futura com aprovação explícita, não nesta
  fase de auditoria.
- Demais scripts que importam de `menu_settings` (`backfill_menu_hierarchy_v1.py`,
  `diagnose_meu_perfil_header_tabs_v1.py`) usam apenas nomes de função reexportados
  (`normalize_menu_process_additional_fields_v1`, `get_sidebar_menu_settings`) — continuam a
  funcionar sem alteração porque o reexport (secção 4) preserva a superfície pública.
- Scripts que fazem `UPDATE`/`SELECT` SQL direto contra a tabela `sidebar_menu_settings`
  (`apply_member_country.py`, `backfill_estado_civil_list_key_v1.py`, `check_perfil_autorizacao_db.py`,
  `sync_member_country_profile_config.py`, `limpar_meu_perfil_*.py`, `validar_meu_perfil_*.py`,
  `diagnostico_estado_civil_lista_v1.py`, `repair_mojibake.py`) não são afetados pela relocação de
  código Python — operam sobre a tabela, não sobre os módulos.

## 7. JavaScript

| Ficheiro | Estado confirmado nesta fase |
|---|---|
| `static/js/process_settings/adminProcessTabs_v1.js` (105 linhas) | **Órfão confirmado nesta fase** (item 11 do assessment da Fase 0, não confirmado até agora). Define `window.AppGenesisAdminProcessTabs_v1` com utilitários de resolução de aba (`getAdminProcessSettingsTabs_v1`, `resolveAdminProcessSettingsTab_v1`, `buildAdminProcessSettingsTabItems_v1`). Grep exaustivo confirma **zero `<script src>`** em qualquer template e **zero referência** a `AppGenesisAdminProcessTabs_v1` em qualquer outro ficheiro do repositório além de si próprio. Não removido nesta fase (regra da Fase 10: sem remoção de código executável) — candidato a remoção futura com a mesma justificação já usada para os 3 ficheiros da Fase 6, ou candidato a reaproveitamento se uma fase F futura decidir construir um controlador de abas único. |
| `process_lists_manager_v1.js` / `process_lists_runtime_v5.js` | Ativos, carregados (`new_user.html:2813,2830`). Sobreposição/condição de corrida entre os dois **não confirmada nem descartada** nesta fase — permanece item inconclusivo (ver secção 12), não lido até ao fim em nenhuma fase até agora. |
| `process_field_options_resolver_v1.js` vs `process_lists_runtime_v5.js` | Sobreposição de responsabilidade (resolução de opções de campo tipo lista) **não confirmada nem descartada** — mesmo estado do assessment da Fase 0, nenhuma fase 1-9 tocou este ponto. |
| `settings_process_tabs.js` vs `settings_default_tab.js` | Sobreposição/distinção de responsabilidade **não confirmada** — mesmo estado da Fase 0. |
| `menu_section_form.js` | Confirmado removido (`e6bf7d1d`, Fase 2) — não existe mais no repositório. |
| `force_lista_tab_v1.js`, `process_lists_v1.js`, `process_lists_runtime_v3.js` | Confirmados removidos (`7c70b578`, Fase 6). |
| `process_additional_fields_manager_v3.js`, `process_quantity_fields_manager_v1.js`, `process_subsequent_fields_manager_v1.js`, `process_fields_config_manager_v7.js`, `configurable_items_manager_core_v1.js` | Ativos, sem duplicação confirmada, sem alteração nesta fase. |

Nenhum destes ficheiros JS foi alterado ou removido nesta fase.

## 8. CSS

Nenhum ficheiro CSS dedicado às 6 abas de configuração de processo foi encontrado (grep por
`settings-tab-`/`process-settings`/`process_settings` em `static/css/` não retornou resultados). A
estilização usa classes genéricas partilhadas com o resto do editor de processo — nada a catalogar
como legado específico desta área.

## 9. Compatibilidade

- **Assinaturas, nomes públicos, rotas e comportamento preservados integralmente** nas Fases 1–9,
  por desenho explícito de cada commit (`ec2f3a4f`: "No behavior, signatures, queries, transactions,
  or entity_id handling were changed"; `c84a33d6`: "sem alterar rotas, decorators, nomes de funcao
  publicos ou comportamento").
- `entity_id` em `SidebarMenuSetting` continua **não usado para particionar** configuração por
  entidade (achado crítico de design da Fase 0, secção 7, reconfirmado nesta fase por leitura de
  `normalizers.py:338` `_resolve_sidebar_menu_settings_entity_id` e `normalizers.py:758`
  `ensure_sidebar_menu_settings_defaults` — comportamento idêntico ao descrito na Fase 0, só
  relocalizado de ficheiro). Protegido por
  `tests/test_process_lists_persistence_isolation_v1.py::test_update_process_lists_ignores_entity_id_column_by_design`.
  **Este documento reafirma, tal como a Fase 0: não tocar neste modelo sem decisão de negócio
  explícita** (ver regras de paragem no fim deste documento).

## 10. Monkeypatches

- **Cadeia `get_sidebar_menu_settings_v2 → _v3 → _v4`** (`menu_settings.py:1254-1373`), deixada
  **intencionalmente intocada na Fase 9** ("the pure-vs-impure Lists wrapper chain ... monkeypatch
  guards ... was left untouched in place due to its module-load-order dependency"). Padrão exato:

  ```python
  if "_original_get_sidebar_menu_settings_for_lists_v1" not in globals():
      _original_get_sidebar_menu_settings_for_lists_v1 = get_sidebar_menu_settings

  def get_sidebar_menu_settings_v2(session): ...  # chama _original_..._v1
  get_sidebar_menu_settings = get_sidebar_menu_settings_v2  # reatribuição de módulo

  if "_original_get_sidebar_menu_settings_for_lists_v2" not in globals():
      _original_get_sidebar_menu_settings_for_lists_v2 = get_sidebar_menu_settings
  def get_sidebar_menu_settings_v3(session): ...  # chama _original_..._v2
  get_sidebar_menu_settings = get_sidebar_menu_settings_v3
  # ... repete para _v4
  ```

  Cada camada reexecuta a mesma query SQL (`SELECT menu_key, menu_config FROM
  sidebar_menu_settings`) e recalcula `process_lists`/`process_list_options` com um normalizador
  diferente (`get_menu_process_lists_v1` → `_v2` → `normalize_menu_process_lists_v3` direto), sendo
  o resultado das duas primeiras camadas sempre sobrescrito pela última. **Confirmado, não é código
  morto** (todas as três camadas executam a cada chamada) — é trabalho redundante (3x a mesma query),
  já identificado desde a Fase 0/6 como risco de consolidação futura, e reconfirmado sem alteração
  nesta fase. Afeta as 6 abas (é a função central de leitura consumida por `services/page.py`), não
  só Listas — colapsar esta cadeia continua fora do âmbito de uma fase autónoma de auditoria.
- **Guardas `if "_original_..." not in globals()`**: padrão de monkeypatch idempotente — protege
  contra redefinição em caso de reimport do módulo (relevante em testes que podem recarregar o
  módulo). Não encontrada nenhuma ocorrência nova deste padrão fora de `menu_settings.py:1254-1373`
  nesta fase.
- Nenhum monkeypatch de teste (`monkeypatch.setattr` sobre estas funções) foi auditado nesta fase —
  fora do escopo (auditoria de código de produção, não de fixtures de teste).

## 11. Chamadas indiretas

- **`resolve_menu_key_alias`**: chamado por nome importado em 6 módulos de handler +
  `settings_handlers.py` — não há indireção maior que uma importação direta, mas fica registado
  porque é o único ponto de tradução entre o valor bruto de `menu_key` (formulário/URL) e a chave
  canónica usada em toda a camada de persistência.
- **Tradução hífen↔underscore de chave de aba** (HTML `data-process-edit-tab="campos-config"` vs.
  backend `settings_tab=configuracao_campos`): a normalização exata que faz esta tradução no
  JavaScript de navegação (`settings_process_tabs.js`) **não foi lida em detalhe nesta fase**
  (mesmo estado da Fase 0) — continua uma chamada indireta não totalmente mapeada.
  `static/js/process_settings/adminProcessTabs_v1.js` (secção 7) já implementa
  `normalizeSettingsTabKey_v1` com exatamente essa normalização (`replace(/-/g, "_")`), mas por ser
  órfão (zero consumidor), **não é ele quem resolve esta tradução em produção hoje** — a tradução
  real deve estar em `settings_process_tabs.js`, ainda não confirmado por leitura completa.
- **`get_sidebar_menu_settings` consumido por `services/page.py`**: não lido em detalhe nesta fase
  (mesma lacuna já registada na Fase 0, secção 5) — o bootstrap injetado em
  `window.__APPGENESIS_BOOTSTRAP__` depende desta cadeia de wrappers sem que o caminho completo
  `page.py → bootstrap → JS` tenha sido confirmado linha a linha.

## 12. Itens inconclusivos (herdados, não resolvidos por esta fase)

Todos os itens abaixo já estavam listados como inconclusivos no assessment da Fase 0 (secções 9 e
"riscos do pedido original não confirmados") e **continuam inconclusivos** após as Fases 1–9, porque
nenhuma delas tocou estes pontos (cada uma teve escopo mais estreito: consolidar uma geração
específica de normalizador/persistência, não investigar concorrência de runtime JS):

1. Concorrência real (listeners duplicados/`MutationObserver`) entre `process_lists_manager_v1.js`
   e `process_lists_runtime_v5.js` — não lidos até ao fim em nenhuma fase.
2. Sobreposição de responsabilidade entre `process_lists_runtime_v5.js` e
   `process_field_options_resolver_v1.js` (ambos resolvem opções de campo tipo lista).
3. Sobreposição/distinção exata entre `settings_process_tabs.js` e `settings_default_tab.js`.
4. "Atualizações amplas de JSON" (substituição total vs. merge parcial) no corpo completo de
   `update_sidebar_menu_*` — não lido linha a linha em nenhuma fase até agora, apesar da relocação
   para `services/process_settings/*.py` ter tornado os ficheiros individualmente mais pequenos e
   mais fáceis de ler por completo numa fase futura.
5. Propósito exato de `adminProcessTabs_v1.js` — **resolvido nesta fase quanto a "está em uso?"
   (não está)**, mas não quanto a "foi deixado para uma fase futura reaproveitar, ou é lixo puro?" —
   sem histórico de commit anterior a esta sequência que o explique, a intenção original não pode
   ser confirmada só por leitura de código.

Novo item inconclusivo desta fase:

6. `scripts/apply_member_country.py` (secção 6) — confirmado que o seu alvo de edição por regex já
   não existe em `menu_settings.py` desde a Fase 9, mas não foi determinado se este script ainda é
   executado por algum processo operacional (não há chamador automatizado encontrado em `scripts/`,
   CI, ou documentação) — pode já ser um script "de uso único" há muito executado e nunca mais
   necessário, ou pode ser reexecutado manualmente por alguém fora deste repositório. Não
   classificado como "provavelmente morto" (regra de paragem desta sequência de fases) por falta de
   confirmação sobre uso operacional atual.

---

## 13. Validações desta fase

- `pytest -q` sobre a suite das 6 abas (337 testes: `test_geral_menu_*`, `test_menu_settings*.py`,
  `test_process_additional_fields_*`, `test_process_fields_config_*`, `test_process_lists_*`
  (exceto os 2 ficheiros Selenium/browser já excluídos do CI), `test_process_quantity_fields_*`,
  `test_process_subsequent_fields_*`, `test_process_editor_redirect_url.py`,
  `test_admin_process_tabs_v1.py`) — **337 passed**.
- `python -m py_compile` sobre `menu_settings.py`, `settings_handlers.py`, todos os ficheiros de
  `services/process_settings/` e `routes/profile/process_settings/` — **sem erros**.
- `python -c "import appgenesis; import web_app"` — **importa sem erro** (só o aviso pré-existente
  e não relacionado de depreciação do `authlib`).
- `git status`/`git diff` revistos: nenhuma alteração de código funcional nesta fase, apenas este
  documento novo.

## 14. Restrições desta fase — confirmação de cumprimento

- Nenhuma função, wrapper, alias, reexport, script, JS ou CSS foi removido ou alterado.
- Nenhum comportamento, rota, assinatura ou query foi alterado.
- Nenhuma decisão de remoção foi tomada — todos os itens das secções 1–12 permanecem no repositório
  exatamente como estavam antes desta fase.
- Ficheiro criado: `docs/refactoring/process-settings-phase-10-legacy-audit.md` (este documento).
- Nenhum outro ficheiro alterado.
