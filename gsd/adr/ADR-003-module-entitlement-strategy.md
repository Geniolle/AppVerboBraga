# ADR-003: Estratégia de Módulos, Entitlements e Tesouraria

Status: proposed
Updated: 2026-07-05

## Context

A Issue #24 exigia definir a estratégia de uso de `app_modules`, `entity_module_entitlements` e Tesouraria.

### Estado atual do mecanismo de módulos

O mecanismo genérico de resolução de acesso a módulos `resolve_module_access` está implementado em `appgenesis/domains/modules/permissions.py` e testado em `tests/test_module_access.py` (6 testes passados).

As tabelas `app_modules` e `entity_module_entitlements` estão populadas no banco com os seguintes módulos:
- `home` (core=True, active=True)
- `administrativo` (core=True, active=True)
- `funcionarios` (core=True, active=True)
- `financeiro` (core=True, active=True)
- `relatorios` (core=True, active=True)
- `links` (core=True, active=True)
- `contato` (core=True, active=True)
- `tutorial` (core=True, active=True)
- `meu_perfil` (core=True, active=True)
- `tesouraria` (core=False, active=True)

### Estado atual do módulo Tesouraria

Após levantamento exaustivo:
- Não existe nenhuma rota FastAPI em `appgenesis/routes/` para `/tesouraria` ou qualquer subpath.
- As rotas `/tesouraria`, `/tesouraria/extratos/importar`, `/tesouraria/movimentos`, `/tesouraria/relatorios` existem apenas como seeds de `sidebar_menu_items` no script `scripts/modules/seed_app_modules.py`.
- A tabela `sidebar_menu_items` pode ter estas entradas, mas os endpoints de backend que as servem não existem.
- Nenhum template HTML ou JavaScript referencia rotas de tesouraria funcionais.

## Decision

### 1. Tesouraria permanece como módulo futuro

O módulo `tesouraria` é reconhecido como planeado mas não implementado. A decisão correta é:
- **Não criar UI falsa** nem rotas placeholder que respondam com conteúdo vazio.
- **Não ativar o menu de Tesouraria** para nenhuma entidade sem feature real validada.
- **Manter o módulo no banco** como `is_active=True` (o seed existe), mas sem expô-lo no menu.

### 2. `resolve_module_access` é o contrato arquitetural correto

O mecanismo `resolve_module_access` em `domains/modules/permissions.py` é o contrato que deve ser usado em toda futura implementação de módulos pagos:
- Módulos `is_core=True` são sempre acessíveis.
- Módulos `is_core=False` exigem `entity_module_entitlements.status = "active"` e validade temporal.

### 3. Integração com menu (futura)

Quando um módulo pago (ex. `tesouraria`) for implementado com rotas reais, o menu lateral deverá:
1. Verificar `resolve_module_access` antes de renderizar entradas de menu do módulo.
2. Bloquear o acesso direto por URL com erro 403 se o entitlement não estiver ativo.
3. Não confiar no frontend para esconder módulos — a verificação deve existir no backend.

## Consequences

- Nenhuma alteração de runtime nesta fase.
- A documentação formaliza o contrato arquitetural para implementações futuras.
- O mecanismo `resolve_module_access` fica documentado como o guard de acesso para módulos pagos.
- A Tesouraria não aparece no menu e não tem rotas acessíveis até que seja implementada.
