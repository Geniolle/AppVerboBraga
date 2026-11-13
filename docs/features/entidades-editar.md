# Entidades: listar, exibir e editar

Onde fica: Administrativo → separador **Entidade** (`/users/new?menu=administrativo&admin_tab=entidade`).

## Fluxo

1. A lista "Entidades criadas" vem de `_dados_gerais_entities` (template `templates/new_user.html`).
2. Cada linha tem o menu de ações (⋮) com:
   - **Exibir detalhes** → `entity_edit_id=<id>&entity_view=1#edit-entity-card` (só leitura).
   - **Editar informações** → `target=edit-entity-card&entity_edit_id=<id>#edit-entity-card`.
3. O servidor (`appgenesis/routes/profile/page_handler.py`, rota `GET /users/new`) carrega a entidade
   e renderiza o cartão `#edit-entity-card` (só existe quando `entity_edit_data` está preenchido).
4. "Guardar" faz `POST /entities/update` (`appgenesis/routes/entities/update_handler.py`) e redireciona
   com `entity_success=...` para `#recent-entities-card`.

## Como o browser escolhe o cartão visível

O alvo (cartão a mostrar) é resolvido em três sítios do JS. Todos devem tratar `#edit-entity-card`
como alvo nativo, sem o converter para a lista:

| Ficheiro | Função | Papel |
|---|---|---|
| `static/js/modules/process_navigation_state_v1.js` | `resolveAdminSelectedTargetV1` | alvo no arranque (a partir de `target` e `hash`) |
| `static/js/modules/process_menu_runtime_v1.js` | `handleHashNavigation` | alvo quando o hash muda |
| `static/js/modules/admin_target_registry_v1.js` | `NATIVE_ADMIN_TARGETS_V1` | lista de alvos nativos da aba Administrativo |

`new_user.js` (`activateSubprocessCardsV1`) aplica o alvo final ao DOM. A última ativação ganha:
se outra ativação correr depois com `#recent-entities-card`, o formulário fica oculto.

## Histórico de correções

- **Primeiro clique em "Editar informações" não abria** (abria só no segundo).
  Causa: `resolveAdminSelectedTargetV1` e `handleHashNavigation` convertiam `#edit-entity-card`
  para `#recent-entities-card`, logo a seguir à ativação correta. A conversão foi removida nos dois
  sítios e `#edit-entity-card → administrativo` foi acrescentado a `hashTargetMenuMap`.
  Cache de scripts: `?v=20260713-entity-edit-startup-v1` e `?v=20260713-entity-edit-hash-v1`.
  Verificado no local: um clique abre o formulário; "Guardar" devolve `entity_success`.

## Testar

- Local: `docker compose up -d` → login de admin → Administrativo → Entidade → ⋮ → Editar informações.
- Produção: mesmo fluxo em `https://verbodavidabraga.pt/login`.
