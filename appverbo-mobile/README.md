# AppVerbo Mobile (React Native)

Este diretorio contem o frontend APP em React Native (Expo), separado do frontend WEB existente.

## Objetivo

- `frontend WEB`: continua no projeto atual (templates + static)
- `frontend APP`: novo projeto em `appverbo-mobile`
- Ambos usam o mesmo backend Python do AppVerboBraga

## Requisitos

- Node.js 20+
- npm 10+
- Expo Go no dispositivo (opcional para testes)

## Configuracao

1. Copiar variaveis de ambiente:

```bash
cp .env.example .env
```

2. Ajustar `EXPO_PUBLIC_API_BASE_URL` no `.env`.

Exemplos:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator / Expo web: `http://localhost:8000`
- Dispositivo fisico: `http://<IP_DA_MAQUINA>:8000`

## Execucao

```bash
npm install
npm run start
```

Comandos uteis:

```bash
npm run android
npm run ios
npm run web
npm run start:lan
npm run start:tunnel
npm run typecheck
```

## Simular no telemovel

1. Instalar a app Expo Go no Android/iOS.
2. No projeto `appverbo-mobile`, arrancar:

```bash
npm run start:tunnel
```

3. Abrir Expo Go e ler o QR code mostrado no terminal.

## Estrutura inicial

```text
appverbo-mobile/
  App.tsx
  src/
    config/api.ts
    services/api.ts
    services/auth.ts
    services/home.ts
    services/modules.ts
```

`src/config/api.ts` resolve a base da API compartilhada.
`src/services/api.ts` contem um ping simples de conectividade.
`src/services/auth.ts` contem login/me/logout para sessao no backend partilhado.
`src/services/home.ts` carrega o resumo de home (dashboard, menus e perfil) para o app.
`src/services/modules.ts` carrega dados por modulo (`/api/mobile/modules` e `/api/mobile/modules/{module_key}`).

## Navegacao atual

- Rota raiz autenticada com abas internas: `Resumo`, `Menus`, `Perfil`
- Fluxo em stack para detalhe de menu (`Menus -> Detalhe`)
- Fonte de dados da navegacao: `home.menu_items` devolvido pelo backend
- No detalhe, o app classifica o menu por `menu_key` (`home`, `perfil`, `admin`, `generico`) para mostrar contexto nativo
- Cada detalhe de menu oferece `Abrir no WEB`, abrindo o `web_path` no frontend WEB com o mesmo backend/sessao
- Menus de modulo com rota nativa dedicada: `funcionarios`, `financeiro`, `tesouraria`, `relatorios`, `eventos`, `escalas`, `cursos`

## Endpoints usados no backend

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/mobile/home`
- `GET /api/mobile/modules`
- `GET /api/mobile/modules/{module_key}`
