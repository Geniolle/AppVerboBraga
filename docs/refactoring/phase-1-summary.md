# Fase 1 — Base comum sem alterar comportamento

## Ficheiros criados

- `appgenesis/shared/__init__.py`
- `appgenesis/shared/errors.py` — `DomainError`, `PermissionDeniedError`, `ValidationError`, `NotFoundError`
- `appgenesis/shared/results.py` — `RedirectOutcome`, `TemplateOutcome`, `JsonOutcome`, `UseCaseResult`
- `appgenesis/shared/pagination.py` — `Page`, `paginate()` (paginação em memória, não faz query)
- `appgenesis/shared/normalization.py` — `normalize_text`, `normalize_bool`, `normalize_int`, `normalize_key`
- `appgenesis/web/__init__.py`
- `appgenesis/web/templates.py` — reexporta a instância única `templates` já criada em `appgenesis/core.py` (não cria uma segunda `Jinja2Templates`, para não divergir cache/globals da instância que `app.py` realmente usa)
- `appgenesis/web/dependencies.py` — `get_db_session`, `get_current_user_dict`, `get_selected_entity_id`, `get_current_user_permissions` — wrappers finos e com imports explícitos sobre `services/session.py` e `services/permissions.py` já existentes
- `appgenesis/web/responses.py` — `outcome_to_response()` converte `RedirectOutcome`/`TemplateOutcome`/`JsonOutcome` em `Response`
- `appgenesis/web/view_context.py` — placeholder vazio, reservado para a Fase 4 (separação de `services/page.py`)

## Ficheiros alterados

Nenhum. Esta fase é 100% aditiva.

## Decisão registada nesta fase

`docs/refactoring/risk-map.md` (Risco #1) foi atualizado com a decisão do utilizador: `appgenesis/admin_subprocesses/` continua a ser a arquitetura definitiva para Entidade, Sessões, Menu, Perfil de autorização e Objeto de autorização. `appgenesis/domains/` (Fase 3+) só será criado para fluxos sem equivalente nativo hoje: Auth, Empresa, Webhooks e Meu Perfil.

## Validação executada

- `python -c "import appgenesis.app"` — OK (só warning de depreciação pré-existente do `authlib`, não relacionado).
- Import direto de todos os módulos novos (`shared.*`, `web.*`) — OK.
- `pytest` — **190 passed**, nenhuma falha, nenhuma alteração de comportamento observável.

## Riscos

Nenhum risco novo introduzido. Nenhum destes módulos é consumido ainda por código existente — serão adotados gradualmente a partir da Fase 2/3.
