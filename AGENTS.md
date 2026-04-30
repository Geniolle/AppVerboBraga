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