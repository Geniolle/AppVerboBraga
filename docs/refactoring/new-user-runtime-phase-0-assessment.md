# Fase 0 - Avaliação do runtime `/users/new`

## Objetivo

Registar a linha de base do runtime frontend atualmente concentrado em `static/js/new_user.js`, sem
alterar comportamento. Esta avaliação serve para isolar os blocos que serão consolidados nas fases
seguintes e para evitar remoção prematura de consumidores ainda ativos.

## Resumo executivo

O ficheiro `static/js/new_user.js` continua a funcionar como orquestrador, mas ainda contém
vários runtimes históricos e concorrentes no mesmo bundle:

- pós-save com múltiplas estratégias sobrepostas;
- quantidade com renderização e sincronização próprias;
- subsequentes com aplicação de visibilidade própria;
- fallback/guard legado de campos adicionais V2;
- ativação inicial de secções do Meu Perfil por URL;
- blocos de navegação e pós-save que ainda dependem de `setTimeout` como retentativa.

Os módulos canónicos já existem para grande parte da lógica, mas o runtime principal ainda mantém
duas responsabilidades misturadas:

1. bootstrap/orquestração da página;
2. implementação histórica de várias features.

## Blocos funcionais atuais em `static/js/new_user.js`

### Bootstrap e diagnóstico

- leitura de `window.__APPGENESIS_BOOTSTRAP__`;
- flags de diagnóstico para o editor de processo e navegação;
- resolução dos registries globais:
  - `AppGenesisProcessKeysRegistryV1`;
  - `AppGenesisProcessReferenceRegistryV1`;
  - `AppGenesisAdminTargetRegistryV1`;
  - `AppGenesisProcessMenuConfigBuilderV1`;
  - `AppGenesisProcessNavigationStateV1`;
  - `AppGenesisProcessCardsVisibilityV1`;
  - `AppGenesisProcessSubmenuRuntimeV1`;
  - `AppGenesisProcessMenuRuntimeV1`.

### Navegação e shell

- normalização de menu e tab de settings;
- resolução de menu atual, target, admin tab e secção dinâmica;
- integração com `AppGenesisProcessShell`;
- ativação de menu, submenu, breadcrumbs e título ativo;
- refresh de cards/tables/search overlays;
- proteção de reload e feedback global.

### Meu Perfil

- leitura de valores do formulário e da versão readonly;
- quantidade do Meu Perfil;
- visibilidade subsequente;
- ativação inicial da secção por URL;
- preservação de secção ativa após ações de navegação;
- sincronização de payloads hidden.

### Processos dinâmicos

- renderização de quantidade por processo;
- leitura de histórico;
- layout de lista dinâmica;
- cards ativos/inativos;
- mudanças de target e secção.

### Campos adicionais

- manager legado V2;
- guard para não executar o V2 quando o V3 está presente;
- callbacks globais expostos em `window`.

### Utilizador e ações auxiliares

- geração de link de convite;
- modo de ação do create-user;
- reposicionamento do botão de convite;
- editor de sidebar sections;
- auto-dismiss de flash messages.

## APIs globais atualmente expostas

### Exposições diretas encontradas

- `window.__appgenesisGetActiveMenuKeyV1`
- `window.AppGenesisSyncUserCreateActionModeV1`
- `window.__appgenesisAddAdditionalFieldV2`
- `window.__appgenesisClearAdditionalFieldV2`

### APIs consumidas como dependências

- `AppGenesisProcessShell`
- `AppGenesisCancelControllerV1`
- `AppGenesisProcessFieldOptionsResolverV1`
- `AppGenesisConfigurableItems`
- `AppGenesisProcessKeysRegistryV1`
- `AppGenesisProcessReferenceRegistryV1`
- `AppGenesisAdminTargetRegistryV1`
- `AppGenesisProcessMenuConfigBuilderV1`
- `AppGenesisProcessNavigationStateV1`
- `AppGenesisProcessCardsVisibilityV1`
- `AppGenesisProcessSubmenuRuntimeV1`
- `AppGenesisProcessMenuRuntimeV1`

## Listeners e gatilhos

### Listeners persistentes encontrados

- `submit`
- `click`
- `formdata`
- `input`
- `change`
- `DOMContentLoaded`
- `appgenesis:profile-section-restored`

### Estratégias de retentativa

O ficheiro ainda usa vários `setTimeout` para recuperar ordem de inicialização e reprocessar o DOM.
Isto aparece, entre outros, nos blocos:

- quantidade do Meu Perfil;
- renderer readonly de quantidade;
- deduplicação de origem de quantidade;
- filtro de secção do Meu Perfil;
- restauro inicial de secção por URL;
- visibilidade subsequente do Meu Perfil;
- auto-dismiss de alertas.

Foram encontrados `33` usos de `setTimeout` em `static/js/new_user.js` no momento da linha de base.

## Inputs ocultos e atributos `data-*`

### Chaves relevantes de `data-*`

- `data-meu-perfil-section-input`
- `data-profile-section-input`
- `data-process-quantity-field-key`
- `data-process-quantity-index`
- `data-process-quantity-rule-key`
- `data-process-quantity-payload`
- `data-meu-perfil-quantity-field-key`
- `data-meu-perfil-quantity-index`
- `data-meu-perfil-quantity-rule-key`
- `data-meu-perfil-quantity-payload`
- `data-profile-section-pane`
- `data-profile-field-key`
- `data-process-additional-fields-manager-v2`
- `data-process-additional-fields-manager-v3`
- `data-appgenesis-cancel`

### Inputs hidden relevantes

- `profile_section`
- `target`
- `return_url`
- `appgenesis_after_save`
- `process_quantity_payload__<rule_key>`

## Ordem de carregamento observada em `templates/new_user.html`

### Cabeçalho

- `navigation_reload_guard_v1.js` é carregado no `head`, antes do HTML principal;
- o runtime global de reload precisa continuar antecipado porque normaliza o reload antes de o
  browser renderizar o conteúdo antigo.

### Corpo final

Os módulos canónicos são carregados antes do runtime principal e mantêm a base para a futura
consolidação:

- `process_additional_fields_manager_v3.js`
- `process_lists_manager_v1.js`
- `process_quantity_fields_manager_v1.js`
- `process_subsequent_fields_manager_v1.js`
- `process_keys_registry_v1.js`
- `process_reference_registry_v1.js`
- `admin_target_registry_v1.js`
- `process_menu_config_builder_v1.js`
- `process_navigation_state_v1.js`
- `process_cards_visibility_v1.js`
- `process_submenu_runtime_v1.js`
- `process_menu_runtime_v1.js`
- `new_user.js`

## Blocos versionados ainda presentes

### Pós-save

- `KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1`
- `POST_SAVE_CONTEXT_CAPTURE_V3`
- `RETURN_URL_POST_SAVE_CAPTURE_V4`
- `FRONTEND_RETURN_URL_POST_SAVE_V6`
- `INITIAL_PROFILE_SECTION_FROM_URL_V1`

### Meu Perfil

- `MEU_PERFIL_QUANTITY_RENDERER_V1`
- `MEU_PERFIL_QUANTITY_READONLY_RENDERER_V1`
- `MEU_PERFIL_QUANTITY_ORIGIN_DEDUP_V1`
- `MEU_PERFIL_EDIT_SECTION_FILTER_V1`
- `MEU_PERFIL_SUBSEQUENT_VISIBILITY_V1`

### Navegação e utilitários

- `ADMIN_TARGET_RESOLVER_V1`
- `ADMIN_SUBPROCESS_GROUP_V1`
- `USER_CREATE_ACTION_MODE_V1`
- `UTILIZADOR_INVITE_LINK_HEADER_V1`
- `AUTO_DISMISS_FLASH_MESSAGES_V1`

## Funções duplicadas ou concorrentes observadas

O inventário atual identifica, pelo menos, os seguintes padrões que precisam de consolidação nas
fases seguintes:

- múltiplos blocos de captura e reaplicação de contexto pós-save;
- múltiplos retries por `setTimeout` para as mesmas features;
- manager legado V2 ainda protegido por guard;
- reaplicação duplicada de secção do Meu Perfil;
- listeners de formulário que coexistem com patches globais em `HTMLFormElement.prototype`.

## Consumidores que ainda impedem remoção agressiva

Os seguintes pontos ainda têm consumidores diretos e não devem ser removidos sem migração:

- `AppGenesisSyncUserCreateActionModeV1` é referenciado pelo fluxo de criação de utilizador;
- `__appgenesisAddAdditionalFieldV2` e `__appgenesisClearAdditionalFieldV2` continuam expostos;
- `setupProcessAdditionalFieldsManagerV2` continua protegido por guard, portanto ainda existe
  caminho de execução no runtime;
- o post-save precisa continuar compatível com o contrato de `return_url` e `appgenesis_after_save`.

## Riscos residuais desta linha de base

- o runtime principal ainda faz demasiado trabalho além de bootstrap;
- o comportamento de retentativa por `setTimeout` pode mascarar problemas de ordem de carregamento;
- o manager V2 legado de campos adicionais continua presente;
- há sobreposição entre lógica de pós-save, navegação e secção inicial do Meu Perfil.

## Conclusão

Esta fase confirma que a consolidação deve começar por:

1. normalizar o contexto pós-save;
2. extrair o registry de campos do Meu Perfil;
3. consolidar quantity e subsequentes;
4. remover o fallback legado de campos adicionais;
5. reduzir `new_user.js` para orquestração.

Nenhuma regra estrutural foi alterada nesta fase.
