# Fase 5 — Acesso a módulos (`domains/modules`)

## Objetivo

O plano de refatoração original previa a Fase 5 como "módulos/acesso" — tornar
`app_modules`/`entity_module_entitlements`/`sidebar_menu_items` uma fonte
oficial de acesso/menu, com enforcement por rota. O `risk-map.md` (Risco #7,
gerado na fase de levantamento) já sinalizava que isto seria "implementação
nova de ponta a ponta (schema → resolução → enforcement por rota), não apenas
'ligar o que já existe'".

## Levantamento prévio (decisão de escopo necessária)

Antes de construir, foi confirmado por grep exaustivo que o schema
`AppModule`/`EntityModuleEntitlement`/`SidebarMenuItem`
(`appgenesis/models/modules/*`) e o respetivo script de seed
(`scripts/modules/seed_app_modules.py`) **não têm nenhum consumidor real**:
zero rotas, zero templates, zero testes em todo o repositório leem estes
modelos. O menu lateral realmente em produção é o `SidebarMenuSetting`
(`menu_settings.py`, 4848 linhas), um mecanismo completamente separado e
não relacionado.

O módulo `tesouraria` (o único não-core no seed) referencia rotas
(`/tesouraria`, `/tesouraria/extratos/importar`, `/tesouraria/movimentos`,
`/tesouraria/relatorios`) que **não existem** em `appgenesis/routes/` —
`appgenesis/modules/treasury/` é um pacote vazio (stub).

Isto caracterizava uma ambiguidade de regra de negócio nos termos da regra 18
do pedido original: construir "enforcement por rota" real exigiria inventar
uma feature de negócio (importação de extrato bancário, conciliação,
relatórios financeiros) sem nenhuma especificação no repositório — trabalho de
produto novo, não refatoração. Foi apresentada a decisão ao utilizador antes
de prosseguir.

**Decisão do utilizador:** construir apenas o mecanismo genérico de
resolução/enforcement de acesso a módulos, sem criar nenhuma rota de negócio
nova. A peça de infraestrutura fica pronta para quando essas rotas existirem.

## Trabalho realizado

Ficheiros criados:
- `appgenesis/domains/modules/__init__.py`
- `appgenesis/domains/modules/repositories.py` — `find_app_module_by_key`,
  `find_entity_module_entitlement`.
- `appgenesis/domains/modules/permissions.py` — `resolve_module_access(session,
  entity_id, module_key)`, seguindo o mesmo padrão `XGranted`/`XDenied`
  (união `ModuleAccessResult`) já usado em `domains/auth` e `domains/empresa`
  desde a Fase 3, para que rotas futuras façam `isinstance()` no resultado tal
  como as restantes rotas migradas.

Regra de acesso implementada:
1. Módulo inexistente ou `is_active=False` → negado.
2. Módulo `is_core=True` → sempre concedido (não depende de haver linha de
   entitlement — módulos core não são "vendáveis").
3. Módulo não-core → exige `EntityModuleEntitlement` com `status="active"`
   para a entidade, dentro da janela `starts_at`/`expires_at` (se definidos).

Não foi criada nenhuma rota FastAPI nova, nenhum `Depends()` genérico, nem
nenhuma UI de tesouraria. A integração com rotas reais fica para quando essa
feature for pedida — este trabalho apenas evita que a próxima pessoa a
implementar um módulo pago tenha de reinventar a lógica de resolução.

### Nota de correção durante o desenvolvimento

`EntityModuleEntitlement.starts_at`/`expires_at` são `DateTime(timezone=True)`,
mas o SQLite (motor de BD por omissão do projeto, `sqlite:///app.db`) não
preserva `tzinfo` na leitura — um datetime gravado como aware volta naive.
Comparar diretamente com `datetime.now(timezone.utc)` (aware) levantaria
`TypeError: can't compare offset-naive and offset-aware datetimes` em
produção sempre que uma entidade tivesse uma entitlement com `expires_at`
definido. Corrigido com um normalizador `_as_naive_utc` interno a
`permissions.py`, testado explicitamente pelo cenário de entitlement expirada.

## Técnica de validação usada

- `python -m pyflakes appgenesis/domains/modules/*.py tests/test_module_access.py`
  — zero erros.
- `python -c "import appgenesis.domains.modules.permissions"` — import limpo.
- `pytest -q` completo — 196/196 aprovados (190 pré-existentes + 6 novos).

## Testes novos (`tests/test_module_access.py`)

Cobrem os 4 cenários exigidos pelo `risk-map.md` mais 2 casos de borda:
1. Módulo core → concedido sem entitlement.
2. Módulo pago com entitlement ativa → concedido.
3. Módulo pago com entitlement inativa → negado.
4. Acesso direto a `module_key` nunca registada → negado.
5. (extra) Módulo pago com entitlement ativa mas `expires_at` no passado →
   negado.
6. (extra) Módulo core mas `is_active=False` → negado (o interruptor de
   manutenção do módulo prevalece sobre `is_core`).

## Ficheiros alterados/criados

- `appgenesis/domains/modules/__init__.py` (novo)
- `appgenesis/domains/modules/repositories.py` (novo)
- `appgenesis/domains/modules/permissions.py` (novo)
- `tests/test_module_access.py` (novo)

## Riscos

Nenhum risco introduzido em comportamento existente — nenhum código
pré-existente foi alterado, apenas adicionado. O risco residual (documentado,
não resolvido nesta fase) é que o schema `app_modules`/
`entity_module_entitlements` continua sem nenhum consumidor real; o valor
desta fase é ter a lógica de resolução pronta e testada para quando essa
integração for necessária, evitando que seja inventada apressadamente nessa
altura.
