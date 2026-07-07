# Especificação de Desenvolvimento — Redesign moderno da tela Estruturas

Data: 2026-07-07  
Projeto: AppGenesis / AppVerboBraga  
Repositório: `Geniolle/AppVerboBraga`  
Escopo principal: `Estruturas > Sessões`

---

## 1. Objetivo

Modernizar o layout da tela **Estruturas**, mantendo o comportamento atual e aplicando um visual mais simples, limpo, funcional e alinhado com boas práticas atuais de sistemas SaaS administrativos.

A alteração deve ser prioritariamente visual, sem mudar regra de negócio, endpoints, permissões, multi-entidade ou comportamento de gravação.

O resultado esperado é uma interface semelhante ao mockup aprovado, com:

- sidebar mais elegante;
- topbar mais discreta;
- área principal com hierarquia visual clara;
- título `Estruturas` com subtítulo;
- abas modernas `Sessões` e `Menu`;
- botão primário `Criar sessão` destacado;
- cards de listagem com cantos arredondados, sombras suaves e pesquisa integrada;
- tabelas limpas;
- badges modernos para `Ativo` e `Inativo`;
- menu de ações por linha em estilo três pontos/kebab;
- paginação/limiter visualmente mais moderno;
- manutenção do padrão técnico atual do projeto.

---

## 2. Regras obrigatórias de implementação

1. Antes de alterar, analisar os ficheiros relacionados indicados nesta especificação.
2. Alterar somente o necessário.
3. Não reescrever ficheiros inteiros sem necessidade.
4. Preservar o comportamento atual de criação, edição, eliminação, ordenação, pesquisa, AJAX e retorno à lista.
5. Não alterar modelos, banco de dados ou migrations para esta tarefa.
6. Não misturar dados entre entidades.
7. Não transformar menus dinâmicos em HTML fixo.
8. Manter compatibilidade com web e futura aplicação mobile/responsiva.
9. Não usar PowerShell.
10. Não usar `Get-Content | Set-Content`, scripts `.ps1`, patches massivos ou scripts temporários para regravar ficheiros.
11. Manter UTF-8 e validar ausência de mojibake (`Ã`, `Â`, `�`, `??`).
12. Manter as marcações/blocos existentes sempre que possível.
13. Criar estilos novos em bloco versionado, com sufixo `V1`, para facilitar manutenção.
14. Preferir um CSS module novo para overrides visuais, evitando espalhar alterações por vários ficheiros.

---

## 3. Ficheiros consultados e contexto técnico atual

### 3.1. Regras locais

- `AGENTS.md`
  - Define o AppGenesis como aplicação SaaS modular para igrejas.
  - Obriga UTF-8, validação contra mojibake, Docker-first e arquitetura modular.
  - Define padrão obrigatório para listas configuráveis: editor superior + tabela/lista inferior + paginação.

### 3.2. Base e shell da página

- `templates/base.html`
  - Define HTML base, charset UTF-8, viewport e CSS global `ui-standards.css`.

- `templates/new_user.html`
  - Página principal do painel do utilizador.
  - Carrega os CSS/JS principais da tela.
  - Inclui `partials/new_user_topbar.html` e `partials/new_user_sidebar.html`.
  - Renderiza o shell do processo no bloco `#menu-tabs-card` com:
    - `#process-shell-header`
    - `#process-shell-title`
    - `#process-shell-actions`
    - `#submenu-items`
  - Renderiza subprocessos administrativos por macros:
    - `render_admin_subprocess_state(admin_subprocess_state)`
    - `render_admin_subprocess_state(auth_profile_subprocess_state)`
    - `render_admin_subprocess_state(auth_objeto_subprocess_state)`
    - `render_admin_subprocess_form(admin_subprocess_menu_state)`

### 3.3. Topbar e sidebar

- `templates/partials/new_user_topbar.html`
  - Renderiza `.topbar`.
  - Contém botão de colapso da sidebar.
  - Contém marca da entidade atual.
  - Contém menu do utilizador/avatar.
  - Carrega `sidebar_collapse_v1.css` e `sidebar_collapse_v1.js`.

- `templates/partials/new_user_sidebar.html`
  - Renderiza `.sidebar`.
  - O menu é dinâmico, usando `sidebar_menu_settings`, `visible_sidebar_menu_keys` e `sidebar_section_options`.
  - Usa macro `sidebar_icon(setting.key)`.
  - Contém footer com branding `𝓖ênesis` e `Chapter v1.01`.

### 3.4. Configuração das sessões

- `appgenesis/admin_subprocesses/registry.py`
  - Define `SIDEBAR_SECTION_FIELDS`:
    - `label` / `Nome da sessão`
    - `visibility_scope_mode` / `Sistema`
    - `status` / `Estado`
  - Define `DEFAULT_COLUMNS`:
    - `NOME`
    - `SISTEMA`
    - `ESTADO`
  - Define `SESSOES_CONFIG`:
    - `key="sessoes"`
    - `create_title="Criar sessão"`
    - `active_title="Sessões ativas"`
    - `inactive_title="Sessões inativas"`
    - endpoints atuais de save, move e delete
    - IDs atuais dos cards/tabelas gerados automaticamente quando não configurados explicitamente.

### 3.5. Macros de renderização dos subprocessos

- `templates/macros/admin_subprocess.html`
  - `render_admin_subprocess_form(state)` renderiza o card/formulário de criação/edição.
  - `render_admin_subprocess_table(state, rows, title, status_value)` renderiza os cards das tabelas ativas/inativas.
  - Cada card de tabela tem:
    - `.card`
    - `.admin-subprocess-card-v1`
    - `.admin-subprocess-table-card-v1`
    - `data-admin-subprocess`
    - `data-admin-subprocess-role`
    - `data-admin-subprocess-status`
  - Cada tabela tem:
    - `.admin-subprocess-table-v1`
    - `.table-limiter`
    - colunas configuradas por `state.config.columns`
    - coluna `AÇÕES`
  - `render_admin_subprocess_row_actions` gera ações atuais: subir, descer, visualizar, editar e eliminar, conforme configuração.

### 3.6. CSS atual relevante

- `static/css/new_user.css`
  - Define variáveis atuais de tema (`--bg`, `--topbar`, `--sidebar-bg`, `--panel-bg`, etc.).
  - Define `.topbar`, `.layout`, `.sidebar`, `.menu-item`, `.content`, `.card` e estilos base.

- `static/css/modules/process_shell_runtime_v1.css`
  - Define visual do shell do processo.
  - Define cabeçalho dos cards pesquisáveis.
  - Define pesquisa por card (`.appgenesis-card-search-v1`).
  - Define limiter/load-more (`.appgenesis-load-more-footer-v1`).
  - Define menu de ações por linha (`.appgenesis-row-actions-*`).

- `static/css/modules/admin_subprocesses_v1.css`
  - Define card/formulário/tabela dos subprocessos.
  - Define colunas semânticas (`admin-col-main-v1`, `admin-col-system-v1`, `admin-col-status-v1`, `admin-col-actions-v1`).
  - Define badges ativos/inativos (`admin-subprocess-badge-active-v1`, `admin-subprocess-badge-inactive-v1`).
  - Define regras responsivas da tabela.

- `static/css/modules/sidebar_sections_layout_v1.css`
  - Contém estilos legados/específicos de sessões e blocos de criação.
  - Deve ser preservado, mas não deve receber a maior parte do redesign se um CSS module novo resolver.

### 3.7. JavaScript atual relevante

- `static/js/modules/process_shell_runtime_v1.js`
  - Cria/enriquece:
    - cabeçalho do processo;
    - pesquisa nos cards;
    - limiter/load-more;
    - menu de ações/kebab;
    - confirmação;
    - toast;
    - responsividade das tabelas.
  - Já possui `enhanceSearchableTableCards`, `enhanceLoadMoreTables` e `enhanceTableActionMenus`.

- `static/js/modules/admin_subprocesses_v1.js`
  - Inicializa ordenação, responsividade e AJAX de gravação das sessões.
  - Após salvar sessão via AJAX, recarrega/substitui os cards:
    - `admin-sidebar-sections-card`
    - `admin-sidebar-sections-card-active`
    - `admin-sidebar-sections-card-inactive`
  - Reaplica os enhancers do `AppGenesisProcessShell`.

### 3.8. Testes existentes importantes

- `tests/test_estruturas_menu_client_navigation.py`
  - Cobre navegação para `Estruturas > Menu` sem refresh.
  - Cobre card ativo/inativo após navegação por clique.
  - Cobre retorno do editor à lista ao cancelar/guardar.
  - Cobre uso do menu de ações/kebab.

- `tests/test_menu_settings.py`
  - Deve continuar válido, pois a tarefa não altera regra de configuração do menu.

---

## 4. Estratégia recomendada

Implementar como **redesign visual incremental**, sem mexer na regra de negócio.

A solução recomendada é criar um módulo CSS novo:

```text
static/css/modules/app_shell_modern_v1.css
```

E carregar esse ficheiro no final do bloco `head_extra` de `templates/new_user.html`, depois dos CSS já existentes, para servir como camada visual moderna.

Isto evita mexer diretamente em muitos blocos antigos e reduz risco de impacto lateral.

Alterações estruturais devem ser pequenas e localizadas:

1. `templates/new_user.html`
   - carregar o novo CSS module;
   - opcionalmente envolver o título em um bloco com subtítulo, preservando IDs existentes;
   - não alterar as macros de dados nem condições de renderização.

2. `templates/partials/new_user_sidebar.html`
   - adicionar um pequeno cabeçalho visual no topo da sidebar, usando dados já disponíveis da entidade;
   - manter o menu dinâmico atual.

3. `templates/partials/new_user_topbar.html`
   - manter dropdown, avatar e botão de colapso;
   - não remover funcionalidades;
   - se necessário, apenas ajustar classes/estrutura mínima para o CSS conseguir posicionar melhor.

4. `static/css/modules/app_shell_modern_v1.css`
   - concentrar o redesign visual.

5. Só alterar JS se for estritamente necessário.
   - A pesquisa, limiter e menu de ações já existem.
   - Preferir estilizar o comportamento atual em vez de trocar a lógica de paginação.

---

## 5. Plano detalhado de implementação

### Fase 0 — Pré-validação

Antes de alterar:

1. Confirmar branch atual.
2. Confirmar que não há alterações locais pendentes.
3. Rever novamente:
   - `templates/new_user.html`
   - `templates/partials/new_user_topbar.html`
   - `templates/partials/new_user_sidebar.html`
   - `templates/macros/admin_subprocess.html`
   - `static/css/new_user.css`
   - `static/css/modules/process_shell_runtime_v1.css`
   - `static/css/modules/admin_subprocesses_v1.css`
   - `static/js/modules/process_shell_runtime_v1.js`
   - `static/js/modules/admin_subprocesses_v1.js`

### Fase 1 — Criar CSS module moderno

Criar:

```text
static/css/modules/app_shell_modern_v1.css
```

Com blocos versionados:

```css
/* ###################################################################################
   APPGENESIS_APP_SHELL_MODERN_V1_START
################################################################################### */
...
/* APPGENESIS_APP_SHELL_MODERN_V1_END */
```

O CSS deve conter:

#### 1. Tokens visuais

Definir tokens locais usando `:root`, sem remover os existentes:

```css
:root {
  --app-shell-bg-v1: #f5f7fb;
  --app-shell-surface-v1: #ffffff;
  --app-shell-border-v1: #e3e8f2;
  --app-shell-text-v1: #0f172a;
  --app-shell-muted-v1: #64748b;
  --app-shell-primary-v1: #0f5fd7;
  --app-shell-primary-hover-v1: #0b4fb4;
  --app-shell-radius-card-v1: 16px;
  --app-shell-radius-control-v1: 10px;
  --app-shell-shadow-card-v1: 0 12px 30px rgba(15, 23, 42, 0.06);
}
```

#### 2. Layout geral

Objetivo visual:

- fundo cinza muito suave;
- conteúdo com espaçamento maior;
- largura total sem parecer “colado”;
- cards mais modernos.

Aplicar em:

- `body`
- `.layout`
- `.content`
- `.container`
- `.card`

Atenção:

- não quebrar `.layout` existente;
- respeitar `appgenesis-sidebar-collapsed`.

#### 3. Sidebar

Objetivo visual:

- sidebar branca;
- itens com cantos arredondados;
- item ativo azul suave;
- secções com labels menores;
- footer `Gênesis` mais refinado.

Aplicar em:

- `.sidebar`
- `.menu-section`
- `.menu-list`
- `.menu-item`
- `.menu-item.active`
- `.menu-icon`
- `.menu-label`
- `.sidebar-brand-footer`
- `.brand-link`
- `.logo`
- `.version`

Adicionar no HTML da sidebar um cabeçalho opcional:

```html
<div class="sidebar-product-header-v1">
  <span class="sidebar-product-mark-v1">...</span>
  <span class="sidebar-product-name-v1">...</span>
</div>
```

Usar preferencialmente os dados já disponíveis:

- `user_personal_data.primary_entity_logo_url`
- `user_personal_data.primary_entity_name`
- fallback textual seguro.

Não fixar manualmente `Deixa Estar Tech` se já existe dado dinâmico.

#### 4. Topbar

Objetivo visual:

- topbar discreta, clara e moderna;
- avatar/menu do utilizador preservado;
- botão de colapso preservado;
- evitar inventar notificações sem backend.

Aplicar em:

- `.topbar`
- `.topbar-left`
- `.topbar-right`
- `.brand`
- `.brand-mark`
- `.brand-name`
- `.user-menu-trigger`
- `.avatar-img`
- `.user-dropdown`

Atenção:

- não remover dropdown;
- não quebrar `sidebar_collapse_v1.js`.

#### 5. Shell do processo

No mockup, a área de `Estruturas` tem:

- breadcrumb discreto;
- título grande;
- subtítulo;
- tabs modernas;
- botão `Criar sessão` alinhado à direita.

Implementar com baixo risco:

- Preservar `#process-shell-title`.
- Preservar `#process-shell-actions`.
- Preservar `#submenu-items`.
- Se adicionar subtítulo, usar um elemento novo:

```html
<p id="process-shell-subtitle" class="process-shell-subtitle-v1">
  Gerencie as sessões e a estrutura do sistema.
</p>
```

Somente mostrar esse subtítulo quando `initial_menu == 'sessoes'` ou quando a tela for o contexto de Estruturas.

Evitar alterar o JS do título.

#### 6. Botão `Criar sessão`

O botão já é gerado pela macro através de `state.config.create_title`.

O CSS deve transformar o botão atual em visual primário moderno:

- azul forte;
- cantos arredondados;
- altura consistente;
- ícone `+` pode ser via CSS `::before`, sem alterar backend.

Aplicar a:

- `.admin-subprocess-create-collapse-v1 > summary`
- `.appgenesis-process-action-toggle-v1`

Garantir que, ao abrir o details, o comportamento atual permanece igual.

#### 7. Cards `Sessões ativas` e `Sessões inativas`

Aplicar visual moderno nos cards gerados por macro:

- `.admin-subprocess-table-card-v1`
- `[data-admin-subprocess='sessoes'][data-admin-subprocess-role='active-table']`
- `[data-admin-subprocess='sessoes'][data-admin-subprocess-role='inactive-table']`

Usar `data-admin-subprocess-status` para colocar ponto de estado no título via CSS:

```css
.admin-subprocess-table-card-v1[data-admin-subprocess-status="ativo"] h2::before { ...verde... }
.admin-subprocess-table-card-v1[data-admin-subprocess-status="inativo"] h2::before { ...vermelho... }
```

Evitar alterar macro só para adicionar ícones se CSS resolver.

#### 8. Cabeçalho dos cards e pesquisa

O JS atual já cria `.appgenesis-card-header-v1` e `.appgenesis-card-search-v1`.

Apenas ajustar CSS:

- pesquisa com ícone, border suave, foco azul;
- largura responsiva;
- alinhamento ao topo do card;
- em mobile, pesquisa abaixo do título.

#### 9. Tabelas

Atualizar visual:

- header com fonte pequena e uppercase;
- linhas com altura confortável;
- hover leve;
- bordas subtis;
- colunas `SISTEMA`, `ESTADO`, `AÇÕES` alinhadas como hoje.

Aplicar a:

- `.admin-subprocess-table-v1`
- `.admin-subprocess-table-v1 th`
- `.admin-subprocess-table-v1 td`
- colunas semânticas já existentes.

Não alterar `AdminColumnConfig` sem necessidade.

#### 10. Badges

Atualizar badges existentes:

- `.admin-subprocess-badge-v1`
- `.admin-subprocess-badge-active-v1`
- `.admin-subprocess-badge-inactive-v1`

Visual esperado:

- verde suave para ativo;
- vermelho/rosa suave para inativo;
- padding horizontal confortável;
- texto semântico preservado.

#### 11. Menu de ações

O JS atual já transforma ações em menu.

Apenas ajustar CSS:

- trigger três pontos discreto;
- hover circular suave;
- popup com sombra, radius e itens legíveis;
- manter acessibilidade por teclado.

Aplicar a:

- `.appgenesis-row-actions-trigger-v1`
- `.appgenesis-row-actions-popup-v1`
- `.appgenesis-row-actions-item-v1`
- `.appgenesis-row-actions-icon-v1`
- `.appgenesis-row-actions-text-v1`

#### 12. Footer/limiter

O comportamento atual é `load more/load less` com contador `[ visíveis / total ]`.

Para esta fase, não trocar por paginação real se isso exigir lógica nova.

Ajustar visual para parecer mais moderno:

- seletor compacto à esquerda;
- contador central limpo;
- botões `Mais`/`Menos` discretos;
- texto `entradas por página` preservado.

Se for necessário implementar paginação real no futuro, criar tarefa separada, porque muda interação e testes.

#### 13. Responsivo/mobile

Adicionar media queries:

- até `1024px`: reduzir largura da sidebar se necessário;
- até `820px`: card header em coluna;
- até `720px`: tabela pode manter scroll/compactação atual;
- até `640px`: conteúdo com padding menor e cards sem excesso de sombra.

Não remover a lógica existente de responsividade das tabelas.

---

## 6. Ficheiros provavelmente modificados

Alterações recomendadas:

1. `templates/new_user.html`
   - adicionar link para `app_shell_modern_v1.css` no final do `head_extra`;
   - opcional: adicionar subtítulo no process shell.

2. `templates/partials/new_user_sidebar.html`
   - adicionar cabeçalho visual da sidebar;
   - manter renderização dinâmica do menu.

3. `templates/partials/new_user_topbar.html`
   - pequenas classes/estrutura se necessário;
   - preservar botão de colapso, brand e user dropdown.

4. `static/css/modules/app_shell_modern_v1.css`
   - novo ficheiro principal do redesign.

Possíveis ajustes mínimos, apenas se o novo CSS não for suficiente:

5. `static/css/modules/process_shell_runtime_v1.css`
   - evitar se possível;
   - usar apenas para conflitos específicos do shell que não sejam resolvidos pelo CSS novo.

6. `static/css/modules/admin_subprocesses_v1.css`
   - evitar se possível;
   - usar apenas se os estilos base impedirem overrides seguros.

7. `static/js/modules/process_shell_runtime_v1.js`
   - não alterar para esta tarefa, salvo se o menu de ações/pesquisa/limiter tiver bug visual impossível de resolver por CSS.

8. `static/js/modules/admin_subprocesses_v1.js`
   - não alterar, pois já reaplica enhancers após AJAX.

---

## 7. Ficheiros que não devem ser alterados nesta tarefa

Não alterar, salvo descoberta de bug real relacionado ao layout:

- models;
- migrations Alembic;
- repositories;
- endpoints de save/move/delete;
- permissões;
- regras de visibilidade por entidade;
- `appgenesis/admin_subprocesses/registry.py`, exceto se for estritamente necessário adicionar metadado visual sem impacto de regra.

---

## 8. Critérios de aceite

### Visual

1. A tela `Estruturas > Sessões` deve parecer moderna, limpa e consistente com o mockup aprovado.
2. Sidebar deve ter visual mais refinado, com item ativo evidente.
3. Topbar deve ficar mais discreta e profissional.
4. Título `Estruturas` deve ter hierarquia clara.
5. Abas `Sessões` e `Menu` devem parecer tabs modernas.
6. Botão `Criar sessão` deve ser o CTA principal.
7. Cards `Sessões ativas` e `Sessões inativas` devem ficar em cards brancos, arredondados, com sombra suave.
8. Pesquisa deve aparecer no canto direito do cabeçalho do card em desktop.
9. Badges `Ativo` e `Inativo` devem ser claros e suaves.
10. Menu de ações deve continuar em três pontos/kebab.

### Funcional

1. Criar sessão continua a abrir o formulário e guardar como antes.
2. Editar sessão continua a funcionar.
3. Subir/descer sessão continua a funcionar.
4. Eliminar sessão inativa continua a pedir confirmação quando aplicável.
5. Pesquisa continua a filtrar linhas.
6. Limiter/load-more continua a funcionar.
7. Navegação entre `Sessões` e `Menu` continua sem refresh manual.
8. Após guardar via AJAX, os cards são atualizados e permanecem com o visual novo.
9. Cancelar/guardar no editor de processo continua a devolver à lista correta.
10. Menu lateral continua dinâmico e respeitando permissões/visibilidade.

### Técnico

1. Sem erros no console relevantes ao carregar a página.
2. Sem traceback nos logs.
3. Sem mojibake.
4. Sem alteração de schema/banco.
5. Testes existentes devem passar.

---

## 9. Comandos de validação sugeridos

Usar Docker quando a aplicação precisar subir:

```bash
docker compose up -d --build
```

Validação de testes principais:

```bash
docker compose exec web python -m pytest tests/test_estruturas_menu_client_navigation.py
```

Validação complementar:

```bash
docker compose exec web python -m pytest tests/test_menu_settings.py
```

Validação de migrations, mesmo sem alteração de banco:

```bash
docker compose exec web python -m alembic check
```

Validação manual:

1. Abrir `/users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card`.
2. Confirmar visual de `Estruturas > Sessões`.
3. Pesquisar em `Sessões ativas`.
4. Abrir menu de ações de uma linha.
5. Clicar em `Criar sessão`.
6. Cancelar.
7. Navegar para aba `Menu`.
8. Voltar para `Sessões`.
9. Confirmar que não houve refresh manual necessário.
10. Testar em largura desktop e largura mobile.

---

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Quebrar navegação SPA entre abas | Não alterar JS de navegação; rodar `tests/test_estruturas_menu_client_navigation.py`. |
| Duplicar brand/topbar/sidebar | Se adicionar header na sidebar, esconder/ajustar brand antiga via CSS sem remover funcionalidade. |
| Impactar outros subprocessos administrativos | Escopar estilos críticos com `.admin-subprocess-*` e, quando necessário, `[data-admin-subprocess='sessoes']`. |
| Quebrar sidebar colapsável | Preservar IDs/classes de `sidebar-collapse-toggle` e `app-sidebar`. Testar colapso. |
| Trocar comportamento de paginação | Não implementar paginação real nesta fase; apenas melhorar visual do limiter atual. |
| Mojibake | Garantir UTF-8 e procurar `Ã`, `Â`, `�`, `??`. |

---

## 11. Prompt completo para o Codex

Copiar e colar no Codex:

```text
Quero implementar um redesign moderno, simples e funcional da tela Estruturas > Sessões no projeto AppGenesis/AppVerboBraga, mantendo o comportamento atual.

Antes de alterar, analise obrigatoriamente estes ficheiros:

- AGENTS.md
- templates/base.html
- templates/new_user.html
- templates/partials/new_user_topbar.html
- templates/partials/new_user_sidebar.html
- templates/macros/admin_subprocess.html
- appgenesis/admin_subprocesses/registry.py
- static/css/new_user.css
- static/css/modules/process_shell_runtime_v1.css
- static/css/modules/admin_subprocesses_v1.css
- static/css/modules/sidebar_sections_layout_v1.css
- static/js/modules/process_shell_runtime_v1.js
- static/js/modules/admin_subprocesses_v1.js
- tests/test_estruturas_menu_client_navigation.py

Objetivo visual:

Modernizar a tela de Estruturas com base no mockup aprovado:

- layout SaaS administrativo moderno;
- fundo cinza muito suave;
- cards brancos com cantos arredondados e sombra leve;
- sidebar limpa, elegante, com item ativo bem marcado;
- topbar discreta;
- título Estruturas com hierarquia clara e subtítulo curto;
- tabs Sessões/Menu modernas;
- botão Criar sessão como CTA principal azul;
- cards Sessões ativas e Sessões inativas com cabeçalho elegante;
- campo de pesquisa moderno em cada card;
- tabela limpa com linhas confortáveis;
- badge Ativo verde suave e Inativo vermelho suave;
- ações em menu de três pontos/kebab;
- limiter/footer visualmente mais refinado;
- boa responsividade desktop/mobile.

Restrições obrigatórias:

- Não usar PowerShell.
- Não usar Get-Content | Set-Content.
- Não usar scripts .ps1.
- Não fazer patch massivo.
- Não reescrever ficheiros inteiros sem necessidade.
- Não alterar regras de negócio.
- Não alterar banco, models ou migrations.
- Não alterar endpoints.
- Não alterar permissões ou multi-entidade.
- Não transformar menus dinâmicos em HTML fixo.
- Não remover código existente sem justificar.
- Manter UTF-8 e validar ausência de mojibake.

Implementação recomendada:

1. Criar um novo ficheiro CSS:

   static/css/modules/app_shell_modern_v1.css

   Concentre nele o redesign visual, com bloco versionado:

   /* ###################################################################################
      APPGENESIS_APP_SHELL_MODERN_V1_START
   ################################################################################### */
   ...
   /* APPGENESIS_APP_SHELL_MODERN_V1_END */

2. Em templates/new_user.html, adicionar o link desse CSS no final do block head_extra, depois dos CSS atuais, com cache busting novo, por exemplo:

   <link rel="stylesheet" href="/static/css/modules/app_shell_modern_v1.css?v=20260707-modern-shell-v1">

3. Melhorar o process shell preservando IDs existentes:

   - manter #process-shell-header;
   - manter #process-shell-title;
   - manter #process-shell-actions;
   - manter #submenu-items;
   - opcionalmente envolver o título em um bloco e adicionar:

     <p id="process-shell-subtitle" class="process-shell-subtitle-v1">Gerencie as sessões e a estrutura do sistema.</p>

   Mostrar esse subtítulo apenas no contexto de Estruturas/Sessões, sem quebrar outras telas.

4. Em templates/partials/new_user_sidebar.html, adicionar um cabeçalho visual pequeno no topo da sidebar, antes das secções, mantendo o menu dinâmico atual. Usar dados já existentes de user_personal_data:

   - primary_entity_logo_url, se existir;
   - primary_entity_name, se existir;
   - fallback seguro.

   Não fixar menus manualmente.

5. Em templates/partials/new_user_topbar.html, preservar:

   - #sidebar-collapse-toggle;
   - #user-menu;
   - #user-menu-trigger;
   - #user-dropdown;
   - avatar e dropdown.

   Fazer apenas ajustes mínimos de classe/estrutura se o CSS precisar.

6. No novo CSS, ajustar:

   - body, .layout, .content, .container;
   - .topbar e seus filhos;
   - .sidebar, .menu-section, .menu-item, .menu-item.active, .sidebar-brand-footer;
   - #menu-tabs-card.appgenesis-process-shell;
   - .process-shell-header, .process-shell-title, .process-shell-actions;
   - .menu-tabs e .submenu-item;
   - .admin-subprocess-form-card-v1;
   - .admin-subprocess-table-card-v1;
   - .admin-subprocess-table-v1 th/td;
   - .admin-subprocess-badge-v1, active e inactive;
   - .appgenesis-card-header-v1;
   - .appgenesis-card-search-v1;
   - .appgenesis-load-more-footer-v1;
   - .appgenesis-row-actions-trigger-v1 e popup.

7. Para os pontos verdes/vermelhos nos títulos dos cards, usar CSS baseado em:

   [data-admin-subprocess-status="ativo"]
   [data-admin-subprocess-status="inativo"]

8. Não alterar static/js/modules/process_shell_runtime_v1.js, salvo se for estritamente necessário. A pesquisa, o limiter e o menu de ações já existem.

9. Não alterar static/js/modules/admin_subprocesses_v1.js, salvo bug real. Ele já reaplica os enhancers depois do AJAX.

10. Garantir responsividade com media queries:

   - max-width 1024px;
   - max-width 820px;
   - max-width 720px;
   - max-width 640px.

11. Validar:

   docker compose exec web python -m pytest tests/test_estruturas_menu_client_navigation.py
   docker compose exec web python -m pytest tests/test_menu_settings.py
   docker compose exec web python -m alembic check

12. Validar manualmente:

   - abrir /users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card;
   - confirmar que Sessões ativas e Sessões inativas aparecem com visual novo;
   - testar pesquisa;
   - testar menu de ações;
   - testar Criar sessão e Cancelar;
   - navegar para aba Menu e voltar;
   - testar sidebar colapsável;
   - testar largura mobile.

No final, entregue um resumo objetivo com:

- ficheiros modificados;
- o que foi alterado;
- testes executados;
- pontos que não foram alterados por segurança.
```

---

## 12. Observação final

Esta especificação propõe uma implementação visual incremental. O comportamento atual de subprocessos administrativos já fornece a maioria dos recursos do mockup: cards, pesquisa, limiter, ações por linha, badges e atualização AJAX. A tarefa deve aproveitar essa base, melhorando principalmente CSS e pequenas estruturas de shell, sem trocar a lógica existente.
