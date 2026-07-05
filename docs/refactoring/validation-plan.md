# Plano de validação — AppGenesis (Fase 0)

Aplica-se a todas as fases 1–10. Cada fase deve rodar, no mínimo, o subconjunto relevante abaixo
e reportar o resultado no seu `phase-N-summary.md`.

## 1. Testes automatizados

```bash
pytest
```

Rodar sempre a suíte completa (não só os testes da área tocada), porque `menu_settings.py` e
`services/page.py` são consumidos por múltiplos domínios (ver `current-architecture.md`).

Se um teste específico precisar de mais contexto (Selenium, ex.
`test_auth_objeto_navigation_selenium.py`, `test_estruturas_menu_client_navigation.py`), correr
isolado e documentar se foi ignorado por falta de browser no ambiente:

```bash
pytest tests/test_auth_objeto_navigation_selenium.py -v
```

## 2. Migrations (Alembic) — via container Docker (regra AGENTS.md #2, Docker-first)

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
```

Resultado esperado de `alembic check`: `No new upgrade operations detected.` Só rodar
`alembic upgrade head` quando uma fase tiver criado migration nova e isso for explicitamente
esperado (nunca em fases que não alteram schema).

Evitar rodar Alembic no `.venv` local quando o banco real da app estiver no Docker (regra
AGENTS.md #2).

## 3. JavaScript

```bash
node --check static/js/new_user.js
node --check static/js/modules/<ficheiro_alterado>.js
```

Rodar para todo `.js` alterado numa fase, não só `new_user.js`.

## 4. Scan de mojibake

Procurar por texto corrompido em ficheiros alterados (`.py`, `.html`, `.js`, `.css`, `.md`):

```bash
git diff --name-only <base>...HEAD | xargs grep -lE "Ã|Â|�|\?\?" 2>/dev/null
```

A entrega de uma fase não está concluída enquanto houver mojibake visível na UI (regra AGENTS.md
#5). Nota: `??` só é sinal de mojibake em palavras portuguesas — não sinalizar falsos positivos em
código (ex. `dict.get(key, "??")` não é mojibake).

## 5. Validação manual mínima (por fase que tocar UI/fluxo)

- Login (`/login`) com utilizador existente.
- Menu lateral carrega e reflete a entidade ativa.
- Aba **Entidade**: criar, editar, listar ativos/inativos.
- Aba **Utilizador**: criar, editar, convite/reenvio.
- Aba **Perfil de autorização** / **Objeto de autorização**: criar, editar, listar.
- Aba **Sessões**: criar, editar (fluxo dedicado, sem `alert`), mover, listar ativas/inativas,
  navegar para outra aba e voltar (validar que os 3 cards reaparecem juntos, sem piscar).
- **Meu Perfil**: dados pessoais, morada, formação, verificação WhatsApp, campos subsequentes
  condicionais.
- Um processo dinâmico com campo `field_type=list` nas 3 variantes (`manual`, `automatic`,
  `field_list`), incluindo um caso de ciclo em `field_list` (deve resultar em lista vazia, não
  erro).

## 6. Validação adicional específica por fase

| Fase | Validação extra |
|---|---|
| 1 | App continua a importar (`python -c "import appgenesis.app"`); nenhuma mudança de comportamento observável |
| 2 | Import de cada handler alterado isoladamente; login e tela principal |
| 3 | Testes de entidade/utilizador/permissões; teste manual criar/editar/inativar/eliminar entidade |
| 4 | Testes de profile/menu/processos dinâmicos; `new_user.html` visualmente idêntico |
| 5 | Módulo core; módulo pago ativo; módulo pago inativo; acesso direto por URL sem permissão → 403 |
| 6 | `process_tabs`, `dynamic_process_layout`, lista manual/automática/`field_list`, ciclo em `field_list` |
| 7 | Registry: subprocesso ativo tem repository/endpoints/status/identity field/cards-tables IDs |
| 8 | `node --check` em todos os JS alterados; botões Guardar/Cancelar; Cancelar global; editor de processo |
| 9 | `alembic current`/`heads`/`check`/`upgrade head` via `docker compose exec web` |
| 10 | Suite completa + checklist de fluxos principais (login, menu, entidade, utilizador, perfil, processo dinâmico, campos lista, módulo com/sem permissão) |

## 7. Critérios de "phase-N-summary.md"

Cada resumo de fase deve conter: ficheiros criados, ficheiros alterados, comandos de validação
executados e resultado, riscos identificados durante a fase (novos ou dos já mapeados em
`risk-map.md`), e confirmação explícita de que o comportamento observável não mudou (exceto
quando a fase exigir mudança, caso em que a mudança deve ser descrita).
