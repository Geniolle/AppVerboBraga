# Mapa de risco — AppGenesis (Fase 0)

Ordenado por impacto potencial em produção.

## Risco #1 (CRÍTICO — bloqueia decisão de arquitetura) — conflito entre `domains/` proposto e `admin_subprocesses/` existente

O plano de refatoração (Fases 3, 5, 6, 7) propõe criar `appgenesis/domains/<area>/{use_cases,
services, repositories, schemas, permissions}.py` como a nova camada de orquestração, e um novo
`appgenesis/domains/modules/menu_provider.py` como fonte oficial de menu/acesso.

Só que **já existe** um motor equivalente, testado e com 30 iterações de correção documentadas em
produção: `appgenesis/admin_subprocesses/{registry,service,models}.py` +
`repositories/*_repository.py` + `templates/macros/admin_subprocess.html`. Ele já cobre Entidade,
Sessões, Perfil de autorização, Objeto de autorização e Menu, e o `AGENTS.md` (regra
`APPGENESIS_ADMIN_SUBPROCESS_CONFIG_BASE_V1`) determina explicitamente que **novos subprocessos
devem ser adicionados a este registry**, não a uma estrutura paralela.

**Se a Fase 3+ criar `domains/` sem reconciliar com `admin_subprocesses/`, o resultado é duas
arquiteturas concorrentes para o mesmo problema** — exatamente o tipo de fragmentação que o
objetivo geral do pedido quer eliminar. Isto é uma "ambiguidade de regra de negócio que pode
quebrar produção" nos termos da regra 18 do pedido original: requer decisão explícita antes de
prosseguir com as Fases 3, 5, 6 e 7, não uma escolha unilateral da IA.

**Decisão (2026-07-05):** opção (a). `appgenesis/admin_subprocesses/` é a arquitetura definitiva
para Entidade, Sessões, Menu, Perfil de autorização e Objeto de autorização — continuam a evoluir
lá, preservando o registry/service/repositories atuais e as 30 regras de incidente do AGENTS.md.
`appgenesis/domains/` só é criado para fluxos que ainda não têm equivalente nativo hoje: Auth,
Empresa, Webhooks e Meu Perfil (que hoje vive em `services/page.py`/`profile_handlers.py`, fora do
motor de subprocessos). A Fase 3 em diante deve seguir esta regra sem reabrir a decisão por fase.

## Risco #2 (ALTO) — cascata de wildcard imports

53 ocorrências de `import *` em `appgenesis/`, em duas camadas (`core.py` reexporta 79 símbolos;
`services/__init__.py`/`legacy.py` reexportam mais 18 módulos). 23 ficheiros importam de `core`
via `*`, 16 de `services` via `*` — na prática quase todo `routes/*/handler.py` faz os dois.

Risco concreto: remover ou renomear qualquer símbolo em `core.py` ou em qualquer módulo de
`services/` pode quebrar silenciosamente um handler que dependia dele por wildcard, sem erro em
tempo de import (só em runtime, ao chamar a função). A Fase 2 deve ser feita arquivo a arquivo,
com testes a correr após cada substituição — nunca em lote.

## Risco #3 (ALTO) — duplicação de gerações em `menu_settings.py` e `services/page.py`

`menu_settings.py` (4848 linhas) tem funções centrais redefinidas 2–3 vezes no mesmo ficheiro
(`normalize_menu_process_additional_fields_v3` 2x, `normalize_menu_process_subsequent_fields` 3x).
`services/page.py` tem `_apply_meu_perfil_subsequent_visibility_v2` definida 2x. Em Python, a
última definição de um nome no módulo é a que vale — isto já funciona hoje, mas qualquer edição
manual futura num destes blocos duplicados sem saber qual definição está "viva" pode reintroduzir
um bug antigo já corrigido. A Fase 4/6 deve identificar e remover as definições mortas primeiro
(com testes), antes de qualquer reorganização estrutural.

## Risco #4 (ALTO) — 30 regras de incidente documentadas para o subprocesso Sessões

O `AGENTS.md` contém as regras `APPGENESIS_SESSOES_*` de V4 a V30, cada uma corrigindo uma
regressão real (piscar de UI, `MutationObserver` duplicando render, cards órfãos fora da aba,
perda de contexto ao navegar, parâmetros de URL do subprocesso Menu vazando para Sessões, etc.).
Qualquer alteração à Fase 6 (motor de processos dinâmicos) ou à Fase 8 (frontend) que toque
`process_tabs.py`, `menu_settings.py`, `admin_subprocesses/service.py`, `new_user.js` ou
`admin_subprocesses_v1.js` tem de ser validada manualmente contra o fluxo completo de Sessões
(criar, editar, mover, listar ativas/inativas, navegar entre abas e voltar) — não basta o pytest.

## Risco #5 (MÉDIO) — autorização multi-tenant sem ponto único de enforcement

Não há middleware/`Depends()` central: cada handler chama `get_user_entity_permissions`
manualmente. Um novo endpoint criado durante a refatoração (ex.: Fase 3, ao extrair use cases)
pode esquecer a chamada e ficar sem proteção de tenant. A Fase 3 deve incluir, para cada use case
extraído, um teste explícito que confirma que a permissão é validada antes de qualquer
persistência — não assumir que "vem de fora" do use case.

## Risco #6 (MÉDIO) — `SidebarMenuSetting` é global, não por entidade

A configuração de menu/processos dinâmicos (`sidebar_menu_settings`) não tem `entity_id` — o
escopo por entidade vive dentro do JSON `menu_config` (`visibility_scope`/`profile_scope`). Uma
refatoração que assuma erradamente que menu é "por tenant" a nível de tabela (ex.: ao desenhar
`domains/modules/menu_provider.py`) pode introduzir uma segmentação multi-tenant que não existe
hoje e quebrar entidades que partilham a mesma configuração de menu por design.

## Risco #7 (MÉDIO) — módulos pagos são scaffolding sem enforcement

`app_modules`/`entity_module_entitlements`/`sidebar_menu_items` existem no schema e são semeados,
mas `require_module_access` não existe e nenhum handler lê estes modelos. A Fase 5 é
implementação nova de ponta a ponta (schema → resolução → enforcement por rota), não apenas "ligar
o que já existe". Deve ser testada explicitamente com os 4 cenários do plano: módulo core, módulo
pago ativo, módulo pago inativo, acesso direto por URL sem permissão.

## Risco #8 (BAIXO/MÉDIO) — dois conjuntos de repositórios de Entidade

`repositories/entity_repository.py` (genérico) e
`admin_subprocesses/repositories/entity_repository.py` (motor administrativo) coexistem. Antes de
criar `domains/entities/repositories.py` (Fase 3), esclarecer se um deve delegar no outro ou se
servem propósitos distintos, para não criar um terceiro repositório concorrente.

## Risco #9 (BAIXO) — inconsistência de metadados no registry administrativo

`UTILIZADOR_CONFIG.enabled=True` mas `repository_class=""` — o registry diz que está "nativo" mas
na prática o subprocesso Utilizador continua servido pelos handlers legados (`routes/users/*`).
Isto pode confundir a Fase 7 (validação automática do registry) se a checagem não distinguir
"registado" de "efetivamente migrado".

## Risco #10 (BAIXO) — acumulação de scripts pontuais `_v1`/`_v2`

`scripts/validar_*`, `scripts/limpar_*`, `scripts/diagnose_*` — conjunto de scripts de
diagnóstico/reparação escritos durante debugging de bugs específicos (mojibake, campos órfãos de
"Meu Perfil", regra de estado civil/cônjuge) e nunca removidos. Baixo risco de execução acidental,
mas ruído para quem procura a lógica "oficial". Não remover sem confirmar que nenhum runbook
operacional ainda depende deles (Fase 9).

## Pontos multi-tenant a preservar em qualquer fase

- `allowed_data_entity_ids` ≠ `allowed_structure_entity_ids` (gestores de tenant não acedem
  automaticamente a dados operacionais de entidades Legado).
- `Entity.profile_scope` (`owner`/`legado`) e o "bootstrap gap" (`can_manage_tenant_structure` é
  verdadeiro também quando não existe nenhuma entidade Owner ativa ainda).
- Filtros de `entity_id`/`MemberEntity.entity_id` são aplicados manualmente em cada
  repositório/serviço — não há filtro automático de sessão SQLAlchemy.
