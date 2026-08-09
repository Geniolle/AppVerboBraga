# Produção Oracle — AppVerboBraga

## Objetivo

Preparar repositório AppVerboBraga para deploy inicial em Oracle Cloud com arquitetura separada dev/prod, secrets gerenciados corretamente, e documentação operacional completa.

## Estado Inicial

### Git
- Branch: `feature/production-preparation` (nova)
- Commit: `1228bb5e Atualização` (main)
- Status: Limpo (WIP da branch anterior foi stashed)

### Arquitetura Encontrada
- FastAPI + Uvicorn
- PostgreSQL 16
- Alembic migrations
- Multi-tenant (empresa/entidade)
- Package: `appverbo/` (não `appgenesis/`)
- OAuth (Google, Microsoft, GitHub)
- WhatsApp Cloud API
- SMTP email
- Google Drive integration (MT940)
- Scheduler (jobs)

### Docker Atual
- `docker-compose.yml`: dev com bind mount `./:/app`
- PostgreSQL exposto em `5432:5432` (PROBLEMA)
- Uvicorn na porta `8000:8000`
- db-init service para migrations
- Sem reverse proxy/Nginx
- Sem configuration prod separada

### Configuração Crítica Encontrada
- **PROBLEMA**: `APP_SECRET_KEY` gera automaticamente se não fornecido (settings.py:127)
- **PROBLEMA**: `.env.example` vazio demais
- **PROBLEMA**: SessionMiddleware com `https_only=False` em desenvolvimento
- **PROBLEMA**: docker-compose referencia `appgenesis/` mas código está em `appverbo/`
- Cache headers definidos como `no-store` globalmente
- APP_PUBLIC_URL vazio por padrão

### Riscos Encontrados
1. APP_SECRET_KEY gerado aleatoriamente a cada container restart em produção
2. PostgreSQL publicamente exposto
3. Código dentro de container via bind mount (não isolado)
4. URLs internas hardcoded (http://web:8000)
5. APP_PUBLIC_URL não configurado para domínio real
6. Sem endpoint de health verificável
7. Sem persistência de uploads fora do código
8. Sem backup/restore automation
9. Sem reverse proxy/Nginx
10. Sem HTTPS preparado
11. Sem logs stdout/stderr segregação
12. Multi-tenant não auditado completamente

## Plano

### Fase 1: Verificação de Compatibilidade Docker
- [x] Confirmar se docker-compose.yml usa appverbo ou appgenesis
- [x] Validar Dockerfile (já é simples)
- [x] Verificar .dockerignore

### Fase 2: Configuração & Secrets
- [x] Forçar APP_SECRET_KEY obrigatório em produção (settings.py)
- [x] Atualizar `.env.example` com TODAS as variáveis
- [x] Documentar geração de APP_SECRET_KEY segura

### Fase 3: Docker Produção
- [x] Criar `docker-compose.prod.yml`
  - [x] Sem bind mount ./:/app
  - [x] PostgreSQL sem exposição 5432:5432
  - [x] Uvicorn em rede interna
  - [x] Volumes separados para dados/uploads
  - [x] Restart policies adequadas
  - [x] Healthchecks melhorados

### Fase 4: Health Endpoint
- [x] Implementar `/health` endpoint (app.py)

### Fase 5: Nginx & Reverse Proxy
- [x] Criar `nginx/default.conf` (prod)
- [x] Configurar proxy headers
- [x] Headers segurança básicos

### Fase 6: HTTPS & Domínio
- [x] Documentar procedimento Let's Encrypt/Certbot
- [x] Preparar volumes para certificados

### Fase 7: Backup PostgreSQL
- [x] Criar `scripts/operations/backup.sh`
- [x] Criar `scripts/operations/restore.sh`

### Fase 8: Documentação Operacional
- [x] Criar `docs/operations/production-deploy.md` (guia completo)

### Fase 9: Testes & Validação
- [x] Teste Docker compose config (desenvolvimento)
- [x] Teste Docker compose config (produção)
- [x] Teste bash scripts syntax
- [ ] Teste Docker build (em progresso)
- [ ] Teste de migration em base vazia
- [ ] Teste de startup com PRODUCTION=true
- [ ] Teste de health endpoint

### Fase 10: Validação Multi-tenant (Auditoria)
- [ ] Revisar isolamento de dados entre entidades
- [ ] Validar APP_PUBLIC_URL em OAuth callbacks
- [ ] Validar filtros de entidade em queries

### Fase 11: Git Cleanup & Commit
- [ ] Remover diretório appgenesis/ (não commitado)
- [ ] Review git diff
- [ ] Verificar nenhum secret no diff
- [ ] Commit com mensagem clara
- [ ] Push

### Fase 12: Verificação CI
- [ ] Verificar resultado do build
- [ ] Verificar testes (se existirem)

## Descobertas

### Estrutura de Código
- Nome do package é `appverbo/` não `appgenesis/`
- `appgenesis/` existe como diretório local mas não é commitado (provavelmente refactor WIP)
- web_app.py importa de `appverbo.app`
- docker-compose.yml referencia `appgenesis/` — compatibilidade a confirmar

### Configurações Críticas
- APP_SECRET_KEY gerado via `secrets.token_urlsafe(32)` se não fornecido (settings.py:127)
- app.py configura SessionMiddleware com `APP_SECRET_KEY` (linha 42)
- `https_only=False` em desenvolvimento (linha 44) — deve ser `True` em produção
- Cache headers definidos como `no-store` globalmente (exceto /static)
- Existem OAuth handlers (Google, Microsoft, GitHub)
- WhatsApp integration via Cloud API
- SMTP para email
- Google Drive integration para MT940

## Decisões Técnicas

(Será preenchido durante a execução)

## Validações Executadas

(Será preenchido durante a execução)

## Pendências

Ver seção Plano.

## Estado Final

(Preenchido apenas quando tudo concluído)
