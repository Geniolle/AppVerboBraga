# Walkthrough de validação manual pós-refatoração

Este documento serve como evidência da validação funcional e visual manual realizada pós-merge no repositório.

## 1. Contexto

* **PR validado**: #22 — `Refactor AppGenesis process architecture`.
* **Issue relacionada**: #29.
* **Tipo de validação**: Feita em browser real interativo.
* **Resultado geral**: Nenhuma regressão funcional ou visual foi encontrada.

## 2. Ambiente

* **Branch validada**: `master` (pós-merge).
* **Infraestrutura**: Aplicação rodando em containers Docker (`appgenesis-web` e `appgenesis-db`).
* **Meio de validação**: Browser real interativo.
* **Utilizador autenticado**: `admin@appverbo.local` (perfil administrador).
* **Data/hora da validação**: 05/07/2026 às 21:00 (GMT+1).

## 3. Cenários validados

### 3.1. Login e Dashboard
* **Login**: Efetuado com sucesso via `/login`.
* **Dashboard / KPIs**: A tela inicial foi carregada corretamente, exibindo os dados consolidados do tenant e renderizando os gráficos estatísticos de entidades e utilizadores (via Chart.js).
* **Menu lateral e navegação**: A navegação entre os menus da sidebar funciona sem recarregamentos desnecessários e reflete as abas ativas.

### 3.2. Aba Entidade (Sistema > Estruturas > Entidade)
* **Criar**: A criação ocorreu no bloco superior de criação (bloco separado). Adicionada a entidade `Entidade de Teste` como `Ativa`.
* **Editar**: Editado o nome da entidade para `Entidade de Teste Editada` e guardado com sucesso.
* **Inativar**: Alterado o estado para `Inativa`. A entidade foi movida automaticamente para o card/bloco de inativos no rodapé da página.
* **Mover**: O isolamento visual funcionou perfeitamente.
* **Eliminar**: A exclusão física ocorreu através do botão de lixeira (🗑) visível no card inferior de inativos após confirmação da caixa de diálogo.

### 3.3. Aba Utilizador (Sistema > Estruturas > Utilizador)
* **Criar**: Criado o utilizador `Utilizador Teste` (`utilizador_teste@appverbo.local`) para a entidade `Deixa Estar Tech`. O registo apareceu no estado **Pendente** no card de inativos/pendentes.
* **Editar**: Edição do nome completo para `Utilizador Teste Editado` foi efetuada e gravada com sucesso.
* **Botão Cancelar**: Ao abrir a edição e clicar no botão **Cancelar**, o card recolheu-se limpando o estado sem recarregar a página.

### 3.4. Aba Sessões (Sistema > Estruturas > Sessões)
* **Criar divisão**: Criada a `Sessão de Teste` e ela foi adicionada como uma nova divisão na sidebar ativa.
* **Editar**: Modificada para `Sessão de Teste Editada` com sucesso.
* **Eliminar/Inativar**: A sessão foi inativada, movida para o card inferior e depois removida do sistema após a exclusão no card de inativos.
* **Persistência de abas e ausência de "piscar"**: Ao transitar para a aba **Menu** e retornar para a aba **Sessões**, os cards correspondentes reapareceram de forma síncrona sem falhas visuais.

### 3.5. Perfis de Autorização (Sistema > Perfil de autorização)
* **Navegar e CRUD**: Criação do perfil `Perfil de Teste`, edição para `Perfil de Teste Editado`, inativação (movido para inativos) e eliminação funcionaram perfeitamente.

### 3.6. Objetos de Autorização
* **Navegação**: A aba carregou e listou os objetos de autorização.

### 3.7. Campos Adicionais Dinâmicos (Tipo Lista)
Editamos o processo **Empresa** para validar o comportamento do editor de campos adicionais configuráveis do tipo Lista:
* **Fonte Manual**: O input de itens comma-separated foi exibido.
* **Fonte Automática**: Os seletores dinâmicos de Processo, Seção/Aba, Campo de origem e a flag de registos ativos foram exibidos.
* **Fonte Lista de outro campo (`field_list`)**: A seleção de campos dependentes funcionou de forma responsiva.
* **Prevenção de ciclos recursivos**: Validamos a lógica interna de `resolve_field_list_options_v1` em `appgenesis/services/profile.py`. A função realiza o controle de recursão via set de visited. Loops e referências circulares resolvem-se como uma lista vazia (`[]`), sem causar estouros de pilha ou exceções de runtime.

### 3.8. Validação Visual Geral e Layout
* O layout está consistente e respeita a hierarquia de grid.
* Cards de criação e cards de listagem de ativos e inativos estão bem delimitados e separados de acordo com as regras estabelecidas.
* Botões **Guardar** e **Cancelar** alinhados à esquerda, na ordem correta, com mesmas dimensões e paddings.

### 3.9. Isolamento de Entidade
* **Nota de limitação**: O isolamento de dados entre entidades não foi exaustivamente validado nesta tarefa de validação de merge, visto requerer cenários avançados de multi-tenant no banco de dados.

---

## 4. Resultado final

* A validação manual pós-refatoração foi concluída com sucesso.
* Nenhuma regressão foi encontrada.
* A issue #29 pode permanecer fechada como concluída.
* As próximas etapas e pendências continuam sob as issues #23, #24, #25, #26, #27 e #28.
