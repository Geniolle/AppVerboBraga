# Fase 3 — Extração de use cases por domínio (Webhooks, Empresa, Auth, Meu Perfil)

## Objetivo

Extrair a lógica de negócio dos route handlers de quatro domínios (Webhooks, Empresa, Auth,
Meu Perfil) para módulos dedicados em `appgenesis/domains/<area>/{schemas,use_cases,repositories,
permissions}.py`, deixando os handlers em `appgenesis/routes/` como consumidores finos (parse de
input HTTP → chamada ao use case → construção da resposta HTTP), sem alteração de comportamento.

Decisão vinculante mantida ao longo da fase: `appgenesis/admin_subprocesses/` continua a ser a
arquitetura definitiva para Entidade/Sessões/Menu/Perfil de autorização/Objeto de autorização;
`appgenesis/domains/` é usado apenas para Auth/Empresa/Webhooks/Meu Perfil.

## Técnica de validação usada

Um commit por unidade coerente de extração, com validação tripla antes de cada commit:
1. `python -m pyflakes <ficheiros>` — zero `undefined name` (ruído de `imported but unused`
   pré-existente é aceite; ruído introduzido pela própria extração foi sempre limpo).
2. `python -c "import <modulo>"` — import limpo em runtime.
3. `pytest -q` completo — 190/190 aprovados, ou o padrão conhecido de testes instáveis (ver
   `phase-2-summary.md`, secção "Testes instáveis").

Para ficheiros grandes, o conteúdo original de referência foi obtido via
`git show HEAD:<ficheiro> > scratch/<nome>_original.py` seguido de leitura desse ficheiro scratch,
evitando reconstrução por memória — técnica adotada após um quase-incidente em que uma reescrita
foi inicialmente redigida por suposição (ver secção "Incidentes").

## Webhooks (`domains/webhooks`)

Ficheiros criados:
- `appgenesis/domains/webhooks/__init__.py`
- `appgenesis/domains/webhooks/repositories.py`
- `appgenesis/domains/webhooks/use_cases.py`

Ficheiros alterados:
- `appgenesis/routes/webhooks/receive_handler.py`
- `appgenesis/routes/webhooks/verify_handler.py`

## Empresa (`domains/empresa`)

Ficheiros criados:
- `appgenesis/domains/empresa/__init__.py`
- `appgenesis/domains/empresa/schemas.py`
- `appgenesis/domains/empresa/permissions.py`
- `appgenesis/domains/empresa/use_cases.py`

Ficheiros alterados:
- `appgenesis/routes/empresa/update_handler.py`

## Auth (`domains/auth`)

Ficheiros criados:
- `appgenesis/domains/auth/__init__.py`
- `appgenesis/domains/auth/schemas.py` — `LoginFormInput`, `SignupFormInput`,
  `InviteAcceptSubmitFormInput`.
- `appgenesis/domains/auth/repositories.py` — `resolve_invite_entity_for_member`.
- `appgenesis/domains/auth/use_cases.py` — login/signup (`execute_login`, `execute_signup`,
  `resolve_signup_entity_lock`), OAuth (`execute_oauth_callback`), convite
  (`resolve_invite_accept_page`, `execute_invite_accept`) e reset de password
  (`execute_password_reset_request`, `resolve_password_reset_token`,
  `execute_password_reset_confirm`).

Ficheiros alterados:
- `appgenesis/routes/auth/session_handlers.py`
- `appgenesis/routes/auth/pages.py`
- `appgenesis/routes/auth/oauth_handlers.py`
- `appgenesis/routes/auth/invite_handlers.py`
- `appgenesis/routes/auth/password_reset_handlers.py` (migrado também de `appgenesis.core` para
  `appgenesis.db.session`/`appgenesis.web.templates`)

Detalhe de comportamento preservado deliberadamente: `PasswordResetConfirmInvalid` tem um campo
`keep_token: bool` porque o handler original devolve o token ao formulário em alguns ramos de erro
(falha de validação de password, falha de commit) mas limpa-o noutros (token inválido, conta
inativa) — este comportamento por-ramo foi replicado exatamente.

## Meu Perfil (`domains/meu_perfil`)

Ficheiros criados:
- `appgenesis/domains/meu_perfil/__init__.py`
- `appgenesis/domains/meu_perfil/repositories.py` — `find_member_for_user`.
- `appgenesis/domains/meu_perfil/schemas.py` — `AddressProfileFormInput`,
  `TrainingProfileFormInput`.
- `appgenesis/domains/meu_perfil/use_cases.py` — `execute_update_address_profile`,
  `execute_update_training_profile`, `execute_verify_whatsapp_profile`.

Ficheiros alterados:
- `appgenesis/routes/profile/profile_handlers.py` — apenas os corpos de
  `update_address_profile`, `update_training_profile` e `verify_whatsapp_profile` foram
  reescritos (edições pontuais, não reescrita total do ficheiro, que tem ~2700 linhas e mistura
  vários escopos).

### Escopo explicitamente fora desta fase (decisões de fronteira arquitetural)

- **`appgenesis/routes/profile/page_handler.py`** (`new_user_page`) e
  **`appgenesis/routes/profile/settings_handlers.py`** (todas as rotas `/settings/menu/*`): apesar
  de viverem em `routes/profile/`, a lógica de ambos é território de Sessões/Menu/Perfil de
  autorização/Objeto de autorização — pertence a `admin_subprocesses/` pela decisão vinculante, não
  a `domains/meu_perfil`. Ambos contêm marcadores densos de correção de incidentes versionados
  (`V1`, `V2`, `V22`, `V26`, etc.), sinalizando fragilidade extrema. **Não foram tocados.**
- **`update_personal_profile`** (`/users/profile/personal`, ~460 linhas) e
  **`update_dynamic_process_profile`** (`/users/profile/process-data`, ~550 linhas) em
  `profile_handlers.py`: analisados integralmente. Confirmado que a maior parte de ambos
  (cerca de 300 linhas em `update_personal_profile`; a totalidade de `update_dynamic_process_profile`,
  que é genericamente parametrizado por `menu_key` e não específico do Meu Perfil) é o motor
  genérico de campos dinâmicos/campos quantidade/regras de campos subsequentes, lido a partir das
  configurações de admin_subprocess em `menu_settings` — o mesmo motor partilhado por todos os
  menus, não lógica exclusiva do Meu Perfil. Este motor está explicitamente planeado como
  workstream próprio (Fase 6 — motor de processos dinâmicos). Extrair apenas "a parte do Meu
  Perfil" agora obrigaria a inventar prematuramente a arquitetura da Fase 6 aplicada a um único
  call site, criando inconsistência e risco sem necessidade. **Ambas as funções foram deixadas
  completamente intactas**, a aguardar a Fase 6.

## Incidente (achado, não causado por esta fase): ficheiros CSS ausentes

Durante o trabalho em Auth foi detetada a ausência de 14 ficheiros `static/css/*` (incluindo
`static/css/modules/`) da working tree, apesar de presentes no índice do git. Confirmado como
regressão real via falha de teste (`FileNotFoundError` em
`test_admin_subprocess_layout.py::test_objeto_autorizacao_edit_form_uses_dedicated_grid_variant`).
Restaurado de forma segura e não destrutiva com `git checkout -- static/css` (o índice do git
estava intacto — recuperação de dados, não ação destrutiva). `pytest -q` completo confirmou
190/190 após a restauração. Não relacionado com o trabalho desta fase.

## Quase-incidente: reescrita por suposição (autocorrigido)

Ao reescrever `appgenesis/routes/auth/oauth_handlers.py`, uma leitura anterior do ficheiro tinha
devolvido conteúdo obsoleto/vazio, e a reescrita foi inicialmente redigida por suposição sem
nunca ter visto o conteúdo real. Detetado e corrigido antes de prosseguir: o conteúdo real foi
obtido via `git show` e comparado linha a linha com o que tinha sido escrito — a reconstrução
coincidiu quase exatamente (uma diferença negligível de timing de abertura de sessão), mas o
processo não era seguro. A técnica de `git show` → ficheiro scratch → `Read` foi adotada a partir
daí para todos os ficheiros grandes restantes.

## Validação final

- `pytest -q` completo executado após cada commit desta fase: sempre 190/190 aprovados, ou
  189/190 com apenas um dos dois testes Selenium instáveis já documentados na Fase 2 a falhar.
- Todos os módulos novos/alterados importam individual e conjuntamente sem erro.
- Nenhuma rota, mensagem de erro, código de status HTTP ou ordem de validação foi alterada face ao
  comportamento original.

## Riscos

Nenhum risco novo introduzido pelas extrações concluídas (Webhooks, Empresa, Auth, e a fatia de
Meu Perfil extraída) — comportamento idêntico, apenas reorganização de código. O risco conhecido
e deliberadamente não assumido nesta fase é a lógica ainda não extraída de `update_personal_profile`
e `update_dynamic_process_profile` (motor de processos dinâmicos, aguardando Fase 6) e de
`page_handler.py`/`settings_handlers.py` (admin_subprocesses, aguardando Fase 7).
