# Refactor Roadmap

## Objetivo

Estruturar uma refatoração melhor para o `AppVerboBraga` sem reiniciar a reorganização já em curso.
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
- Os routers novos por domínio já estão publicados em `appverbo/app.py`.
- Há testes básicos para auth, profile, menu settings e WhatsApp.
- Há migrações, scripts operacionais e uma divisão inicial entre backend e assets.

### Principais problemas que ainda travam a refatoração

1. `appverbo/core.py` continua a ser um agregador global de framework, settings, DB, modelos e utilitários.
   Hoje 24 módulos ainda dependem de `from appverbo.core import *`.

2. As rotas continuam com lógica de aplicação e acesso a dados embutidos.
   Há pelo menos 59 ocorrências de `session.execute/select/update/delete` dentro de `appverbo/routes`.

3. Os serviços estão grandes e misturam responsabilidades.
   Exemplos:
   - `appverbo/menu_settings.py`
   - `appverbo/services/page.py`
   - `appverbo/routes/profile/profile_handlers.py`
   - `appverbo/routes/profile/settings_handlers.py`

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
appverbo/http/
  deps/
  presenters/
  responses/
```

Se não quiser renomear tudo agora, manter `routes/` e introduzir subpastas claras:

```text
appverbo/routes/<dominio>/
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
appverbo/use_cases/
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
appverbo/domain/
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
appverbo/infrastructure/
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
appverbo/use_cases/auth/
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

`appverbo/menu_settings.py` deve virar um package próprio.

Sugestão:

```text
appverbo/menu_settings/
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

- remover novos usos de `from appverbo.core import *`;
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

- `appverbo/http/templates.py`
- `appverbo/http/session_middleware.py`
- `appverbo/db/session.py`
- `appverbo/config/settings.py`
- `appverbo/integrations/oauth.py`
- `appverbo/domain/constants.py` ou módulos equivalentes por domínio

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
appverbo/repositories/
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
appverbo/use_cases/dashboard/get_home_dashboard.py
appverbo/use_cases/page/build_new_user_page_context.py
appverbo/use_cases/entities/get_entity_edit_data.py
appverbo/use_cases/users/get_user_edit_data.py
```

### `services/auth.py`

Dividir em:

```text
appverbo/use_cases/auth/passwords.py
appverbo/use_cases/auth/invites.py
appverbo/use_cases/auth/oauth.py
appverbo/use_cases/auth/login_page.py
appverbo/use_cases/auth/upsert_user_by_email.py
```

### `routes/profile/profile_handlers.py`

Dividir em handlers menores:

```text
appverbo/routes/profile/handlers/personal.py
appverbo/routes/profile/handlers/address.py
appverbo/routes/profile/handlers/training.py
appverbo/routes/profile/handlers/whatsapp.py
appverbo/routes/profile/handlers/process_data.py
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
