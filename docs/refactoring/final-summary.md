# Resumo final — Refatoração de arquitetura por processo (Fases 0-10)

## Contexto

Este documento fecha o esforço de refatoração autónomo de 11 fases (Fase 0
a Fase 10) da branch `refactor/appgenesis-process-architecture`, cujo
objetivo era separar o código por domínio/processo/módulo/caso de
uso/serviço/repositório/validação/UI reutilizável, preservando o
comportamento atual e melhorando segurança, performance, manutenibilidade
e reutilização — sem tocar em `master`/`main` e sem quebrar produção.

51 commits, cada um correspondendo a uma unidade coerente de extração ou a
um documento de fase, com `pytest -q` corrido entre cada um.

## O que mudou, fase a fase

- **Fase 0** (levantamento, não documentada em `phase-N-summary.md` — ver
  `risk-map.md`, `validation-plan.md`, `inventory.md`, `current-architecture.md`):
  mapeou os 10 riscos do projeto e o plano de validação por fase.
- **Fase 1**: base comum aditiva — `appgenesis/shared/` (`errors.py`,
  `results.py`, `pagination.py`, `normalization.py`) e `appgenesis/web/`
  (`templates.py`, `dependencies.py`, `responses.py`, `view_context.py`
  placeholder). Zero ficheiros alterados, só criados.
- **Fase 2**: eliminadas todas as cascatas `from appgenesis.core import *` /
  `from appgenesis.services import *` em 23 ficheiros (16 route handlers +
  7 módulos de `services/`), substituídas por imports explícitos. Achado
  registado, não corrigido nesta fase: `_apply_meu_perfil_subsequent_visibility_v2`
  duplicada em `services/page.py`.
- **Fase 3**: extraídos os casos de uso de 4 domínios para
  `appgenesis/domains/{webhooks,empresa,auth,meu_perfil}/`, com os route
  handlers reduzidos a consumidores finos. Decisão de fronteira registada:
  `page_handler.py`/`settings_handlers.py` (Sessões/Menu/Perfis de
  autorização) e o motor de campos dinâmicos (`update_personal_profile`,
  `update_dynamic_process_profile`) ficaram deliberadamente fora, por
  pertencerem a `admin_subprocesses/` (Fase 7) e ao motor de processos
  (Fase 6), respetivamente.
- **Fase 4**: removido o bloco morto `V1` de
  `_apply_meu_perfil_subsequent_visibility_v2` (achado da Fase 2,
  confirmado como código inalcançável); `get_page_data`
  (`services/page.py`) decomposto de ~740 para ~430 linhas em 6 funções
  privadas nomeadas, sem alterar nenhuma chave/valor do dicionário de
  retorno.
- **Fase 5**: após confirmar por levantamento que o schema
  `app_modules`/`entity_module_entitlements` não tinha nenhum consumidor
  real e que as rotas de `tesouraria` citadas no seed não existiam
  (ambiguidade de negócio sinalizada ao utilizador via `AskUserQuestion`),
  construído apenas o mecanismo genérico `resolve_module_access` em
  `domains/modules/`, sem nenhuma rota de negócio nova — decisão explícita
  do utilizador.
- **Fase 6**: investigada a hipótese de duplicação entre o bloco V2 de
  visibilidade do Meu Perfil e o motor genérico de `services/profile.py`;
  confirmado que não era duplicação mas orquestração legítima adicional.
  Bloco movido (sem alteração de lógica) para
  `domains/meu_perfil/visibility.py`.
- **Fase 7**: construído `admin_subprocesses/validation.py`, que distingue
  um subprocesso **registado** no `ADMIN_SUBPROCESS_REGISTRY` de um
  **efetivamente migrado** (repositório real por trás) — capturando o caso
  `utilizador` (`enabled=True`, sem `repository_class`). Confirmado e
  documentado, mas deliberadamente não resolvido: `settings_handlers.py`
  ainda não usa repositórios reais de escrita (área de 27 incidentes
  documentados, fora do âmbito de uma fase autónoma).
- **Fase 8**: removidos 25 ficheiros JS + 1 CSS em `static/{js,css}/modules/`
  comprovadamente sem nenhuma referência em templates/rotas/outros
  ficheiros (logo nunca carregados em runtime). 3 ficheiros órfãos de
  template mas citados por um script dormente (`restore_template.py`)
  foram deliberadamente mantidos.
- **Fase 9**: levantamento confirmou que a disposição de 3 tabelas legadas
  (`songs`, `admin_definitions`, `process_view_authorization_rules`) já
  tinha sido investigada exaustivamente por um processo de governação
  separado (`gsd/`, 5 relatórios + 1 ADR + decisões formais) e permanece
  pendente de validação humana explícita — esta fase não tentou
  resolver essa ambiguidade de negócio. Trabalho realizado: inventário dos
  19 scripts pontuais sem referências de código (Risco #10), não removidos
  por não ser possível provar ausência de uso como runbook operacional; e
  confirmação via `docker compose exec web python -m alembic
  current/heads/check` de que a baseline documentada se mantém sem novo
  drift.
- **Fase 10**: sem âmbito vinculativo pré-definido em `risk-map.md`/
  `validation-plan.md`. Após confirmação explícita do utilizador (via
  `AskUserQuestion`), criado `.github/workflows/ci.yml` — primeira
  infraestrutura de CI do repositório. Corre `pytest` (gate real,
  bloqueante) e `pyflakes` (relatório informativo, não bloqueante, por
  causa de 36 falsos positivos pré-existentes de "undefined name" em
  `models/*.py`, causados por forward refs de `relationship()` do
  SQLAlchemy). Confirmado que a suite não-Selenium (180 testes) não
  depende de Postgres — usa fixtures SQLite em memória isoladas por
  ficheiro de teste.

## Decisões arquiteturais vinculantes mantidas em todas as fases

1. `appgenesis/admin_subprocesses/` continua a ser a arquitetura definitiva
   para Entidade/Sessões/Menu/Perfil de autorização/Objeto de autorização.
   `appgenesis/domains/` cobre apenas Auth/Empresa/Webhooks/Meu Perfil (e,
   desde a Fase 5, Modules).
2. Um commit por ficheiro/unidade coerente de extração, com `pytest`
   corrido entre cada um.

## Ambiguidades de negócio identificadas e explicitamente não resolvidas

Nenhuma destas foi decidida unilateralmente por esta refatoração — todas
foram ou escaladas ao utilizador (Fase 5, Fase 10) ou já estavam escaladas
e pendentes por um processo de governação separado (Fase 9):

- Disposição final das 3 tabelas legadas (`songs`, `admin_definitions`,
  `process_view_authorization_rules`) — pendente de decisão de negócio
  (`gsd/adr/ADR-001-legacy-authorization-granularity.md`).
- Se o schema `app_modules`/`entity_module_entitlements` (incluindo o
  módulo `tesouraria`) ainda corresponde a uma feature de negócio ativa —
  só o mecanismo genérico de resolução foi construído, sem rotas.
- Remoção dos 19 scripts pontuais em `scripts/` sem referências de
  código — requer confirmação operacional (não apenas de código) de que
  nenhum é usado como runbook manual.
- Unificação total do motor de visibilidade V2 do Meu Perfil com o motor
  genérico de `services/profile.py` — haveria mudança real de
  comportamento (tratamento de acentos, regras malformadas) sem testes de
  regressão que a validem.
- Migração de `settings_handlers.py`/`profile_handlers.py` para
  repositórios reais de escrita via `admin_subprocesses` — área de maior
  risco documentado do projeto (27 incidentes), fora do âmbito de uma
  fase autónoma sem pedido de negócio explícito e isolado.

## Validação acumulada

- Testes: 190 (baseline) → 196 (Fase 5, +6 `test_module_access.py`) → 201
  (Fase 7, +5 `test_admin_subprocess_validation.py`) → 201 (Fases 8-10,
  sem novos testes, sem regressão). Suite completa confirmada a passar
  201/201 no final desta fase.
- Nenhum ficheiro de modelo, rota ativa, template vivo ou handler de
  escrita de Sessões/Menu/Perfis de autorização foi alterado em nenhuma
  fase.
- Toda remoção de ficheiro (Fase 4: bloco de código morto; Fase 8: 26
  ficheiros JS/CSS) foi precedida de confirmação de zero referências, não
  de suposição.
- CI (Fase 10) confirma automaticamente, a partir de agora, em cada
  push/PR: `pytest` (180 testes não-Selenium, sem depender de Postgres) e
  relatório de `pyflakes`.
- **Validação Manual**: As evidências da validação funcional manual de ponta a ponta, executada em ambiente com browser real interativo, encontram-se documentadas em:
  `docs/refactoring/walkthrough.md`

## O que fica deliberadamente pendente após esta refatoração

- As 5 ambiguidades de negócio listadas acima continuam a exigir decisão
  humana explícita antes de qualquer ação adicional.
- Os 4 testes Selenium (incluindo os 2 encontrados só na Fase 10:
  `test_navigation_refresh_home.py`,
  `test_navigation_reload_and_loading_overlay.py`) continuam a exigir
  validação manual local com browser real — não correm em CI.
- `appgenesis/core.py` e `appgenesis/services/{__init__.py,legacy.py}`
  continuam como hubs de compatibilidade anotados (Fase 2), candidatos a
  remoção numa fase futura já com confirmação de zero consumidores.
- As 6 abas de configuração de processo (Geral, Configuração dos campos,
  Campos Adicionais, Campos Quantidade, Listas, Campos Subsequentes) em
  `settings_handlers.py`/`menu_settings.py` continuam deliberadamente fora
  do âmbito desta refatoração (mesma decisão da Fase 3/7). Um levantamento
  isolado (Fase 0 própria, sem alteração de código) está documentado em
  `docs/refactoring/process-settings-phase-0-assessment.md`.

## Ficheiros de referência desta refatoração

- `docs/refactoring/risk-map.md`, `validation-plan.md`, `inventory.md`,
  `current-architecture.md` — documentos de Fase 0.
- `docs/refactoring/phase-1-summary.md` a `phase-10-summary.md` — resumo
  detalhado de cada fase.
- Este ficheiro (`final-summary.md`) — síntese de fecho.
- `docs/refactoring/process-settings-phase-0-assessment.md` — levantamento
  isolado das 6 abas de configuração de processo, fora do âmbito das fases
  acima.
