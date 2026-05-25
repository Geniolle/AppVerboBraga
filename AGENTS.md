# AGENTS.md - Instruções do Projeto AppVerboBraga

Este ficheiro contém as regras locais obrigatórias para qualquer trabalho realizado no repositório AppVerboBraga.

O objetivo deste ficheiro é orientar o Codex e outros agentes de desenvolvimento com instruções claras, curtas e prioritárias. Manter este documento objetivo para evitar truncamento pelo limite padrão de leitura de instruções do Codex.

Este ficheiro representa a versão consolidada das regras do projeto. Regras antigas que tenham sido substituídas não devem coexistir com regras novas concorrentes.

## 1) Identidade do projeto

O AppVerboBraga é uma aplicação SaaS modular para igrejas.

A aplicação deve crescer por módulos ativáveis por entidade, por exemplo:

- Núcleo/Base;
- Tesouraria;
- Eventos;
- Escalas;
- Cursos;
- Relatórios avançados.

Novas funcionalidades comerciais devem ser criadas como módulos, não como páginas soltas.

## 2) Ordem de prioridade das instruções

Ao executar tarefas neste repositório, seguir esta ordem:

1. Instruções explícitas do utilizador na conversa atual.
2. Este ficheiro `AGENTS.md`.
3. Convenções já existentes no código.
4. Boas práticas gerais de desenvolvimento.

Se houver conflito entre regras, aplicar a instrução mais específica e mais recente dentro desta ordem.

Não criar `AGENTS.override.md` sem pedido explícito do utilizador. Usar `AGENTS.override.md` apenas para overrides temporários, documentados e claramente justificados.

## 3) Regras operacionais obrigatórias

Antes de alterar ficheiros:

- entender a funcionalidade existente;
- evitar alterações fora do escopo pedido;
- criar backup dos ficheiros alterados quando a alteração for feita por script;
- preservar nomes, rotas e contratos existentes sempre que possível;
- não remover compatibilidade temporária sem validação;
- não mascarar divergências entre código, models, migrations e comportamento real.

Depois de alterar ficheiros:

- validar sintaxe;
- validar ausência de mojibake;
- mostrar `git diff`;
- executar `git diff --check`;
- mostrar `git status`;
- reiniciar Docker quando aplicável;
- verificar logs recentes quando a aplicação for afetada.

Backups criados por script devem ficar em pasta própria com timestamp, preservando o caminho relativo original dos ficheiros alterados.

Exemplo de pasta:

```text
backups/<nome_da_tarefa>_<YYYYMMDD_HHMMSS>/
```

## 4) Docker-first

Este projeto usa Docker.

Sempre que a tarefa envolver banco de dados, Alembic, migrations, models, validação da aplicação ou execução do backend, usar o container `web`.

Comandos corretos:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head
```

Evitar executar Alembic no ambiente local `.venv` quando o banco real usado pela aplicação estiver no Docker.

Reiniciar Docker é obrigatório quando forem alterados:

- backend Python;
- models;
- migrations;
- dependências;
- variáveis de ambiente;
- configuração da aplicação;
- templates ou código carregado no arranque da aplicação.

Para alterações apenas em JS/CSS estático, reiniciar Docker só é obrigatório se a aplicação não refletir a alteração, se houver cache/build envolvido ou se o comportamento depender do backend.

Para logs recentes, usar preferencialmente:

```bash
docker compose logs --tail=100 web
```

Se outros serviços forem afetados, incluir também esses serviços.

## 5) Codificação de texto

Todos os ficheiros de código, templates, assets e documentação devem ficar em UTF-8.

Extensões principais:

- `.py`;
- `.html`;
- `.js`;
- `.css`;
- `.md`;
- `.json`;
- `.yml`;
- `.yaml`;
- `.ini`;
- `.toml`.

Nunca deixar texto com mojibake no produto final.

Exemplos de texto corrompido:

```text
ConfiguraÃ§Ã£o
CabeÃ§alho
InformaÃ§Ãµes
AÃ§Ãµes
NÃ£o
Â
�
```

Exemplos corretos:

```text
Configuração
Cabeçalho
Informações
Ações
Não
```

Depois de alterar ficheiros `.py`, `.html`, `.js`, `.css` ou `.md`, procurar por caracteres suspeitos como:

```text
Ã
Â
�
```

A entrega não deve ser concluída enquanto houver texto corrompido visível na UI ou nos ficheiros alterados.

## 6) Estrutura por blocos

Sempre dividir código e scripts em blocos de processo para melhorar leitura e manutenção.

Em Python e PowerShell, usar comentários com `#`.

Exemplo:

```python
# ###################################################################################
# (1) VALIDAR DADOS
# ###################################################################################
```

Em JavaScript, usar comentários com `//`.

Exemplo:

```javascript
//###################################################################################
// (1) VALIDAR DADOS
//###################################################################################
```

Não usar `//` em comandos PowerShell.

## 7) PowerShell para alterações no projeto

Quando for criado script PowerShell para alterar o projeto, o bloco deve ser completo e pronto para copiar e colar.

O script deve:

- começar por `cd C:\workspace\AppVerboBraga`;
- validar a existência da pasta `appverbo`;
- definir `$ErrorActionPreference = "Stop"`;
- criar backup antes de alterar ficheiros;
- validar o conteúdo depois da alteração;
- executar validações aplicáveis;
- mostrar `git diff`;
- executar `git diff --check`;
- mostrar `git status`;
- reiniciar Docker quando aplicável;
- executar teste HTTP quando a aplicação web for afetada;
- mostrar logs recentes quando a aplicação web for afetada.

Exemplo mínimo de início:

```powershell
cd C:\workspace\AppVerboBraga
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\appverbo")) {
    throw "Pasta appverbo não encontrada. Confirme que está em C:\workspace\AppVerboBraga."
}
```

Quando a aplicação web for afetada, executar teste HTTP contra uma rota estável do projeto e confirmar que não retorna erro 500.

## 8) Validações obrigatórias por tipo de ficheiro

Para Python alterado, executar `py_compile`.

Exemplo:

```bash
docker compose exec web python -m py_compile appverbo/<ficheiro>.py
```

Para JavaScript alterado, executar `node --check`.

Exemplo:

```bash
node --check static/js/<ficheiro>.js
node --check static/js/modules/<ficheiro>.js
```

Para alterações estruturais no banco, executar:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
```

Para validação de whitespace e conflitos, executar:

```bash
git diff --check
```

## 9) Banco de dados e migrations

Não criar alterações estruturais no banco sem migration Alembic.

Qualquer nova tabela, coluna, índice ou constraint deve passar por migration.

Ao criar ou alterar models:

1. criar ou ajustar migration;
2. validar `alembic current`;
3. validar `alembic heads`;
4. validar `alembic check`;
5. aplicar `alembic upgrade head` quando necessário.

Comandos:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head
```

Não mascarar divergências entre models e migrations.

Resultado esperado para models sincronizados:

```text
No new upgrade operations detected.
```

## 10) Arquitetura modular

As tabelas principais da arquitetura modular são:

- `app_modules`;
- `sidebar_menu_items`;
- `entity_module_entitlements`.

Módulos core aparecem por padrão.

Módulos pagos só aparecem se a entidade tiver acesso ativo em `entity_module_entitlements`.

Regra principal:

```text
entity_module_entitlements.status = active
```

Se o módulo estiver inativo, ele não deve aparecer no menu e não deve permitir acesso direto por URL.

Antes de implementar lógica core/pago, verificar o model e a tabela existentes. Não criar novo campo para isso sem migration e validação do contrato atual.

## 11) Segurança de módulos pagos

Não confiar apenas no frontend para esconder módulos.

Toda rota de módulo pago deve validar acesso no backend.

Se a entidade não tiver acesso ativo, retornar erro 403.

Exemplo conceitual:

```python
require_module_access(session, entity_id, "tesouraria")
```

O frontend pode ocultar opções, mas a autorização real deve estar sempre no backend.

## 12) Menu lateral

Evitar criar menus fixos diretamente no HTML.

O menu lateral deve evoluir para ser gerado a partir das tabelas:

- `app_modules`;
- `sidebar_menu_items`;
- `entity_module_entitlements`.

A tabela antiga `sidebar_menu_settings` é compatibilidade temporária e não deve ser removida sem plano de migração.

Não remover compatibilidade legada enquanto o backend ainda depender dela.

## 13) Regras para datas

Em Google Apps Script relacionado ao projeto AppVerboBraga, formatar datas com:

```javascript
const dataFormatada = Utilities.formatDate(new Date(dataTexto), "GMT+1", "dd/MM/yyyy");
```

Em JavaScript normal de frontend ou Node.js, não usar `Utilities.formatDate`, porque `Utilities` é específico de Google Apps Script.

Para JavaScript normal, usar função própria existente no projeto ou `Intl.DateTimeFormat`, preservando o formato `dd/MM/yyyy` quando aplicável.

## 14) Pesquisa dinâmica de colunas

Sempre que uma rotina depender de colunas de tabelas, planilhas, arrays tabulares ou cabeçalhos, pesquisar dinamicamente o índice pelo nome da coluna no cabeçalho.

Não usar posição fixa de coluna como regra principal.

O nome da coluna é a referência absoluta.

Esta regra aplica-se a:

- planilhas;
- tabelas HTML;
- arrays tabulares;
- importações CSV/Excel;
- payloads com cabeçalhos;
- rotinas JavaScript;
- rotinas Python.

## 15) Versionamento de funções ajustadas

Quando for solicitado ajuste em função existente, criar nova função com sufixo sequencial apenas quando houver risco real de regressão, dependência externa ou necessidade de compatibilidade temporária.

Exemplo:

```text
euvouaroma()
euvouaroma_v1()
euvouaroma_v2()
```

Quando a alteração for interna, segura e sem contrato externo, é permitido ajustar a função existente.

Ao criar versão nova de função:

- documentar porque a versão antiga permanece;
- indicar onde a versão nova é usada;
- evitar acumular código morto indefinidamente.

Não sobrescrever comportamento antigo sem necessidade quando houver risco de regressão.

## 16) Listas configuráveis

Sempre que uma funcionalidade permitir criar múltiplos itens configuráveis, a interface deve seguir este padrão:

1. Bloco superior para criar ou editar apenas um item por vez.
2. Tabela ou lista inferior com itens já criados.
3. Paginação obrigatória na tabela ou lista.
4. A tabela ou lista deve ser a fonte visual principal para o utilizador.

Não criar formulários longos com todos os itens abertos simultaneamente.

Containers antigos podem existir apenas como compatibilidade temporária e devem ficar ocultos.

O submit deve reconstruir os inputs no formato esperado pelo backend atual.

Extrair lógica genérica para manager reutilizável quando houver repetição.

O ficheiro `new_user.js` deve apenas inicializar managers sempre que possível, evitando concentrar lógica extensa.

## 17) Abas configuráveis do processo

Toda nova aba configurável dentro do editor de processo deve ter apenas dois blocos visuais principais:

1. Bloco superior de criação/edição.
2. Bloco inferior com tabela ou lista paginada.

Não criar terceiro bloco visual externo envolvendo os dois blocos principais.

O container principal do manager deve ser estrutural, sem borda, fundo ou padding visual.

As ações da tabela devem usar ícones alinhados lado a lado:

- editar;
- subir;
- descer;
- remover.

Toda aba configurável deve ter manager JavaScript próprio em:

```text
static/js/modules
```

Regra geral: abas configuráveis podem ter manager JavaScript próprio.

Exceção: quando uma aba já estiver migrada para padrão server-render/AdminSubprocess, o JavaScript não deve reconstruir cards, formulários ou listas. Deve apenas executar ações auxiliares.

## 18) Validação de templates e assets

Sempre que alterar `templates/new_user.html` ou assets usados por ele:

- atualizar cache buster dos ficheiros CSS ou JS alterados;
- validar JavaScript com `node --check`;
- validar ausência de mojibake;
- confirmar referências no template;
- confirmar que não existem duplicações de scripts ou CSS.

Exemplos:

```bash
node --check static/js/new_user.js
node --check static/js/modules/<ficheiro_alterado>.js
```

## 19) Campos lado a lado em abas configuráveis

Quando uma aba configurável precisar apresentar campos lado a lado:

- HTML define a estrutura;
- CSS define o grid;
- JavaScript gere apenas dados, ações, validações, sincronização de payload, renderização de listas e eventos.

Os campos lado a lado devem nascer como filhos diretos do mesmo bloco no template HTML.

O JavaScript não deve:

- criar wrappers visuais para alinhar campos;
- mover campos existentes para outro container;
- duplicar selects já existentes no HTML;
- criar segunda coluna por script quando ela pode nascer no template.

## 20) Botões Guardar e Cancelar

Sempre que existir um par de botões Guardar e Cancelar:

- os botões devem ficar no lado esquerdo;
- os dois botões devem ter o mesmo tamanho;
- a ordem deve ser Guardar primeiro e Cancelar depois;
- os textos devem ser exatamente Guardar e Cancelar.

Usar as classes globais sempre que possível:

```text
action-btn
action-btn-cancel
```

Não posicionar Guardar e Cancelar no lado direito, salvo exceção explícita aprovada.

## 21) Bloco ou card de criação

Sempre que uma aba, subprocesso ou listagem administrativa tiver ação para criar nova entrada, o botão `Criar + nome` deve ficar em card ou bloco separado acima da tabela/lista.

Exemplos:

- Criar entidade;
- Criar utilizador;
- Criar sessão;
- Criar menu.

O card deve seguir o padrão visual da aba Entidade:

- fundo cinza claro;
- borda suave;
- cantos arredondados;
- altura mínima padronizada;
- botão alinhado à esquerda.

A tabela/lista inferior deve ficar em outro card separado.

Não colocar botão de criação no lado direito do cabeçalho da tabela/lista.

Quando o formulário abrir:

- não deixar faixa vazia acima dos campos;
- não manter espaço reservado para botão oculto;
- não criar linha separando toolbar vazia dos campos.

## 22) Registos ativos e inativos

Sempre que existir listagem administrativa com estado ativo/inativo:

- o bloco principal deve listar apenas registos ativos ou criados;
- o bloco de inativos deve ser um card separado abaixo;
- registos inativos nunca devem ficar dentro do mesmo card/tabela dos registos ativos;
- o botão de eliminar deve aparecer apenas no bloco de inativos;
- o backend também deve impedir eliminar registos ativos.

Esta regra aplica-se, no mínimo, a:

- Utilizadores;
- Entidades;
- Sessões;
- qualquer nova listagem com estados ativo/inativo.

## 23) Status e tabelas administrativas de utilizadores

A normalização e tradução visual do status devem ficar em:

```text
appverbo/services/user_status.py
```

Não duplicar lógica de status diretamente em `page.py`, handlers ou templates.

O banco deve guardar valores canónicos em inglês:

- `active`;
- `inactive`;
- `pending`;
- `blocked`.

O português deve ser apenas label visual:

- Ativo;
- Inativo;
- Pendente;
- Bloqueado.

Tabelas administrativas de utilizadores devem usar partial reutilizável em:

```text
templates/partials/admin_user_table_v1.html
```

CSS de rodapé, paginação e badges deve ficar em módulo reutilizável dentro de:

```text
static/css/modules
```

## 24) Sessões do sidebar

A aba Sessões deve seguir o padrão Entidade/AdminSubprocess.

Regra principal:

- renderização pelo backend/template;
- criação e edição processadas pelo fluxo do subprocesso administrativo;
- listas ativas e inativas separadas pelo backend;
- JavaScript apenas auxiliar;
- sem reconstrução completa de cards, formulários ou listas por JavaScript.

O botão Criar sessão pertence apenas à aba Sessões e deve aparecer acima da listagem quando a aba Sessões estiver ativa.

O card Criar sessão não pode aparecer no fim da aba Entidade, Utilizador, Menu ou qualquer outra.

Ao sair da aba Sessões, blocos órfãos de Sessões não devem permanecer visíveis.

Ao voltar para a aba Sessões, os cards e a listagem devem ser renderizados ou reidratados a partir do backend/configuração persistida.

Campos visíveis ao criar sessão:

- Nome da sessão;
- Sistema;
- Estado.

A chave técnica da sessão deve:

- continuar a existir para gravação no BD;
- ser gerada automaticamente a partir do Nome da sessão;
- ficar oculta no bloco de criação;
- ser preservada durante edição.

A ação Editar de Sessões não deve usar `alert`.

A edição deve seguir o fluxo padrão Entidade/AdminSubprocess, com carregamento dos dados pelo backend e renderização do formulário pelo template.

Se a implementação atual usar parâmetro técnico como `sidebar_section_edit_key`, preservar esse contrato até migração validada.

Se o estado for Ativo, a sessão aparece no bloco principal.

Se o estado for diferente de Ativo, aparece no bloco Sessões inativas.

A alteração de estado deve persistir no BD através de:

```text
section_status
```

## 25) Escopo de scripts de subprocessos

Scripts de um subprocesso ou aba não podem criar, mover ou exibir blocos fora da própria aba ativa.

Para a aba Sessões:

- o card Criar sessão só pode aparecer quando Sessões estiver ativa;
- o card Sessões inativas só pode aparecer quando Sessões estiver ativa;
- nenhum bloco de Sessões pode aparecer no fim da aba Entidade, Utilizador, Menu ou qualquer outra.

Não usar apenas URL/hash como critério, porque a URL pode manter hash de outro card mesmo com a aba correta ativa.

A validação de escopo deve considerar:

- aba ativa;
- visibilidade real do card;
- contexto do subprocesso;
- estado visual dos botões/tabs.

## 26) Regras de HTML, CSS e JavaScript

HTML deve definir estrutura.

CSS deve definir layout visual.

JavaScript deve gerir:

- dados;
- ações;
- validações;
- sincronização de payload;
- renderização de listas quando aplicável;
- eventos.

JavaScript não deve resolver problemas estruturais que pertencem ao HTML ou problemas visuais que pertencem ao CSS, exceto em compatibilidade temporária justificada.

Evitar concentrar lógica extensa em:

```text
static/js/new_user.js
```

Sempre que possível, criar ou evoluir managers em:

```text
static/js/modules
```

## 27) Compatibilidade temporária

Containers, campos e estruturas legadas podem existir apenas como compatibilidade temporária.

Quando mantidos, devem:

- ficar ocultos se não forem a fonte visual principal;
- ser sincronizados antes do submit;
- ser documentados no código;
- não conflitar com a UI nova.

Não remover legado sem confirmar que o backend já não depende dele.

Compatibilidade temporária deve ser tratada como transitória, não como padrão definitivo.

## 28) Checklist final antes de concluir

Antes de concluir qualquer alteração, validar:

- aplicação sobe no Docker;
- logs recentes sem traceback;
- texto sem mojibake;
- migrations sincronizadas;
- menu lateral não quebrou;
- módulos pagos continuam protegidos no backend;
- JavaScript alterado passa em `node --check`;
- Python alterado passa em `py_compile`;
- `git diff --check` não mostra erros;
- `git status` mostra apenas alterações esperadas.

Quando a aplicação web for afetada, também validar uma rota HTTP estável e confirmar ausência de erro 500.

## 29) Regra de manutenção deste ficheiro

Manter este `AGENTS.md` curto, consistente e sem Markdown quebrado.

Evitar acumular regras históricas duplicadas.

Quando uma regra nova substituir uma regra antiga, consolidar a versão final em vez de adicionar múltiplas versões concorrentes.

Não inserir notas de conversa, comentários temporários ou blocos incompletos neste ficheiro.

Se o ficheiro crescer demais, mover detalhes extensos para documentação auxiliar e manter aqui apenas o resumo obrigatório.

## 30) Padrão de subprocesso administrativo (referência obrigatória)

Sempre que criar ou ajustar um novo subprocesso administrativo, seguir o mesmo padrão consolidado de Entidade/Departamentos:

- manter renderização principal no backend/template e usar JavaScript apenas para ações auxiliares;
- usar card separado para ação de criação (`Criar + nome`) acima da listagem;
- o botão de criação deve refletir o subprocesso/aba ativa em tempo real (ex.: `Criar Liderança`, `Criar sessão`, `Criar entidade`);
- usar card separado para formulário de criação/edição;
- quando a ação `Editar` abrir card/formulário de subprocesso, o card de edição deve usar fundo cinzento claro padrão (igual Entidade), nunca fundo branco;
- os campos do formulário de criação/edição devem ser exatamente os campos configurados em `Menu > Editar processo` para o processo e subprocesso (aba/header) ativo;
- não deixar faixa vazia no topo quando formulário estiver oculto;
- usar pares `Guardar` e `Cancelar` no lado esquerdo e com tamanho consistente;
- quando houver estado, separar em dois cards: bloco de ativos e bloco de inativos;
- não misturar ativos e inativos na mesma tabela;
- mostrar eliminar apenas no bloco inativo;
- listar ações com ícones alinhados lado a lado na ordem: exibir, editar e eliminar (quando aplicável);
- em listagens administrativas deste padrão, o eliminar deve executar direto, sem popup nativo `window.confirm`;
- manter toolbar `Total` e `Procurar` dentro de cada card de tabela, nunca em card acima das tabelas;
- garantir que o total atualiza após renderização dinâmica, filtro e mudança de linhas;
- manter paginação padrão em cada tabela de ativos/inativos;
- para Departamentos, não exibir coluna `Criado em` na tabela padrão;
- manter badges de estado com labels visuais em PT (`Ativo`/`Inativo`);
- preservar compatibilidade de dados legados de `section_key` (ex.: `field:<campo>`) para não ocultar registos antigos quando a configuração muda de campo para header;
- em qualquer alteração de JS/CSS/template deste fluxo, atualizar cache buster no template e validar carregamento.
