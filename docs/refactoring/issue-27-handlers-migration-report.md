# Relatório — Migração de settings_handlers e profile_handlers para Repositórios Reais (Issue #27)

Updated: 2026-07-05

## Contexto

A Issue #27 pede a avaliação e migração dos `settings_handlers.py` e `profile_handlers.py` para repositórios reais no padrão `BaseAdminSubprocessRepository`.

## Estado Atual dos Subprocessos

### Subprocessos com repositório real (migrados)

| Subprocesso | Repositório |
|---|---|
| `entidade` | `entity_repository.EntityAdminRepository` |
| `sessoes` | `sidebar_section_repository.SidebarSectionAdminRepository` |
| `perfil_autorizacao` | `auth_profile_repository.AuthorizationProfileAdminRepository` |
| `objeto_autorizacao` | `objeto_autorizacao_repository.ObjetoAutorizacaoAdminRepository` |
| `menu` | `menu_repository.MenuAdminRepository` |

### Subprocessos sem repositório real

| Subprocesso | `migration_status` | `enabled` | Situação |
|---|---|---|---|
| `utilizador` | `native` | `True` | ⚠️ Registado mas servido por handlers legados |
| `contas` | `legacy_pending` | `False` | Desativado, sem prioridade |

## Diagnóstico do Subprocesso `utilizador`

O subprocesso `utilizador` está configurado em `UTILIZADOR_CONFIG` com:
- `enabled=True`
- `migration_status="native"`
- `repository_class=""` (vazio)

Isso significa que é registado no motor administrativo mas **não é servido pelo motor** — continua dependente dos handlers legados:
- `appgenesis/routes/users/create_handler.py`
- `appgenesis/routes/users/update_handler.py`
- `appgenesis/routes/users/delete_handler.py`
- `appgenesis/routes/users/resend_handler.py`
- `appgenesis/services/page.py` (carregamento da lista de utilizadores)

## Análise de Risco

A migração completa de `utilizador` para um repositório real implica:

1. Criar `user_repository.py` com `UserAdminRepository(BaseAdminSubprocessRepository)`.
2. Implementar `list_rows`, `get_for_edit`, `create`, `update`, `delete` respeitando scope de entidade, owner, legado e multi-tenant.
3. Migrar os handlers legados (4 ficheiros + page.py) para usar o repositório.
4. Atualizar testes (`test_create_user_use_case.py`, `test_update_user_handler.py`, etc.).
5. Garantir que os 27 incidentes documentados no `final-summary.md` (Fase 7) são cobertos.

**Isso é trabalho significativo**, fora do âmbito de uma etapa de análise/documentação isolada.

## Decisão

De acordo com o padrão documental desta série de PRs pós-refatoração:

1. **Não criar código de migração incompleto** que possa introduzir regressões.
2. **Documentar formalmente o estado atual** do subprocesso `utilizador`.
3. **Registar como risco controlado** a existência de `migration_status='native'` sem `repository_class`.
4. **Estabelecer o caminho técnico** para implementação futura: criar `user_repository.py` seguindo o padrão dos repositórios existentes.

## Caminho Técnico Para Implementação Futura

```python
# appgenesis/admin_subprocesses/repositories/user_repository.py

from appgenesis.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository

class UserAdminRepository(BaseAdminSubprocessRepository):
    def list_rows(self, session, context=None): ...
    def get_for_edit(self, session, edit_key, context=None): ...
    def create(self, session, payload, context=None): ...
    def update(self, session, edit_key, payload, context=None): ...
    def delete(self, session, edit_key, context=None): ...
```

Em `registry.py`:
```python
UTILIZADOR_CONFIG = AdminSubprocessConfig(
    ...
    repository_class="appgenesis.admin_subprocesses.repositories.user_repository.UserAdminRepository",
    ...
)
```

## Validação

- `validate_admin_subprocess_registry()` identifica 1 aviso: `[utilizador] ... registado != efetivamente migrado`.
- Nenhum erro crítico. O aviso é esperado e documentado.
- Todos os 180 testes (não-Selenium) passam.
