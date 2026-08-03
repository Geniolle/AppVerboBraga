# Runbook de scripts operacionais (`scripts/`)

Updated: 2026-07-06 — remoção do `smoke_test.py` hardcoded.

## Contexto

A Fase 9 do PR #22 (`docs/refactoring/phase-9-summary.md`) identificou scripts em
`scripts/` sem nenhuma referência de código fora da própria pasta (nem em
`README.md`, nem em testes, nem em `docker-compose.yml`, nem importados por
outro módulo Python), mas não os removeu por não conseguir provar que nenhum
operador ainda os corria manualmente como runbook.

Esta issue (#25) completa esse levantamento: lê o conteúdo de cada script,
confirma o que faz, se muta dados, se é seguro repetir, e decide entre manter
(documentado aqui), consolidar (v1→v2) ou remover (comprovadamente morto,
duplicado ou redundante com uma migration formal).

## Scripts operacionais mantidos e documentados (já existentes, sem alteração)

Estes já estavam documentados em `README.md` e continuam sem alteração:

- `bootstrap_admin.py`
- `init_db.py`
- `validate_web_app.py`

## Scripts pontuais mantidos

Nenhum destes é referenciado por código, testes ou CI — são runbooks manuais,
invocados via `docker compose exec web python scripts/<nome>.py` quando um
operador precisa diagnosticar ou corrigir um caso específico.

| Script | Classificação | Muta dados? | Notas |
|---|---|---|---|
| `limpar_meu_perfil_campos_orfaos_v1.py` | runbook manual | Sim, só com `--apply` (dry-run por omissão, cria backup JSON em `backups/meu_perfil_cleanup/`) | Contraparte de escrita de `validar_meu_perfil_campos_orfaos_v1.py`. |
| `validar_meu_perfil_campos_orfaos_v1.py` | runbook manual | Não (só leitura) | Contraparte de leitura do script acima; correr primeiro para inspecionar antes de aplicar a limpeza. |
| `limpar_meu_perfil_campos_subsequentes_ocultos_v1.py` | runbook manual | Sim, só com `--apply` (dry-run por omissão, backup em `backups/meu_perfil_subsequent_cleanup/`) | Limpa valores de campos escondidos por regras de subsequência que ficaram "presos". |
| `validar_meu_perfil_campos_subsequentes_v1.py` | runbook manual | Não (só leitura) | Validador genérico das regras de "campos subsequentes" do Meu Perfil (chaves duplicadas, operador inválido, referência circular, etc.). É o mais abrangente do grupo — cobre o mesmo espaço de configuração que os validadores de estado civil/cônjuge, de forma genérica. |
| `validar_existencia_campos_subsequentes_meu_perfil_v2.py` | runbook manual | Não (só leitura) | Verifica se existe configuração de "campos subsequentes" para o Meu Perfil e em que chave de armazenamento está. Substitui a v1 (removida — ver abaixo), que era um subconjunto estrito desta. |
| `validar_meu_perfil_regra_estado_civil_conjuge_v2.py` | runbook manual | Não (só leitura) | Valida a regra específica "estado civil → nome do cônjuge" contra os dados de todos os membros. Substitui a v1 (removida — ver abaixo), que exigia match exato de uma única regra; a v2 aceita qualquer regra com o mesmo par de campos. |
| `validar_meu_perfil_visibilidade_estado_civil_conjuge_v1.py` | runbook manual | Não (só leitura) | Verifica a mesma regra acima, mas chamando o serviço real (`get_page_data`) em vez de reimplementar a lógica sobre o JSON — mais próximo de um teste de integração que os outros dois. |
| `repair_mojibake.py` | runbook manual | Sim (sem dry-run, sempre aplica; sem backup automático) | Ferramenta genérica de reparação de mojibake (UTF-8/CP1252) em templates/código/estático e nas colunas `sidebar_menu_settings`, `app_modules`, `sidebar_menu_items`. Fazer backup da base de dados antes de correr. |
| `sync_member_country_profile_config.py` | runbook manual | Sim (idempotente — só insere o campo "País" onde ainda não existe) | Backfill de configuração para instalações onde a funcionalidade de país ainda não foi sincronizada no `menu_config` do Meu Perfil. |
| `limpar_entidade_lixo_igreja_braga_v1.py` | runbook manual | Sim, só com `--apply` (dry-run por omissão, cria backup JSON em `backups/entity_cleanup/`) | Remove a entidade de lixo "Igreja Braga" criada por versões antigas de `smoke_test.py` (critério restrito: `entity_number IS NULL`, `name='Igreja Braga'`, `email='consultorsapclaytonlopes@gmail.com'`, `is_active IS FALSE`). Usa `sqlalchemy.inspect` para descobrir dinamicamente todas as FKs de qualquer tabela para `entities.id` (não uma lista fixa) e aborta sem apagar nada se qualquer tabela relacionada (exceto a exceção abaixo) tiver linhas. Única exceção controlada ao "nunca CASCADE": vínculos em `member_entities` para esta entidade também são removidos, mas só se o membro ligado tiver pelo menos outra entidade associada (nunca deixa um membro sem nenhuma). Em produção (verificado em 2026-07-06), a entidade `id=22` tinha 1 vínculo em `member_entities` com o membro "Admin Sistema" (`member_id=1`), que também está ligado à entidade "Deixa Estar Tech" (`id=8`) — logo o vínculo pode ser removido em segurança antes da entidade. |
| `backfill_estado_civil_list_key_v1.py` | legado (mantido) | Sim (sem backup) | Corrige `list_key` desalinhado num campo do tipo lista ("Estado civil"). Não há evidência de que precise voltar a correr, mas mantido para referência caso o mesmo desalinhamento reapareça noutra instalação. |
| `backfill_menu_hierarchy_v1.py` | legado (mantido) | Sim (idempotente) | Recalcula a hierarquia de processos do menu a partir de `additional_fields`, após uma mudança de modelo de hierarquia já mergeada. |
| `diagnose_meu_perfil_header_tabs_v1.py` | legado (mantido) | Não (só leitura) | Diagnóstico pontual de uma investigação já resolvida sobre abas de cabeçalho no Meu Perfil. Inofensivo de manter. |
| `diagnostico_estado_civil_lista_v1.py` | legado (mantido) | Não (só leitura) | Diagnóstico pontual da mesma família de `backfill_estado_civil_list_key_v1.py`. |
| `apply_member_country.py` | legado (mantido) | Sim (idempotente — mas já aplicado) | Script gerador que introduziu a funcionalidade "País" (modelo, migration `membercountry01_add_country_to_members`, serviços, template, e o próprio `sync_member_country_profile_config.py`). Confirmado que todos os alvos já estão aplicados no código atual. Mantido como registo histórico de como a funcionalidade foi introduzida — não se espera que volte a correr. |

## Scripts removidos nesta auditoria

Removidos por serem comprovadamente mortos, duplicados ou substituídos — não
por uma decisão de negócio, apenas por factos técnicos verificáveis:

| Script removido | Motivo |
|---|---|
| `scripts/smoke_test.py` e wrapper raiz `smoke_test.py` | Criavam dados de demonstração diretamente na base, incluindo a entidade hardcoded `"Igreja Braga"`. Não eram usados no arranque normal, produção, CI ou testes automatizados e podiam sujar bases reais quando executados manualmente. |
| `validate_login_auto_entity_v1b.py` | **Quebrado**: `ast.parse` falha com `IndentationError` na linha 99 (bloco de verificação do modo "admin" incompleto). Não podia ser executado. Nenhuma referência fora de `scripts/`. |
| `validar_existencia_campos_subsequentes_meu_perfil_v1.py` | Subconjunto estrito de `validar_existencia_campos_subsequentes_meu_perfil_v2.py` (mesma lógica, v2 cobre mais formatos de regra). |
| `validar_meu_perfil_regra_estado_civil_conjuge_v1.py` | Subconjunto estrito de `validar_meu_perfil_regra_estado_civil_conjuge_v2.py` (v1 exigia match exato de uma regra; v2 generaliza). |
| `repair_settings_process_tabs_data.py` | Duplicado de `repair_mojibake.py`: mesmas 3 tabelas/colunas-alvo, mas com uma tabela de substituições fixa em vez de deteção automática de mojibake (superconjunto mantido). |
| `ensure_members_country_column.py` | Redundante: a coluna `members.country` já é garantida pela migration formal `membercountry01_add_country_to_members` (Alembic), que já está mergeada e aplicada. |
| `restore_template.py` | Não funcional: dependia de ficheiros `templates/new_user.html.bak_*` que já não existem no repositório. O incidente que motivou o script já está resolvido. |
| `validate_sidebar_jinja_v1.py` | Consolidado em teste automatizado: `tests/test_template_syntax.py` cobre a mesma verificação (sintaxe Jinja de `templates/partials/new_user_sidebar.html`) e corre em CI a cada push/PR, em vez de depender de execução manual. |

## Lacuna conhecida (não resolvida nesta issue)

`validate_login_auto_entity_v1b.py` verificava que o modo "admin" do login
mantém o seletor de entidade e o modo comum não. Essa lógica continua viva em
`appgenesis/domains/auth/use_cases.py` e `templates/login.html`, mas não há
atualmente nenhum teste pytest equivalente. Registado aqui como um gap de
cobertura para uma issue futura — não resolvido agora para não misturar
decisão de cobertura de testes de autenticação com esta auditoria de scripts.

## Critério de conclusão (issue #25)

- [x] Listados os scripts pontuais identificados na Fase 9 (e os 2 adicionados depois, na issue #26: as versões `_v2` de estado civil/cônjuge).
- [x] Cada script classificado como ativo/runbook manual/legado/duplicado/removível.
- [x] Confirmado, por grep em todo o repositório, que nenhum é usado em produção/CI/testes.
- [x] Scripts ativos/runbook documentados nesta página.
- [x] Duplicados `_v1`/`_v2` consolidados (mantida só a versão mais recente/abrangente).
- [x] Removidos apenas os scripts comprovadamente sem uso, quebrados ou redundantes com uma migration formal.
- [x] Criado teste automatizado para o único script cuja verificação era genérica e barata de mover para pytest (`test_template_syntax.py`); os restantes dependem de base de dados/estado específico e continuam como scripts manuais com fluxo `--apply`/dry-run já existente onde aplicável.
- [x] `README.md` atualizado para apontar para este runbook.
