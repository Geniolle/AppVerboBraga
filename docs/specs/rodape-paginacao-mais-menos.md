# Rodapé de paginação "Mais / Menos" (regra global)

Padrão único para toda tabela ou lista paginada do sistema (cartões de Menu, Sessões,
Departamentos, Funções, Utilizador, Entidade, listas de processo como Agenda, Ensaio e Músicas,
e os editores de configuração de processo).

Toda nova lista paginada **tem de** usar este rodapé. Não criar paginação própria
(setas, "anterior/seguinte", números de página).

## 1. Como ligar numa tabela nova

Opção A — tabela administrativa ou lista de processo (controlador partilhado):

```html
<table id="minha-lista-table"> ... <tbody> ... </tbody></table>
<div id="minha-lista-limiter" class="table-limiter"></div>
```

- O rodapé é um elemento `.table-limiter` (ou `.admin-status-table-footer-v1`).
- A tabela associada é encontrada por: `data-appgenesis-table-id` no rodapé; ou pelo id do
  rodapé `<prefixo>-limiter` → tabela `<prefixo>-table`; ou a tabela irmã/anterior.
- Depois de criar ou redesenhar as linhas, chamar `enhanceProcessShellTables(cartão)`
  (em `static/js/new_user.js`). Isto cria o controlador na primeira vez e faz `reset`
  (recarrega as linhas) nas seguintes.
- **Nunca** apagar o conteúdo do rodapé (`innerHTML = ""`): o controlador guarda
  referências ao seletor, aos botões e ao contador. Para esconder, usar só `style.display`.

Opção B — editores de itens configuráveis (Campos, Listas, Quantidade, Subsequentes,
Campos adicionais): macro `render_configurable_items_pagination_footer`
(`templates/macros/configurable_items_pagination.html`) com o gestor
`static/js/modules/configurable_items_manager_core_v1.js`. Segue as mesmas regras abaixo.

## 2. Estrutura (gerada pelo JS)

```html
<div class="table-limiter appgenesis-load-more-footer-v1">
  <div class="appgenesis-load-more-page-size-v1">
    <select>5 · 10 · 20 · 50</select>
    <span>entradas por página</span>
  </div>
  <div class="appgenesis-load-more-status-v1">
    <button class="appgenesis-load-more-btn-v1">Mais</button>
    <span class="appgenesis-load-more-counter-v1">[ 5 / 8 ]</span>
  </div>
  <div class="appgenesis-load-more-less-v1">
    <button class="appgenesis-load-more-btn-v1">Menos</button>
  </div>
</div>
```

## 3. Medidas e estilo (desktop)

| Elemento | Especificação |
|---|---|
| Rodapé | altura mínima 44px, largura 100% do cartão, `margin-top: 12px`, padding `12px 12px 0 0`, sem linha superior |
| Seletor | 72 × 30px, fonte 13px, padding `2px 24px 2px 12px`, encostado à esquerda |
| Espaço seletor → texto | 6px |
| "entradas por página" | fonte 12px, cor `#33425c`, sem quebra de linha |
| Bloco "Mais" + contador | largura mínima 96px, no centro exato do rodapé (`left: 50%` + `translate(-50%, -50%)`); "Mais" em cima, contador embaixo, 2px entre eles |
| "Mais", "Menos" e contador | fonte 12px, negrito, cor `#0a6ed1`, sem borda nem fundo; hover `#085caf` com sublinhado |
| "Menos" | mesmo estilo, encostado à direita |

Celular (até 720px): o rodapé vira coluna, seletor em cima e "Mais"/contador centralizado
embaixo, 8px entre eles; o bloco central deixa de ser absoluto.

Fonte do estilo: `static/css/modules/process_shell_runtime_v1.css`, blocos
`APPGENESIS_LOAD_MORE_*`. Não sobrepor estes estilos por cartão.

## 4. Regras de funcionamento

| Regra | Comportamento |
|---|---|
| Tamanho de página (N) | valor do seletor; padrão 5; opções 5, 10, 20, 50 |
| Abertura | mostra as primeiras N linhas |
| Linhas contadas | `tbody tr`, exceto a linha "sem resultados" da pesquisa |
| Contador | `[ visíveis / total ]`; com pesquisa, o total é o filtrado |
| "Mais" | soma N linhas, sem passar do total; some quando todas estão visíveis |
| "Menos" | volta ao bloco anterior: `max(N, floor((visíveis - 1) / N) * N)`; só aparece com mais de N linhas visíveis |
| Trocar o seletor | reinicia: mostra só as primeiras N linhas |
| Pesquisa | filtra e reinicia a contagem (N do resultado) |
| Lista vazia | o rodapé inteiro fica oculto |
| Acessibilidade | botões com `aria-controls` (id da tabela) e `aria-disabled` quando não se aplicam |

## 5. Onde está no código

- Controlador partilhado: `createLoadMoreTableController` e `enhanceLoadMoreTables` em
  `static/js/modules/process_shell_runtime_v1.js` (padrões nas constantes `DEFAULT_PAGE_SIZE`
  e `DEFAULT_PAGE_SIZE_OPTIONS`).
- Ligação nas telas: `enhanceProcessShellTables` e `setupTableLimiter` em `static/js/new_user.js`.
- Listas de processo (Agenda, Ensaio, Músicas...): `renderDynamicProcessListTableCardV1` em
  `static/js/new_user.js` mostra o rodapé `#dynamic-process-active-limiter` /
  `#dynamic-process-inactive-limiter` e chama `enhanceProcessShellTables`.
- Editores de configuração: `renderPagination_v1` em
  `static/js/modules/configurable_items_manager_core_v1.js`.
