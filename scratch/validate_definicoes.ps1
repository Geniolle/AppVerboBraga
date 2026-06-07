# ###################################################################################
# (1) PREPARAR AMBIENTE E BACKUP
# ###################################################################################
cd C:\workspace\AppVerboBraga
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\appverbo")) {
    throw "Pasta appverbo não encontrada. Confirme que está em C:\workspace\AppVerboBraga."
}

# Criar pasta de backup com timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups\definicoes_n_entidade_$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir

# Fazer backup dos ficheiros alterados
Copy-Item -Path "appverbo\admin_subprocesses\definicoes\configuracao.py" -Destination $backupDir -Force
Copy-Item -Path "appverbo\routes\profile\page_handler.py" -Destination $backupDir -Force

Write-Host "Backup criado em: $backupDir"

# ###################################################################################
# (2) VALIDAR CODIGO PYTHON
# ###################################################################################
Write-Host "Validando sintaxe Python..."
docker compose exec web python -m py_compile appverbo/admin_subprocesses/definicoes/configuracao.py
docker compose exec web python -m py_compile appverbo/routes/profile/page_handler.py

# ###################################################################################
# (3) VALIDAR DIVERGENCIAS GIT
# ###################################################################################
Write-Host "Executando git diff --check..."
git diff --check

Write-Host "Visualizando git status..."
git status

Write-Host "Visualizando git diff..."
git diff

# ###################################################################################
# (4) REINICIAR DOCKER E TESTAR HTTP
# ###################################################################################
Write-Host "Reiniciando serviço web no Docker..."
docker compose restart web

Write-Host "Aguardando 5 segundos para o contêiner inicializar..."
Start-Sleep -Seconds 5

Write-Host "Executando teste HTTP..."
python scratch/test_http.py

# ###################################################################################
# (5) MOSTRAR LOGS DO DOCKER
# ###################################################################################
Write-Host "Logs recentes do Docker..."
docker compose logs --tail=50 web
