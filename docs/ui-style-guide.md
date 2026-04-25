# UI Style Guide

Este guia define o padrao visual minimo para campos e botoes no AppVerboBraga.

## Fonte da verdade

- Tokens globais: `static/css/ui-standards.css`
- Implementacao por pagina:
  - `static/css/new_user.css`
  - `static/css/login.css`
  - `static/css/user_invite_accept.css`

## Campos (input/select/textarea)

- Altura padrao de controle: `42px`
- Padding horizontal: `12px`
- Border radius: `6px`
- Tamanho de fonte: `14px`
- Borda padrao: `#cfd5df`
- Focus:
  - cor da borda `#8fb4e7`
  - ring `0 0 0 3px rgba(47, 108, 229, 0.14)`

Tokens usados:

- `--ui-control-height`
- `--ui-control-padding-x`
- `--ui-control-border-radius`
- `--ui-control-border-color`
- `--ui-control-focus-border`
- `--ui-control-focus-ring`

## Botoes padrao de acao

- Border radius: `6px`
- Fonte: `14px`
- Peso: `600`
- Padding horizontal: `15px`
- Line-height: `1.2`

Tokens usados:

- `--ui-button-padding-x`
- `--ui-button-border-radius`
- `--ui-button-font-size`
- `--ui-button-font-weight`
- `--ui-button-line-height`

## Excecoes permitidas

- Botoes iconicos compactos (`.table-icon-btn`, paginacao, remover item) podem manter tamanho proprio.
- Componentes de navegacao (topbar/menu) nao devem herdar estilo de botoes de formulario.

## Regra de manutencao

Quando criar nova tela:

1. Reutilizar os tokens de `ui-standards.css`.
2. Evitar valores hardcoded para tamanho de campo e botao.
3. Se precisar de variacao, criar classe derivada mantendo os tokens base.
