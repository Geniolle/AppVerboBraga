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
