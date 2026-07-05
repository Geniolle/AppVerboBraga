# Fase 7 — Validação do registry de admin_subprocesses

## Objetivo

O plano original referia a Fase 7 como "conclusão do registry de
admin_subprocesses", cobrindo `page_handler.py` e `settings_handlers.py`.
O `risk-map.md` (Risco #9, gerado na Fase 0) já tinha delimitado o âmbito
concreto: "validação automática do registry" que distinga um subprocesso
**registado** (presente no `ADMIN_SUBPROCESS_REGISTRY`, `enabled=True`) de
um subprocesso **efetivamente migrado** (com repositório real por trás),
citando o caso concreto `UTILIZADOR_CONFIG` (`enabled=True`,
`repository_class=""`).

## Levantamento prévio

Antes de alterar qualquer coisa, foi confirmado que:

- `page_handler.py` já usa `build_admin_subprocess_state` +
  `get_admin_subprocess_config` para os 4 subprocessos nativos (Sessões,
  Perfil de autorização, Objeto de autorização, Menu) — o lado de leitura
  do registry já está bem integrado, não há god-function nem duplicação
  óbvia a resolver aqui.
- `settings_handlers.py` (2699 linhas) e `profile_handlers.py` (rotas
  `auth-profile-save`/`auth-objeto-save`) **não usam o registry** — cada
  subprocesso tem handlers de escrita (save/move/delete) próprios e
  independentes. Isto é esperado: os repositórios em
  `admin_subprocesses/repositories/*.py` (confirmado lendo
  `base.py`/`sidebar_section_repository.py`) só implementam `list_rows`/
  `get_for_edit` — não há `create`/`update`/`move`/`delete` reais
  implementados em nenhum deles, apesar de `BaseAdminSubprocessRepository`
  declarar essas assinaturas.
- Reescrever os handlers de escrita para usarem os repositórios exigiria
  tocar exatamente a área que o `AGENTS.md`/`risk-map.md` (Risco #4)
  identifica como a mais frágil do projeto: 27 regras de incidente
  `APPGENESIS_SESSOES_V4`–`V30` documentadas, com funções já em `_v19`/
  `_v25` por causa de regressões reais anteriores. Isso não é uma
  "conclusão do registry" segura para uma fase autónoma — seria reescrever
  ~5000 linhas do código mais historicamente instável do repositório sem
  pedido explícito de negócio, na prática reimplementando save/move/delete
  de Sessões, Menu, Perfil de autorização e Objeto de autorização. Ficou
  fora do âmbito desta fase por ser desproporcional ao risco.
- Também se confirmou que `repository_class` (string com o caminho
  `módulo.Classe`) nunca é resolvida em nenhum ponto do código — os
  consumidores reais (`page_handler.py`) importam as classes diretamente
  por `import` estático, não leem este campo. Ou seja, o campo é meramente
  descritivo hoje, sem nenhuma validação de que aponta para algo real.

## Trabalho realizado

Criado `appgenesis/admin_subprocesses/validation.py`:

- `resolve_admin_subprocess_repository_class(dotted_path)` — resolve
  dinamicamente o caminho `módulo.Classe` e confirma que é uma subclasse de
  `BaseAdminSubprocessRepository`; devolve `None` em qualquer falha
  (import quebrado, atributo inexistente, classe errada).
- `is_admin_subprocess_effectively_migrated(config)` — `True` apenas se o
  `repository_class` resolver com sucesso.
- `validate_admin_subprocess_config(config)` /
  `validate_admin_subprocess_registry()` — devolvem uma lista de
  `AdminSubprocessValidationIssue` (severidade `error`/`warning`):
  - `error`: `repository_class` preenchido mas não resolve (drift/typo).
  - `warning`: `repository_class` vazio mas `enabled=True` e
    `migration_status` em `{"native", "native_next"}` — o caso "registado
    mas não migrado" (hoje só `utilizador`).
  - Nenhum problema é reportado para configs deliberadamente não
    habilitadas (ex.: `contas`, `enabled=False`,
    `migration_status="legacy_pending"`).

Nenhuma rota, template ou handler de escrita existente foi alterado — é
uma peça de tooling puramente aditiva.

## Técnica de validação usada

- `python -m pyflakes appgenesis/admin_subprocesses/validation.py
  tests/test_admin_subprocess_validation.py` — zero erros.
- `python -c "import appgenesis.admin_subprocesses.validation"` — import
  limpo.
- Execução manual de `validate_admin_subprocess_registry()` contra o
  registry real, confirmando o resultado esperado: apenas `utilizador`
  gera aviso; `entidade`, `sessoes`, `perfil_de_autorizacao`,
  `objeto_de_autorizacao` e `menu` resolvem sem problemas;
  `contas` não gera nenhum problema.
- `pytest -q` completo — 201/201 aprovados (196 pré-existentes + 5 novos).

## Testes novos (`tests/test_admin_subprocess_validation.py`)

1. Os 5 configs nativos com `repository_class` real não geram nenhum
   problema e são marcados como efetivamente migrados.
2. `utilizador` gera exatamente um aviso com a mensagem "registado !=
   efetivamente migrado".
3. `contas` (desabilitado, `legacy_pending`) não gera nenhum problema.
4. Um `repository_class` com caminho inexistente gera um erro.
5. A validação completa do registry só assinala `utilizador`.

## Ficheiros alterados/criados

- `appgenesis/admin_subprocesses/validation.py` (novo)
- `tests/test_admin_subprocess_validation.py` (novo)

## Riscos

Nenhum risco introduzido em comportamento existente — apenas código
adicionado, nenhum handler de escrita ou rota tocada. O risco residual
(documentado, deliberadamente não resolvido nesta fase) é que
`settings_handlers.py`/`profile_handlers.py` continuam sem repositórios de
escrita reais por trás do registry — os campos `create`/`update`/`move`/
`delete` de `BaseAdminSubprocessRepository` continuam por implementar.
Migrar isso é um trabalho de reescrita de grande risco (área com 27 regras
de incidente documentadas) que deve ser um pedido de negócio explícito e
isolado, não parte de uma fase de refatoração autónoma.
