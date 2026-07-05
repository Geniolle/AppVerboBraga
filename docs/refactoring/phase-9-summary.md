# Fase 9 — DB/migrations/bootstrap

## Objetivo

O plano original referia a Fase 9 como "DB/migrations/bootstrap". O
`risk-map.md` liga explicitamente esta fase a dois itens concretos:

- Risco #10 (`scripts/validar_*`, `scripts/limpar_*`, `scripts/diagnose_*`
  — acumulação de scripts pontuais de diagnóstico/reparação): "Não
  remover sem confirmar que nenhum runbook operacional ainda depende
  deles (Fase 9)."
- A drift de baseline do Alembic e a disposição de três tabelas legadas
  (`songs`, `admin_definitions`, `process_view_authorization_rules`),
  já profundamente investigada por um processo de governação separado
  (`gsd/`).

## Levantamento prévio

### Drift de Alembic / tabelas legadas

Antes de qualquer ação, li os 5 relatórios em `gsd/reports/` (todos
datados de 2026-07-03/04) mais `gsd/adr/ADR-001-legacy-authorization-granularity.md`
e `gsd/DECISIONS.md` (Decisões 011, 012, 013, 014, 015). Todos convergem
na mesma conclusão, de forma consistente e repetida:

- `songs`, `admin_definitions` e `process_view_authorization_rules`
  existem na base de dados, contêm dados reais, mas não têm nenhum
  modelo/repositório/serviço ativo no código atual.
- A reconciliação de `process_view_authorization_rules` contra o storage
  atual (`sidebar_menu_settings` + `members.profile_custom_fields`)
  mostrou correspondência **parcial**, não completa — apagar a tabela
  agora perderia granularidade de subprocesso/departamento/scope que
  ainda não foi migrada.
- `ADR-001` tem estado `proposed` (não `accepted`) e todas as suas
  perguntas de decisão estão explicitamente marcadas `pendente de
  validação humana`.
- `gsd/DECISIONS.md` já contém regras vinculativas (011, 012, 014, 015)
  que proíbem remover ou reintroduzir estas tabelas sem uma decisão de
  negócio explícita.
- `gsd/STATE.md` lista esta decisão como prioridade "near-term" ainda em
  aberto, não como trabalho concluído.

Confirmei também que a correção segura já aplicada nesse processo
(`appgenesis/models/user.py`: `system_type` com
`server_default="default"`) já está presente no código atual — nada a
fazer aqui.

**Conclusão:** isto é exatamente o caso "ambiguidade de regra de negócio
que pode quebrar produção" da regra 18 do pedido original — e já foi
sinalizado repetidamente (5 relatórios + 1 ADR + 4 decisões formais) sem
resolução, porque depende de uma decisão de produto que só um humano
pode tomar (ex.: o perfil "Tesouraria" ainda é necessário? as permissões
separadas "Importar extrato"/"Dados de extrato" ainda importam?). A
Decisão 008 do próprio `gsd/DECISIONS.md` reforça que estes artefactos de
planeamento não devem ditar alterações de runtime por si só. Esta fase
de refatoração **não** tenta resolver essa ambiguidade — respeita a
mesma cautela já adotada pelo processo `gsd/`, e não mexe nas 3 tabelas
nem nos seus modelos/dados.

### Scripts de diagnóstico/reparação pontuais (Risco #10)

Listado o conteúdo de `scripts/`: 27 ficheiros no total. Cruzando com
`README.md` (linha 16: "scripts/: comandos operacionais
(`bootstrap_admin`, `init_db`, `smoke_test`, `validate_web_app`)") e com
grep a todo o repositório (`.py`, `.md`, `docker-compose.yml`, sem
diretórios `.github/workflows` — não existem neste projeto):

- **Scripts operacionais documentados e mantidos** (usados e
  referenciados fora de `scripts/`): `bootstrap_admin.py`, `init_db.py`,
  `smoke_test.py`, `validate_web_app.py`.
- **Scripts pontuais sem nenhuma referência fora de `scripts/`** (nem em
  `README.md`, nem em testes, nem em outro código Python, nem em
  `docker-compose.yml`): `apply_member_country.py`,
  `backfill_estado_civil_list_key_v1.py`,
  `backfill_menu_hierarchy_v1.py`,
  `diagnose_meu_perfil_header_tabs_v1.py`,
  `diagnostico_estado_civil_lista_v1.py`,
  `ensure_members_country_column.py`,
  `limpar_meu_perfil_campos_orfaos_v1.py`,
  `limpar_meu_perfil_campos_subsequentes_ocultos_v1.py`,
  `repair_mojibake.py`, `repair_settings_process_tabs_data.py`,
  `restore_template.py`, `sync_member_country_profile_config.py`,
  `validar_existencia_campos_subsequentes_meu_perfil_v1.py`,
  `validar_existencia_campos_subsequentes_meu_perfil_v2.py`,
  `validar_meu_perfil_campos_orfaos_v1.py`,
  `validar_meu_perfil_campos_subsequentes_v1.py`,
  `validar_meu_perfil_regra_estado_civil_conjuge_v1.py`,
  `validar_meu_perfil_regra_estado_civil_conjuge_v2.py`,
  `validar_meu_perfil_visibilidade_estado_civil_conjuge_v1.py`,
  `validate_login_auto_entity_v1b.py`, `validate_sidebar_jinja_v1.py`
  (19 ficheiros).
  (As poucas ocorrências textuais encontradas durante o grep —
  `limpar_edit_key` em `page_handler.py`, `_backfill_legacy_rules` numa
  migração Alembic, `test_member_user_backfill_*` em
  `test_member_user_migration.py` — são coincidências de substring, não
  referências reais a estes ficheiros.)

**Diferença crítica em relação à Fase 8:** na Fase 8, "zero referências"
provava que um ficheiro JS/CSS nunca era carregado pelo browser, logo
apagar era seguro. Aqui, estes scripts são pontos de entrada CLI
autónomos (`python scripts/repair_mojibake.py`) — "zero referências no
código" **não prova** que nenhum operador ainda os corre manualmente
como ferramenta de runbook. Por isso, ao contrário da Fase 8, não os
removi.

## Trabalho realizado

Nenhuma alteração de código, schema ou dados nesta fase. Este ficheiro
de resumo é o único artefacto novo — documenta e fecha o levantamento
sem tomar ações destrutivas nem resolver ambiguidades de negócio por
conta própria.

## Técnica de validação usada

Não aplicável (nenhum código alterado). Confirmado via `git status` que
nenhum ficheiro de aplicação foi tocado nesta fase.

## Ficheiros alterados/criados

- `docs/refactoring/phase-9-summary.md` (novo)

## Riscos

Nenhum risco introduzido — fase puramente documental. Riscos residuais
(pré-existentes, deliberadamente não resolvidos aqui):

- A disposição final de `songs`, `admin_definitions` e
  `process_view_authorization_rules` continua pendente de validação
  humana explícita (ver `gsd/adr/ADR-001-legacy-authorization-granularity.md`).
  `alembic check` continua vermelho por causa destas 3 tabelas — isto é
  esperado e já documentado, não uma regressão.
- Os 19 scripts pontuais em `scripts/` continuam no repositório. Antes
  de os remover, alguém com visibilidade operacional (não só de código)
  deve confirmar que nenhum já foi promovido a passo de runbook.
