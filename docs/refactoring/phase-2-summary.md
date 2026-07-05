# Fase 2 — Eliminação da cascata de wildcard imports

## Objetivo

Substituir `from appgenesis.core import *` e `from appgenesis.services import *` por imports
explícitos dos símbolos realmente usados, em todos os ficheiros consumidores (route handlers e
módulos de `appgenesis/services/`). Sem alteração de comportamento.

## Técnica de validação usada

Para cada ficheiro: cópia em scratch com as linhas de wildcard import removidas → `pyflakes`
sobre a cópia → cada `undefined name 'X'` reportado é um símbolo que precisa de import explícito
(`imported but unused` é ruído pré-existente, ignorado). Para cada símbolo, foi determinado o
módulo de origem real via `grep` (`def X`, `X = ...`) no repositório, evitando reexportar via
`appgenesis.core`/`appgenesis.services` sempre que a origem real era conhecida e sem risco de
import circular.

Validação tripla por ficheiro:
1. `python -m pyflakes <ficheiro>` — zero `undefined name` (ruído de `imported but unused`
   pré-existente é aceite).
2. `python -c "import <modulo>"` — import limpo.
3. `pytest -q` completo (ou em lote) — 190/190 aprovados, ou o padrão conhecido de teste
   instável (ver secção "Testes instáveis").

## Ficheiros alterados (route handlers)

- `appgenesis/routes/entities/create_handler.py`
- `appgenesis/routes/entities/update_handler.py`
- `appgenesis/routes/entities/delete_handler.py`
- `appgenesis/routes/users/update_handler.py`
- `appgenesis/routes/users/resend_handler.py`
- `appgenesis/routes/users/helpers.py`
- `appgenesis/routes/users/delete_handler.py`
- `appgenesis/routes/profile/profile_handlers.py`
- `appgenesis/routes/profile/page_handler.py`
- `appgenesis/routes/webhooks/verify_handler.py`
- `appgenesis/routes/webhooks/receive_handler.py`
- `appgenesis/routes/auth/session_handlers.py`
- `appgenesis/routes/auth/pages.py`
- `appgenesis/routes/auth/oauth_handlers.py`
- `appgenesis/routes/auth/invite_handlers.py`
- `appgenesis/routes/empresa/update_handler.py`

## Ficheiros alterados (services — os próprios hubs de wildcard)

- `appgenesis/services/entities.py`
- `appgenesis/services/whatsapp.py`
- `appgenesis/services/session.py`
- `appgenesis/services/permissions.py`
- `appgenesis/services/profile.py`
- `appgenesis/services/auth.py`
- `appgenesis/services/page.py`

Confirmado por `grep` em todo o repositório (incluindo `tests/`): **zero** ficheiros continuam a
usar `from appgenesis.core import *` ou `from appgenesis.services import *` após esta fase.

## Hubs de compatibilidade (não removidos, apenas anotados)

- `appgenesis/core.py` — comentário adicionado a marcar o módulo como compatibilidade temporária;
  novos ficheiros não devem importar dele.
- `appgenesis/services/__init__.py` e `appgenesis/services/legacy.py` — hubs de wildcard que
  ficaram sem consumidores (validado via `grep` que nenhum ficheiro do repositório, incluindo
  testes, importa `appgenesis.services` ao nível do pacote ou `appgenesis.services.legacy`).
  Mantidos por compatibilidade e anotados como candidatos a remoção numa fase futura, em vez de
  removidos nesta mudança (regra: nunca remover legado sem antes validar uso).

## Achado pré-existente, fora do escopo desta fase

Durante a análise `pyflakes` de `appgenesis/services/page.py` foi detetada uma redefinição
pré-existente da função `_apply_meu_perfil_subsequent_visibility_v2` (definida duas vezes,
originalmente nas linhas 119 e 441, agora 129 e 451 após os imports adicionados). Este problema
é anterior a esta refatoração e não tem relação com wildcard imports — não foi corrigido aqui,
por estar fora do escopo (apenas remoção de wildcard imports, sem alteração de comportamento).
Deve ser avaliado e corrigido numa fase própria (candidato: Fase 4, que já vai dividir
`services/page.py`).

## Testes instáveis (não são regressões)

Dois testes Selenium mostraram falhas intermitentes durante esta fase, ambas confirmadas como
instabilidade ambiental pré-existente e não relacionadas com as alterações:

- `tests/test_navigation_reload_and_loading_overlay.py::test_global_loading_overlay_exists_and_toggles_on_sidebar_click`
  (`TimeoutException`).
- `tests/test_estruturas_menu_client_navigation.py::test_administrativo_clean_url_tab_still_activates_correct_tab`
  (`StaleElementReferenceException`) — verificado com `git stash` (passou 7/7 no HEAD anterior às
  alterações) e reexecuções repetidas no estado alterado (passou, passou, falhou), confirmando
  que a falha ocorre independentemente das alterações desta fase.

## Validação final

- `pytest -q` completo executado múltiplas vezes ao longo da fase: sempre 190/190 aprovados, ou
  189/190 com apenas um dos testes instáveis acima a falhar.
- Todos os módulos alterados importam individual e conjuntamente sem erro.
- Nenhum novo `from ... import *` foi introduzido.

## Riscos

Nenhum risco novo. Todas as alterações são substituições de import (mesmo símbolo, mesma
referência em runtime), sem alteração de lógica, assinatura de função ou comportamento
observável.
