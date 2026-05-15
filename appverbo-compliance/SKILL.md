---
name: appverbo-compliance
description: >-
  usar quando o utilizador pedir qualquer tarefa relacionada ao projeto appverbobraga, incluindo análise, planeamento, implementação, correção, refatoração, revisão de código, criação de scripts powershell, validação de git diff, validação de ficheiros, criação de migrations, alterações em templates, javascript, css, python, docker, alembic, menu lateral, módulos pagos, sessões, entidades, utilizadores ou qualquer pedido que precise respeitar o agents.md. aplicar sempre uma abordagem agents-first: interpretar primeiro a definição funcional desejada pelo utilizador, mapear as regras aplicáveis do agents.md, estruturar a implementação correta e só depois propor código, script, diff, validações ou checklist final.
---

# AppVerbo Compliance

Aplicar esta Skill para garantir que qualquer trabalho no projeto AppVerboBraga respeite o `AGENTS.md`, com foco em estrutura correta, segurança, modularidade, validações e ausência de regressões.

A prioridade é organizar o pensamento antes de escrever código.

## 1) Regra principal

Antes de escrever código, script, patch, plano técnico ou checklist, fazer sempre esta sequência:

1. Identificar a definição funcional desejada pelo utilizador.
2. Identificar quais partes do AppVerboBraga podem ser afetadas.
3. Mapear as regras aplicáveis do `AGENTS.md`.
4. Definir a estrutura correta da solução.
5. Só depois escrever código, script, plano, diff ou validação.

Nunca começar pela implementação sem antes alinhar a solução com o `AGENTS.md`.

## 2) Ordem de prioridade

Seguir sempre esta ordem:

1. Instruções explícitas do utilizador na conversa atual.
2. `AGENTS.md` do projeto AppVerboBraga.
3. Convenções já existentes no código.
4. Boas práticas gerais de desenvolvimento.

Se houver conflito, aplicar a instrução mais específica e mais recente.

Não inventar estrutura quando for possível consultar o código existente, o diff, o ficheiro enviado ou o repositório.

## 3) Modo AGENTS-first

Sempre que o pedido envolver AppVerboBraga, responder usando este modo mental:

```text
1. O que o utilizador quer funcionalmente?
2. Isto afeta backend, frontend, template, css, javascript, banco, migration, docker, menu, sessão, módulo ou permissão?
3. Que regras do AGENTS.md são obrigatórias?
4. Existe risco de mojibake, regressão, duplicação, quebra de contrato, migration ausente ou validação incompleta?
5. Qual é a estrutura correta?
6. Qual é a implementação mais segura?
7. Quais validações finais são obrigatórias?
```

## 4) Formato padrão de resposta

Quando o utilizador pedir análise, plano ou implementação, estruturar a resposta assim, adaptando conforme o caso:

```text
## Definição entendida

Resumo objetivo do que o utilizador quer.

## Regras do AGENTS.md aplicáveis

Lista curta das regras relevantes.

## Estrutura correta da solução

Explicação da organização esperada antes do código.

## Implementação

Código, script, patch ou instruções.

## Validações obrigatórias

Comandos e verificações necessárias.

## Checklist final

Confirmação do que precisa passar antes de concluir.
```

Se o pedido for simples, compactar a resposta, mas nunca ignorar as regras críticas.

## 4.1) Limpeza da resposta final

A resposta final ao utilizador não deve incluir ruídos internos, logs de ferramenta, mensagens de aplicação, marcadores de raciocínio ou textos técnicos que não façam parte da conclusão.

Nunca incluir na resposta final expressões como:

```text
Received app response
Thought for ...
tool call
app response
analysis
internal reasoning
```

Se alguma ferramenta, conector ou ambiente informar que uma Skill não está disponível como executável, explicar isso de forma limpa e útil.

Exemplo correto:

```text
A Skill appverbo-compliance não estava disponível como Skill executável neste ambiente, então apliquei manualmente a abordagem definida por ela: AGENTS-first, validação da estrutura e comparação com o repositório.
```

Não expor detalhes internos do processamento.

## 5) Regras obrigatórias antes de alterar código

Antes de propor alteração em ficheiros:

- entender a funcionalidade existente;
- evitar alterações fora do escopo pedido;
- preservar nomes, rotas e contratos existentes sempre que possível;
- não remover compatibilidade temporária sem validação;
- identificar impacto em backend, frontend, templates, assets, migrations e Docker;
- verificar se há risco de mojibake;
- verificar se há risco de duplicar lógica existente;
- verificar se há risco de quebrar módulos pagos ou permissões.

Se a alteração for feita por script, incluir criação de backup antes de modificar ficheiros.

## 6) Docker-first

Quando a tarefa envolver banco de dados, Alembic, migrations, models, validação da aplicação ou execução do backend, usar Docker e o container `web`.

Comandos base:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head
```

Evitar executar Alembic no `.venv` local quando o banco real usado pela aplicação estiver no Docker.

Reiniciar Docker quando forem alterados:

- backend Python;
- models;
- migrations;
- dependências;
- variáveis de ambiente;
- configuração da aplicação;
- templates ou código carregado no arranque.

Para logs recentes, preferir:

```bash
docker compose logs --tail=100 web
```

## 7) UTF-8 e mojibake

Todos os ficheiros devem permanecer em UTF-8.

Após alterar `.py`, `.html`, `.js`, `.css`, `.md`, `.json`, `.yml`, `.yaml`, `.ini` ou `.toml`, procurar caracteres suspeitos:

```text
Ã
Â
�
```

Exemplos de texto corrompido:

```text
ConfiguraÃ§Ã£o
CabeÃ§alho
InformaÃ§Ãµes
AÃ§Ãµes
NÃ£o
```

Exemplos corretos:

```text
Configuração
Cabeçalho
Informações
Ações
Não
```

Não concluir resposta como finalizada se houver texto corrompido visível na UI ou nos ficheiros alterados.

## 8) Banco de dados e migrations

Não criar alterações estruturais no banco sem migration Alembic.

Qualquer nova tabela, coluna, índice ou constraint deve passar por migration.

Ao criar ou alterar models:

1. criar ou ajustar migration;
2. validar `alembic current`;
3. validar `alembic heads`;
4. validar `alembic check`;
5. aplicar `alembic upgrade head` quando necessário.

Não mascarar divergências entre models e migrations.

Resultado esperado para models sincronizados:

```text
No new upgrade operations detected.
```

## 9) Arquitetura modular

O AppVerboBraga é uma aplicação SaaS modular para igrejas.

Novas funcionalidades comerciais devem ser criadas como módulos, não como páginas soltas.

Tabelas principais da arquitetura modular:

```text
app_modules
sidebar_menu_items
entity_module_entitlements
```

Módulos core aparecem por padrão.

Módulos pagos só aparecem se a entidade tiver acesso ativo:

```text
entity_module_entitlements.status = active
```

Se o módulo estiver inativo:

- não deve aparecer no menu;
- não deve permitir acesso direto por URL;
- o backend deve retornar 403.

Nunca confiar apenas no frontend para esconder módulos pagos.

## 10) Menu lateral

Evitar criar menus fixos diretamente no HTML.

O menu lateral deve evoluir a partir das tabelas:

```text
app_modules
sidebar_menu_items
entity_module_entitlements
```

A tabela antiga `sidebar_menu_settings` é compatibilidade temporária.

Não remover `sidebar_menu_settings` ou estruturas legadas sem confirmar que o backend já não depende delas.

## 11) HTML, CSS e JavaScript

Separar responsabilidades:

```text
HTML       = estrutura
CSS        = layout visual
JavaScript = dados, ações, validações, eventos e sincronização
```

JavaScript não deve resolver problemas estruturais que pertencem ao HTML nem problemas visuais que pertencem ao CSS, exceto em compatibilidade temporária justificada.

Evitar concentrar lógica extensa em:

```text
static/js/new_user.js
```

Sempre que possível, criar ou evoluir managers em:

```text
static/js/modules
```

## 12) Abas configuráveis e listas

Para funcionalidades com múltiplos itens configuráveis, usar sempre:

1. Bloco superior para criar ou editar um item por vez.
2. Bloco inferior com tabela ou lista paginada.
3. Tabela/lista como fonte visual principal para o utilizador.

Não criar formulários longos com todos os itens abertos simultaneamente.

Containers antigos podem existir apenas como compatibilidade temporária, ocultos e sincronizados antes do submit.

## 13) Botões Guardar e Cancelar

Quando existir par de botões Guardar e Cancelar:

- posicionar à esquerda;
- usar mesmo tamanho;
- ordem: Guardar primeiro, Cancelar depois;
- textos exatos: `Guardar` e `Cancelar`;
- usar classes globais quando possível:

```text
action-btn
action-btn-cancel
```

Não posicionar no lado direito salvo exceção explícita aprovada.

## 14) Cards de criação

Quando uma aba, subprocesso ou listagem administrativa tiver ação de criação, o botão `Criar + nome` deve ficar num card separado acima da tabela/lista.

O card deve seguir o padrão visual da aba Entidade:

- fundo cinza claro;
- borda suave;
- cantos arredondados;
- altura mínima padronizada;
- botão alinhado à esquerda.

A tabela/lista inferior deve ficar em outro card separado.

Não colocar botão de criação no lado direito do cabeçalho da tabela/lista.

## 15) Registos ativos e inativos

Em listagens administrativas com estado ativo/inativo:

- o bloco principal lista apenas registos ativos ou criados;
- os inativos ficam em card separado abaixo;
- registos inativos não ficam na mesma tabela/card dos ativos;
- botão eliminar aparece apenas no bloco de inativos;
- backend também deve impedir eliminar registos ativos.

Aplicar no mínimo a:

```text
Utilizadores
Entidades
Sessões
novas listagens com estados ativo/inativo
```

## 16) Sessões do sidebar

A aba Sessões deve seguir o padrão Entidade/AdminSubprocess.

Regra principal:

- renderização pelo backend/template;
- criação e edição pelo fluxo do subprocesso administrativo;
- listas ativas e inativas separadas pelo backend;
- JavaScript apenas auxiliar;
- sem reconstrução completa de cards, formulários ou listas por JavaScript.

O botão Criar sessão pertence apenas à aba Sessões.

O card Criar sessão não pode aparecer no fim da aba Entidade, Utilizador, Menu ou qualquer outra.

Campos visíveis ao criar sessão:

```text
Nome da sessão
Sistema
Estado
```

A chave técnica da sessão deve:

- existir para gravação no BD;
- ser gerada automaticamente a partir do Nome da sessão;
- ficar oculta no bloco de criação;
- ser preservada durante edição.

A ação Editar não deve usar `alert`.

A edição deve seguir o fluxo padrão Entidade/AdminSubprocess, com dados carregados pelo backend e formulário renderizado pelo template.

Se existir contrato como `sidebar_section_edit_key`, preservar até migração validada.

Estado:

```text
Ativo               -> bloco principal
diferente de Ativo  -> bloco Sessões inativas
```

A alteração de estado deve persistir no BD através de:

```text
section_status
```

## 17) Escopo de scripts de subprocessos

Scripts de subprocesso ou aba não podem criar, mover ou exibir blocos fora da própria aba ativa.

Para Sessões:

- card Criar sessão só pode aparecer quando Sessões estiver ativa;
- card Sessões inativas só pode aparecer quando Sessões estiver ativa;
- nenhum bloco de Sessões pode aparecer no fim de Entidade, Utilizador, Menu ou outra aba.

Não usar apenas URL/hash como critério.

Validar também:

- aba ativa;
- visibilidade real do card;
- contexto do subprocesso;
- estado visual dos botões/tabs.

## 18) Status de utilizadores

Normalização e tradução visual do status devem ficar em:

```text
appverbo/services/user_status.py
```

Não duplicar lógica de status em `page.py`, handlers ou templates.

Banco deve guardar valores canónicos em inglês:

```text
active
inactive
pending
blocked
```

Português deve ser apenas label visual:

```text
Ativo
Inativo
Pendente
Bloqueado
```

Tabelas administrativas de utilizadores devem usar partial reutilizável:

```text
templates/partials/admin_user_table_v1.html
```

CSS de rodapé, paginação e badges deve ficar em módulo reutilizável dentro de:

```text
static/css/modules
```

## 19) Pesquisa dinâmica de colunas

Sempre que uma rotina depender de colunas de tabelas, planilhas, arrays tabulares ou cabeçalhos, pesquisar dinamicamente o índice pelo nome da coluna no cabeçalho.

Não usar posição fixa de coluna como regra principal.

O nome da coluna é a referência absoluta.

Aplicar a:

```text
planilhas
tabelas HTML
arrays tabulares
CSV
Excel
payloads com cabeçalhos
rotinas JavaScript
rotinas Python
```

## 20) Datas

Em Google Apps Script, usar:

```javascript
const dataFormatada = Utilities.formatDate(new Date(dataTexto), "GMT+1", "dd/MM/yyyy");
```

Em JavaScript normal de frontend ou Node.js, não usar `Utilities.formatDate`.

Para JavaScript normal, usar função existente no projeto ou `Intl.DateTimeFormat`, preservando `dd/MM/yyyy` quando aplicável.

## 21) Versionamento de funções ajustadas

Criar função com sufixo sequencial apenas quando houver risco real de regressão, dependência externa ou compatibilidade temporária.

Exemplo:

```text
euvouaroma()
euvouaroma_v1()
euvouaroma_v2()
```

Quando a alteração for interna, segura e sem contrato externo, é permitido ajustar a função existente.

Ao criar nova versão:

- documentar porque a antiga permanece;
- indicar onde a nova é usada;
- evitar acumular código morto indefinidamente.

## 22) PowerShell

Quando criar script PowerShell para alterar o projeto, o bloco deve ser completo e pronto para copiar e colar.

O script deve:

- começar por `cd C:\workspace\AppVerboBraga`;
- validar a pasta `appverbo`;
- definir `$ErrorActionPreference = "Stop"`;
- criar backup antes de alterar ficheiros;
- validar conteúdo depois;
- executar validações aplicáveis;
- mostrar `git diff`;
- executar `git diff --check`;
- mostrar `git status`;
- reiniciar Docker quando aplicável;
- executar teste HTTP quando a aplicação web for afetada;
- mostrar logs recentes quando a aplicação web for afetada.

Início obrigatório:

```powershell
cd C:\workspace\AppVerboBraga
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\appverbo")) {
    throw "Pasta appverbo não encontrada. Confirme que está em C:\workspace\AppVerboBraga."
}
```

Não usar `//` em PowerShell.

## 23) Validações obrigatórias

Para Python alterado:

```bash
docker compose exec web python -m py_compile appverbo/<ficheiro>.py
```

Para JavaScript alterado:

```bash
node --check static/js/<ficheiro>.js
node --check static/js/modules/<ficheiro>.js
```

Para migrations/models/banco:

```bash
docker compose exec web python -m alembic current
docker compose exec web python -m alembic heads
docker compose exec web python -m alembic check
docker compose exec web python -m alembic upgrade head
```

Para whitespace e conflitos:

```bash
git diff --check
```

Para estado final:

```bash
git status
```

Para logs:

```bash
docker compose logs --tail=100 web
```

## 24) Quando analisar um pedido antes de implementar

Se o utilizador pedir para criar, corrigir ou alterar algo, responder primeiro com a definição entendida.

Exemplo:

```text
Definição entendida:
Criar uma nova aba administrativa com formulário superior, lista paginada inferior, cards separados para ativos/inativos, validação backend e assets sem mojibake.
```

Depois listar regras aplicáveis.

Exemplo:

```text
Regras aplicáveis:
- listas configuráveis com bloco superior e lista inferior;
- HTML define estrutura, CSS layout, JS comportamento;
- JS em static/js/modules;
- node --check para JS;
- cache buster se alterar assets usados por new_user.html;
- git diff --check no final.
```

Só depois propor implementação.

## 25) Quando rever código ou diff

Ao rever código, procurar obrigatoriamente:

- violações do `AGENTS.md`;
- alterações fora de escopo;
- mojibake;
- falta de migration;
- falta de validação backend;
- módulo pago protegido só no frontend;
- JavaScript criando estrutura que deveria estar no HTML;
- CSS sendo manipulado por JS sem necessidade;
- duplicação de scripts ou assets;
- cache buster ausente;
- `node --check` ausente;
- `py_compile` ausente;
- `git diff --check` ausente;
- Docker/Alembic executado fora do container;
- risco de quebrar compatibilidade temporária.

Formato recomendado:

```text
## Conformidade

Aprovado / Parcial / Reprovado

## Violações encontradas

1. ...
2. ...

## Correções necessárias

1. ...
2. ...

## Validações obrigatórias

...
```

Ao concluir uma revisão estrutural do AppVerboBraga, usar sempre um veredito claro:

```text
Veredito: conforme
Veredito: parcialmente conforme / em migração
Veredito: não conforme
```

Quando houver componentes legados ainda em uso, classificar como `parcialmente conforme / em migração`, não como 100% conforme.

Sempre separar:

- o que já está conforme;
- o que está em migração;
- o que precisa ser corrigido;
- quais validações locais ainda precisam ser executadas.

## 25.1) Evidências e referências

Quando a análise usar ficheiros reais do repositório, diffs, conectores ou documentos enviados, citar ou mencionar claramente os ficheiros verificados.

Não afirmar que algo existe no projeto sem indicar a origem quando a ferramenta permitir citar.

Exemplo:

```text
Verificado em:
- appverbo/admin_subprocesses/registry.py
- templates/new_user.html
- docker-compose.yml
- alembic.ini
```

Quando citações formais estiverem disponíveis no ambiente, usá-las para sustentar afirmações importantes.

## 26) Quando gerar código

Quando gerar código para o utilizador:

- respeitar a preferência de entregar ficheiro/código completo quando houver alteração;
- não entregar apenas fragmentos se o utilizador pediu correção completa;
- preservar nomes, rotas e contratos existentes;
- localizar colunas por nome, nunca por posição fixa;
- separar HTML, CSS e JavaScript conforme responsabilidade;
- evitar lógica extensa em `new_user.js`;
- criar managers em `static/js/modules` quando aplicável;
- incluir validações finais;
- incluir comandos necessários.

## 27) Checklist final padrão

Antes de considerar qualquer alteração como pronta, validar:

```text
[ ] aplicação sobe no Docker
[ ] logs recentes sem traceback
[ ] texto sem mojibake
[ ] migrations sincronizadas
[ ] menu lateral não quebrou
[ ] módulos pagos protegidos no backend
[ ] JavaScript alterado passa em node --check
[ ] Python alterado passa em py_compile
[ ] git diff --check sem erros
[ ] git status mostra apenas alterações esperadas
[ ] rota HTTP estável não retorna erro 500 quando a aplicação web for afetada
```

## 28) Frases de controlo para o agente

Usar estas regras como travões internos:

```text
Não escrever código antes de mapear o AGENTS.md.
Não criar estrutura visual por JavaScript se pertence ao HTML/CSS.
Não alterar banco sem migration.
Não validar Alembic fora do Docker.
Não esconder módulo pago apenas no frontend.
Não deixar mojibake.
Não remover legado sem confirmar dependência.
Não criar menus fixos diretamente no HTML.
Não usar coluna por posição fixa.
Não finalizar sem git diff --check.
```

## 29) Resultado esperado da Skill

A Skill deve fazer com que qualquer resposta sobre AppVerboBraga seja:

- orientada pelo `AGENTS.md`;
- estruturada antes de implementar;
- segura contra regressões;
- coerente com Docker-first;
- cuidadosa com migrations;
- cuidadosa com UTF-8/mojibake;
- consistente em HTML/CSS/JS;
- compatível com a arquitetura modular;
- clara nas validações finais.

O objetivo não é apenas revisar depois.

O objetivo é impedir que a implementação nasça fora do padrão.
ç
