# Module Access — Referência Técnica

Updated: 2026-07-05

## Visão Geral

O AppGenesis usa um sistema de módulos configuráveis para controlar o acesso a funcionalidades pagas.

## Tabelas

### `app_modules`

Registo de todos os módulos disponíveis na plataforma.

| Coluna | Tipo | Descrição |
|---|---|---|
| `module_key` | `VARCHAR` | Chave única do módulo (ex. `tesouraria`) |
| `module_name` | `VARCHAR` | Nome legível |
| `is_core` | `BOOLEAN` | Se `True`, o módulo é sempre acessível sem entitlement |
| `is_active` | `BOOLEAN` | Se `False`, o módulo está globalmente desativado |

### `entity_module_entitlements`

Registo de acesso por entidade a módulos não-core.

| Coluna | Tipo | Descrição |
|---|---|---|
| `entity_id` | `INTEGER` | FK para `entities.id` |
| `module_key` | `VARCHAR` | Chave do módulo |
| `status` | `VARCHAR` | `"active"` ou `"inactive"` |
| `starts_at` | `TIMESTAMP` | Data de início do acesso (opcional) |
| `expires_at` | `TIMESTAMP` | Data de expiração do acesso (opcional) |

## Módulos Registados

| `module_key` | `is_core` | Estado |
|---|---|---|
| `home` | ✅ Core | Ativo |
| `administrativo` | ✅ Core | Ativo |
| `funcionarios` | ✅ Core | Ativo |
| `financeiro` | ✅ Core | Ativo |
| `relatorios` | ✅ Core | Ativo |
| `links` | ✅ Core | Ativo |
| `contato` | ✅ Core | Ativo |
| `tutorial` | ✅ Core | Ativo |
| `meu_perfil` | ✅ Core | Ativo |
| `tesouraria` | ❌ Pago | Planeado — sem rotas funcionais ainda |

## Função de Resolução

```python
from appgenesis.domains.modules.permissions import resolve_module_access

result = resolve_module_access(session, entity_id, "tesouraria")
# -> ModuleAccessGranted(module_key="tesouraria")
# -> ModuleAccessDenied(reason="...")
```

### Regras de Resolução

1. Se o módulo não existir ou estiver `is_active=False` → **Negado**.
2. Se o módulo for `is_core=True` → **Concedido** (sem verificar entitlement).
3. Se não existir `entity_module_entitlements` com `status="active"` → **Negado**.
4. Se o acesso ainda não começou (`starts_at > now`) → **Negado**.
5. Se o acesso expirou (`expires_at < now`) → **Negado**.
6. Caso contrário → **Concedido**.

## Módulo Tesouraria — Estado Atual

O módulo `tesouraria` está registado em `app_modules` com `is_core=False, is_active=True`.

**Não existem rotas FastAPI para `/tesouraria` ou qualquer subpath.**

As referências a rotas de Tesouraria no seed (`scripts/modules/seed_app_modules.py`) são
placeholders para implementação futura. A decisão de não criar UI falsa está documentada
no [ADR-003](file:///c:/workspace/AppVerboBraga/gsd/adr/ADR-003-module-entitlement-strategy.md).

## Contrato Para Implementações Futuras

Quando um módulo pago for implementado:

1. Criar rotas reais em `appgenesis/routes/<module_key>/`.
2. Cada rota deve chamar `resolve_module_access` antes de servir conteúdo.
3. Se `ModuleAccessDenied`, retornar erro `403 Forbidden`.
4. O menu lateral deve verificar o acesso antes de renderizar entradas do módulo.
5. Nunca confiar no frontend para esconder módulos pagos.
