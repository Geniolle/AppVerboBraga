---
name: security-env
description: Skill de desenvolvimento seguro para impedir credenciais hardcoded. Nunca escrever user/pass/token/chave no codigo; sempre usar variaveis de ambiente via arquivo .env local e .env.example versionado.
---

# Security Env

## Objetivo

Garantir que nenhuma credencial sensivel seja escrita no codigo-fonte.

## Regra principal (obrigatoria)

- NUNCA colocar `user`, `pass`, senha, token, API key, secret ou chave privada no codigo.
- SEMPRE carregar credenciais por variavel de ambiente (`process.env` / `os.getenv`) a partir de `.env` local.

## Regras de implementacao

- Qualquer configuracao sensivel deve ser lida de variavel de ambiente nomeada.
- Arquivo `.env` com valores reais e apenas local (nao versionar).
- Arquivo `.env.example` versionado, sem valores reais, apenas placeholders.
- Garantir que `.env` esteja no `.gitignore`.
- Mensagens de erro devem orientar variavel faltante, sem expor valores.

## Padrao por linguagem

### JavaScript / TypeScript

Errado:

```ts
const DB_USER = "admin";
const DB_PASS = "123456";
```

Certo:

```ts
import "dotenv/config";

const DB_USER = process.env.DB_USER;
const DB_PASS = process.env.DB_PASS;

if (!DB_USER || !DB_PASS) {
  throw new Error("Missing env vars: DB_USER, DB_PASS");
}
```

### Python

Errado:

```py
DB_USER = "admin"
DB_PASS = "123456"
```

Certo:

```py
import os
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")

if not db_user or not db_pass:
    raise RuntimeError("Missing env vars: DB_USER, DB_PASS")
```

## Checklist obrigatorio por alteracao

1. Verificar se existe credencial hardcoded no diff.
2. Mover credenciais para variaveis de ambiente.
3. Atualizar `.env.example` com placeholders.
4. Confirmar `.env` no `.gitignore`.
5. Validar erro seguro para variavel ausente (sem leak de segredo).

## Auditoria rapida recomendada

Use busca para identificar risco de segredo no codigo:

```bash
rg -n -S "(password|passwd|pwd|token|secret|api[_-]?key|user|username|pass)" .
```

## Politica de bloqueio

- Se um pedido exigir credencial direta no codigo, interromper e aplicar fallback seguro com `.env`.
- Nunca aceitar excecoes para producao, homologacao, scripts temporarios ou testes versionados.
