# AGENTS.md - Instrucoes do Projeto AppVerboBraga

Este ficheiro contem as regras locais obrigatorias para qualquer trabalho realizado no repositorio AppVerboBraga.

O objetivo deste ficheiro e orientar o Codex e outros agentes de desenvolvimento com instrucoes claras, curtas e prioritarias. Manter este documento objetivo para evitar truncamento pelo limite padrao de leitura de instrucoes do Codex.

## 1) Identidade do projeto

O AppVerboBraga e uma aplicacao SaaS modular para igrejas.

A aplicacao deve crescer por modulos ativaveis por entidade: Nucleo/Base, Tesouraria, Eventos, Escalas, Cursos e Relatorios avancados.

Novas funcionalidades comerciais devem ser criadas como modulos, nao como paginas soltas.

## 2) Ordem de prioridade das instrucoes

Ao executar tarefas neste repositorio, seguir esta ordem:

1. Instrucoes explicitas do utilizador na conversa atual.
2. Este ficheiro AGENTS.md.
3. Convencoes ja existentes no codigo.
4. Boas praticas gerais de desenvolvimento.

Se houver conflito entre regras, aplicar a instrucao mais especifica e mais recente.

Nao criar AGENTS.override.md sem pedido explicito. Usar AGENTS.override.md apenas para overrides temporarios e claramente justificados.

## 3) Regras operacionais obrigatorias

Antes de alterar ficheiros:

- entender a funcionalidade existente;
- evitar alteracoes fora do escopo pedido;
- criar backup dos ficheiros alterados quando a alteracao for feita por script;
- preservar nomes, rotas e contratos existentes sempre que possivel;
- nao remover compatibilidade temporaria sem validacao.

Depois de alterar ficheiros:

- validar sintaxe;
- validar ausencia de mojibake;
- mostrar git diff;
- executar git diff --check;
- mostrar git status;
- reiniciar Docker quando aplicavel;
- verificar logs recentes.

## 4) Docker-first

Este projeto usa Docker.

Sempre que a tarefa envolver banco de dados, Alembic, migrations, models, validacao da aplicacao ou execucao do backend, usar o container web.

Comandos corretos:

docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head

Evitar executar Alembic no ambiente local .venv quando o banco real usado pela aplicacao estiver no Docker.

## 5) Codificacao de texto

Todos os ficheiros de codigo, templates, assets e documentacao devem ficar em UTF-8.

Nunca deixar texto com mojibake no produto final.

Depois de alterar ficheiros .py, .html, .js, .css ou .md, procurar por caracteres suspeitos como texto corrompido, simbolos invalidos e palavras portuguesas quebradas.

A entrega nao deve ser concluida enquanto houver texto corrompido visivel na UI ou nos ficheiros alterados.

## 6) Estrutura por blocos

Sempre dividir codigo e scripts em blocos de processo para melhorar leitura e manutencao.

Em PowerShell, usar comentarios com #.

Em JavaScript, usar comentarios com //.

Nao usar // em comandos PowerShell.

## 7) PowerShell para alteracoes no projeto

Quando for criado script PowerShell para alterar o projeto, o bloco deve ser completo e pronto para copiar e colar.

O script deve comecar por cd C:\workspace\AppVerboBraga, validar a pasta appverbo e usar ErrorActionPreference como Stop.

Sempre que alterar ficheiros por script: criar backup antes, validar conteudo depois, executar validacoes aplicaveis, mostrar git diff, executar git diff --check, mostrar git status, reiniciar Docker quando aplicavel, executar teste HTTP e mostrar logs recentes.

## 8) Validacoes obrigatorias por tipo de ficheiro

Para Python alterado, executar py_compile.

Para JavaScript alterado, executar node --check.

Para alteracoes estruturais no banco, executar docker compose exec web python -m alembic check.

Para validacao de whitespace e conflitos, executar git diff --check.

## 9) Banco de dados e migrations

Nao criar alteracoes estruturais no banco sem migration Alembic.

Qualquer nova tabela, coluna, indice ou constraint deve passar por migration.

Ao criar ou alterar models: criar ou ajustar migration, validar alembic current, validar alembic heads, validar alembic check e aplicar alembic upgrade head quando necessario.

Nao mascarar divergencias entre models e migrations.

## 10) Arquitetura modular

As tabelas principais da arquitetura modular sao app_modules, sidebar_menu_items e entity_module_entitlements.

Modulos core aparecem por padrao.

Modulos pagos so aparecem se a entidade tiver entity_module_entitlements.status = active.

Se o modulo estiver inactive, ele nao deve aparecer no menu e nao deve permitir acesso direto por URL.

## 11) Seguranca de modulos pagos

Nao confiar apenas no frontend para esconder modulos.

Toda rota de modulo pago deve validar acesso no backend.

Se a entidade nao tiver acesso ativo, retornar erro 403.

## 12) Menu lateral

Evitar criar menus fixos diretamente no HTML.

O menu lateral deve evoluir para ser gerado a partir das tabelas app_modules, sidebar_menu_items e entity_module_entitlements.

A tabela antiga sidebar_menu_settings e compatibilidade temporaria e nao deve ser removida sem plano de migracao.

## 13) Regras para datas

Quando houver logica JavaScript ou Google Apps Script relacionada ao projeto AppVerboBraga, formatar datas com Utilities.formatDate(new Date(dataTexto), GMT+1, dd/MM/yyyy).

## 14) Pesquisa dinamica de colunas

Sempre que uma rotina depender de colunas de tabelas, planilhas, arrays tabulares ou cabecalhos, pesquisar dinamicamente o indice pelo nome da coluna no cabecalho.

Nao usar posicao fixa de coluna como regra principal.

O nome da coluna e a referencia absoluta.

## 15) Versionamento de funcoes ajustadas

Sempre que for solicitado ajuste em funcao existente, criar uma nova funcao com sufixo sequencial.

Exemplo: se existir euvouaroma, criar euvouaroma_v1. Se ja existir _v1, criar _v2, e assim sucessivamente.

Nao sobrescrever comportamento antigo sem necessidade quando houver risco de regressao.

## 16) Listas configuraveis

Sempre que uma funcionalidade permitir criar multiplos itens configuraveis, a interface deve ter bloco superior para criar ou editar apenas um item por vez e tabela ou lista inferior com itens ja criados.

A tabela ou lista deve ter paginacao obrigatoria e ser a fonte visual principal para o utilizador.

Containers antigos podem existir apenas como compatibilidade temporaria e devem ficar ocultos.

O submit deve reconstruir os inputs no formato esperado pelo backend atual.

Nao criar formularios longos com todos os itens abertos simultaneamente.

Extrair logica generica para manager reutilizavel quando houver repeticao.

O ficheiro new_user.js deve apenas inicializar managers sempre que possivel.

## 17) Abas configuraveis do processo

Toda nova aba configuravel dentro do editor de processo deve ter apenas dois blocos visuais principais: bloco superior de criacao/edicao e bloco inferior com tabela ou lista paginada.

Nao criar terceiro bloco visual externo envolvendo os dois blocos principais.

O container principal do manager deve ser estrutural, sem borda, fundo ou padding visual.

Acoes da tabela devem usar icones alinhados lado a lado: editar, subir, descer e remover.

Toda aba configuravel deve ter manager JavaScript proprio em static/js/modules.

## 18) Validacao de templates e assets

Sempre que alterar templates/new_user.html ou assets usados por ele: atualizar cache buster dos ficheiros CSS ou JS alterados, validar JavaScript com node --check, validar ausencia de mojibake, confirmar referencias no template e confirmar que nao existem duplicacoes de scripts ou CSS.

## 19) Campos lado a lado em abas configuraveis

Quando uma aba configuravel precisar apresentar campos lado a lado: HTML define a estrutura, CSS define o grid e JavaScript gere apenas dados e acoes.

Os campos lado a lado devem nascer como filhos diretos do mesmo bloco no template HTML.

O JavaScript nao deve criar wrappers visuais, mover campos existentes para outro container, duplicar selects ja existentes no HTML ou criar segunda coluna por script quando ela pode nascer no template.

## 20) Botoes Guardar e Cancelar

Sempre que existir um par de botoes Guardar e Cancelar, os botoes devem ficar no lado esquerdo, ter o mesmo tamanho, usar a ordem Guardar primeiro e Cancelar depois, e usar os textos Guardar e Cancelar.

Usar as classes globais action-btn e action-btn-cancel sempre que possivel.

Nao posicionar Guardar e Cancelar no lado direito, salvo excecao explicita aprovada.

## 21) Bloco ou card de criacao

Sempre que uma aba, subprocesso ou listagem administrativa tiver acao para criar nova entrada, o botao Criar + nome deve ficar em card ou bloco separado acima da tabela/lista.

O card deve seguir o padrao visual da aba Entidade: fundo cinza claro, borda suave, cantos arredondados, altura minima padronizada e botao alinhado a esquerda.

A tabela/lista inferior deve ficar em outro card separado.

Nao colocar botao de criacao no lado direito do cabecalho da tabela/lista.

Quando o formulario abrir, nao deixar faixa vazia acima dos campos, nao manter espaco reservado para botao oculto e nao criar linha separando toolbar vazia dos campos.

## 22) Registos ativos e inativos

Sempre que existir listagem administrativa com estado ativo/inativo, o bloco principal deve listar apenas registos ativos ou criados e o bloco de inativos deve ser um card separado abaixo.

Nunca colocar registos inativos dentro do mesmo card/tabela dos registos ativos.

O botao de eliminar deve aparecer apenas no bloco de inativos.

O backend tambem deve impedir eliminar registos ativos.

Esta regra aplica-se, no minimo, a Utilizadores, Entidades, Sessoes e qualquer nova listagem com estados ativo/inativo.

## 23) Status e tabelas administrativas de utilizadores

A normalizacao e traducao visual do status devem ficar em appverbo/services/user_status.py.

Nao duplicar logica de status diretamente em page.py, handlers ou templates.

O banco deve guardar valores canonicos em ingles: active, inactive, pending, blocked.

O portugues deve ser apenas label visual: Ativo, Inativo, Pendente, Bloqueado.

Tabelas administrativas de utilizadores devem usar partial reutilizavel em templates/partials/admin_user_table_v1.html.

CSS de rodape, paginacao e badges deve ficar em modulo reutilizavel dentro de static/css/modules.

## 24) Sessoes do sidebar

Na aba Sessoes, o botao Criar sessao pertence apenas a aba Sessoes e deve aparecer acima da listagem quando a aba Sessoes estiver ativa.

O card Criar sessao nao pode aparecer no fim da aba Entidade, Utilizador, Menu ou qualquer outra.

Ao sair da aba Sessoes, blocos orfaos de Sessoes devem ser removidos.

Ao voltar para a aba Sessoes, os cards e a listagem devem ser recriados ou reidratados automaticamente.

A listagem inferior deve ser sempre reidratada a partir do BD/configuracao persistida.

Campos visiveis ao criar sessao: Nome da sessao, Sistema e Estado.

A chave tecnica da sessao deve continuar a existir para gravacao no BD, ser gerada automaticamente a partir do Nome da sessao, ficar oculta no bloco de criacao e ser preservada durante edicao.

O botao de editar deve abrir edicao diretamente na linha, sem usar alert.

Durante a edicao, substituir os icones de acao por Guardar e Cancelar.

Se o estado for Ativo, a sessao aparece no bloco principal. Se for diferente de Ativo, aparece no bloco Sessoes inativas.

A alteracao de estado deve persistir no BD atraves de section_status.

## 25) Escopo de scripts de subprocessos

Scripts de um subprocesso ou aba nao podem criar, mover ou exibir blocos fora da propria aba ativa.

Para a aba Sessoes, os cards Criar sessao e Sessoes inativas so podem aparecer quando Sessoes estiver ativa.

Nao usar apenas URL/hash como criterio, porque a URL pode manter hash de outro card mesmo com a aba correta ativa.

## 26) Regras de HTML, CSS e JavaScript

HTML deve definir estrutura. CSS deve definir layout visual. JavaScript deve gerir dados, acoes, validacoes, sincronizacao de payload, renderizacao e eventos.

JavaScript nao deve resolver problemas estruturais que pertencem ao HTML ou problemas visuais que pertencem ao CSS, exceto em compatibilidade temporaria justificada.

Evitar concentrar logica extensa em static/js/new_user.js. Sempre que possivel, criar ou evoluir managers em static/js/modules.

## 27) Compatibilidade temporaria

Containers, campos e estruturas legadas podem existir apenas como compatibilidade temporaria.

Quando mantidos, devem ficar ocultos se nao forem a fonte visual principal, ser sincronizados antes do submit, ser documentados no codigo e nao conflitar com a UI nova.

Nao remover legado sem confirmar que o backend ja nao depende dele.

## 28) Checklist final antes de concluir

Antes de concluir qualquer alteracao, validar: aplicacao sobe no Docker, logs recentes sem traceback, texto sem mojibake, migrations sincronizadas, menu lateral nao quebrou, modulos pagos continuam protegidos no backend, JavaScript alterado passa em node --check, Python alterado passa em py_compile, git diff --check nao mostra erros e git status mostra apenas alteracoes esperadas.

## 29) Regra de manutencao deste ficheiro

Manter este AGENTS.md curto, consistente e sem Markdown quebrado.

Evitar acumular regras historicas duplicadas. Quando uma regra nova substituir uma regra antiga, consolidar a versao final em vez de adicionar multiplas versoes concorrentes.

Se o ficheiro crescer demais, mover detalhes extensos para documentacao auxiliar e manter aqui apenas o resumo obrigatorio.
