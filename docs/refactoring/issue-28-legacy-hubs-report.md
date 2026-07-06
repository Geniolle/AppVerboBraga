# Relatório — Remoção dos Hubs de Compatibilidade `core` e `services legacy` (Issue #28)

Updated: 2026-07-06

## Contexto

Após o PR #22, `appgenesis/core.py` e os hubs `appgenesis/services/__init__.py` e
`appgenesis/services/legacy.py` continuaram a existir por segurança, como
candidatos a remoção futura apenas após confirmação de zero consumidores
(Risco documentado em `docs/refactoring/risk-map.md`).

Esta issue mapeia os consumidores reais de cada um e age de acordo com a prova
encontrada — sem misturar essa decisão técnica com nenhuma decisão de negócio.

## Levantamento

### `appgenesis/core.py`

Grep de `from appgenesis.core import` em todo o repositório (excluindo o
próprio `core.py`) encontrou **21 consumidores reais**, todos com imports
nomeados explícitos (nenhum `import *`):

- 11 em `appgenesis/` (rotas, serviços, `appgenesis/web/templates.py`).
- 9 em `scripts/` (scripts pontuais documentados em `docs/operations/scripts-runbook.md`).
- 4 em `tests/` (testes Selenium de navegação).

**Conclusão**: `core.py` não tem zero consumidores — continua a ser um módulo
partilhado ativo (constantes derivadas de `settings`, `SessionLocal`,
`templates`, modelos). Não é seguro nem correto removê-lo. O comentário de
topo do ficheiro já orienta novo código a importar da origem real do símbolo
em vez de `appgenesis.core`; esse comentário foi reforçado com a data e o
resultado deste levantamento.

### Código morto encontrado dentro de `core.py`

Apesar de `core.py` continuar necessário, uma parte do seu conteúdo estava
morta: `app = FastAPI(title="AppGenesis User Admin")`, com o `app.mount(...)`
e `app.add_middleware(...)` associados. Grep confirmou **zero** ocorrências de
`from appgenesis.core import app` ou `appgenesis.core.app` em todo o
repositório. A aplicação FastAPI real é criada em
`appgenesis/app.py::create_app()` (com o mesmo título, mount e middleware) e é
essa a instância usada por `web_app.py`. A de `core.py` era uma sobra nunca
consumida.

Removida essa instância morta e os imports que só ela usava (`FastAPI`,
`StaticFiles`, `SessionMiddleware`), e removida a entrada `"app"` de
`__all__`. `templates = Jinja2Templates(...)` foi mantido — está listado em
`__all__` e é consumido por `appgenesis/web/templates.py` e por múltiplos
handlers de rota via `from appgenesis.core import ..., templates`.

### `appgenesis/services/__init__.py`

Este hub já tinha sido validado em 2026-07-05 (comentário no próprio
ficheiro): nenhum ficheiro do repositório importava `appgenesis.services` ao
nível do pacote. Esta issue repetiu a validação de forma independente
(grep por `from appgenesis.services import` e `import appgenesis.services`
sem sufixo de submódulo) e confirmou o mesmo resultado — nenhuma ocorrência.

Todos os consumidores reais dos serviços importam diretamente do submódulo
(ex.: `from appgenesis.services.profile import ...`,
`import appgenesis.services.auth as auth_service`), nunca através do
wildcard hub do pacote.

**Ação**: com prova de zero uso confirmada duas vezes, os 11 `from
appgenesis.services.X import *` foram removidos de `__init__.py`. O ficheiro
continua a existir (necessário para `services` ser reconhecido como pacote),
agora vazio de imports, apenas com o comentário a registar a decisão.

### `appgenesis/services/legacy.py`

Mesma verificação: zero referências a `appgenesis.services.legacy` em todo o
repositório, fora do próprio ficheiro.

**Ação**: removido por completo — não é um `__init__.py`, não há nenhuma
restrição de pacote a preservar, e não há nenhum consumidor.

## Regra que impede regressão

Criado `tests/test_no_wildcard_imports.py`: percorre todos os `.py` de
`appgenesis/` e `web_app.py` via `ast`, falha se encontrar qualquer
`from X import *`. Corre em CI a cada push/PR (nenhuma configuração adicional
necessária). Isto substitui a necessidade de uma regra de lint separada.

## Itens do checklist não aplicados (e porquê)

- **"Marcar funções/constantes legadas como deprecated quando necessário"**:
  não aplicado às constantes de `core.py` — são meros alias de
  `settings.X` usados ativamente por 21 consumidores; emitir
  `DeprecationWarning` nelas arriscaria ruído em runtime sem benefício, e
  substituir os 21 call-sites por imports diretos de `appgenesis.config.settings`
  é uma refatoração maior, fora do escopo desta issue (planeamento, não
  execução em massa). Registado como trabalho futuro caso `core.py` volte a
  ser revisitado.
- **"Substituir imports restantes por imports explícitos"**: já estava feito
  — confirmado que todos os 21 consumidores de `core.py` já usam imports
  nomeados explícitos, não wildcard.

## Validação

- `pytest -q` (excluindo Selenium, igual à CI): 182 passed (181 anteriores + o
  novo `test_no_wildcard_imports.py`).
- Smoke de import: `appgenesis.app.create_app()` continua a criar a aplicação
  normalmente; `appgenesis.core` importa sem `app`; `appgenesis.services`
  importa sem erros.
- `python -m pyflakes appgenesis/ web_app.py`: sem novos avisos nos ficheiros
  alterados (os avisos de wildcard import em `services/__init__.py` e
  `services/legacy.py` desapareceram, pois deixaram de existir).

## Critério de conclusão

- [x] Mapeados todos os imports de `appgenesis.core` (21 consumidores reais).
- [x] Mapeados todos os imports wildcard de `appgenesis.services` (nenhum —
      o próprio pacote é que continha os wildcards, sem consumidores).
- [x] Consumidores internos (`appgenesis/`) separados de externos
      (`scripts/`, `tests/`) na tabela acima.
- [x] Criado teste que impede novo wildcard import (`tests/test_no_wildcard_imports.py`).
- [x] Confirmado que os imports restantes já são explícitos.
- [x] Deprecated não aplicado — justificado acima.
- [x] Removidos apenas os exports comprovadamente sem uso: `app` de
      `core.py`, o hub `services/__init__.py` (esvaziado) e
      `services/legacy.py` (apagado).
- [x] Suite completa e smoke de import executados com sucesso.

`core.py` em si **não** foi removido nem está pronto para remoção — continua
a ter 21 consumidores reais. A remoção final desse ficheiro fica para uma
issue futura, apenas depois de todos os consumidores migrarem para a origem
real de cada símbolo.
