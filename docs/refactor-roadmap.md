# Refactor Roadmap

## Objetivo

Estruturar uma refatoração melhor para o `AppGenesis` sem reiniciar a reorganização já em curso.
O projeto já saiu do formato monolítico original, mas ainda mantém acoplamentos fortes entre rotas, serviços, queries SQL, templates e JavaScript do ecrã principal.

Esta proposta prioriza:

- mudanças pequenas e reversíveis;
- redução de acoplamento;
- extração de responsabilidades por domínio;
- aumento de cobertura útil de testes;
- eliminação gradual de pontos centrais de risco.

## Diagnóstico Atual

### O que já está melhor

- Já existe separação inicial por `config`, `db`, `models`, `routes`, `services`, `repositories`, `schemas`.
- Os routers novos por domínio já estão publicados em `appgenesis/app.py`.
- Há testes básicos para auth, profile, menu settings e WhatsApp.
- Há migrações, scripts operacionais e uma divisão inicial entre backend e assets.

### Estado medido em 2026-11-28

Os números abaixo desta secção são históricos. Medição atual (`wc -l`, `grep`):

| Item | Valor |
|---|---|
| `from appgenesis.core import *` / `import *` em `appgenesis/` | 0 |
| Importadores explícitos de `appgenesis.core` | 25 em `appgenesis/`, 16 em `tests/`, 12 em `scripts/` |
| Funções de topo redefinidas no mesmo módulo (`appgenesis/`) | 0 |
| SQL direto em `appgenesis/routes` (`session.execute/scalar/get`, `select/update/delete(`) | 67 linhas (34 em `routes/users`) |
| `menu_settings.py` / `services/page.py` | 1720 / 1466 linhas |
| `routes/profile/profile_handlers.py` / `settings_handlers.py` | 2654 / 1391 linhas |
| `templates/new_user.html` / `static/js/new_user.js` / `static/css/new_user.css` | 2567 / 10721 / 7133 linhas |
| Testes / migrations | 98 ficheiros / 24 migrations |
| Módulos pagos | `domains/modules/permissions.resolve_module_access` existe; nenhuma rota o chama |

### Principais problemas que ainda travam a refatoração

1. `appgenesis/core.py` continua a ser um agregador global de framework, settings, DB, modelos e utilitários.
   Hoje 24 módulos ainda dependem de `from appgenesis.core import *`.

2. As rotas continuam com lógica de aplicação e acesso a dados embutidos.
   Há pelo menos 59 ocorrências de `session.execute/select/update/delete` dentro de `appgenesis/routes`.

3. Os serviços estão grandes e misturam responsabilidades.
   Exemplos:
   - `appgenesis/menu_settings.py`
   - `appgenesis/services/page.py`
   - `appgenesis/routes/profile/profile_handlers.py`
   - `appgenesis/routes/profile/settings_handlers.py`

4. O ecrã principal continua monolítico no frontend.
   Exemplos:
   - `templates/new_user.html` com ~2000 linhas
   - `static/js/new_user.js` com ~2300 linhas
   - `static/css/new_user.css` com ~1500 linhas

5. Há duplicação de normalização e regras entre Python e JavaScript.
   Funções de processo dinâmico e de menu aparecem dos dois lados com regras semelhantes.

6. Os repositórios existem, mas ainda têm uso marginal.
   A maior parte das queries continua espalhada entre rotas e serviços.

7. Ainda existem sinais de texto corrompido/mojibake na aplicação.
   Isso precisa ser tratado como dívida transversal e não como detalhe cosmético.

## Direção Arquitetural Recomendada

Em vez de uma refatoração "big bang", a melhor estrutura é aprofundar a divisão atual em 4 camadas pragmáticas:

### 1. HTTP / Presentation

Responsável por:

- routers FastAPI;
- leitura de `Request/Form/Query`;
- conversão de erros para `RedirectResponse/TemplateResponse/JSONResponse`;
- composição mínima de contexto de página.

Estrutura sugerida:

```text
appgenesis/http/
  deps/
  presenters/
  responses/
```

Se não quiser renomear tudo agora, manter `routes/` e introduzir subpastas claras:

```text
appgenesis/routes/<dominio>/
  router.py
  handlers/
  presenters/
```

### 2. Application / Use Cases

Responsável por:

- regras de negócio de cada fluxo;
- validações de aplicação;
- coordenação entre repositórios, integrações e policies;
- retorno de DTOs/resultados sem dependência de FastAPI/Jinja.

Estrutura sugerida:

```text
appgenesis/use_cases/
  auth/
  users/
  entities/
  profile/
  menu_settings/
  dashboard/
```

### 3. Domain

Responsável por:

- entidades de domínio já existentes via models;
- regras puras;
- enums;
- policies;
- normalização reutilizável.

Estrutura sugerida:

```text
appgenesis/domain/
  auth/
  users/
  entities/
  profile/
  menu_settings/
  shared/
```

### 4. Infrastructure

Responsável por:

- SQLAlchemy repositories;
- email;
- OAuth;
- WhatsApp;
- storage de logos;
- bootstrap/migração técnica.

Estrutura sugerida:

```text
appgenesis/infrastructure/
  db/
  email/
  oauth/
  whatsapp/
  storage/
```

## Estrutura Alvo por Domínio

O melhor corte aqui não é "por tipo técnico" apenas, mas por feature.
O projeto já está perto disso nas rotas; falta levar o mesmo princípio para serviços, repositórios e frontend.

### Auth

Separar:

- login/logout/session;
- OAuth;
- convite/ativação;
- métricas do login admin.

Sugestão:

```text
appgenesis/use_cases/auth/
  login.py
  oauth_login.py
  invite_user.py
  accept_invite.py
  admin_metrics.py
```

### Users

Separar:

- criação;
- atualização;
- reenvio de convite;
- remoção/bloqueio;
- resolução de entidade do utilizador;
- políticas de permissão.

### Entities

Separar:

- criação;
- atualização;
- remoção;
- upload/logo;
- regras de `profile_scope`;
- numeração interna.

### Profile

Separar:

- dados pessoais;
- morada;
- formação;
- verificação WhatsApp;
- processos dinâmicos;
- montagem do perfil para renderização.

### Menu Settings

`appgenesis/menu_settings.py` deve virar um package próprio.

Sugestão:

```text
appgenesis/menu_settings/
  __init__.py
  constants.py
  normalizers.py
  field_options.py
  repository.py
  service.py
  visibility.py
```

Hoje esse ficheiro mistura:

- constantes;
- normalização;
- correção de texto;
- queries SQL;
- regras de negócio;
- persistência;
- ordenação;
- segurança de menus do sistema.

## Refatoração Prioritária por Fases

## Fase 0: Consolidar Base

Objetivo: parar de aumentar a dívida durante a refatoração.

Entregas:

- remover novos usos de `from appgenesis.core import *`;
- adotar imports explícitos nos ficheiros novos/alterados;
- criar guideline curta para handlers, use cases e repositories;
- ampliar testes antes de mexer nos módulos mais instáveis.

Testes a adicionar primeiro:

- `tests/routes/test_users_create.py`
- `tests/routes/test_entities_create.py`
- `tests/routes/test_profile_personal.py`
- `tests/services/test_page_context.py`
- `tests/menu_settings/test_visibility.py`

## Fase 1: Matar o `core.py`

Objetivo: eliminar o hub global de dependências.

Extrair para módulos específicos:

- `appgenesis/http/templates.py`
- `appgenesis/http/session_middleware.py`
- `appgenesis/db/session.py`
- `appgenesis/config/settings.py`
- `appgenesis/integrations/oauth.py`
- `appgenesis/domain/constants.py` ou módulos equivalentes por domínio

Regra:

- nenhum módulo novo deve importar `core.py`;
- módulos antigos passam a migrar por toque;
- `core.py` fica temporariamente como compat layer curta, depois é removido.

## Fase 2: Levar SQL para Repositories

Objetivo: tirar queries das rotas.

Prioridade:

1. `routes/users/*`
2. `routes/entities/*`
3. `routes/profile/profile_handlers.py`
4. `routes/auth/*`

Criar repositórios por agregado:

```text
appgenesis/repositories/
  user_repository.py
  member_repository.py
  entity_repository.py
  profile_repository.py
  menu_settings_repository.py
```

Regra prática:

- router não faz `select/update/delete`;
- router chama use case;
- use case chama repository.

## Fase 3: Dividir os serviços grandes

Objetivo: substituir serviços genéricos por casos de uso menores.

### `services/page.py`

Dividir em:

```text
appgenesis/use_cases/dashboard/get_home_dashboard.py
appgenesis/use_cases/page/build_new_user_page_context.py
appgenesis/use_cases/entities/get_entity_edit_data.py
appgenesis/use_cases/users/get_user_edit_data.py
```

### `services/auth.py`

Dividir em:

```text
appgenesis/use_cases/auth/passwords.py
appgenesis/use_cases/auth/invites.py
appgenesis/use_cases/auth/oauth.py
appgenesis/use_cases/auth/login_page.py
appgenesis/use_cases/auth/upsert_user_by_email.py
```

### `routes/profile/profile_handlers.py`

Dividir em handlers menores:

```text
appgenesis/routes/profile/handlers/personal.py
appgenesis/routes/profile/handlers/address.py
appgenesis/routes/profile/handlers/training.py
appgenesis/routes/profile/handlers/whatsapp.py
appgenesis/routes/profile/handlers/process_data.py
```

## Fase 4: Quebrar o ecrã `new_user`

Objetivo: reduzir o maior ponto de fragilidade do frontend.

### Templates

Separar `templates/new_user.html` em partials por card/área:

```text
templates/new_user/
  page.html
  sections/home_summary.html
  sections/profile_personal.html
  sections/profile_address.html
  sections/profile_training.html
  sections/dynamic_process.html
  sections/admin_users.html
  sections/admin_entities.html
  sections/admin_settings.html
```

### JavaScript

Separar `static/js/new_user.js` em módulos por feature:

```text
static/js/new_user/
  bootstrap.js
  navigation.js
  menu-tabs.js
  profile-form.js
  dynamic-process.js
  admin-users.js
  admin-entities.js
  admin-settings.js
  charts.js
  utils.js
```

### CSS

Separar `static/css/new_user.css` por blocos de UI:

```text
static/css/new_user/
  base.css
  layout.css
  cards.css
  forms.css
  tabs.css
  dashboard.css
  profile.css
  admin.css
```

Regra importante:

- o backend deve entregar um bootstrap JSON estável;
- o JS deve consumir esse bootstrap;
- evitar duplicar normalização de regras de negócio no browser.

## Fase 5: Fechar dívidas transversais

Objetivo: estabilizar a manutenção.

Incluir:

- correção sistemática de mojibake;
- centralização de mensagens PT-PT;
- tipagem melhor de DTOs e resultados;
- padronização de erros de validação;
- smoke tests dos principais fluxos;
- revisão de logs para não expor dados sensíveis.

## Ordem Recomendada de Ataque

Se for para executar isto com menor risco, a ordem mais eficiente é:

1. testes de regressão dos fluxos críticos;
2. eliminação progressiva de `core.py`;
3. extração de repositories/use cases nas rotas de utilizadores e entidades;
4. split de `menu_settings.py`;
5. split de `services/page.py`;
6. split do ecrã `new_user`;
7. limpeza de encoding e mensagens.

## O Que Não Vale a Pena Fazer Agora

- renomear toda a árvore do projeto de uma vez;
- trocar framework ou ORM;
- criar arquitetura excessivamente abstrata;
- mover tudo para patterns complexos sem cobertura de testes;
- mexer no frontend e backend ao mesmo tempo no mesmo fluxo sem testes antes.

## Primeiros PRs Recomendados

### PR 1

Escopo:

- adicionar testes de criação de utilizador, entidade e update de perfil;
- introduzir imports explícitos nos ficheiros tocados;
- documentar guideline de camadas.

### PR 2

Escopo:

- criar `member_repository.py` e `menu_settings_repository.py`;
- migrar queries de `routes/users/create_handler.py`;
- criar use case `create_user`.

### PR 3

Escopo:

- migrar `routes/entities/create_handler.py` para use case próprio;
- isolar upload de logo em serviço/repositório de storage.

### PR 4

Escopo:

- dividir `menu_settings.py` em package;
- manter API pública compatível temporariamente.

### PR 5

Escopo:

- extrair `build_new_user_page_context`;
- começar a quebrar `new_user.html` e `new_user.js`.

## Critérios de Conclusão da Refatoração

Considerar a refatoração bem estruturada quando:

- `core.py` deixar de ser ponto central;
- routers deixarem de fazer SQL direto;
- `menu_settings.py`, `page.py` e `new_user.*` deixarem de ser ficheiros gigantes;
- cada fluxo crítico tiver testes de regressão;
- o frontend principal estiver dividido por secções reutilizáveis;
- não houver texto PT-PT corrompido nos fluxos principais.

## Registo de execução

Cada etapa segue a regra 17 do `AGENTS.md`. Estado registado aqui.

| Etapa | Descrição | PR | Testes | Validação | Estado |
|---|---|---|---|---|---|
| 0 | Regra de execução por etapas e registo | #95 | n/a (docs) | revisão | concluída |
| 1 | Remover ferramentas de debug de flicker (`debug_flicker`) | #96 (deploy prd ok) | `test_debug_flicker_removed_v1.py` + CI (503 passed) | dev sem scripts de flicker, sem erros; prd healthy | concluída |
| 1b | Logs de depuração gated por flag no backend (`_debug_sessoes_*`, `_log_sessoes_*`, `_debug_process_editor_*`, `_log_process_editor_*`) | #101 (deploy prd ok) | `test_no_debug_logging_helpers_v1.py` + CI (511 passed) | dev/prd: páginas 200, sem tracebacks | concluída |
| 1c | Logs de depuração gated por flag no frontend (`navigation_reload_guard_v1.js`, `return_after_save.js`, `new_user.js`, `admin_subprocesses_v1.js`, `configurable_items_manager_core_v1.js`, `global_loading_overlay_v1.js`, `sidebar_global_refresh_v1.js`, `tabs_overflow_v1.js`) | - | - | - | pendente |
| 2 | Versão de assets automática (substitui `?v=` manuais) | (esta etapa) | `test_static_asset_version_v1.py` + CI (506 passed) | dev: 60 refs `/static/` com a mesma versão, sem erros na consola | concluída (prd no deploy) |
| 3 | Assets de código saem do volume de produção (`static_prod`) | #98 | `test_prod_compose_static_volumes_v1.py` + CI; `docker compose config` válido | prd: 1 logo, 1 foto, 1 `eventos.json` copiados para `app_*_prod` (checksums iguais); health 200; logo/foto/css 200; volume `app_static_prod` mantido como legado | concluída |
| 4 | Remover remendos de texto corrompido (JS `ui_text_cleanup`, `settings_process_tabs`, `_fix_common_mojibake`, tabela `??`) | (esta etapa) | `test_no_mojibake_literals_v1.py` + CI (509 passed); pyflakes 79→78 | dev e prd: 0 registos corrompidos (`DB_TARGETS`, leitura); páginas sem Ã/�, sem erros na consola | em curso |
| 5a | `new_user.html`: bootstrap inline (`window.__APPGENESIS_BOOTSTRAP__`, 30 chaves) → bloco JSON `#appgenesis-bootstrap` + `static/js/modules/app_bootstrap_v1.js` | #100 (deploy prd ok) | `test_app_bootstrap_json_v1.py` (2) + CI | dev: 30 chaves, dados corretos, 0 erros; prd 200 | concluída |
| 5b | `new_user.js` (10.721 linhas) por domínio: auth/menu/perfil/processos/utilizadores, uma fatia por PR, cada uma com teste e validação | ver registo 15 | ver registo 15 | ver registo 15 | concluída (numa só PR: divisão mecânica verificada por AST) |
| 5c | `new_user.css` (7.133 linhas) por componente, mantendo a ordem de cascata | ver registo 16 | ver registo 16 | ver registo 16 | concluída |
| 6 | Testes excluídos do CI e pyflakes bloqueante | - | - | - | pendente |
| 7 | Isolamento da lista de utilizadores por entidade da sessão; filtro no SQL; admins do sistema só para owner | #398 (deploy prd ok) | `test_scoped_users_isolation_v1.py` + CI (638 passed, 2 falhas pré-existentes) | dev: HTTP com login owner/legado, sem vazamento de emails; prd health 200, 0 membros com vínculo em 2 entidades | concluída |
| 8 | Alinhar números dos documentos ao código (medição 2026-11-28); modelo `EntityMenuData` (alembic check limpo) | #399 (deploy prd ok) | n/a (docs) | revisão | concluída |
| 9 | Remover `appgenesis/core.py`: 53 importadores passam à origem (`db.session`, `web.templates`, `config.settings`, `authlib`) | #400 (deploy prd ok) | CI (639 passed, 2 falhas pré-existentes); `app.routes` 13 = 13 | dev: login owner/legado, abas Administrativo com HTML de tamanho idêntico, sem traceback | concluída |
| 10 | Etapa 3: SQL de `routes/users/*` para `repositories/user_repository.py`; helpers duplicados de `create_user.py` removidos; owner só gere admins do sistema (`legado`/`owner`) e membros das suas entidades de dados; "último admin" sem query por candidato | #401 (deploy prd ok) | `test_scoped_users_isolation_v1.py` (+2) + CI (641 passed, 2 falhas pré-existentes) | dev: owner edita admin legado (ok) e é recusado ao editar utilizador comum da 1001 por POST direto; abas sem vazamento | concluída |
| 11 | Etapa 4: `profile_handlers.py` (2654) e `settings_handlers.py` (1391) partidos em `routes/profile/handlers/` (`auth_profile`, `personal`, `process_data`, `admin_lists`, `profile_common`, `sidebar_sections`, `menu_subprocess`) por AST, sem mudar corpos; 6 funções mortas removidas | #403 (deploy prd ok) | CI (641 passed, 2 falhas pré-existentes); 63 rotas iguais (método, caminho, função) | dev: 7 GET 200 e 16 POST sem 5xx (owner e admin legado), sem traceback | concluída |
| 12 | Segurança: criar/apagar menu partilhado e eliminar entidade exigem owner do tenant (antes bastava `is_admin_user`, que aceita `system_type=owner` ligado só a entidade legado); gravação em lote de sessões recusa pedido sem linhas | #406 (deploy prd ok) | `test_tenant_structure_guards_v1.py` (4) + CI (645 passed, 2 falhas pré-existentes) | dev: utilizador owner-em-legado recusado nas 4 rotas; owner verdadeiro cria menu; sem traceback | concluída |
| 13 | Etapa 8 (parcial): pyflakes bloqueante no CI; base a zero (146 imports mortos removidos, reexportações e imports de efeito em `__all__`, forward refs dos modelos em `TYPE_CHECKING`, 2 variáveis mortas) | #407 (deploy prd ok) | CI (645 passed); 63 rotas iguais; nenhum acesso por atributo a nome removido | dev: HTML de 3 páginas do owner idêntico a `master`; validações HTTP anteriores repetidas sem diferença | concluída; job Selenium não criado (precisa de app+Postgres+Chrome no runner) |
| 14 | Etapa 7: administrador de entidade legado por função (`is_entity_admin_v1`): gere membros (`default`), funções de membros e perfis de autorização da própria entidade; sem escalada (não cria/promove Admin/Super User/Legado, não mexe em funções de administrador nem noutros administradores). Corrige também a página de erro da criação de utilizador (rebentava com `UndefinedError` e não mostrava `errors`) | (esta etapa) | `test_entity_admin_v1.py` (4) + `test_create_user_use_case.py` (+1) + CI (652 passed, 2 falhas pré-existentes) | dev com filtro ligado: admin legado cria/edita membros, recusado em owner/outros admins/funções de admin/menus; membro 403; owner igual; 0 tracebacks | concluída |
| 15 | Etapa 5b: `static/js/new_user.js` (10.721 linhas) dividido em 16 scripts clássicos em `static/js/new_user/` (estado, menus, home, processo dinâmico ×3, navegação, Meu Perfil, construtores de processo, ligação aos runtimes, utilizadores, arranque, runtimes de Meu Perfil, retorno pós-gravação, secções, feedback de UI), carregados por ordem no template. Só declarações `function` mudaram de sítio (hoisting); todo o código que corre no load mantém a ordem original | (esta etapa) | AST: mesmas 358 instruções e mesma ordem das executáveis; 0 leituras de nomes de fatias posteriores no load (análise precisa e conservadora); `node --check` por ficheiro (também no CI); `test_new_user_js_parts_v1.py`; CI (637 passed) | dev, master vs branch: 13 URLs do owner + 6 do admin de entidade + 6 do membro, desktop e mobile, e cliques em todos os menus e abas: menu ativo, cards visíveis, aba ativa e URL idênticos; 0 erros JS | concluída |
| 16 | Etapa 5c: `static/css/new_user.css` (7.133 linhas) partido em 11 ficheiros consecutivos em `static/css/new_user/` (base, controlos de Meus dados, formulários/tabelas, configuração de processos, responsivo, layout de campos/entidade, paginação, formulários admin/botões, extras de Meus dados, empresa/entidade, processos de lista/agenda), carregados no mesmo ponto do template e pela mesma ordem: cascata igual. Mantida a chaveta `}` a mais pré-existente (linha 6476 do original, agora em `11_process_lists_agenda.css`), que faz o browser descartar a regra `.dynamic-process-list-title-group-v1`; corrigida a seguir (a regra era morta: classe sem uso desde `2f7c3e70`), com teste de chavetas equilibradas | (esta etapa) | concatenação igual byte a byte ao original; cortes só no nível de topo (fora de regras, `@media` e comentários); `test_new_user_css_parts_v1.py` | dev, master vs branch: estilos computados e caixas de 31.786 elementos (9 URLs do owner, desktop e mobile) iguais, exceto o spinner de loading em rotação | concluída |
| 17 | Etapa 8 (resto): job `browser` no CI com Postgres vazio, seed mínimo (`scripts/ci_seed_browser.py`: admin owner + menu Definições), app real com o filtro por função ligado e Chrome headless. Testes desatualizados corrigidos (perfil de autorização é aba de Administrativo; ids `admin-sidebar-sections-card-active` e `recent-entities-card`; rota `/settings/menu/edit` já não existe; wrapper `setActiveSubmenu`). 3 ficheiros sem browser voltam ao job `test` | (esta etapa) | job `browser`: 48 passed, 3 skipped, 15 em quarentena (precisam de processos com dados); job `test` verde | CI | concluída; quarentena documentada no workflow |
| 18 | Etapa 8 (fim da quarentena): seed do CI com entidade owner 1000, config de Empresa e processo de formulário `calendario` (só estrutura). Testes alinhados ao produto: editor abre em Geral (só leitura), Cancelar/Guardar pela aba Sessão, Guardar fica no editor com toast, Cancelar de campos-config abre o formulário primeiro, lista automática aponta para Administrativo > Perfil de autorização, cache buster dinâmico, erro inline sem segunda navegação. **Bug corrigido:** o menu Empresa abria vazio desde o #347 (`#empresa-card` só com scope `administrativo`); agora `administrativo,empresa` | (esta etapa) | job `browser`: 66 passed, 0 skipped, 0 em quarentena; job `test` verde; `test_empresa_card_scope_v1.py` | dev: Empresa mostra Dados da empresa; o card não aparece noutros menus (URL e cliques) | concluída |
| 19 | Etapa 6: `require_module_access` (domínio, 403, fail closed) e dependency `require_module(module_key)` (revalida a entidade da sessão com `get_current_user` antes de verificar o entitlement). Ainda não há rotas de módulo; o primeiro módulo usa a dependency em todas as rotas | (esta etapa) | `test_require_module_v1.py` (entidade ativa/inativa/expirada, core, inexistente, sem login, `entity_id` forjado: um mutante sem revalidação é apanhado); CI (660 passed); pyflakes | n/a (sem rota em produção que use o guard) | concluída |
