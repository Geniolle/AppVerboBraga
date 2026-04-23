# AppVerboBraga

## Docker

Subir app web + PostgreSQL:

```bash
docker compose up -d --build
```

Ver estado:

```bash
docker compose ps
docker compose logs web --tail=100
```

Criar admin inicial:

```bash
docker compose exec web python bootstrap_admin.py --name "Admin Sistema" --phone "+351910000099" --email "admin@appverbo.local" --password "NovaSenhaForte123" --entity "Igreja Braga"
```

Abrir no browser:

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/login/admin` (login do ADMIN com metricas)

Parar containers:

```bash
docker compose down
```

Parar e remover dados do PostgreSQL:

```bash
docker compose down -v
```

## Notas

- Em `docker-compose.yml`, altere `APP_SECRET_KEY` e `POSTGRES_PASSWORD` para valores fortes.
- Se a porta `5432` estiver ocupada na maquina, mude o mapeamento de portas no servico `db`.

## Login Por Provedores

A tela de login suporta autenticacao externa por:

- Google
- Microsoft (Hotmail/Outlook)
- GitHub

Configure no `.env` (ou variaveis de ambiente no deploy):

```bash
ADMIN_LOGIN_EMAIL=admin@appverbo.local
ADMIN_PROFILE_NAMES=admin,administrador
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
APP_PUBLIC_URL=http://127.0.0.1:8000
USER_INVITE_TTL_HOURS=72
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=AppVerboBraga
SMTP_USE_TLS=true
```

Redirect URIs para configurar em cada provedor (ambiente local):

- `http://127.0.0.1:8000/oauth/callback/google`
- `http://127.0.0.1:8000/oauth/callback/microsoft`
- `http://127.0.0.1:8000/oauth/callback/github`

## Verificação WhatsApp

Para validação automática do número de telefone via WhatsApp Cloud API, configure no `.env`:

```bash
WHATSAPP_GRAPH_API_VERSION=v22.0
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_TEMPLATE_NAME=
WHATSAPP_TEMPLATE_LANGUAGE=pt_PT
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
```

Webhook da aplicação:

- Verificação (GET): `http://127.0.0.1:8000/webhooks/whatsapp`
- Eventos de estado (POST): `http://127.0.0.1:8000/webhooks/whatsapp`

No perfil do utilizador existe o botão `Verificar no WhatsApp`; o estado passa para pendente e é atualizado automaticamente quando o webhook recebe `delivered/read/failed`.

## Convite De Utilizador

No menu administrativo, o registo de utilizador passa a funcionar por convite:

- O administrador cria o utilizador sem palavra-passe.
- A conta fica em estado `pending`.
- O sistema envia email com link de ativacao para o utilizador concluir os dados e definir palavra-passe.

Sem configuracao SMTP (`SMTP_HOST` e `SMTP_FROM_EMAIL`), a conta sera criada mas o envio do convite por email falhara.

## App de Validacao

Existe um validador de fluxos web em:

- `validate_web_app.py`

Executar (usa signup automatico para criar conta de teste):

```bash
python validate_web_app.py --base-url http://127.0.0.1:8000
```

Executar com utilizador existente:

```bash
python validate_web_app.py --base-url http://127.0.0.1:8000 --email utilizador@dominio.com --password "Senha"
```

Se quiser falhar quando a verificação WhatsApp não estiver configurada:

```bash
python validate_web_app.py --base-url http://127.0.0.1:8000 --expect-whatsapp-config
```
