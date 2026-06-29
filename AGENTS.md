# AGENTS.md - Regras Locais do Projeto AppVerboBraga

Estas regras são obrigatórias para qualquer alteração no projeto AppVerboBraga.

## 1) Objetivo do projeto

O AppVerboBraga é uma aplicação SaaS modular para igrejas.

A aplicação deve crescer por módulos ativáveis por entidade, por exemplo:

- Núcleo/Base
- Tesouraria
- Eventos
- Escalas
- Cursos
- Relatórios avançados

Novas funcionalidades comerciais devem ser criadas como módulos, não como páginas soltas.

## 2) Docker-first

Este projeto usa Docker.

Sempre que a tarefa envolver banco de dados, Alembic, migrations, validação de models ou execução da aplicação, usar o container `web`.

Comandos corretos:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head
```

Evitar executar Alembic no ambiente local `.venv` quando o banco real usado pela aplicação estiver no Docker.

## 3) Codificação de texto

Todos os ficheiros de código e templates devem ficar em UTF-8.

Extensões principais:

- `.py`
- `.html`
- `.js`
- `.css`
- `.md`
- `.json`
- `.yml`
- `.yaml`
- `.ini`
- `.toml`

Nunca deixar texto com mojibake no produto final.

Textos errados:

- `ConfiguraÃ§Ã£o`
- `CabeÃ§alho`
- `InformaÃ§Ãµes`
- `AÃ§Ãµes`
- `NÃ£o`
- `Â`
- `�`
- `??` em palavras portuguesas

Textos corretos:

- `Configuração`
- `Cabeçalho`
- `Informações`
- `Ações`
- `Não`

## 4) PowerShell

No PowerShell, comentários são feitos com `#`.

Não usar `//` em comandos PowerShell.

Correto:

```powershell
####################################################################################
# (1) VALIDAR PROJETO
####################################################################################
```

Incorreto em PowerShell:

```powershell
//###################################################################################
```

## 5) Validação obrigatória contra mojibake

Depois de alterar ficheiros `.py`, `.html`, `.js`, `.css` ou `.md`, procurar por caracteres suspeitos:

- `Ã`
- `Â`
- `�`
- `??`

A entrega não deve ser concluída enquanto houver texto corrompido visível na UI.

## 6) Estrutura por blocos

Sempre dividir código em blocos de processo.

Em Python/PowerShell:

```python
# ###################################################################################
# (1) DESCRIÇÃO DO BLOCO
# ###################################################################################
```

Em JavaScript:

```javascript
//###################################################################################
// (1) DESCRIÇÃO DO BLOCO
//###################################################################################
```

## 7) Arquitetura modular

As tabelas principais da nova arquitetura modular são:

- `app_modules`
- `sidebar_menu_items`
- `entity_module_entitlements`

Regra:

- Módulos core aparecem por padrão.
- Módulos pagos só aparecem se a entidade tiver `entity_module_entitlements.status = active`.

Exemplo:

```text
module_key = tesouraria
status = active
```

Se o módulo estiver `inactive`, ele não deve aparecer no menu e não deve permitir acesso direto por URL.

## 8) Menu lateral

Evitar criar menus fixos diretamente no HTML.

O menu lateral deve evoluir para ser gerado a partir das tabelas:

- `app_modules`
- `sidebar_menu_items`
- `entity_module_entitlements`

A tabela antiga `sidebar_menu_settings` é compatibilidade temporária.

## 9) Segurança de módulos pagos

Não confiar apenas no frontend para esconder módulos.

Toda rota de módulo pago deve validar acesso no backend.

Exemplo conceitual:

```python
require_module_access(session, entity_id, "tesouraria")
```

Se a entidade não tiver acesso ativo, retornar erro 403.

## 10) Migrations

Não criar alterações estruturais no banco sem migration Alembic.

Qualquer nova tabela, coluna, índice ou constraint deve passar por migration.

Após criar ou alterar models, validar:

```bash
docker compose exec web python -m alembic check
```

Resultado esperado:

```text
No new upgrade operations detected.
```

## 11) Regras para datas

Quando houver lógica JavaScript/Google Apps Script relacionada ao projeto AppVerboBraga, formatar datas com:

```javascript
const dataFormatada = Utilities.formatDate(new Date(dataTexto), "GMT+1", "dd/MM/yyyy");
```

## 12) Regra final

Antes de concluir qualquer alteração, validar:

- aplicação sobe no Docker;
- logs sem traceback;
- texto sem mojibake;
- migrations sincronizadas;
- menu não quebrou;
- módulos pagos continuam protegidos.

<!-- APPVERBO_CONFIGURABLE_ITEMS_LAYOUT_V1_START -->

## 13) Layout obrigatório para listas configuráveis

Sempre que uma funcionalidade permitir criar múltiplos itens configuráveis, como campos adicionais, listas, regras, abas, sessões, opções, permissões ou estruturas semelhantes, a interface deve seguir obrigatoriamente o padrão abaixo:

1. Um bloco superior para criar ou editar apenas um item por vez.
2. Uma tabela ou lista inferior com os itens já criados.
3. Paginação obrigatória na tabela ou lista.
4. A tabela ou lista visível deve ser a fonte visual principal para o utilizador.
5. Containers antigos podem existir apenas como compatibilidade temporária e devem ficar ocultos.
6. O submit deve reconstruir os inputs no formato esperado pelo backend atual.
7. Não criar formulários longos com todos os itens abertos simultaneamente.
8. A lógica genérica deve ser extraída para um manager reutilizável sempre que houver repetição de comportamento.
9. O ficheiro `new_user.js` deve apenas inicializar managers sempre que possível, evitando concentrar lógica extensa de layout.
10. Cada ajuste relevante em função existente deve criar uma nova função com sufixo sequencial.

Exemplo de versionamento obrigatório:

    setupProcessAdditionalFieldsManagerV2()
    setupProcessAdditionalFieldsManagerV3()

Estrutura recomendada para listas configuráveis:

    Editor superior
    Tabela ou lista paginada inferior
    Container legado oculto, se necessário
    Sincronização dos inputs antes do submit

Exemplos de funcionalidades que devem seguir este padrão:

- Campos adicionais
- Listas do processo
- Campos subsequentes
- Sessões do menu lateral
- Opções configuráveis
- Permissões configuráveis
- Regras administrativas

<!-- APPVERBO_CONFIGURABLE_ITEMS_LAYOUT_V1_END -->
## 14) Padrão obrigatório para abas configuráveis do processo

Toda nova aba configurável dentro do editor de processo deve seguir o padrão visual e técnico abaixo:

1. A aba deve ter apenas dois blocos visuais principais:
   - bloco superior de criação/edição;
   - bloco inferior com tabela ou lista paginada dos itens criados.

2. Não deve existir um terceiro bloco visual externo envolvendo os dois blocos principais.
   O container principal do manager deve ser apenas estrutural, sem borda, fundo ou padding visual.

3. O bloco superior deve editar apenas um item por vez.

4. A tabela inferior deve ser a fonte visual principal dos itens já criados.

5. As ações da tabela devem usar ícones alinhados lado a lado:
   - editar;
   - subir;
   - descer;
   - remover.

6. Toda aba configurável deve ter um manager JavaScript próprio em `static/js/modules`.

Exemplos de nomes esperados:

```text
process_lists_manager_v1.js
process_subsequent_fields_manager_v1.js
process_fields_config_manager_v1.js
process_additional_fields_manager_v3.js


E eu também acrescentaria uma pequena seção operacional:

```markdown
## 15) Validação de alterações em templates e assets

Sempre que alterar `templates/new_user.html` ou assets usados por ele:

1. Atualizar o cache buster dos ficheiros CSS/JS alterados.
2. Validar JavaScript com:

```bash
node --check static/js/new_user.js
node --check static/js/modules/<ficheiro_alterado>.js

<!-- APPVERBO_STATIC_GRID_RULE_V1_START -->

## Regra obrigatoria para campos lado a lado em abas configuraveis

Quando uma aba configuravel do processo precisar apresentar campos lado a lado, a logica deve seguir o mesmo padrao usado na aba Campos adicionais.

Regra principal:

- O HTML deve definir a estrutura.
- O CSS deve definir o grid.
- O JavaScript deve gerir apenas dados e acoes.

Os campos que ficam lado a lado devem nascer como filhos diretos do mesmo bloco no template HTML.

Exemplo correto em HTML:

<div data-process-fields-config-editor-block class="configurable-items-editor-grid-v1 process-fields-config-editor-grid-v1">
  <div class="field">
    <label>Nome do campo</label>
    <select></select>
  </div>

  <div class="field">
    <label>Cabecalho do campo</label>
    <select></select>
  </div>

  <div class="form-action-row">
    <button>Guardar</button>
    <button>Cancelar</button>
  </div>
</div>

Regra de CSS:

[data-process-fields-config-editor-block] {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(260px, 1fr);
  gap: 12px;
  align-items: end;
}

[data-process-fields-config-editor-block] > .field {
  min-width: 0;
  width: 100%;
}

[data-process-fields-config-editor-block] select,
[data-process-fields-config-editor-block] input {
  width: 100%;
  min-height: 38px;
}

[data-process-fields-config-editor-block] .form-action-row {
  grid-column: 1 / -1;
}

Regra de JavaScript:

- Pode ler valores.
- Pode validar duplicados.
- Pode criar hidden inputs.
- Pode renderizar tabela/lista.
- Pode controlar botoes de editar, subir, descer e remover.
- Pode sincronizar o payload antes do submit.

Nao deve:

- criar wrappers visuais para alinhar campos;
- mover campos existentes para outro container;
- duplicar selects ja existentes no HTML;
- criar a segunda coluna por script quando ela pode nascer no template.

Na aba Configuracao dos campos, os campos Nome do campo e Cabecalho do campo devem existir diretamente em templates/new_user.html dentro do bloco data-process-fields-config-editor-block.

Motivo: tentativas de criar o campo Cabecalho do campo por JavaScript causaram duplicacao de campo, conflito entre grid externo e grid interno, campos empilhados, desaparecimento dos botoes Guardar/Cancelar e dificuldade de manutencao.

<!-- APPVERBO_STATIC_GRID_RULE_V1_END -->

<!-- APPVERBO_RULE_LAYOUT_ATIVOS_INATIVOS_V1_START -->
## Regra padrão: blocos separados para registos ativos/criados e inativos

Sempre que existir uma listagem administrativa com estado ativo/inativo, o layout padrão do AppVerboBraga deve manter os registos em blocos/cards separados:

1. O bloco principal deve listar apenas registos ativos/criados.
2. O bloco de inativos deve ser um card separado, abaixo do bloco principal.
3. Nunca colocar registos inativos dentro do mesmo card/tabela dos registos ativos/criados.
4. O estado deve usar badge visual:
   - Ativo: `entity-status entity-status-active`, com cor verde.
   - Inativo: `entity-status entity-status-inactive`, com cor vermelha.
5. O botão de eliminar deve aparecer apenas no bloco de inativos.
6. O backend também deve validar a regra de eliminação, impedindo eliminar registos ativos.
7. O rodapé das tabelas deve seguir o padrão visual da aba Entidade:
   - seletor de entradas por página com espaçamento da linha superior;
   - paginação alinhada à direita;
   - botões de paginação com layout arredondado e consistente.
8. Esta regra aplica-se, no mínimo, aos blocos de Utilizadores, Entidades e qualquer nova listagem com estados ativo/inativo.
9. Quando ajustar uma listagem existente, validar que:
   - o contexto/backend separa ativos e inativos;
   - o template possui sections/cards separados;
   - o CSS mantém o layout padrão;
   - não existe bloco legado misturando ativos e inativos.
<!-- APPVERBO_RULE_LAYOUT_ATIVOS_INATIVOS_V1_END -->

<!-- APPVERBO_RULE_USER_STATUS_REFACTOR_V1_START -->
## Regra padrão: reutilização de status e tabelas administrativas

Sempre que houver listagens administrativas com status de utilizador:

1. A normalização e tradução visual do status do utilizador devem ficar em `appverbo/services/user_status.py`.
2. Não duplicar lógica de status diretamente em `page.py`, handlers ou templates.
3. O banco deve guardar valores canónicos em inglês:
   - `active`
   - `inactive`
   - `pending`
   - `blocked`
4. O português deve ser apenas label visual:
   - `Ativo`
   - `Inativo`
   - `Pendente`
   - `Bloqueado`
5. Tabelas administrativas de utilizadores devem usar partial reutilizável em `templates/partials/admin_user_table_v1.html`.
6. CSS de rodapé, paginação e badges de status deve ficar em módulo reutilizável dentro de `static/css/modules`.
7. Não criar guard JavaScript para reexibir card oculto se a causa puder ser corrigida na lista principal de cards da aba.
8. Se uma nova listagem tiver ativos/inativos, usar cards separados e reutilizar a estrutura existente antes de criar novo HTML duplicado.
<!-- APPVERBO_RULE_USER_STATUS_REFACTOR_V1_END -->

<!-- APPVERBO_SAVE_CANCEL_BUTTON_RULE_V1_START -->
## Regra geral para botões Guardar e Cancelar

Sempre que existir um par de botões **Guardar** e **Cancelar** no projeto AppVerboBraga:

1. Os botões devem ficar sempre no lado esquerdo da tela ou do bloco/formulário.
2. Os dois botões devem ter a mesma largura, altura, padding e alinhamento vertical.
3. A ordem visual deve ser sempre: **Guardar** primeiro e **Cancelar** depois.
4. O texto do botão principal deve ser **Guardar**.
5. O texto do botão secundário deve ser **Cancelar**.
6. Não usar textos alternativos como "Gravar alterações", "Salvar", "Voltar" ou "Fechar" para esse par padrão, exceto quando existir regra funcional específica documentada.
7. Em formulários administrativos, rodapés de tabelas, subprocessos e telas dinâmicas, usar as classes globais existentes `action-btn` e `action-btn-cancel` sempre que possível.
8. Não posicionar Guardar/Cancelar no lado direito da tela, salvo exceção explícita aprovada.
<!-- APPVERBO_SAVE_CANCEL_BUTTON_RULE_V1_END -->

<!-- APPVERBO_GLOBAL_CANCEL_CONTROLLER_RULE_V1_START -->
## Regra global para o botão Cancelar

Todo botão **Cancelar** do AppVerboBraga deve usar obrigatoriamente o controller global `static/js/modules/appverbo_cancel_controller_v1.js`.

Regras:

1. É proibido criar `onclick` inline para **Cancelar**.
2. É proibido criar lógica de cancelamento específica por processo quando o controller global já resolver o caso.
3. Novos processos, cards, editores e formulários devem usar `data-appverbo-cancel="1"`.
4. Quando existir um alvo explícito, usar `data-appverbo-cancel-target` e, se necessário, `data-appverbo-cancel-return-target`.
5. Botões **Cancelar** criados dinamicamente por JavaScript também devem receber `data-appverbo-cancel="1"`.
6. Managers específicos não devem controlar o clique diretamente; quando precisarem limpar estado interno, devem reagir ao evento `appverbo:cancelled`.
7. O cancelamento deve fechar ou resetar apenas o contexto visual local.
8. É proibido usar `window.location.assign`, `window.location.href`, `window.location.replace`, `href` de ação, `onclick` inline ou `POST` para implementar **Cancelar**.
9. A regra aplica-se a processos atuais e futuros.
<!-- APPVERBO_GLOBAL_CANCEL_CONTROLLER_RULE_V1_END -->

<!-- APPVERBO_CREATE_ENTRY_BLOCK_RULE_V1_START -->
## Regra global para criação de entradas em abas/subprocessos

Sempre que uma aba, subprocesso ou lista administrativa tiver a opção de criar uma nova entrada relacionada ao processo atual:

1. Deve existir um bloco separado acima da tabela/lista principal.
2. Dentro desse bloco, o botão inicial deve ficar no lado esquerdo e seguir o padrão: **Criar + nome da aba/processo**.
   - Exemplos: **Criar entidade**, **Criar utilizador**, **Criar sessão**, **Criar menu**.
3. O botão de criação não deve ficar no lado direito do cabeçalho da tabela/lista.
4. Ao clicar em **Criar + nome**, o bloco deve expandir/apresentar os campos necessários para preencher a nova entrada.
5. Os botões **Guardar** e **Cancelar** devem ficar dentro desse mesmo bloco de criação.
6. Os botões **Guardar** e **Cancelar** devem ficar sempre alinhados à esquerda, com o mesmo tamanho e dimensão em todo o projeto.
7. A ordem visual deve ser sempre: **Guardar** primeiro e **Cancelar** depois.
8. A tabela/lista inferior deve permanecer separada, exibindo apenas os registos já criados e as ações de cada registo.
9. Quando a entrada for cancelada, limpar os campos do bloco e fechar/ocultar a área de preenchimento.
10. Quando a entrada for guardada, validar os campos obrigatórios antes de inserir/gravar.
<!-- APPVERBO_CREATE_ENTRY_BLOCK_RULE_V1_END -->

<!-- APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_RULE_V2_START -->
## Regra global para bloco separado de criação

Sempre que uma aba, subprocesso ou lista administrativa tiver ação para criar uma nova entrada do processo atual:

1. A opção **Criar + nome da aba/processo** deve ficar em um bloco/card separado acima da tabela/lista.
2. Esse bloco deve ficar visualmente separado da tabela/lista principal, com margem inferior e borda própria.
3. O botão **Criar + nome** deve ficar sempre à esquerda dentro desse bloco.
4. Ao clicar no botão **Criar + nome**, os campos de preenchimento devem aparecer dentro do mesmo bloco separado.
5. Os botões **Guardar** e **Cancelar** devem ficar dentro desse mesmo bloco separado, sempre à esquerda, com o mesmo tamanho e dimensão.
6. A tabela/lista inferior deve exibir somente os registos já criados e as ações da listagem.
7. Não colocar botão de criação no lado direito do cabeçalho da tabela/lista.
8. Não misturar o formulário de criação dentro da área visual da tabela/lista, exceto quando tecnicamente necessário, mantendo sempre separação visual clara.
<!-- APPVERBO_CREATE_ENTRY_SEPARATE_BLOCK_RULE_V2_END -->

<!-- APPVERBO_CREATE_ENTRY_SEPARATE_CARD_RULE_V3_START -->
## Regra global para card separado de criação

Sempre que uma aba/subprocesso tiver uma opção de criar nova entrada:

1. O botão **Criar + nome da aba/processo** deve ficar em um **card/bloco próprio**, separado visualmente do card da tabela/lista.
2. O card de criação deve ficar acima do card da tabela/lista, no mesmo padrão visual usado na aba **Entidade**.
3. O botão de criação deve ficar no lado esquerdo do card de criação.
4. Ao clicar no botão de criação, os campos devem abrir dentro desse mesmo card de criação.
5. Os botões **Guardar** e **Cancelar** do formulário de criação devem ficar dentro do card de criação, sempre à esquerda e com o mesmo tamanho.
6. A tabela/lista deve ficar em outro card separado, exibindo apenas os registos já criados e as ações da listagem.
7. Não colocar o bloco de criação dentro do mesmo card da lista quando o layout de referência separar criação e listagem.
<!-- APPVERBO_CREATE_ENTRY_SEPARATE_CARD_RULE_V3_END -->

<!-- APPVERBO_CREATE_CARD_STANDARD_RULE_V4_START -->
## Regra global para card/bloco de criação

Sempre que uma aba, subprocesso ou lista administrativa tiver a opção de criar uma nova entrada:

1. O botão **Criar + nome da aba/processo** deve ficar em um card/bloco separado acima da tabela/lista.
2. Esse card/bloco deve seguir o padrão visual da aba **Entidade**:
   - fundo cinza claro;
   - borda suave;
   - cantos arredondados;
   - altura mínima padronizada;
   - botão alinhado à esquerda e centralizado verticalmente.
3. O tamanho padrão do card/bloco de criação deve ser:
   - largura: 100% do container;
   - altura mínima: 64px;
   - padding horizontal e vertical: 16px;
   - margem inferior: 12px.
4. O botão **Criar + nome** deve ficar sempre à esquerda.
5. Ao clicar no botão, os campos de criação devem abrir dentro do mesmo card/bloco.
6. Os botões **Guardar** e **Cancelar** devem ficar dentro do mesmo card/bloco, sempre à esquerda e com o mesmo tamanho.
7. A tabela/lista inferior deve ficar em outro card separado, exibindo apenas os registos já criados.
8. Este padrão é global e deve ser reaproveitado em todas as abas que tenham ação de criação.
<!-- APPVERBO_CREATE_CARD_STANDARD_RULE_V4_END -->

<!-- APPVERBO_DYNAMIC_LIST_PROCESS_STANDARD_RULE_V1_START -->
## Regra global para processos dinâmicos listáveis

Sempre que for criado ou configurado um novo processo dinâmico/listável no AppVerboBraga:

1. O processo deve usar o layout standard de gestão/listagem, sem HTML específico duplicado por processo.
2. O layout standard deve conter:
   - card/bloco de ação com botão **Criar [singular]**;
   - card de **[plural] ativos**;
   - card de **[plural] inativos**;
   - pesquisa;
   - tabela com cabeçalho e colunas;
   - paginação;
   - seletor de entradas por página e contador/rodapé;
   - estado persistido no registo;
   - ações reutilizáveis de editar, ativar/inativar e, quando aplicável, eliminar.
3. A definição de que um processo é listável deve ficar numa configuração central reutilizável, por exemplo `process_layout: "list"`, ou equivalente já suportado pelo projeto.
4. Os labels singular/plural devem nascer da configuração central do processo, com fallback genérico apenas quando não existir label específico.
5. É proibido criar hacks visuais, `MutationObserver`, scripts externos ou branches soltas só para um processo quando o comportamento esperado for standard.
6. O backend e o frontend devem reutilizar a mesma definição central do processo listável.
<!-- APPVERBO_DYNAMIC_LIST_PROCESS_STANDARD_RULE_V1_END -->

<!-- APPVERBO_SUBPROCESS_DYNAMIC_FIELDS_RULE_V1_START -->
## Regra de campos em subprocessos admin (AdminSubprocessConfig)

Apenas os processos **Administrativo** e **Estruturas** (sessoes) podem ter campos hardcoded em `AdminSubprocessConfig.fields`.

Todos os outros subprocessos dinâmicos (ex: Objeto de autorização) **devem** ler os seus campos de conteúdo da configuração do processo:

1. Definir `uses_dynamic_fields=True` em `AdminSubprocessConfig`.
2. Definir `dynamic_fields_menu_key` com a chave do processo pai (ex: `"perfil_de_autorizacao"`).
3. Definir `dynamic_fields_section_header_key` com a chave do header configurado (ex: `"custom_objeto_de_autorizacao"`).
4. O resolver reutilizável é `resolve_subprocess_section_fields_v1` em `appverbo/services/process_tabs.py` — filtra `process_visible_field_rows` por `header_key` e retorna os campos configurados.
5. A função centralizadora de exceção é `is_system_hardcoded_process(menu_key)` em `appverbo/services/process_tabs.py` — retorna `True` apenas para `{"administrativo", "sessoes"}`.
6. Os campos técnicos (Sistema, Estado) ficam em `fields=` do config. Os campos de conteúdo vêm de `resolved_dynamic_fields` no estado.
7. O formulário Jinja2 renderiza `state.resolved_dynamic_fields` (com `name="process_field__<key>"`) antes dos campos técnicos de `state.config.fields`.
8. O save handler lê `process_field__*` do formulário e passa `dynamic_values` ao repositório.
9. O repositório armazena os campos dinâmicos nos seus próprios keys, mais o label canónico em `objeto_de_autorizacao`/`custom_objeto_label` para compatibilidade.
10. É proibido adicionar campos de conteúdo hardcoded num subprocesso dinâmico — os campos devem vir sempre de `Configuração dos campos`.
<!-- APPVERBO_SUBPROCESS_DYNAMIC_FIELDS_RULE_V1_END -->

<!-- APPVERBO_SESSOES_DB_FIELDS_CREATE_RULE_V4_START -->
## Regra para campos de criação baseados na edição/BD

Sempre que existir um botão **Criar + nome da aba/processo**:

1. Os botões **Guardar** e **Cancelar** devem existir apenas dentro do bloco/card de criação.
2. Não deve existir outro par **Guardar/Cancelar** no rodapé da tabela/lista para a mesma ação de criação.
3. Ao clicar em **Criar + nome**, devem aparecer todos os campos necessários que existem na edição ou na configuração persistida no BD.
4. Para sessões do sidebar, o formulário de criação deve permitir preencher:
   - Nome da sessão;
   - Chave da sessão;
   - Visibilidade/Sistema.
5. Campos derivados podem ser gravados como hidden, mas os campos editáveis principais devem estar visíveis no bloco de criação.
6. A tabela/lista inferior deve ficar apenas com a listagem e ações por linha.
<!-- APPVERBO_SESSOES_DB_FIELDS_CREATE_RULE_V4_END -->

<!-- APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_START -->
## Regra para criação de sessões do sidebar

Na aba **Sessões**, ao clicar em **Criar sessão**, os campos visíveis disponíveis para preenchimento devem ser exatamente:

1. **Nome da sessão**;
2. **Sistema**;
3. **Estado**.

A chave técnica da sessão deve continuar a existir para gravação no BD, mas deve ser gerada automaticamente a partir do Nome da sessão e não deve aparecer como campo visível no bloco de criação.

O campo **Sistema** deve gravar a visibilidade/sistema da sessão.

O campo **Estado** deve gravar se a sessão está ativa ou inativa.

Os botões **Guardar** e **Cancelar** devem existir apenas no bloco de criação, nunca no rodapé da listagem.
<!-- APPVERBO_SESSOES_CREATE_FIELDS_NOME_SISTEMA_ESTADO_V5_END -->

<!-- APPVERBO_SESSOES_REIDRATAR_BD_V6_START -->
## Regra para reidratação das Sessões pelo BD

Na aba **Sessões**, a lista inferior deve sempre ser reidratada a partir do BD/configuração persistida.

1. O bloco **Criar sessão** é apenas o formulário de criação.
2. A listagem **Sessões do sidebar** deve mostrar todas as sessões existentes no BD.
3. Se o JavaScript principal falhar ou montar a tela sem linhas, deve existir recuperação consultando o endpoint de dados das sessões.
4. Os campos visíveis de criação devem permanecer:
   - Nome da sessão;
   - Sistema;
   - Estado.
5. A chave técnica continua oculta e gerada automaticamente.
6. Os botões Guardar/Cancelar devem ficar apenas no bloco de criação.
7. A hierarquia da tabela deve ser gravada conforme a ordem das linhas renderizadas.
<!-- APPVERBO_SESSOES_REIDRATAR_BD_V6_END -->

<!-- APPVERBO_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_START -->
## Regra para evitar espaço vazio no bloco/card de criação

Quando o botão **Criar + nome** abre o formulário dentro do bloco/card de criação:

1. O espaço reservado ao botão oculto não deve continuar ocupando altura.
2. Os campos do formulário devem começar no topo útil do bloco/card.
3. Não deve existir faixa vazia acima dos campos.
4. Não deve existir borda/linha horizontal separando uma toolbar vazia dos campos.
5. Quando o formulário estiver fechado, o botão **Criar + nome** deve continuar alinhado à esquerda e centralizado verticalmente.
6. Quando o formulário estiver aberto, apenas os campos e os botões **Guardar** e **Cancelar** devem ocupar o bloco/card.
<!-- APPVERBO_CREATE_CARD_NO_EMPTY_TOP_SPACE_V7_END -->

<!-- APPVERBO_SESSOES_EDIT_INLINE_V8_START -->
## Regra para edição de Sessões

Na aba **Sessões**, o botão de editar da coluna **Ações** deve abrir edição diretamente na linha, sem usar `alert`.

Campos editáveis da linha:

1. **Nome da sessão**;
2. **Sistema**;
3. **Estado**.

A chave técnica da sessão deve continuar oculta e preservada, para não quebrar vínculos existentes dos menus/processos.

Durante a edição da linha:

1. Substituir os ícones de ação por **Guardar** e **Cancelar**.
2. **Guardar** atualiza os campos ocultos, grava a ordem atual e submete o formulário.
3. **Cancelar** restaura os valores anteriores sem gravar.
4. Não mostrar mensagens temporárias do tipo "edição será ajustada no próximo passo".
<!-- APPVERBO_SESSOES_EDIT_INLINE_V8_END -->

<!-- APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START -->
## Regra para Estado das Sessões e blocos Ativo/Inativo

Na aba **Sessões**:

1. O campo **Estado** deve ser assumido corretamente ao criar ou editar uma sessão.
2. Quando o estado for **Ativo**, a sessão deve aparecer no bloco principal da lista.
3. Quando o estado for diferente de **Ativo**, a sessão deve aparecer em um bloco separado abaixo, chamado **Sessões inativas**.
4. A alteração do estado deve persistir no BD através do campo `section_status`.
5. A alteração de estado durante a edição deve mover automaticamente a linha para o bloco correto.
6. O botão de edição não deve usar `alert`; deve editar Nome da sessão, Sistema e Estado diretamente na linha.
7. A chave técnica da sessão deve continuar oculta e preservada.
<!-- APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END -->

<!-- APPVERBO_SESSOES_SCOPE_GUARD_V11_START -->
## Regra de escopo para subprocessos dinâmicos

Scripts de um subprocesso/aba não podem criar, mover ou exibir blocos fora da própria aba ativa.

Para a aba **Sessões**:

1. O bloco **Criar sessão** só pode aparecer quando a aba **Sessões** estiver ativa.
2. O card **Sessões inativas** só pode aparecer quando a aba **Sessões** estiver ativa.
3. Se a aba ativa for **Entidade**, **Utilizador**, **Menu** ou qualquer outra, o JavaScript de Sessões deve remover qualquer bloco órfão de Sessões.
4. A validação de escopo deve verificar aba ativa, visibilidade do card e contexto da URL/hash.
5. Nenhum bloco de Sessões pode aparecer no fim da aba Entidade ou fora do card correto do subprocesso.
<!-- APPVERBO_SESSOES_SCOPE_GUARD_V11_END -->

<!-- APPVERBO_SESSOES_SCOPE_CORRETO_V12_START -->
## Regra correta de escopo da aba Sessões

O botão **Criar sessão** pertence ao subprocesso/aba **Sessões** e deve aparecer sempre dentro dessa aba.

Regras:

1. Quando a aba ativa for **Sessões**, o card **Criar sessão** deve estar visível acima da lista de sessões.
2. Quando a aba ativa não for **Sessões**, qualquer card órfão de Sessões deve ser removido.
3. O card **Criar sessão** não pode aparecer no final da aba **Entidade** ou fora do subprocesso **Sessões**.
4. O card **Sessões inativas** também pertence somente ao subprocesso **Sessões**.
5. A validação deve considerar o botão/tab ativo pelo texto **Sessões**, classes de estado ativo e visibilidade real do card de sessões.
6. Não usar apenas URL/hash como critério, porque a URL pode manter hash de outro card mesmo com a aba Sessões ativa.
<!-- APPVERBO_SESSOES_SCOPE_CORRETO_V12_END -->

<!-- APPVERBO_SESSOES_RELOAD_ON_RETURN_V13_START -->
## Regra para retorno à aba Sessões

Na área administrativa, ao navegar entre as abas do subprocesso e voltar para **Sessões**:

1. O card **Criar sessão** deve reaparecer automaticamente dentro da aba **Sessões**.
2. O card **Sessões inativas** deve reaparecer automaticamente dentro da aba **Sessões**.
3. A lista de sessões deve ser reidratada novamente a partir do BD/configuração.
4. Blocos de Sessões continuam proibidos fora da aba **Sessões**.
5. Ao sair para **Entidade**, **Utilizador** ou **Menu**, qualquer bloco órfão de Sessões deve ser removido.
6. Ao retornar para **Sessões**, a montagem da aba deve ser executada novamente mesmo sem reload da página.
<!-- APPVERBO_SESSOES_RELOAD_ON_RETURN_V13_END -->

<!-- APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START -->
## Regra de recriação do card Criar sessão

Na aba **Sessões**, o card **Criar sessão** deve ser resiliente à navegação entre abas.

1. Ao entrar inicialmente em **Sessões**, o card **Criar sessão** deve aparecer acima da listagem.
2. Ao sair de **Sessões**, o card pode ser removido para não aparecer em outras abas.
3. Ao retornar para **Sessões**, o card **Criar sessão** deve ser recriado automaticamente.
4. Nenhum guard antigo pode remover o card **Criar sessão** quando a aba **Sessões** estiver ativa.
5. A detecção de aba ativa deve usar o botão/tab ativo pelo texto **Sessões** e a visibilidade real do card de sessões.
6. A URL/hash não deve ser usada como único critério, pois pode continuar apontando para outro card.
7. O card deve continuar permitindo criar com os campos: Nome da sessão, Sistema e Estado.
<!-- APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END -->

<!-- APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START -->
## Regra visual para Sessões inativas

Na aba **Sessões**, a área **Sessões inativas** deve ficar sempre em card/bloco próprio, separado abaixo do card **Sessões do sidebar**.

Regras:

1. **Sessões do sidebar** deve conter somente a listagem das sessões ativas.
2. **Sessões inativas** deve ficar em outro card abaixo, com borda, fundo e espaçamento iguais ao padrão de **Entidades inativas**.
3. Quando não houver sessões inativas, o card deve permanecer visível com a mensagem **Sem sessões inativas.**
4. O bloco de inativas não pode ficar dentro do mesmo card visual das sessões ativas.
5. Ao retornar para a aba **Sessões**, a separação em cards deve ser reaplicada automaticamente.
<!-- APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END -->

<!-- APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START -->
## Regra do subprocesso Sessões igual ao fluxo da Entidade

Na aba **Sessões**, a ação **Editar** deve seguir o mesmo padrão funcional da aba **Entidade**.

Regras:

1. O botão **Editar** da linha não deve editar inline.
2. Ao clicar em **Editar**, deve navegar/recarregar para a aba **Sessões** com o parâmetro técnico da sessão em edição.
3. Após o reload, o bloco superior da aba deve abrir em modo **Editar sessão**, com os campos preenchidos.
4. Os campos editáveis são:
   - **Nome da sessão**;
   - **Sistema**;
   - **Estado**.
5. O botão **Guardar** deve submeter um formulário dedicado para backend, semelhante ao fluxo de atualização da Entidade.
6. O botão **Cancelar** deve sair do modo edição e retornar para a lista da aba **Sessões**.
7. O botão **Criar sessão** continua pertencendo ao bloco superior da aba **Sessões**.
8. O bloco **Sessões inativas** deve permanecer separado abaixo, como card próprio.
9. A chave técnica da sessão deve ser preservada na edição.
<!-- APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END -->

<!-- APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START -->
## Regra para editar Sessões sem saltar para Menu

Na aba **Sessões**, a ação **Editar** deve permanecer sempre no subprocesso **Sessões**.

Regras:

1. O clique em **Editar** deve usar a URL atual como base.
2. Deve adicionar apenas o parâmetro técnico `sidebar_section_edit_key`.
3. Não deve adicionar `settings_edit_key`, `settings_action` ou `settings_tab`, porque esses parâmetros pertencem ao fluxo de Menu e podem abrir o subprocesso errado.
4. O botão **Cancelar** deve remover apenas `sidebar_section_edit_key` e retornar para a própria aba Sessões.
5. Após **Guardar**, o backend deve redirecionar para a URL de retorno enviada pelo formulário, preservando a aba Sessões.
6. A edição deve abrir o bloco superior como **Editar sessão**, com Nome da sessão, Sistema e Estado preenchidos.
<!-- APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END -->

<!-- APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START -->
## Regra definitiva do subprocesso Sessões no padrão Entidade

O subprocesso **Sessões** deve seguir o mesmo padrão funcional do subprocesso **Entidade**.

Regras:

1. O botão **Editar** da linha não deve editar inline.
2. Ao clicar em **Editar**, a página deve navegar/recarregar para a mesma aba **Sessões** com o parâmetro `sidebar_section_edit_key`.
3. Depois do reload, o bloco superior deve abrir em modo **Editar sessão**, com os campos preenchidos.
4. Os campos editáveis são:
   - **Nome da sessão**;
   - **Sistema**;
   - **Estado**.
5. O botão **Guardar** deve enviar um formulário dedicado para o backend.
6. O botão **Cancelar** deve remover o modo edição e voltar para a lista da aba **Sessões**.
7. O botão **Criar sessão** permanece no mesmo bloco superior, quando não houver sessão em edição.
8. O endpoint dedicado deve gravar somente a sessão criada/editada, preservando as demais sessões existentes.
9. Não usar `settings_edit_key`, `settings_action` ou `settings_tab` para editar Sessões, pois esses parâmetros pertencem ao fluxo do subprocesso Menu.
10. A listagem de ativos e o card de **Sessões inativas** continuam separados.
<!-- APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END -->

<!-- APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START -->
## Regra para persistência do Estado em Sessões

Na aba **Sessões**, quando o campo **Estado** for alterado em modo criação ou edição:

1. O valor selecionado deve ser enviado explicitamente ao backend.
2. O backend deve gravar `status`, `is_active` e `status_label` na configuração da sessão.
3. Ao gravar **Inativo**, a sessão deve voltar como **Inativo** após o reload.
4. Ao gravar **Ativo**, a sessão deve voltar como **Ativo** após o reload.
5. O endpoint dedicado de Sessões deve ser único para `/settings/menu/sidebar-section-save`.
6. A gravação não pode cair no fluxo antigo em lote nem no fluxo do subprocesso Menu.
7. A sessão editada deve preservar a chave técnica original.
<!-- APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END -->

<!-- APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START -->
## Regra para renderização das Sessões inativas a partir do BD

Na aba **Sessões**:

1. O card **Sessões inativas** deve ser montado a partir dos dados reais retornados por `/settings/menu/sidebar-sections-data`.
2. Toda sessão com `status` diferente de **ativo** deve aparecer no card **Sessões inativas**.
3. Toda sessão com `is_active` igual a `false` deve aparecer no card **Sessões inativas**.
4. Após alterar uma sessão de **Ativo** para **Inativo** e gravar, ela deve aparecer no card inferior após o reload.
5. O card deve permanecer visível mesmo quando não houver inativas, mostrando **Sem sessões inativas.**
6. O botão **Editar** dentro do card de inativas deve continuar usando o fluxo padrão Entidade da aba Sessões.
7. O card **Sessões inativas** não pode aparecer fora da aba **Sessões**.
<!-- APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END -->

<!-- APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START -->
## Regra para não contaminar Sessões com contexto da Entidade

Na aba **Sessões**:

1. A URL não pode manter `dynamic_process_section=field:entidade`.
2. Ao editar, guardar, cancelar ou retornar para **Sessões**, remover sempre:
   - `dynamic_process_section`;
   - `settings_edit_key`;
   - `settings_action`;
   - `settings_tab`;
   - `sidebar_section_return_url`;
   - `appverbo_after_save`.
3. O backend de `/settings/menu/sidebar-section-save` também não pode preservar `dynamic_process_section` no redirect.
4. O card **Sessões inativas** deve ser renderizado pelo BD sempre que `admin_tab=sessoes` ou `sidebar_sections_tab=sessoes`.
5. Uma sessão com `status=inativo` ou `is_active=false` deve aparecer no card **Sessões inativas**.
<!-- APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END -->

<!-- APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START -->
## Regra definitiva para Sessões no padrão Entidade

A aba **Sessões** deve tratar itens **Ativos** e **Inativos** no mesmo padrão do subprocesso **Entidade**.

Regras:

1. A separação entre ativos e inativos deve acontecer no backend/contexto da página.
2. A página deve receber:
   - `active_sidebar_sections`;
   - `inactive_sidebar_sections`;
   - `sidebar_section_edit_key`;
   - `sidebar_section_edit_data`.
3. O `admin_tab=sessoes` deve ser aceito no page handler, sem cair para `entidade`.
4. Quando `admin_tab=sessoes`, o target inicial deve ser `#admin-sidebar-sections-card`.
5. Quando `admin_tab=sessoes`, limpar qualquer `dynamic_process_section`, especialmente `field:entidade`.
6. A sessão com `status=inativo` ou `is_active=false` deve aparecer em **Sessões inativas**.
7. A sessão inativa não pode aparecer na lista principal **Sessões do sidebar**.
8. O card **Sessões inativas** deve existir mesmo vazio, mostrando **Sem sessões inativas.**
9. A ação **Editar** deve permanecer no fluxo dedicado de Sessões, com `sidebar_section_edit_key`, sem usar parâmetros do subprocesso Menu.
10. O backend de gravação não deve preservar `dynamic_process_section`, `settings_edit_key`, `settings_action` ou `settings_tab`.
<!-- APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END -->

<!-- APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START -->
## Regra definitiva para Sessões sem piscar

A aba **Sessões** deve ter apenas um controlador visual ativo.

Regras:

1. Não usar `MutationObserver` para renderizar continuamente os cards de Sessões.
2. Não reescrever `innerHTML` repetidamente se os dados não mudaram.
3. Não forçar a URL para `admin_tab=sessoes` quando o utilizador clicar noutro subprocesso.
4. O renderizador de Sessões só pode atuar quando a aba **Sessões** estiver realmente ativa.
5. O split ativo/inativo deve vir do backend, igual ao padrão da Entidade.
6. O card **Sessões do sidebar** deve renderizar apenas sessões ativas.
7. O card **Sessões inativas** deve renderizar apenas sessões inativas.
8. O card **Sessões inativas** deve permanecer visível mesmo vazio.
9. Os blocos antigos V15, V18, V20, V21 e V22 não podem continuar a observar/mexer no DOM.
10. A ação **Editar** deve usar `sidebar_section_edit_key`, sem `dynamic_process_section`.
<!-- APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END -->

<!-- APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START -->
## Regra para ações visíveis nas Sessões inativas

Na aba **Sessões**:

1. O bloco **Sessões inativas** deve mostrar ações visíveis.
2. Cada linha inativa deve apresentar, no mínimo:
   - ação **Visualizar**;
   - ação **Editar**.
3. Os botões não podem aparecer vazios.
4. As ações de inativas devem usar o mesmo padrão visual das ações de ativas.
5. O botão **Editar** de uma sessão inativa deve continuar usando `sidebar_section_edit_key`.
6. Não usar `dynamic_process_section` nas ações da aba Sessões.
<!-- APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END -->

<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START -->
## Regra definitiva: Sessões igual ao subprocesso Entidade

A aba **Sessões** deve seguir o mesmo procedimento do subprocesso **Entidade**.

Fluxo obrigatório:

1. A ação **Editar** navega para `/users/new` com:
   - `menu=administrativo`;
   - `admin_tab=sessoes`;
   - `sidebar_sections_tab=sessoes`;
   - `sidebar_section_edit_key=<key>`.
2. O `page_handler.py` carrega `sidebar_section_edit_data` no backend.
3. O template `new_user.html` renderiza o formulário de edição diretamente no HTML, como acontece com `entity_edit_data`.
4. O formulário envia para `/settings/menu/sidebar-section-save`.
5. O backend grava no BD/JSON `sidebar_menu_settings.menu_config.sidebar_sections`.
6. Depois do commit, redireciona para a aba **Sessões**.
7. O backend separa e entrega:
   - `active_sidebar_sections`;
   - `inactive_sidebar_sections`.
8. O template renderiza diretamente:
   - card de criar/editar sessão;
   - card **Sessões do sidebar**;
   - card **Sessões inativas**.
9. JavaScript não pode reconstruir listas nem formulários de Sessões.
10. JavaScript só pode atuar em comportamento auxiliar, como visualizar detalhes ou controlar visibilidade da aba.
<!-- APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END -->

<!-- APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START -->
## Correção do split backend das Sessões

Na aba **Sessões**, as listas devem ser separadas no backend antes do template.

Regras:

1. Recalcular sempre `active_sidebar_sections` e `inactive_sidebar_sections` a partir da configuração normalizada.
2. Uma sessão deve ser considerada inativa quando:
   - `is_active` for `false`; ou
   - `status` for `inativo`.
3. Uma sessão deve ser considerada ativa quando:
   - `is_active` for `true`; ou
   - `status` for `ativo`; ou
   - não existir estado explícito de inativo.
4. O template não deve depender de JavaScript para reconstruir as linhas.
5. O card **Sessões do sidebar** deve mostrar todas as sessões ativas.
6. O card **Sessões inativas** deve mostrar apenas as sessões inativas.
<!-- APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END -->

<!-- APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START -->
## Regra de persistência visual do card Criar sessão

Na aba **Sessões**:

1. O card de criação/edição `admin-sidebar-sections-form-card` deve permanecer visível sempre que a aba **Sessões** estiver ativa.
2. Ao alternar para Entidade, Utilizador ou Menu, os cards de Sessões podem ser ocultados.
3. Ao retornar para Sessões, devem reaparecer juntos:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`.
4. O card de criação não deve depender de reconstrução por JavaScript.
5. O JavaScript só pode controlar visibilidade, sem recriar listas, formulários ou linhas.
6. Não usar `MutationObserver` para este comportamento.
<!-- APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END -->

<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START -->
## Regra definitiva: Sessões no fluxo nativo igual ao subprocesso Entidade

A aba **Sessões** deve seguir o mesmo padrão de renderização da aba **Entidade**.

Regras obrigatórias:

1. O template só deve renderizar os cards de Sessões quando `admin_tab == "sessoes"`.
2. Não usar `data-admin-tab-pane="sessoes"` como mecanismo paralelo de visibilidade.
3. Não usar JavaScript para forçar aparecer/desaparecer o card **Criar sessão**.
4. O card **Criar sessão** deve existir no HTML apenas quando a aba Sessões for carregada pelo backend.
5. Ao navegar para Entidade/Menu/Utilizador, os cards de Sessões não devem existir no HTML da resposta.
6. Ao voltar para Sessões, o backend deve renderizar novamente:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`.
7. O JavaScript de Sessões só pode tratar ação auxiliar de visualizar detalhes.
8. As listas de sessões ativas e inativas devem ser renderizadas pelo template com dados do backend.
9. A ação **Editar** deve navegar com `sidebar_section_edit_key`, igual ao fluxo da Entidade com `entity_edit_id`.
10. Não usar `MutationObserver` no subprocesso Sessões.
<!-- APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END -->

<!-- APPVERBO_ADMIN_SUBPROCESS_CONFIG_BASE_V1_START -->
## Motor reutilizável de subprocessos administrativos

A partir desta configuração, todo subprocesso administrativo deve seguir o contrato comum `AdminSubprocess`.

Arquivos principais:

- `appverbo/admin_subprocesses/models.py`
- `appverbo/admin_subprocesses/registry.py`
- `appverbo/admin_subprocesses/service.py`
- `appverbo/admin_subprocesses/repositories/base.py`
- `templates/macros/admin_subprocess.html`
- `static/css/modules/admin_subprocesses_v1.css`
- `static/js/modules/admin_subprocesses_v1.js`

Configurações atribuídas inicialmente:

- `entidade`: subprocesso de referência, mantendo o padrão atual server-render.
- `sessoes`: próximo subprocesso a migrar para o padrão nativo reutilizável.
- `utilizador`, `menu` e `contas`: registados como `legacy_pending` para migração posterior.

Regras obrigatórias:

1. URL define `admin_tab` e o parâmetro de edição.
2. Registry identifica a configuração do subprocesso.
3. Repository carrega dados da origem correta.
4. Service monta `AdminSubprocessState`.
5. Template/macro renderiza criar, editar, ativos e inativos.
6. Endpoint grava e redireciona para o `admin_tab` correto.
7. JavaScript não renderiza listas, formulários ou cards.
8. JavaScript só pode executar ações auxiliares.
9. Novos subprocessos devem ser criados adicionando uma configuração no registry e, quando necessário, um repository.
<!-- APPVERBO_ADMIN_SUBPROCESS_CONFIG_BASE_V1_END -->

<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_START -->
## Ordem definitiva da aba Sessões

Na aba **Sessões**, a ordem visual correta é:

1. Primeiro o card central de ABAS (`menu-tabs-card`);
2. Depois o bloco do subprocesso renderizado por `render_admin_subprocess_state(admin_subprocess_state)`;
3. Nenhum bloco de Sessões pode ficar antes do card de ABAS;
4. Não devem existir sections manuais antigas com:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`;
   - classes `appverbo-sessoes-*`;
5. A renderização de Sessões deve depender de `admin_tab == "sessoes"` e `admin_subprocess_state`.
<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V4_END -->

<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_START -->
## Ordem definitiva da aba Sessões

Na aba **Sessões**, a ordem visual correta é:

1. Primeiro o card central de ABAS (`menu-tabs-card`);
2. Depois o bloco do subprocesso renderizado por `render_admin_subprocess_state(admin_subprocess_state)`;
3. Nenhum bloco manual antigo de Sessões pode ficar antes do card de ABAS;
4. Não devem existir sections manuais antigas com:
   - `admin-sidebar-sections-form-card`;
   - `admin-sidebar-sections-card`;
   - `admin-sidebar-sections-inactive-card`;
   - classes `appverbo-sessoes-*`;
5. A renderização de Sessões deve depender de `admin_tab == "sessoes"` e `admin_subprocess_state`.
<!-- APPVERBO_CORRIGIR_ORDEM_ABAS_SESSOES_ADMIN_SUBPROCESS_V5_END -->

<!-- APPVERBO_UNIFIED_SUBMENU_TABS_V1_START -->
## Regra definitiva: Abas e Cards Orientados pelo Backend

Todo processo ou menu que possui abas superiores deve seguir obrigatoriamente a arquitetura unificada orientada pelo backend:

1. As abas do menu ativo devem ser resolvidas pelo backend (usando `resolve_process_tabs_v1`) e renderizadas diretamente no Jinja2 template dentro do elemento `#submenu-items`.
2. O JavaScript não deve destruir ou recriar os elementos do menu sob `#submenu-items` se eles já vierem renderizados do backend e corresponderem às abas configuradas.
3. A visibilidade inicial dos cards e tabelas na primeira pintura (first paint) deve ser definida pelo backend usando o atributo `style="display: none;"` baseado no parâmetro `initial_menu_target`.
4. Os cards dinâmicos do processo (`#dynamic-process-card`, `#dynamic-process-active-card`, `#dynamic-process-inactive-card`) e os cards nativos do subprocesso só devem ser exibidos se fizerem parte da aba atualmente ativa.
5. Após ações de guardar ou eliminar dados de processos dinâmicos ou nativos, o redirecionamento pós-save deve conter os parâmetros corretos (`menu`, `target`, `dynamic_process_section`) para retornar o utilizador à aba exata em que se encontrava, preservando a coerência visual e evitando dupla navegação.
<!-- APPVERBO_UNIFIED_SUBMENU_TABS_V1_END -->

<!-- APPVERBO_SUBPROCESS_GROUP_VISIBILITY_V1_START -->
## Regra definitiva: Agrupamento de Cards de Subprocesso Nativo

Todo subprocesso nativo que usa o macro `render_admin_subprocess_state` deve ter os seus cards (formulário, tabela ativa, tabela inativa) tratados como **grupo** pelo JavaScript:

1. **`process_tabs.py`**: A aba principal do subprocesso deve apontar para o `default_target` do `AdminSubprocessConfig` (ex: `#auth-profile-card`), não para o card da tabela ativa (ex: `#auth-profile-active-card`). O `default_target` é o card que contém o accordion de criação.

2. **`getAdminSubprocessKeyByTargetV1`** em `new_user.js`: Todos os targets nativos do subprocesso (card principal, form-card, active-card, inactive-card) devem estar no `targetMap`, retornando a `key` do `AdminSubprocessConfig` (ex: `"objeto_de_autorizacao"`). Para subprocessos dentro do mesmo menu (como `perfil_de_autorizacao` e `objeto_de_autorizacao`), cada um tem a sua própria chave para que o JS possa distingui-los.

3. **`supportsStructuredAdminGroups`** em `applyContentForMenuTarget`: O `menuKey` do subprocesso (o menu pai, ex: `"perfil_de_autorizacao"`) deve estar incluído nesta condição. Subprocessos filhos no mesmo menu partilham o mesmo `menuKey` mas têm `data-admin-subprocess` distintos.

4. **`normalizeSubmenuTargetAlias`** em `new_user.js`: Os targets de tabela (active-card, inactive-card) e de edição (form-card) devem ser alias do `default_target` para que a aba correta fique ativa no submenu quando qualquer um desses cards é visível.

5. **`menuConfig`**: Se o subprocesso é nativo (não está em `sidebarMenuSettings`), o `menuConfig` deve ser inicializado explicitamente após `mergeDynamicProcessMenus()` verificando `visibleSidebarMenuKeys` ou a presença dos cards no DOM.

6. **`_build_*_return_url`** no backend: A URL de retorno pós-save deve apontar para o `default_target` do subprocesso, não para o card da tabela ativa. Isso garante que a aba principal é seleccionada após guardar.

### Subprocessos nativos actuais e os seus targets:

| Subprocesso (config key) | `default_target` | `menu_scope` | `menuConfig` key |
|---|---|---|---|
| `sessoes` | `admin-sidebar-sections-card` | `administrativo,sessoes` | `sessoes` (via sidebarMenuSettings) |
| `perfil_de_autorizacao` | `auth-profile-card` | `perfil_de_autorizacao` | inicializado por APPVERBO_AUTH_PROFILE_MENUCONFIG_INIT_V1 |
| `objeto_de_autorizacao` | `auth-objeto-card` | `perfil_de_autorizacao` | partilhado com `perfil_de_autorizacao` (mesma entrada no menuConfig, aba diferente) |
| `menu` | `menu-subprocess-card` | `administrativo,sessoes` | `sessoes` (via sidebarMenuSettings) |
| `entidade` | `create-entity-card` | `administrativo` | `administrativo` (via sidebarMenuSettings) |

**Nota:** Quando dois subprocessos partilham o mesmo `menu_scope` (ex: `perfil_de_autorizacao` e `objeto_de_autorizacao`), o macro `admin_subprocess.html` usa a lista de targets do config (`default_target`, `edit_target`, `active_card_id`, `inactive_card_id`) para determinar se o subprocesso está activo. Apenas os cards do subprocesso cujos targets correspondem ao `initial_menu_target` ficam visíveis no servidor. O JavaScript usa o `data-admin-subprocess` (= `config.key`) para o agrupamento correcto.

### Proibido:
- Apontar a aba principal para `*-active-card` ou `*-inactive-card` (reservados para as tabelas).
- Usar `_build_*_return_url` para forçar o redirect para `*-active-card` quando o `default_target` é suficiente.
- Criar patches visuais específicos por processo quando a regra de agrupamento padrão resolve.
<!-- APPVERBO_SUBPROCESS_GROUP_VISIBILITY_V1_END -->

<!-- APPVERBO_UI_DIALOG_AND_FIELD_SOURCE_RULE_V1_START -->
## Regra global: validações UI e fonte única de campos configuráveis

Sempre que uma validação ou mensagem de erro precisar ser mostrada na UI do AppVerboBraga:

1. Não usar `alert()` nem `window.alert()` no fluxo final entregue ao utilizador.
2. Usar um dialog/modal reutilizável do sistema, preferencialmente via módulo partilhado.
3. O dialog deve abrir centrado, bloquear a interação de fundo e ter pelo menos título, mensagem e botão de confirmação.
4. A regra vale para managers de listas configuráveis, abas configuráveis do processo e subprocessos administrativos.

Sempre que uma área depender de “campos disponíveis” derivados de “Campos adicionais”:

1. A fonte de verdade deve ser única e partir da configuração persistida do próprio processo.
2. É proibido manter listas paralelas desalinhadas entre:
   - `Campos criados`;
   - selects de `campos disponíveis`;
   - `process_visible_fields`;
   - `process_visible_field_rows`;
   - renderização final do processo.
3. Depois de criar, editar, remover ou reordenar um campo adicional, os consumidores dependentes devem reconstruir as opções a partir do resolver partilhado.
4. A correção deve ser reutilizável para processos atuais e futuros, sem branch específica por menu.
<!-- APPVERBO_UI_DIALOG_AND_FIELD_SOURCE_RULE_V1_END -->
