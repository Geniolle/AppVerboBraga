# AppGenesis — Documentação técnica e plano de refatoração

Documento de referência para o agente de refatoração. Base: código atual (medições feitas em 2026-11-27), `AGENTS.md`, `AGENT_HANDOFF.md`, `docs/refactor-roadmap.md`, `docs/refactoring/*`, `docs/architecture-guidelines.md`, `docs/module-access.md`, `docs/ui-style-guide.md`, `docs/operations/*`, `graphify-out/GRAPH_REPORT.md`.

Este documento não pede autorização. Cada decisão em aberto está registrada na secção 9 com a opção escolhida e o motivo. Quando um passo exigir mudança de comportamento para o utilizador final, o agente deve implementar a opção registrada e documentar a diferença no PR.

---

## 1. Visão do produto

- SaaS multi-tenant para igrejas, em Python.
- Tenant = `Entity` (entidade). Cada entidade tem `entity_number` (Nº da entidade) e `profile_scope`:
  - `owner` → entidade 1000 (DeixaEstarService, a empresa dona do sistema). Só o owner gere estrutura do sistema.
  - `legado` → entidades operacionais (ex.: 1001 Verbo Braga). Cada uma gere os seus próprios dados.
- Novas funcionalidades comerciais devem ser módulos ativáveis por entidade (`AGENTS.md` §1, §7–9), não páginas soltas.

Perfis de utilizador (`users.system_type`, rótulos em `appgenesis/services/user_system.py`):

| Valor no BD | Rótulo na UI | Uso |
|---|---|---|
| `default` | User | utilizador comum |
| `owner` | Admin | administrador (owner = entidade 1000) |
| `super_user` | Super User | existe no seletor, sem regra específica documentada |
| `legado` | Legado | administrador de sistema legado, criado só pelo owner |

---

## 2. Stack e execução

- Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Jinja2, Postgres 16 (produção, `psycopg`), SQLite apenas para alguns testes unitários.
- Frontend: Jinja2 + JavaScript vanilla (módulos em `static/js/modules/`) + CSS em `static/css/`.
- Docker-first (`AGENTS.md` §2): `docker-compose.yml` (dev: `db` + `web`) e `docker-compose.prod.yml` (produção).
- Entrada: `web_app.py` → `appgenesis/app.py`. Sessão via `SessionMiddleware` (cookie assinado com `APP_SECRET_KEY`); `https_only` só em produção.
- Migrations: `migrations/versions/`, cadeia linear. Head atual: `entmenudata01` (revisão anterior `procrec01`). `init_db.py` aplica `alembic upgrade head`.
- CI: `.github/workflows/ci.yml`, check `CI / test`. Testes Selenium estão excluídos do comando de CI (ver §8).

Comandos de referência:

```bash
docker compose up -d db web
docker compose exec web python -m alembic current
docker compose exec web python -m alembic check
python -m pytest -q -p no:warnings tests --continue-on-collection-errors
```

Dev local sem Docker (usado em 2026-11-27): Postgres em container `appgenesis-db` (`docker compose -p appgenesis_local up -d db`), `DATABASE_URL` apontando para `localhost:5432/app_igreja` na própria linha de comando, `uvicorn web_app:app --host 127.0.0.1 --port 8000`. Não usar o `.env` de desenvolvimento sem confirmar o banco de destino (aponta para um banco remoto).

---

## 3. Mapa de código (estado medido)

### 3.1 Pacotes em `appgenesis/`

| Pacote | Conteúdo | Observação |
|---|---|---|
| `routes/` | routers FastAPI por domínio (`auth`, `entities`, `users`, `profile`, `empresa`, `webhooks`, …) | handlers ainda contêm queries SQL |
| `services/` | `page.py` (contexto da página), `permissions`, `session`, `process_tabs.py`, `auth.py`, `profile.py`, `user_entity_scope.py`, `sidebar_section_ownership.py`, `entity_menu_data.py`, `navigation_context.py`, `access_filter.py`, … | módulos grandes e com responsabilidades misturadas |
| `use_cases/` | `users/create_user.py` (único caso de uso extraído) | padrão a expandir |
| `domains/` | `auth`, `empresa`, `meu_perfil`, `modules`, `webhooks` (com `use_cases`, `repositories`, `schemas`, `permissions`) | em uso parcial |
| `repositories/` | `entity_repository`, `profile_repository`, `user_repository` | cobertura pequena |
| `shared/` | `errors`, `normalization`, `pagination`, `results` | base reutilizável |
| `web/` | `dependencies`, `responses`, `templates`, `view_context` | camada HTTP incipiente |
| `admin_subprocesses/` | motor de subprocessos administrativos: `registry.py`, `service.py`, `models.py`, `validation.py`, `repositories/*` | **arquitetura definitiva** para Entidade, Sessões, Menu, Perfil de autorização, Objeto de autorização, Utilizador (ver §5) |
| `process_settings/` | `admin_tabs.py`, `context_builder.py`, `menu_origin.py`, `normalizers.py`, `list_service`, … | configuração de processos dinâmicos |
| `models/` | SQLAlchemy: `User`, `Member`, `Entity`, `MemberEntity`, `Department`, `ProcessRecord`, `Profile`, `SidebarMenuSetting`, módulos (`AppModule`, `EntityModuleEntitlement`, `SidebarMenuItem`) | |
| `integrations/` | `oauth.py` | |
| `modules/` | `core/`, `treasury/` (vazios) | módulos pagos ainda não implementados |
| `config/`, `db/`, `i18n/`, `schemas/` | settings, bootstrap de schema, textos, validação de formulários | |
| `core.py` | removido em 2026-11-28 (etapa 2) | usar a origem do símbolo |
| `menu_settings.py` | 1720 linhas, 63 KB | ver §6 |
| `dynamic_process_layout.py` | 16 KB | layout de processos dinâmicos |

Contagens medidas agora (diferem dos documentos antigos, que estavam desatualizados):

Medição de 2026-11-28 (a de 2026-11-27 contava um comentário como import):

- `from appgenesis.core import *` / `import *` em `appgenesis/`: 0 (documentos antigos citam 23 e 53).
- Importadores explícitos de `appgenesis.core`: 25 em `appgenesis/`, 16 em `tests/`, 12 em `scripts/`.
- Funções de topo redefinidas no mesmo módulo: 0 em todo `appgenesis/`.
- SQL direto em `appgenesis/routes`: 67 linhas (34 em `routes/users`).
- Testes: 98 ficheiros em `tests/`.
- Migrations: 24 ficheiros em `migrations/versions/`.

Tamanhos atuais (linhas): `routes/profile/profile_handlers.py` 2654; `routes/profile/settings_handlers.py` 1391; `routes/profile/page_handler.py` 1283; `services/page.py` 1467; `menu_settings.py` 1720; `admin_subprocesses/registry.py` 1057.

Frontend (linhas): `templates/new_user.html` 2567; `static/js/new_user.js` 10721; `static/css/new_user.css` 7133. Estes três são o maior ponto de fragilidade do projeto.

### 3.2 Fluxo de um pedido à página administrativa

```
GET /users/new?menu=administrativo&admin_tab=<key>
  → routes/profile/page_handler.py  (resolve menu, aba, alvo inicial)
    → services/permissions.get_user_entity_permissions  (escopo do ator)
    → services/page.get_page_data  (listas, entidades, menus, flags)
    → services/process_tabs.resolve_process_tabs_v1  (abas do menu)
    → admin_subprocesses/registry.py  (AdminSubprocessConfig por aba)
    → AdminSubprocessState  → templates/macros/admin_subprocess.html
  → templates/new_user.html  (página única)
```

Escrita: formulário → `/users/new` (POST, `routes/users/create_handler.py`) → `use_cases/users/create_user.py` → redirect com `admin_tab` e `#target`.

### 3.3 Escopo de dados e permissões

- `services/permissions.get_user_entity_permissions(session, user_id, email, selected_entity_id)` devolve:
  - `allowed_data_entity_ids`: entidades onde o utilizador tem vínculo ativo (`MemberEntity`).
  - `allowed_structure_entity_ids`: entidades para estrutura (todas se `can_manage_tenant_structure`, senão só a selecionada).
  - Aliases antigos (`can_manage_all_entities`, `allowed_entity_ids`) continuam por compatibilidade.
- A lista de utilizadores (`_resolve_scoped_users` em `services/page.py`, desde PR #398) mostra só quem tem vínculo ativo na **entidade da sessão**, e só se essa entidade estiver em `allowed_data_entity_ids`; senão a lista é vazia. O filtro é feito no SQL. Com `apply_scope_filter=False` (só a lista de Administradores do sistema, só para owner) não há escopo de entidade e o filtro `system_types` vai no SQL.
- `get_page_data` sem ator usa escopo vazio (falha fechada).
- Entidade selecionada vive em `request.session["entity_id"]` (`services/session.py`). Ao entrar, a sessão recebe a primeira entidade do utilizador. O owner pode ver outra entidade só se trocar a sessão.
- Não existe `Depends()` central de autorização; cada handler chama o serviço de permissões explicitamente.

### 3.4 Motor de subprocessos administrativos

- `AdminSubprocessConfig` (frozen dataclass em `admin_subprocesses/models.py`) descreve colunas, campos, ações e ids de cartões/tabelas.
- `registry.py` mantém `ADMIN_SUBPROCESS_REGISTRY`. Configs atuais: `entidade`, `sessoes`, `authorization_profile`, `objeto_autorizacao`, `utilizador`, `admin_sistema`, `menu`, `contas` (desativado).
- `admin_sistema` (`ADMIN_SISTEMA_CONFIG`) é `replace()` de `utilizador` com ids próprios. Herda `repository_class=""`, por isso a validação emite aviso igual ao de `utilizador` (estado "ainda servido por handlers legados").
- Regra `APPGENESIS_ADMIN_SUBPROCESS_CONFIG_BASE_V1` (`AGENTS.md`): novos subprocessos entram no registry, não numa estrutura paralela.

---

## 4. Modelo de dados (tabelas relevantes)

| Tabela | Papel | Notas |
|---|---|---|
| `entities` | entidades | `entity_number` único; `profile_scope IN ('owner','legado')` (CHECK) |
| `members` | pessoas | `member_status`, `is_collaborator` |
| `member_entities` | vínculo pessoa↔entidade | `status` ativo/inativo; chave para escopo de dados |
| `users` | login | `member_id` único; `login_email` único; `account_status` (`pending`, `active`, `inactive`, `blocked`); `system_type` (default, owner, super_user, legado) |
| `user_profiles` | perfil do utilizador | |
| `sidebar_menu_settings` | menus (JSON em `menu_config`) | compatibilidade; uma linha por `menu_key` e entidade |
| `entity_menu_data` | dados por entidade dentro de um menu | PK `(entity_id, menu_key, data_key)`; criada por `entmenudata01` |
| `process_records` | registos de processos | migração `procrec01` |
| `departments` | departamentos | |
| `app_modules`, `sidebar_menu_items`, `entity_module_entitlements` | modularização paga | schema e seed existem; **nenhum serviço lê em runtime** |

Regra de menus (commit `200e4357`, `docs/operations/migrations/2026-11-27-menus-compartilhados.sql`): menus Default são uma linha por `menu_key`, criada pela entidade 1000. Dados inseridos por cada entidade ficam em `entity_menu_data`. Authorization profiles/functions de entidade pertencem a 1001 nesse estado.

---

## 5. Regras de negócio consolidadas (estado em 2026-11-27)

### 5.1 Abas de Administrativo

| Aba | Visível para | Dados | Criação |
|---|---|---|---|
| Entidade | owner (tenant structure) | entidades | owner |
| Dados da empresa | quem tem permissão de empresa | perfil da entidade selecionada | edição |
| Utilizador | todos com acesso ao menu | utilizadores **da entidade da sessão** (qualquer `system_type`) | na entidade do ator (owner: 1000) |
| Administradores do sistema | **só owner** | administradores de sistemas legados (`legado` e, na decisão de §9, `owner`) de todas as entidades | só owner, escolhe entidade legada |
| Perfil de autorização | conforme permissões | perfis | |
| Funções administrativas | conforme permissões | funções | |

### 5.2 Criação de utilizadores

- Utilizador local (`default`, `owner`, `super_user`): entidade = entidade do ator. Owner cria em 1000. Dropdown de entidade removido (PR #394).
- Administrador do sistema (`legado`): só owner, só pelo formulário da aba Administradores do sistema (campo oculto `return_admin_tab=admin_sistema`), só para entidade com `profile_scope='legado'`.
- Normal form com `system_profile=legado` é recusado no servidor.
- Entidade do ator é a primeira `MemberEntity` ativa (`get_actor_primary_entity_v1`). Ponto de atenção: um owner com mais de um vínculo ativo pode cair numa entidade que não é a da sessão.

### 5.3 Menus e sessões

- Sessões (`sidebar_section_ownership.py`): dono (owner map) e criador (creator map) gravados em `administrativo`. Só o owner altera sessões Default.
- Regras de incidente da aba Sessões (V1–V30 em `AGENTS.md`): piscar de UI, cards órfãos, `MutationObserver` duplicando render, perda de estado entre abas. Qualquer alteração que toque `process_tabs.py`, `menu_settings.py`, `admin_subprocesses/service.py`, `new_user.js` ou `admin_subprocesses_v1.js` exige validação manual do fluxo completo de Sessões.

### 5.4 Entidade 1000 vs 1001

- Números internos: `entities.id` 2 = 1000 (owner), `entities.id` 1 = 1001 (legado). Negócio usa `entity_number`, nunca `id` (memória do projeto).
- Nome "Genesis" aparece só para legado nas sessões (regra de visibilidade).

### 5.5 Administradores do sistema e isolamento da lista (concluído, PR #398)

Merge em `master` como `0f2771ea`, em produção desde 2026-11-28 (backup `appgenesis-prod-pre-pr398-20261128-062052.sql.gz`). Histórico do trabalho:

- `appgenesis/services/page.py`: `get_page_data` devolve `system_admin_active_users` e `system_admin_inactive_users`, lista sem escopo de entidade filtrada por `system_type in ('legado','owner')`.
- `appgenesis/routes/profile/page_handler.py`: aba Utilizador passa a mostrar todos os utilizadores do escopo (sem filtrar `legado`); aba Administradores do sistema usa as duas listas novas.
- Testes focados: `test_legacy_admin_tab_v1.py`, `test_create_user_use_case.py`, `test_auth_profile_hash_menu_administrativo_v1.py` → 21 passed.
- Validação (2026-11-27, servidor local com o código do branch, sessão do owner 1000 via `fetch` no navegador embutido, HTML renderizado):
  - Aba Administradores do sistema (ativos): `Owner Teste` (owner, 1000) e `Admin Legado Teste` (legado, 1001). Ambos listados, sem escopo de entidade.
  - Aba Utilizador (sessão 1000): só `Owner Teste`. Correto pelo escopo da sessão.
  - Inativos: vazio (nenhum admin inativo nos dados de teste).
  - Não validado visualmente: o painel do navegador ficou com viewport 0×0 (oculto); captura de ecrã indisponível. Não validado: aba Utilizador na entidade 1001 com admin legado listado (exige troca de entidade na sessão, sem UI conhecida; ver §6.12).
- Correções antes do PR: a lista sem escopo era calculada em cada pedido para qualquer ator (custo e dados de outros tenants em memória); passou a ser calculada só para owner, com filtro no SQL. A lista Utilizador passou a usar só a entidade da sessão.
- Validação final: HTTP real com login no servidor local (owner, admin legado, utilizador 1001); nenhum email de outro utilizador no HTML dos não-owner. Produção: 0 membros com vínculo ativo em 2 entidades, portanto sem mudança visível. Sem captura de ecrã.

Motivação registrada pelo owner: a aba Administradores do sistema é gestão do sistema. Administradores aparecem ali para manutenção do owner, e continuam a aparecer normalmente na entidade legada.

---

## 6. Dívida técnica e riscos (com evidência)

Ordenado por impacto. Os números são de 2026-11-27.

1. **Frontend monolítico.** `static/js/new_user.js` (10721 linhas), `templates/new_user.html` (2567), `static/css/new_user.css` (7133). Roadmap: etapas 5b e 5c pendentes. Alterações tendem a afetar abas não relacionadas.
2. **Queries SQL dentro de rotas.** `routes/profile/profile_handlers.py` (2654 linhas) e `settings_handlers.py` (1391). Roadmap Fase 2 pendente.
3. **Funções redefinidas no mesmo módulo.** Medido em 2026-11-28: 0 em `appgenesis/` (já resolvido em fases anteriores). Etapa 1 fica só como verificação.
4. **Duas arquiteturas para o mesmo problema.** Decisão registrada em `docs/refactoring/risk-map.md` (2026-07-05): `admin_subprocesses/` é a arquitetura definitiva para Entidade, Sessões, Menu, Perfil de autorização e Objeto de autorização. `domains/` só para Auth, Empresa, Webhooks e Meu Perfil. Sem reabrir.
5. **Módulos pagos não funcionais.** Schema e seed existem. `domains/modules/permissions.resolve_module_access` existe e tem teste (`tests/test_module_access.py`), mas nenhuma rota o chama. `AGENTS.md` §9 exige validação no backend.
6. **Mojibake.** `AGENTS.md` §3 e §5. Roadmap etapa 4 concluída, mas a regra continua valendo: validar com busca por `Ã`, `Â`, `�`, `??`.
7. **Documentação antiga.** Resolvido em 2026-11-28: `refactor-roadmap.md` tem a tabela "Estado medido em 2026-11-28"; `current-architecture.md` e `risk-map.md` têm aviso de números históricos.
8. **Grafo.** `graphify update .` rodado em 2026-11-28. `graphify-out/` é local (não versionado). Rodar de novo depois de mudar código.
14. **`is_admin_user` não chega para estrutura partilhada (corrigido em 2026-11-28).** `is_admin_user` aceita qualquer `system_type='owner'`, mesmo ligado só a entidade legado (em produção: 1 utilizador, id 4, entidade 1001). Menus, sessões e entidades são de todos os tenants: as rotas de escrita usam `_require_menu_settings_owner_v1` / `can_manage_tenant_structure`. Ainda a rever com o mesmo critério: `get_page_data` chamado só para validar permissão em `admin_lists._departments_actor_allowed` (custo alto por pedido); webhook WhatsApp sem verificação de assinatura `X-Hub-Signature-256`.
13. **Drift do Alembic (resolvido em 2026-11-28).** `entity_menu_data` não tinha modelo SQLAlchemy; `alembic check` propunha `DROP TABLE`. Criado `appgenesis/models/entity_menu_data.py` (sem mudança de schema). A tabela não tem FK para `entities`: dados órfãos se uma entidade for apagada.
9. **Ambiente local.** `.env` aponta para banco remoto (Neon). Qualquer execução local deve passar `DATABASE_URL` explícito.
10. **Testes com ruído conhecido.** 2 falhas pré-existentes e 14 erros de coleção Selenium (ver §8).
11. **Admin legado sem acesso.** `services/auth.is_admin_user` só reconhece `owner`. Administradores legados (`system_type='legado'`) não entram no menu Administrativo. Decisão pendente registrada em §9.
12. **Escopo de listas.** A aba Administradores do sistema é owner-only e lê sem escopo de entidade (§5.5). A aba Utilizador usa só a entidade da sessão. Outras listas (perfis, funções, processos) ainda devem ser auditadas com o mesmo critério.

---

## 7. Procedimentos operacionais

### 7.1 Deploy em produção (fluxo usado em 2026-11-27, PRs #390–#397)

1. Branch a partir de `master` atualizado (`git checkout master && git pull`, `git checkout -b <tipo>/<descricao>`).
2. Commits com o trailer `Co-Authored-By` que a sessão atual indicar (o modelo muda entre sessões). PR com corpo descritivo e linha `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
3. Esperar `CI / test` verde (`gh pr view <n> --json statusCheckRollup`).
4. Squash merge (`gh pr merge <n> --squash --delete-branch`). Só com CI verde.
5. Backup do banco no servidor, antes de qualquer mudança:
   ```bash
   sudo docker exec appverbobraga-db-prod pg_dump -U appgenesis -d app_igreja --no-owner | gzip > /home/ubuntu/backups/appgenesis-prod-pre-<tema>-<timestamp>.sql.gz
   gzip -t <arquivo>
   ```
6. No servidor (`/opt/appgenesis/app`):
   ```bash
   sudo git pull --ff-only origin master
   sudo docker compose -f docker-compose.prod.yml build web
   sudo docker compose -f docker-compose.prod.yml up -d web
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health   # esperado 200
   ```
7. Validar no browser (produção `verbodavidabraga.pt`): página, aba, ação principal.
8. Mudanças de dados em produção: `BEGIN; ... DO $$ ... IF n <> <esperado> THEN RAISE EXCEPTION ...; $$; COMMIT;` com contagem antes/depois e backup antes. Registrar no PR (`AGENTS.md` §17.7).

Credenciais e IP do servidor não são registrados neste documento; estão na memória local do utilizador.

### 7.2 Migrations

- Qualquer alteração estrutural passa por migration Alembic (`AGENTS.md` §10).
- Migrations que criam tabela já existente em produção devem ser idempotentes (checar `_has_table`), como `entmenudata01`.
- Validar com `alembic check` no container.

### 7.3 Testes

- Execução focada antes do commit: `python -m pytest -q -p no:warnings <ficheiros>`.
- Suíte CI (sem Selenium): `python -m pytest -q -p no:warnings tests --continue-on-collection-errors`.
- Estado atual (2026-11-28): 638 passed; 2 falhas pré-existentes (`test_new_user_html_form_action_occurrence_counts_for_geral_routes`, `test_new_user_js_keeps_stage6_wrappers_for_process_submenu_runtime`); 14 erros de coleção Selenium.
- Regra de proporcionalidade (`AGENTS.md`, "Estratégia proporcional de validação"): verificações estáticas primeiro (`node --check`, `py_compile`, `git diff --check`), depois testes focados, depois suíte.

### 7.4 Validação no browser (regras e problemas observados)

- Ferramenta: navegador embutido (`mcp__Claude_Browser__*`). Em 2026-11-27 o navegador ficou sem responder (timeout de 300 s) em `127.0.0.1:8000`, e o painel ficou com viewport 0×0 (oculto), o que impede capturas. Causas observadas: (a) Docker Desktop parado, o que derrubou o Postgres local e fez o servidor retornar 500/timeout; (b) painel oculto. Antes de validar: confirmar com `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health` (esperado 200) e `docker ps` (container `appgenesis-db` ativo).
- Alternativa quando o painel está oculto: `javascript_tool` com `fetch` (login por `POST /login` com `mode=login`, `login_mode=user`, `email`, `password`; depois `GET` das páginas e `DOMParser` sobre as tabelas). Não substitui captura visual.
- Processos de teste: um único `uvicorn` na porta 8000. Antes de subir outro, matar o processo que já ocupa a porta (`Get-NetTCPConnection -LocalPort 8000`). Instância antiga não recarrega código (sem `--reload`).
- Fluxos a validar para Administrativo: abas visíveis por perfil; criação em cada aba; redirecionamento para a aba correta; mensagem de erro de email duplicado; ausência de botões duplicados no cabeçalho de criação.

### 7.5 Dados de teste locais (não usar em produção)

Criados localmente em 2026-11-27: `owner.teste@local.test` (owner, 1000), `legado.teste@local.test` (default, 1001), `adm.legado@local.test` (legado, 1001). A senha de teste é local e não consta deste documento.

---

## 8. Estado da validação (linha de base)

| Item | Resultado |
|---|---|
| Suíte CI sem Selenium | 638 passed (2026-11-28) |
| Falhas pré-existentes | 2 (ver §7.3) |
| Erros de coleção Selenium | 14 (ficheiros `*_browser*`, `test_process_*_v1` com browser) |
| `alembic check` | limpo no banco local depois do modelo `EntityMenuData` (§6.13); head `entmenudata01` |
| `graphify` | atualizado em 2026-11-28 |
| Produção | `0f2771ea` (PR #398); mudança de dados `system_type` sem PR (§9.1) |

---

## 9. Decisões registradas (sem pedir autorização)

Estas decisões valem para o plano. Se o agente encontrar outro caminho melhor, deve documentar a alteração no PR; não deve voltar a perguntar.

### 9.1 Dados de produção movidos em 2026-11-27

- 93 utilizadores com `system_type='default'` ligados a entidades `profile_scope='legado'` foram para `system_type='legado'` (transação com verificação de 93 linhas). Backup: `appgenesis-prod-pre-move-legado-admins-20261127-150953.sql.gz`.
- Reversão, se necessária: restaurar o backup, ou `UPDATE users SET system_type='default' WHERE system_type='legado';` (isto também reverte legados criados depois da migração).
- Estado após a mudança: `legado` 93 (72 ativos, 21 inativos); `default` 1 (1000); `owner` 3.

### 9.1b Utilizador 4 passou a `legado` (2026-11-28)

- Utilizador id 4 (`IT VERBO BRAGA`, entidade 1001) tinha `system_type='owner'` sem vínculo à 1000. Passou a `legado`, a pedido do owner. Transação com verificação de 1 linha. Backup: `appgenesis-prod-pre-user4-legado-20261128-074041.sql.gz`.
- Estado após a mudança: `legado` 94, `owner` 2 (ambos na 1000), `default` 1.
- Efeito: como `is_admin_user` só reconhece `owner`, esta conta deixa de entrar no menu Administrativo até haver função configurada (etapa 7).
- Reversão: `UPDATE users SET system_type='owner' WHERE id=4;` ou restaurar o backup.

### 9.1c Função `LEGADO` na 1001 (2026-11-28, incidente)

- Incidente: com `APPGENESIS_ACCESS_FILTER_V1=1` em produção, cada utilizador só vê os menus dados por uma função da sua entidade. A única função da 1001 (`user`) era para `default`. Depois de §9.1 (93 utilizadores `default` → `legado`) e de §9.1b, os 94 `legado` da 1001 recebiam 403 "Sem acesso ao sistema".
- Correção: criada na 1001 a função `legado` (rótulo `LEGADO`, perfil `legado`, ativa) com os mesmos perfis da função `user`: `home`, `meu_perfil`, `agenda_user`. Feita pelo `FunctionsAdminRepository` dentro do container (mesma validação da UI). Backup: `appgenesis-prod-pre-funcao-legado-20261128-080236.sql.gz`.
- Verificação: `resolve_allowed_menu_keys_v1` para `legado` → `agenda`, `home`, `meu_perfil`; `get_page_data` do utilizador 4 e de outro `legado` ativo com os mesmos menus.
- Regra: antes de mudar `system_type` em produção, confirmar que a entidade tem uma função ativa para o perfil de destino (o filtro está ligado).
- Reversão: remover a função `legado` em Funções administrativas da 1001, ou restaurar o backup.

### 9.1d Membros revertidos para `default` (2026-11-28)

- O owner confirmou que os 93 utilizadores movidos em §9.1 são **membros comuns**, não administradores. A mudança de §9.1 foi revertida: os ids que eram `default` no backup `appgenesis-prod-pre-move-legado-admins-20261127-150953.sql.gz` e estavam `legado` voltaram a `default` (93 linhas, transação com verificação). Backup antes: `appgenesis-prod-pre-revert-membros-default-20261128-083129.sql.gz`.
- Estado: `default` 94, `legado` 1 (utilizador 4, IT VERBO BRAGA, administrador da 1001), `owner` 2 (1000).
- Acesso verificado: 72 membros ativos `default` da 1001 e o utilizador 4 com `agenda`, `home`, `meu_perfil` (funções `user` e `legado`). Aba Administradores do sistema: owner 1000 + IT VERBO BRAGA 1001.
- Pré-existente, não alterado: o utilizador id 3 (`default`, entidade 1000) não tem menus porque a 1000 não tem funções.
- Regra: `legado` = administrador da entidade legado, não membro.

### 9.1e Perfil "Administrativo" na 1001 (2026-11-28)

- Depois do deploy da etapa 7 (#415): criado na 1001 o perfil de autorização "Administrativo" (key `administrativo`, menu `administrativo`, ações exibir/editar/criar/eliminar) e acrescentado à função `legado`. Mesmo formato dos registos existentes (texto JSON em `entity_menu_data`). Backup: `appgenesis-prod-pre-perfil-administrativo-1001-20261128-085621.sql.gz`.
- Verificação em produção: utilizador 4 (IT VERBO BRAGA) é admin de entidade, com Administrativo + agenda/home/meu_perfil; 72 membros ativos com os mesmos 3 menus e sem admin; owner inalterado.
- Reversão: remover `administrativo` da função `legado` (Funções administrativas da 1001, como owner) ou restaurar o backup.

### 9.2 Interpretação do pedido "todos os admins na aba Administradores do sistema"

- Admin = `system_type IN ('legado','owner')`. Motivo: `owner` aparece com o rótulo "Admin" na coluna PERFIL NO SISTEMA; `legado` é o perfil dos administradores de sistemas legados.
- Utilizador local de entidade legada continua na lista da entidade (não é removido da aba Utilizador).
- (2026-11-28) Membros de entidades legado são `default`; só administradores são `legado` (ver §9.1d).
- Aba Administradores do sistema é owner-only e não aplica escopo de entidade da sessão (§5.5).

### 9.3 Admin legado e acesso ao menu

- Opção escolhida: manter `is_admin_user` só para `owner`. Admin legado acede a Administrativo por função configurada (Funções administrativas), não por mudança de `is_admin_user`. Motivo: `is_admin_user` controla várias permissões; alterá-lo sem mapeamento de funções amplia o acesso sem controlo. A refatoração pode substituir isto por resolução de perfis (`access_filter.py`), com testes.

### 9.4 Refatoração — ordem

- Seguir `docs/refactor-roadmap.md` e `AGENTS.md` §17: uma etapa por PR, com teste, validação no dev, registo no "Registo de execução", PR, CI verde, merge, deploy com backup.
- Etapas pendentes do roadmap: 5b (`new_user.js`), 5c (`new_user.css`), 6 (testes fora do CI e pyflakes bloqueante). Fases 1–4 do roadmap (`core.py`, repositórios, serviços grandes, template) estão parcialmente feitas; medir antes de cada etapa.

### 9.5 Documentos

- `AGENTS.md` §17.6 pede para não criar documentos novos sobre o mesmo assunto. Este documento foi pedido explicitamente; a partir daqui, atualizar este ficheiro e o roadmap, e não criar outro.

---

## 10. Plano de refatoração proposto

Cada etapa cabe num PR. Ordem obrigatória. Não avançar com teste vermelho, validação por fazer ou etapa aberta.

### Etapa 0 — Saneamento da base (pré-requisito)

- Concluir o trabalho em curso (§5.5): validar no browser, commit, PR, merge, deploy com backup.
- Atualizar `current-architecture.md`, `risk-map.md`, `refactor-roadmap.md` com os números medidos (§3.1).
- Rodar `graphify update .`.
- Rodar `alembic check` no container; registar o resultado.
- Critério de saída: suíte CI com mesmas falhas pré-existentes (ou menos); documentos alinhados ao código.

### Etapa 1 — Remover funções mortas e duplicadas

- Medido em 2026-11-28: 0 nomes redefinidos (§6.3). Sem trabalho; manter só a verificação abaixo.
- Para cada nome redefinido no mesmo módulo (ver §6.3): medir com grep, manter a última definição que é a viva, apagar as outras, com teste que cubra o comportamento.
- Ficheiros: `appgenesis/menu_settings.py`, `appgenesis/services/page.py`.
- Testes: `tests/test_menu_settings*`, `tests/test_geral_menu*`, `tests/test_sidebar_section_ownership_v1.py`, testes de Meu Perfil.
- Critério: nenhum nome repetido no módulo; suíte focada verde.

### Etapa 2 — Eliminar `core.py` por consumidor

- **Concluída em 2026-11-28 (`core.py` removido; `templates` vive em `appgenesis/web/templates.py`; constantes lidas como `settings.NOME`).**
- Não há `import *`. Há 53 importadores explícitos (25 `appgenesis/`, 16 `tests/`, 12 `scripts/`). Trocar cada import pela origem do símbolo (`config`, `db`, `web/templates`, …), um grupo por PR; depois remover `core.py` se não sobrar importador.
- Critério: `grep -rn "appgenesis.core" appgenesis tests` vazio; app sobe; suíte verde.

### Etapa 3 — Queries de `routes/users/*` para repositório

- **Concluída em 2026-11-28.** 0 `session.execute/scalar/get`/`select(` em `routes/users`. Regra de segurança nova em `user_repository.member_is_within_permissions`: o owner gere administradores do sistema (`legado`/`owner`) de qualquer entidade e os membros das entidades onde tem dados; deixa de poder editar/apagar/reenviar convite a utilizadores comuns de entidades legado por POST direto.

- Criar `appgenesis/repositories/user_repository.py` (já existe; expandir) e mover `select/update/delete` dos handlers de utilizadores.
- Handlers chamam `use_cases/users/*`.
- Critério: `grep -n "session.execute\|select(" appgenesis/routes/users` sem resultados de acesso direto; testes `test_create_user_use_case.py` e de utilizadores verdes.

### Etapa 4 — Partir `profile_handlers.py` e `settings_handlers.py`

- **Concluída em 2026-11-28.** Novos módulos em `appgenesis/routes/profile/handlers/`: `auth_profile.py`, `personal.py` (inclui WhatsApp), `process_data.py`, `admin_lists.py` (funções e departamentos), `profile_common.py` (helpers partilhados), `sidebar_sections.py`, `menu_subprocess.py`. Mortas removidas: `_sanitize_sidebar_section_return_url_v17`, `_is_history_process`, `_is_authorization_profile_process`, `_build_users_new_url_with_return_context_v4`, `_sanitize_users_new_return_url_post_save_v4`, `_append_after_save_marker_to_users_new_url_v4`.

- Dividir por área (pessoal, morada, formação, WhatsApp, processos dinâmicos) em `routes/profile/handlers/*.py`, mantendo as assinaturas das rotas.
- Critério: mesmo número de rotas registadas (comparar `app.routes` antes e depois); testes de perfil verdes.

### Etapa 5 — Frontend por domínio (roadmap 5b, 5c)

- **5b concluída em 2026-11-28.** `static/js/new_user.js` passou a `static/js/new_user/01_state.js` … `16_ui_feedback.js`, scripts clássicos com o mesmo escopo global, carregados pela ordem numerada em `templates/new_user.html`. Regras para mexer neles: (1) código que corre no load só pode ler nomes declarados no mesmo ficheiro ou num anterior (funções de ficheiros posteriores ainda não existem); (2) `10_runtime_wiring.js` liga os runtimes externos e por isso vem depois dos ficheiros de funções; (3) ficheiro novo = número novo e `<script>` no template (o teste `test_new_user_js_parts_v1.py` falha se faltar). Testes que procuram texto usam `tests/new_user_js_source.read_new_user_js()`.

- `static/js/new_user.js` em módulos por feature (uma fatia por PR, com `node --check` e teste).
- **5c concluída em 2026-11-28.** `static/css/new_user.css` passou a `static/css/new_user/01_base_layout.css` … `11_process_lists_agenda.css`, no mesmo ponto do template e pela mesma ordem (cascata igual). Regra nova vai para o ficheiro do componente; nunca reordenar os `<link>`. A `}` a mais pré-existente foi removida com a regra morta `.dynamic-process-list-title-group-v1` (classe sem uso desde `2f7c3e70`); `test_new_user_css_parts_v1.py` falha se voltar a haver chavetas desequilibradas.
- `static/css/new_user.css` por componente, preservando a ordem de cascata (regra §"Regra que venceu a cascata" em `AGENT_HANDOFF.md`).
- Validar desktop e mobile em cada fatia. Não repetir Selenium quando o código funcional não mudou.
- Critério: página igual antes/depois nas abas Administrativo, Sessões, Meu Perfil, Entidade.

### Etapa 6 — Módulos pagos (Fase 5 do roadmap)

- Decidir a relação entre `entity_module_entitlements` e `admin_subprocesses/registry.py` (ambos resolvem "o que está ativo"). Decisão registrada: `registry.py` continua a controlar subprocessos administrativos; entitlements controlam módulos de negócio (tesouraria, eventos, …). Não duplicar regras.
- Implementar `require_module_access(session, entity_id, module_key)` e chamá-lo nas rotas de módulo.
- Critério: rota de módulo inativo devolve 403 pelo backend (§9 de `AGENTS.md`); teste por entidade ativa e inativa.

### Etapa 7 — Acesso de admin legado

- **Concluída em 2026-11-28.** Admin de entidade = owner, ou `system_type='legado'` com o filtro por função ligado e uma função ativa que dê o menu Administrativo na entidade da sessão (`services/permissions.is_entity_admin_v1`). Pode: criar/editar/desativar/reenviar convite a membros (`default`) da própria entidade; gerir funções de perfil `default`; gerir perfis de autorização da entidade. Não pode: criar ou atribuir Admin/Super User/Legado; editar/apagar outros administradores; criar/editar/apagar funções de perfil não-`default`; mexer em estrutura partilhada (menus, sessões, entidades). Membros (`default`) nunca são admin, mesmo com o menu.

- Implementar §9.3: perfis/funções para `legado` em Administrativo, via `access_filter.py`, sem alterar `is_admin_user`.
- Critério: admin legado vê Administrativo apenas com função configurada; owner inalterado; teste de ambos.

### Etapa 8 — Testes fora do CI e pyflakes bloqueante (roadmap 6)

- Separar testes Selenium em job próprio; pyflakes bloqueante no CI.
- Critério: CI verde com pyflakes; Selenium rodando em job opcional.

---

## 11. Checklist por etapa (obrigatório)

1. Ler `AGENTS.md` (§13–§17) e a secção do roadmap.
2. Alterar só o escopo da etapa.
3. Adicionar ou atualizar testes do que mudou.
4. `node --check` (JS), `python -m py_compile` (Python), `git diff --check`.
5. Testes focados; depois suíte CI sem Selenium.
6. Mojibake: buscar `Ã`, `Â`, `�`, `??` nos ficheiros alterados.
7. Validar no dev: página real, logs sem traceback, menus e módulos não quebraram.
8. Registar no "Registo de execução" do roadmap: etapa, PR, testes, validação, riscos.
9. PR para `master`; CI verde; merge; deploy com backup (§7.1).
10. Não avançar sem concluir o item anterior.

---

## 12. Glossário

- **Entidade**: tenant (igreja ou empresa). `entity_number` é o número visível (1000, 1001).
- **Owner**: entidade 1000, gere a estrutura do sistema.
- **Legado**: entidade operacional criada no sistema antigo, `profile_scope='legado'`.
- **Subprocesso administrativo**: aba configurável do menu Administrativo, definida em `registry.py`.
- **Cartão ativo/inativo**: blocos de lista separados por estado (Ativo/Inativo), padrão em `AGENTS.md`.
- **Escopo de dados**: entidades visíveis ao utilizador (`allowed_data_entity_ids`).
