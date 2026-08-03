# Arquitetura atual — AppGenesis (Fase 0)

## Visão geral

AppGenesis é uma aplicação FastAPI + SQLAlchemy + Jinja2, multi-tenant (por `Entity`), com uma
página administrativa central (`/users/new`, servida por `routes/profile/page_handler.py` +
`services/page.py`) que concentra várias abas: Entidade, Utilizador, Menu, Sessões, Perfil de
autorização, Objeto de autorização, Meu Perfil, e processos dinâmicos configuráveis.

```
Request
  → routes/<area>/router.py (registo de rotas por efeito colateral de import)
    → routes/<area>/<handler>.py
        (double wildcard: from appgenesis.core import *; from appgenesis.services import *)
      → services/permissions.get_user_entity_permissions   (autorização, por handler)
      → services/page.get_page_data                        (contexto de página, se aplicável)
      → menu_settings.py / process_tabs.py / dynamic_process_layout.py  (config de processo dinâmico)
      → admin_subprocesses/service.py + registry.py + repositories/*    (subprocessos nativos)
      → repositories/*.py ou queries diretas via SQLAlchemy Session
    → templates/new_user.html (+ macros/admin_subprocess.html)
```

## Camada de compatibilidade (`appgenesis/core.py`)

`core.py` (166 linhas) não faz `import *` ele próprio — é um hub de **re-export explícito** com
`__all__` de 79 símbolos: templates Jinja2, uma segunda instância `FastAPI` (não usada em
produção, mas instanciada ao importar o módulo), engine/`SessionLocal`, `oauth`, todas as
constantes de `settings`, funções de bootstrap de schema, os modelos principais, e reexports do
SQLAlchemy/Starlette (`select`, `func`, `Session`, `HTMLResponse`, `RedirectResponse`, ...).

`appgenesis/services/__init__.py` e `appgenesis/services/legacy.py` formam um **segundo nível de
hub**: `services/__init__.py` faz `from appgenesis.services.<módulo> import *` para 11 módulos;
`services/legacy.py` faz o mesmo para 7 módulos.

Resultado: 23 ficheiros fazem `from appgenesis.core import *` e 16 fazem
`from appgenesis.services import *` — na prática, quase todos os handlers de rota fazem os dois,
recebendo dezenas de símbolos no namespace sem import explícito. Este é o alvo da Fase 2.

## `services/page.py` — função God `get_page_data`

1508 linhas no total. `get_page_data(session, actor_user_id=None, actor_login_email="",
selected_entity_id=None)` tem sozinha ~740 linhas (L479–L1219) e resolve, na mesma função:
permissões do ator, entidade ativa/selecionada, listas de entidades para formulários, sidebar
menu settings, opções de campos dinâmicos, e os dados de "Meu Perfil" com regras de visibilidade
condicional. É o alvo natural da Fase 4.

O ficheiro também contém **duplicação de gerações**: existem duas implementações lado a lado da
lógica de visibilidade condicional do "Meu Perfil" (`_v1`, L51–178, e `_v2`, L232–478), e a função
`_apply_meu_perfil_subsequent_visibility_v2` está **definida duas vezes no mesmo ficheiro**
(L120 e L442 — a segunda definição sobrepõe a primeira em runtime; a primeira é código morto).

## `menu_settings.py` — o maior ficheiro do projeto (4848 linhas)

Concentra normalização/validação de campos de menu, listas de processo, campos "quantity",
seções de sidebar, CRUD de `sidebar_menu_settings`, resolução de aliases de menu, e o refresh
global de versão do sidebar.

**Achado crítico de manutenção**: o ficheiro acumulou gerações paralelas (`_v1/_v2/_v3/_v4`) de
quase todas as funções centrais, com **nomes redefinidos múltiplas vezes no mesmo módulo**:
- `normalize_menu_process_additional_fields_v3` definida 2x (L2807 e L3053).
- `normalize_menu_process_subsequent_fields` definida 3x (L3854, L4170, L4325).
- `get_sidebar_menu_settings` tem variantes `_v2/_v3/_v4` que, por grep de chamadores, **não são
  usadas fora deste ficheiro** — a única versão consumida externamente é a sem sufixo.

Isto significa que uma parcela do ficheiro é código morto seguro de remover, mas requer
confirmação individual por função antes de apagar (Fase 4/6), não um corte em bloco.

## `process_tabs.py` e `dynamic_process_layout.py`

- `services/process_tabs.py` (597 linhas): `is_system_hardcoded_process(menu_key)` — lista fixa
  `{"administrativo", "sessoes"}` que nunca são tratados como processo dinâmico;
  `resolve_subprocess_section_fields_v1` — resolve campos visíveis de uma secção de subprocesso
  dinâmico; `resolve_process_tabs_v1` — monta as abas de um processo a partir de
  `sidebar_menu_settings`.
- `dynamic_process_layout.py` (437 linhas): função pública única
  `resolve_dynamic_process_layout_config` — decide layout (lista vs registo único), colunas de
  tabela, e se o processo usa histórico de registos.
- Relação: `menu_settings.py` é a base de configuração persistida (JSON em
  `sidebar_menu_settings.menu_config`); `process_tabs.py` consome essa configuração para decidir
  campos/abas; `dynamic_process_layout.py` consome a mesma configuração para decidir o layout de
  renderização. `services/page.py` e `routes/profile/{page_handler,profile_handlers}.py` são os
  consumidores finais.

## Motor de subprocessos administrativos (`admin_subprocesses/`)

**Este motor já existe e já implementa parte do que o plano de refatoração propõe construir do
zero em `appgenesis/domains/`.** Arquitetura documentada no próprio `AGENTS.md`
(`APPGENESIS_ADMIN_SUBPROCESS_CONFIG_BASE_V1`):

```
URL (admin_tab=<key>) → registry.py (AdminSubprocessConfig) → repositories/<key>_repository.py
  → service.py (monta AdminSubprocessState) → templates/macros/admin_subprocess.html
  → endpoint dedicado grava e redireciona
```

Registry atual (`admin_subprocesses/registry.py`, 846 linhas):

| Config | enabled | migration_status | repository_class |
|---|---|---|---|
| `entidade` | True | native | `EntityAdminRepository` |
| `sessoes` | True | native_next | `SidebarSectionAdminRepository` |
| `authorization_profile` | True | native | `AuthorizationProfileAdminRepository` |
| `objeto_autorizacao` | True | native | `ObjetoAutorizacaoAdminRepository` |
| `utilizador` | True | native | **vazio** (ainda servido pelos handlers legados `routes/users/*`) |
| `menu` | True | native | `MenuAdminRepository` |
| `contas` | **False** | legacy_pending | vazio (feature ainda não implementada) |

A aba **Sessões** sozinha acumulou **30 regras versionadas** no `AGENTS.md` (V1 a V30) descrevendo
incidentes reais de regressão (piscar de UI, cards órfãos fora da aba, `MutationObserver`
duplicando renderização, perda de estado ao navegar entre abas, etc.) até convergir para o padrão
atual "server-render igual à Entidade". Qualquer alteração ao motor de subprocessos ou ao
`process_tabs.py`/`menu_settings.py` que sirva Sessões tem risco real de reabrir estes incidentes.

## Multi-tenant e permissões

Não existe middleware nem `Depends()` central de tenant/autorização (confirmado por grep — não há
`Depends(` em `routes/` nem `services/`). Cada handler chama explicitamente
`get_user_entity_permissions(session, user_id, login_email, selected_entity_id)`
(`services/permissions.py:67`), que devolve `allowed_data_entity_ids` (dados operacionais,
sempre = entidades vinculadas via `MemberEntity`) e `allowed_structure_entity_ids` (estrutura de
tenant, todas as entidades se `can_manage_tenant_structure`, senão só a selecionada). Aliases
"deprecated" (`can_manage_all_entities`, `allowed_entity_ids`) continuam no dict de retorno por
compatibilidade.

Contexto de entidade selecionada vive em `request.session` (cookie assinado via
`SessionMiddleware`/`APP_SECRET_KEY`), gerido por `services/session.py`.

## Módulos pagos/core

Schema e seed existem (`AppModule`, `EntityModuleEntitlement`, `SidebarMenuItem`,
`scripts/modules/seed_app_modules.py`), mas **nenhum serviço ou rota lê estes modelos em
runtime**. `require_module_access` não existe no código. `appgenesis/modules/core/` e
`appgenesis/modules/treasury/` são pacotes vazios. A Fase 5 do plano é, portanto, construção nova,
não migração de algo parcialmente feito — mas deve decidir explicitamente a relação com
`admin_subprocesses/registry.py`, que já resolve um problema adjacente (quais subprocessos estão
ativos) por um mecanismo diferente.

## Bootstrap e scripts

Ficheiros na raiz (`init_db.py`, `bootstrap_admin.py`, `smoke_test.py`, `validate_web_app.py`) são
shims de 6 linhas que chamam `scripts.<mesmo_nome>.main()`. `scripts/init_db.py` aplica migrações
Alembic até `head`. Existe um cluster grande de scripts pontuais de diagnóstico/backfill/reparação
(`_v1`/`_v2`) relacionados a "Meu Perfil" e a correção de mojibake, acumulados ao longo do tempo.

## Frontend

`static/js/new_user.js` orquestra a página, delegando a managers em `static/js/modules/*`
(cancel controller global, managers de campos adicionais/listas/quantidade/subsequentes, resolver
de opções de lista, motor de subprocessos administrativos). O `AGENTS.md` já documenta um padrão
obrigatório detalhado (editor superior + tabela paginada inferior + managers versionados) que
qualquer alteração de frontend na Fase 8 deve respeitar à risca.
