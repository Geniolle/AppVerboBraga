# Inventário técnico — AppGenesis (Fase 0)

> Documento gerado como parte da Fase 0 da refatoração `refactor/appgenesis-process-architecture`.
> Levantamento read-only — nenhum ficheiro funcional foi alterado para produzir este documento.

## 1. Estrutura atual do projeto

```
appgenesis/
  app.py                      # FastAPI app real (usada em produção)
  core.py                     # hub de compatibilidade (re-export explícito, 166 linhas, __all__ com 79 símbolos)
  config/                     # settings.py
  db/                         # engine/session (session.py) + bootstrap.py
  models/                     # Entity, Member, MemberEntity, User, Department/Role, Profile, SidebarMenuSetting, enums, modules/*
  modules/                    # core/ e treasury/ — pacotes VAZIOS (stubs para módulos comerciais futuros)
  admin_subprocesses/         # motor reutilizável de subprocessos administrativos (registry, service, models, repositories/*)
  process_settings/           # admin_tabs.py, context_builder.py, menu_origin.py
  menu_settings.py            # 4848 linhas — normalização/CRUD de sidebar_menu_settings (o maior ficheiro do projeto)
  dynamic_process_layout.py   # 437 linhas — decide layout (lista vs registo único) de processos dinâmicos
  routes/
    auth/        users/        entities/        profile/        empresa/        webhooks/
    (cada um com router.py + handlers .py; existem também shims *_routes.py de 4 linhas na raiz de routes/)
  services/
    __init__.py  (wildcard-hub: reexporta 11 módulos via `import *`)
    legacy.py    (wildcard-hub de 2º nível, reexporta 7 módulos de services/ via `import *`)
    page.py (1508 linhas), permissions.py, profile.py, process_tabs.py, session.py, auth.py,
    entities.py, user_status.py, user_system.py, user_entity_scope.py, user_member.py,
    auth_profile_entity_scope.py, passwords.py, phone_country.py, navigation_context.py,
    navigation/, modules/ (pacotes vazios/stub)
  repositories/               # entity_repository.py, profile_repository.py, user_repository.py, modules/, navigation/
  schemas/                    # auth.py, entity.py, user.py, modules/, navigation/
  use_cases/
    users/create_user.py      # único use case "puro" já existente — referência de padrão para a Fase 3
  integrations/oauth.py
  i18n/{pt,en,es,fr}.json

web_app.py                    # entrypoint ASGI na raiz
scripts/                      # ver secção 9
templates/                    # Jinja2, base.html + partials/ + macros/admin_subprocess.html
static/{css,js}/              # static/js/new_user.js + static/js/modules/*
tests/                        # ver secção 13
docs/ui-style-guide.md, docs/refactoring/ (este diretório)
```

**Nota importante**: o `README.md` já descreve esta separação por `routes/services/repositories/schemas` como resultado de uma refatoração anterior. Ou seja, o projeto **já não é um monólito plano** — grande parte do objetivo geral pedido (separação por domínio/serviço/repositório) já foi iniciada em rondas de trabalho anteriores. O que falta, tal como o levantamento abaixo evidencia, é principalmente: (a) remover os wildcard imports remanescentes, (b) quebrar `services/page.py` e `menu_settings.py` que ainda concentram lógica de múltiplos domínios, (c) decidir a relação entre a proposta `appgenesis/domains/` deste plano e a arquitetura `appgenesis/admin_subprocesses/` **que já existe e já cumpre parte do mesmo papel** (ver `risk-map.md`, ponto crítico #1).

## 2. Principais domínios existentes

| Domínio | Onde vive hoje |
|---|---|
| Autenticação/sessão/convites | `routes/auth/*`, `services/auth.py`, `services/session.py`, `services/passwords.py`, `integrations/oauth.py` |
| Entidades (tenant) | `routes/entities/*`, `services/entities.py`, `repositories/entity_repository.py`, `admin_subprocesses/repositories/entity_repository.py` |
| Utilizadores | `routes/users/*`, `services/user_status.py`, `services/user_system.py`, `services/user_member.py`, `repositories/user_repository.py`, `use_cases/users/create_user.py` |
| Perfil ("Meu Perfil") | `routes/profile/profile_handlers.py`, `services/profile.py`, `services/user_entity_scope.py` |
| Página principal/administração (`/users/new`) | `routes/profile/page_handler.py`, `services/page.py` (`get_page_data`) |
| Menu lateral / configuração de processos dinâmicos | `menu_settings.py`, `services/process_tabs.py`, `dynamic_process_layout.py`, `process_settings/*` |
| Subprocessos administrativos (Entidade, Sessões, Perfil de autorização, Objeto de autorização, Menu, Utilizador*, Contas*) | `admin_subprocesses/registry.py`, `admin_subprocesses/service.py`, `admin_subprocesses/repositories/*`, `templates/macros/admin_subprocess.html` |
| Módulos comerciais/entitlements (schema pronto, sem runtime) | `models/modules/*`, `scripts/modules/seed_app_modules.py` |
| Permissões multi-tenant | `services/permissions.py` (`get_user_entity_permissions`, `is_entity_within_permissions`) |
| Empresa (perfil institucional da entidade ativa) | `routes/empresa/*` |
| WhatsApp / Webhooks | `routes/webhooks/*`, `services/whatsapp.py` |

\* `utilizador` e `contas` estão registados no `admin_subprocesses/registry.py` mas sem `repository_class` funcional — ver risk-map.

## 3. Endpoints principais por router

### auth
- `GET /`, `GET /home`, `GET /login` — páginas (`pages.py`)
- `POST /login`, `POST /signup`, `POST /logout` — `session_handlers.py`
- `GET /oauth/login/{provider}`, `GET /oauth/callback/{provider}` — `oauth_handlers.py`
- `GET|POST /users/invite/accept` — `invite_handlers.py`
- `GET|POST /password/forgot`, `GET|POST /password/reset` — `password_reset_handlers.py`

### users
- `POST /users/new` — `create_handler.py`
- `POST /users/update` — `update_handler.py`
- `POST /users/delete` — `delete_handler.py`
- `POST /users/generate-invite`, `POST /users/resend-invite` — `resend_handler.py`

### profile (o router mais grande — mistura 3 domínios: página administrativa principal, "meu perfil" pessoal, configurações de menu/sidebar)
- `GET /users/new` — `page_handler.py` (página principal de administração, apesar do nome)
- `POST /users/profile/auth-profile-save`, `/auth-profile-delete`, `/auth-objeto-save`, `/personal`, `/process-data`, `/address`, `/training`, `/whatsapp/verify` — `profile_handlers.py`
- `GET /settings/menu/sidebar-refresh-version`, `/sidebar-sections-data`
- `POST /settings/menu/sidebar-section-save`, `/sidebar-section-move-one`, `/sidebar-section-delete`, `/sidebar-sections`, `/edit`, `/create`, `/move`, `/delete`, `/field-move`, `/process-additional-fields`, `/process-fields`, `/process-quantity-fields`, `/process-lists`, `/process-subsequent-fields`, `/menu-save`, `/menu-move`, `/menu-delete` — `settings_handlers.py`

Convenção de nomes dos handlers é inconsistente (`_v1`, `_v2`, `_v6`, `_v19`, `_v25` no mesmo ficheiro) — sinal de muitas iterações sem limpeza.

### entities
- `POST /entities/new`, `/update`, `/delete`

### empresa
- `POST /empresa/update`

### webhooks
- `POST /webhooks/whatsapp` (receive), `GET /webhooks/whatsapp` (verify)

**Achado**: existem shims `routes/{auth,entity,user,profile,webhook}_routes.py` (4 linhas cada) que apenas reexportam o `router` do respetivo pacote. Não são usados por `app.py`. Candidatos a remoção após confirmar zero referências externas.

## 4. Services existentes

Ver lista completa em `appgenesis/services/*.py` (secção 1). Destaques:
- `services/page.py` (1508 linhas) — contexto de página, ver `current-architecture.md`.
- `services/permissions.py` — único ponto de cálculo de `allowed_data_entity_ids`/`allowed_structure_entity_ids`.
- `services/profile.py` — resolução de campos de perfil, incluindo `resolve_field_list_options_v1`.
- `services/process_tabs.py` — resolução de tabs/campos de subprocessos dinâmicos.
- `services/__init__.py` e `services/legacy.py` — hubs de wildcard import (ver secção 8).

## 5. Repositories existentes

- `appgenesis/repositories/{entity_repository,profile_repository,user_repository}.py` + stubs `modules/`, `navigation/`.
- `appgenesis/admin_subprocesses/repositories/{base,entity_repository,menu_repository,objeto_autorizacao_repository,auth_profile_repository,sidebar_section_repository}.py` — repositórios específicos do motor de subprocessos administrativos (padrão `AdminRepository`).

Existem **dois conjuntos de repositórios de entidade** (`repositories/entity_repository.py` genérico e `admin_subprocesses/repositories/entity_repository.py` do motor administrativo) — relação entre os dois deve ser esclarecida antes de criar um terceiro em `domains/entities/repositories.py`.

## 6. Use cases existentes

- `appgenesis/use_cases/users/create_user.py` — único use case já extraído no padrão que o plano de refatoração (Fase 3) pede como referência. Testado por `tests/test_create_user_use_case.py`.
- Todo o resto da lógica de negócio (update/delete de utilizador, entidade, perfil) ainda vive nos handlers de rota (`routes/*/*_handler.py`), com wildcard imports (secção 8).

## 7. Models existentes

| Model | Tabela | Multi-tenant |
|---|---|---|
| `Entity` | `entities` | topo do tenant; `profile_scope` (`owner`/`legado`) |
| `Member` | `members` | dados pessoais; 1:1 com `User`, 1:N com `MemberEntity` |
| `MemberEntity` | `member_entities` | **tabela de junção multi-tenant central** (`member_id`, `entity_id`, `status`) |
| `User` | `users` | sem `entity_id` direto — vínculo sempre via `Member → MemberEntity` |
| `Department`, `Role` | `departments`, `roles` | `entity_id` direto |
| `DepartmentMembership`, `DepartmentMembershipOperation`, `DepartmentMembershipRole` | — | via `member_entity_id` (herda tenant do `MemberEntity`) |
| `Profile`, `UserProfile` | `profiles`, `user_profiles` | catálogo global, sem `entity_id` |
| `SidebarMenuSetting` | `sidebar_menu_settings` | **global ao sistema**, sem `entity_id` — escopo por entidade fica dentro do JSON `menu_config` |
| `AppModule`, `EntityModuleEntitlement`, `SidebarMenuItem` | `app_modules`, `entity_module_entitlements`, `sidebar_menu_items` | infraestrutura de módulos pagos — schema pronto, sem consumidor em runtime |

## 8. Scripts operacionais

Ver detalhe completo em `current-architecture.md` secção "Bootstrap e scripts". Resumo: shims de 6 linhas na raiz → lógica real em `scripts/`. Existe um cluster grande de scripts pontuais `_v1`/`_v2` de diagnóstico/reparação/backfill da feature "Meu Perfil" e do encoding (mojibake), acumulados ao longo do tempo e nunca removidos.

## 9. Templates e assets principais

- `templates/new_user.html` — template central da página `/users/new` (administração + meu perfil + menu). É o alvo de todas as regras de UI do `AGENTS.md`.
- `templates/macros/admin_subprocess.html` — macro genérico do motor de subprocessos administrativos.
- `static/js/new_user.js` — orquestrador principal do frontend (ficheiro aberto pelo utilizador nesta sessão).
- `static/js/modules/*` — managers reutilizáveis (`appgenesis_cancel_controller_v1.js`, `process_lists_manager_v1.js`, `process_fields_config_manager_v7.js`, `process_subsequent_fields_manager_v1.js`, `process_quantity_fields_manager_v1.js`, `admin_subprocesses_v1.js`, `process_field_options_resolver_v1.js`, etc.)
- `static/css/ui-standards.css`, `static/css/modules/*`.

## 10. Dependências de `appgenesis.core`

23 ficheiros fazem `from appgenesis.core import *`; 16 ficheiros fazem `from appgenesis.services import *` (que por sua vez reexporta via `services/__init__.py`/`services/legacy.py`). Lista completa e cadeia de wildcard em `risk-map.md` ponto #2.

## 11. Imports wildcard (`import *`)

53 ocorrências mapeadas. Padrão dominante: cada handler de rota faz **duplo wildcard** (`from appgenesis.core import *` + `from appgenesis.services import *`). Detalhe ficheiro:linha em `risk-map.md`.

## 12. Pontos de risco

Ver `risk-map.md` (documento dedicado).

## 13. Pontos multi-tenant

- Não existe middleware/dependency central de tenant. Cada handler chama explicitamente `get_user_entity_permissions(session, user_id, login_email, selected_entity_id)` (`services/permissions.py:67`).
- `allowed_data_entity_ids` (dados operacionais) e `allowed_structure_entity_ids` (estrutura/tenant) são conjuntos **distintos** — gestores de tenant não acedem automaticamente a dados operacionais de entidades "Legado". Regra de negócio subtil, documentada em comentário no próprio código.
- `SidebarMenuSetting` é global (sem `entity_id`); o escopo por entidade é aplicado via `visibility_scope`/`profile_scope` dentro do JSON `menu_config`, não por FK — qualquer refatoração de menu/módulos precisa preservar este modelo.

## 14. Pontos de Owner/Legado

- `Entity.profile_scope` (`owner` / `legado`, via `settings.ENTITY_PROFILE_SCOPE_*`).
- `can_manage_tenant_structure` em `services/permissions.py`: admin **e** (vínculo ativo com entidade Owner **ou** não existe nenhuma Owner ativa — "bootstrap gap" documentado no código).

## 15. Pontos de módulos pagos/core

- Tabelas e models (`app_modules`, `entity_module_entitlements`, `sidebar_menu_items`) existem e são semeadas por `scripts/modules/seed_app_modules.py`.
- **`require_module_access` não existe em lugar nenhum do código.** Nenhum handler ou serviço lê `EntityModuleEntitlement` em runtime. `appgenesis/modules/core/` e `appgenesis/modules/treasury/` estão vazios.
- Conclusão: a Fase 5 do plano (tornar módulos a fonte oficial de acesso/menu) é trabalho **novo**, não uma migração de algo parcialmente feito.

## 16. Pontos de processos dinâmicos

- `resolve_field_list_options_v1` → `services/profile.py:966`
- `normalize_menu_process_additional_fields_v3` → `menu_settings.py` (definida duas vezes no ficheiro — ver risk-map)
- `resolve_subprocess_section_fields_v1`, `is_system_hardcoded_process` → `services/process_tabs.py:330`/`:320`
- `resolve_dynamic_process_layout_config` → `dynamic_process_layout.py:288`
- Regras de negócio detalhadas (3 fontes de lista: manual/automatic/field_list, detecção de ciclo, proibição de hardcode) já documentadas em `AGENTS.md` secções 16 e "APPGENESIS_LIST_FIELD_RESOLUTION_RULE_V1".
