# Fase 8 — Consolidação de frontend (JS/CSS mortos)

## Objetivo

O plano original referia a Fase 8 como "consolidação de frontend"
(JS/CSS/templates duplicados). O `risk-map.md` (linhas 57-59) e o
`AGENTS.md` marcam esta área como a mais frágil do projeto: `new_user.js`
(~9974 linhas) orquestra `static/js/modules/*`, com 27 regras de
incidente documentadas (`APPGENESIS_SESSOES_V4`–`V30`), e qualquer
alteração ao comportamento carregado em runtime exige validação manual
no browser — validação que não posso executar de forma autónoma.

## Levantamento prévio

Antes de alterar qualquer coisa, foi confirmado que:

- Reescrever ou fundir managers versionados *ativos* (ex.: unificar as 6
  versões de `process_fields_config_manager_v1`–`v6` num só ficheiro)
  seria editar código carregado em produção sem poder validar no
  browser — desproporcional ao risco nesta fase autónoma.
- Existe, no entanto, um subconjunto de "consolidação" categoricamente
  seguro: ficheiros que **nunca são carregados por nenhum caminho de
  execução**. Apagar um ficheiro que nada referencia não pode alterar
  comportamento em runtime, ao contrário de editar um ficheiro vivo.

## Metodologia usada para identificar ficheiros mortos

1. Listar todos os ficheiros em `static/js/modules/` e
   `static/css/modules/`.
2. Extrair de todos os templates (`templates/*.html`) todas as
   referências `<script src="...">` / `<link href="...">` a esses
   diretórios.
3. Comparar as duas listas para encontrar ficheiros com zero referências
   em templates.
4. Para cada candidato, correr grep a todo o repositório (`.py`, `.html`,
   `.js`, excluindo `.venv`, `node_modules`, `appgenesis-mobile`, `.git`)
   para excluir referência dinâmica/indireta (ex.: construção de nome de
   ficheiro em runtime, `scripts/*.py` de manutenção).
5. Só ficheiros com zero referências em qualquer sítio foram
   considerados seguros para remover.

## Trabalho realizado

Removidos via `git rm`:

- 25 ficheiros em `static/js/modules/`: a família `additional_fields_*`
  (`compact_layout_v1-v3`, `equal_rows`, `header_groups_v3-v5`,
  `header_separators_v1`, `hierarchy_v2-v3`, `table_mode_v1`),
  `header_hierarchy_arrows.js`, `process_fields_config_manager_v1-v6.js`
  (só `v7` está vivo, referenciado em `templates/new_user.html`),
  `process_fields_config_save_persist_v1.js` e
  `process_fields_header_manager_v1-v6.js` (sem substituto vivo — família
  aparentemente substituída por `process_additional_fields_manager_v3.js`
  / `process_fields_config_manager_v7.js`).
- 1 ficheiro em `static/css/modules/`:
  `process_fields_header_alignment_v1.css` (único órfão entre os 14
  ficheiros CSS do diretório).

Corrigida também uma referência desatualizada em `AGENTS.md`, que citava
`process_fields_config_manager_v1.js` como exemplo ilustrativo — passou a
citar `process_fields_config_manager_v7.js` (o ficheiro vivo atual).

Deliberadamente **não removidos** (cautela adicional): `force_lista_tab_v1.js`,
`process_lists_v1.js`, `process_lists_runtime_v3.js`. Estes também não têm
nenhuma referência em templates vivos, mas são citados por nome dentro de
`scripts/restore_template.py` — um script histórico de reparo pontual,
dormente mas ainda presente no repositório. Por prudência (regra 18: nunca
remover código legado sem validar o uso), optei por não os apagar nesta
fase.

Nenhum ficheiro vivo/carregado foi editado. Nenhuma rota, template ou
manager ativo foi tocado.

## Técnica de validação usada

- `python -m pyflakes appgenesis/` — sem novos erros introduzidos (ruído
  pré-existente já documentado, ex.: redefinições em `menu_settings.py`,
  Risco #3, confirmado não relacionado com esta fase).
- `pytest -q` completo: numa primeira execução em background, 1 teste
  falhou (`test_administrativo_clean_url_tab_still_activates_correct_tab`,
  `StaleElementReferenceException` do Selenium — uma condição de corrida
  ao ler `.text` de um elemento que a página ainda estava a re-renderizar).
- Investigação da falha, por ser um teste Selenium sensível a timing:
  - Re-executado isoladamente no estado modificado (com as remoções) →
    falhou de novo.
  - `git stash` para voltar ao estado limpo (antes das remoções) e
    re-executado isoladamente → passou.
  - `git stash pop` para restaurar as remoções, seguido de 3 execuções
    consecutivas do mesmo teste isolado no estado modificado → passou
    nas 3.
  - Resultado: 4 passagens em 5 execuções totais, span­ando estado limpo
    e estado modificado, sem nenhum ficheiro apagado estar relacionado
    com a navegação testada (`top_menu_active_v1.js`, não tocado nesta
    fase). Conclusão: falha esporádica pré-existente do Selenium
    (condição de corrida de timing), não uma regressão introduzida pelas
    remoções desta fase.
- `pytest -q` completo confirmado com 201/201 aprovados (sem alteração ao
  número de testes; só ficheiros estáticos e um comentário de
  documentação foram tocados).

## Ficheiros alterados/criados

- 25 ficheiros JS removidos em `static/js/modules/` (ver lista completa
  no commit)
- 1 ficheiro CSS removido:
  `static/css/modules/process_fields_header_alignment_v1.css`
- `AGENTS.md` (exemplo ilustrativo corrigido)
- `docs/refactoring/phase-8-summary.md` (este ficheiro)

## Riscos

Nenhum risco introduzido em comportamento existente — todos os ficheiros
removidos tinham zero referências verificáveis em qualquer template,
rota, handler Python ou outro ficheiro JS do repositório; apagar um
ficheiro nunca carregado não pode alterar o que corre em produção.

Risco residual (documentado, deliberadamente fora do âmbito desta fase):
nenhum ficheiro JS/CSS *vivo* foi consolidado ou refatorado — a
duplicação real de managers ativos (ex.: múltiplas versões ainda
carregadas em paralelo, se existirem) continua por resolver, porque essa
consolidação exigiria validação manual no browser que não pode ser feita
de forma autónoma nesta fase, dado o histórico de 27 incidentes
documentados nesta área. Os 3 ficheiros não removidos
(`force_lista_tab_v1.js`, `process_lists_v1.js`,
`process_lists_runtime_v3.js`) permanecem como órfãos de template mas
referenciados por um script dormente — uma decisão de negócio futura
deve decidir se `scripts/restore_template.py` ainda é necessário antes de
os remover.
