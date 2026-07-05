# Fase 10 — CI/docs/resumo final

## Objetivo

O plano original referia a Fase 10 como "CI/docs/resumo final". Ao
contrário das Fases 1-9, nem o `risk-map.md` nem o `validation-plan.md`
atribuem um âmbito concreto e vinculativo a esta fase — não há nenhuma
referência a "Fase 10", "CI" ou "resumo final" em nenhum dos dois
documentos.

## Levantamento prévio

Não existia nenhuma infraestrutura de CI no repositório (confirmado por
`glob` a `.github/workflows/*.yml`, que só devolveu correspondências de
terceiros dentro de `.venv` e `appgenesis-mobile/node_modules`; a única
configuração no root é `docker-compose.yml`, que é o compose de
desenvolvimento/runtime da aplicação, não um pipeline de CI).

Criar uma pipeline de CI nova é qualitativamente diferente de todo o
trabalho de refatoração puramente interna feito nas Fases 1-9: é
infraestrutura nova, partilhada, que passa a correr automaticamente em
cada push/PR para toda a equipa — precisamente o tipo de ação que as
minhas próprias diretrizes de operação assinalam como merecedora de
confirmação explícita antes de avançar ("modifying CI/CD pipelines",
"actions visible to others or that affect shared state"). Por isso, em
vez de decidir unilateralmente, usei `AskUserQuestion` para perguntar
se deveria (a) criar uma pipeline básica de CI (pytest + pyflakes em
push/PR) ou (b) saltar essa parte e só finalizar documentação/resumo.

**Resposta do utilizador:** "Add a basic CI workflow (Recommended)".

## Trabalho realizado

### Levantamento técnico antes de escrever a pipeline

- `requirements.txt` não lista `pytest`, `pyflakes` nem `selenium`
  (dependências de teste, não de runtime) — confirmado por leitura
  completa do ficheiro.
- Identificados 4 ficheiros de teste que dependem de um browser Chrome
  real e de um servidor da aplicação a correr em
  `http://127.0.0.1:8000` (`from selenium import webdriver` +
  `webdriver.Chrome(...)` + pedidos HTTP diretos):
  `tests/test_auth_objeto_navigation_selenium.py`,
  `tests/test_estruturas_menu_client_navigation.py`,
  `tests/test_navigation_refresh_home.py` e
  `tests/test_navigation_reload_and_loading_overlay.py`. (Os dois
  últimos não tinham sido identificados no levantamento inicial feito
  antes da compactação da conversa; confirmados agora por grep a
  `selenium` em todo `tests/*.py`.)
- Verificado, por grep a todo `tests/*.py`, que **nenhum** ficheiro de
  teste importa `appgenesis.db.session` nem usa
  `settings.DATABASE_URL` diretamente — os ficheiros que tocam em base
  de dados (`test_admin_subprocess_entity_repository.py`,
  `test_auth_services.py`, `test_create_user_use_case.py`,
  `test_update_user_handler.py`, `test_user_entity_scope.py`,
  `test_menu_settings.py`, `test_module_access.py`,
  `test_member_user_migration.py`) constroem o seu próprio engine
  SQLite em memória (`create_engine("sqlite+pysqlite:///:memory:",
  poolclass=StaticPool)`), isolado do Postgres real usado em
  desenvolvimento. Confirmado experimentalmente correndo a suite
  completa (excluindo os 4 ficheiros Selenium) sem qualquer serviço de
  base de dados: **180 testes passaram**, 0 falharam.
- Concluído, portanto, que a pipeline de CI **não precisa** de um
  container de serviço Postgres — só precisa de Python + dependências
  de `requirements.txt` + `pytest`/`pyflakes`.

### Ficheiro criado

`.github/workflows/ci.yml`:

- Dispara em `push`/`pull_request` para `main` e para
  `refactor/appgenesis-process-architecture`.
- Instala Python 3.12 (igual ao `Dockerfile` e ao ambiente local),
  `requirements.txt`, e `pytest==9.1.1`/`pyflakes==3.4.0` (mesmas
  versões já instaladas localmente).
- Corre `python -m pyflakes appgenesis/ web_app.py` como passo
  **informativo, não bloqueante** (`continue-on-error: true`) —
  decisão justificada abaixo.
- Corre `pytest -q` excluindo os 4 ficheiros Selenium via `--ignore`.

### Porque é que o pyflakes não bloqueia o build

Corrido `python -m pyflakes appgenesis/ web_app.py` localmente antes de
decidir: 213 linhas de output, das quais:

- 171 ocorrências de "imported but unused" (ruído pré-existente já
  documentado nas fases anteriores como aceitável).
- 4 ocorrências de "redefinition of unused" (`menu_settings.py`, já
  atribuído ao Risco #3 do `risk-map.md`, não relacionado com esta
  fase).
- 36 ocorrências de "undefined name", todas em `appgenesis/models/*.py`
  (`department.py`, `entity.py`, `member.py`, `profile.py`, `user.py`,
  `modules/*.py`). Inspecionado o código: são falsos positivos —
  referências a classes irmãs (`"MemberEntity"`, `"Entity"`, `"User"`,
  etc.) dentro de `relationship(back_populates=...)` e anotações
  `Mapped[...]`, resolvidas em runtime pelo registo de mapeamento do
  SQLAlchemy, não por `import` Python normal. Nenhum destes ficheiros
  foi tocado em qualquer fase desta refatoração — é ruído de baseline
  pré-existente, não uma regressão introduzida agora.

Transformar o pyflakes num gate rígido faria o CI ficar
permanentemente vermelho por motivos que não refletem nenhum defeito
real de runtime nem nenhuma regressão desta refatoração — o que
tornaria o sinal do CI inútil já no primeiro commit. Por isso o passo
de lint fica como relatório visível (aparece nos logs do workflow),
enquanto o `pytest` continua a ser o gate real e bloqueante.

## Técnica de validação usada

- `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
  — sintaxe YAML válida.
- `python -m pytest -q --ignore=tests/test_auth_objeto_navigation_selenium.py --ignore=tests/test_estruturas_menu_client_navigation.py --ignore=tests/test_navigation_refresh_home.py --ignore=tests/test_navigation_reload_and_loading_overlay.py`
  corrido localmente exatamente como a pipeline o fará: **180 passed**,
  0 falhados, sem qualquer ligação a Postgres.
- `python -m pyflakes appgenesis/ web_app.py` corrido localmente para
  confirmar e categorizar o output antes de decidir torná-lo
  não-bloqueante (ver secção acima).

## Ficheiros alterados/criados

- `.github/workflows/ci.yml` (novo)
- `docs/refactoring/phase-10-summary.md` (este ficheiro)

## Riscos

- Os 4 testes Selenium continuam a não correr em CI — continuam a
  exigir validação manual local com browser real, tal como já
  documentado nas Fases 1-9 para qualquer alteração de frontend vivo.
- O relatório de pyflakes não bloqueia merges; se o ruído de baseline
  (36 falsos positivos + 171 imports não usados) crescer de forma
  descontrolada no futuro, isso não será apanhado automaticamente por
  este workflow — ficará dependente de revisão manual, tal como já
  acontecia antes desta fase.
- Nenhuma alteração de comportamento da aplicação: este ficheiro é
  puramente infraestrutura de CI, não código de produção.
