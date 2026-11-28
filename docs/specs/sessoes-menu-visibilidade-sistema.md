# Sessões e Menu: visibilidade pela coluna SISTEMA

Status: regra confirmada pelo utilizador. O código já a cumpre (verificado em 2026-11-25 com teste de regressão em `tests/test_menu_settings.py`).

## Regra

A coluna **SISTEMA** do processo **Sessões → Menu** (e do processo **Perfil de autorização**, mesma coluna `visibility_scope_label`) define quem vê o menu ou o perfil:

| Valor na coluna | Quem vê |
|---|---|
| **Default** | Todas as entidades. |
| **Owner** | Somente a entidade **1000** (`entities.entity_number = 1000`). |
| **Legado** | Somente a entidade que **criou** o registo. |

## Quem cria cada valor

- Só a entidade **Owner (1000)** cria registos para todas as entidades (Default e Owner).
- A entidade **Legado** cria sempre para si própria. Logo, o criador de um registo Legado é o seu próprio `entity_id`.

## Estado atual no código

- Valor guardado em `sidebar_menu_settings.menu_config.visibility_scopes`:
  - `null` ou `["owner", "legado"]` → Default (`appgenesis/services/process_settings/normalizers.py`, `_resolve_visibility_scope_label_from_mode`).
  - `["owner"]` → Owner.
  - `["legado"]` → Legado.
- Filtro em runtime: `get_visible_sidebar_menu_keys` (`appgenesis/menu_settings.py:619`) compara `visibility_scopes` com `entities.profile_scope` da entidade ativa.
- Entidades em produção (leitura de 2026-11-25):
  - id 1, `entity_number` 1001, "Verbo Braga", `profile_scope = legado`.
  - id 2, `entity_number` 1000, "DeixaEstarService", `profile_scope = owner`.

## Como o código cumpre a regra

1. **Linhas por entidade**: `_menu_rows_for_entity` (`appgenesis/menu_settings.py:174`) carrega só as linhas `sidebar_menu_settings` da entidade ativa, mais as linhas **Default** do owner. Por isso um Legado de uma entidade nunca aparece a outra.
2. **Filtro**: `get_visible_sidebar_menu_keys` mostra uma linha se `visibility_scopes` contém o `profile_scope` da entidade ativa. `Default` contém os dois; `Owner` só `owner`; `Legado` só `legado`, e como só entram linhas da própria entidade, fica limitado a ela.
3. **Owner = entidade 1000**: o código identifica o owner por `profile_scope = owner`, não pelo número 1000. Hoje coincide (só a entidade 1000 é `owner`).
4. **Perfil de autorização** (`auth_profile_entity_scope.py`): não alterado neste PR; a regra acima aplica-se aos menus.

## Decisão

- Legado: visível só quando a entidade ativa é a dona do registo (`registo.entity_id = entidade ativa`). Não é preciso campo novo.
- Owner e Default: registo criado pela entidade 1000. Owner visível só a 1000; Default visível a todas.
- Não é preciso alterar código de menus. Falta só confirmar o perfil de autorização.
