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
$backupDir = "backups\menu_n_entidade_$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir

# Fazer backup dos ficheiros alterados
Copy-Item -Path "templates\new_user.html" -Destination $backupDir -Force
Copy-Item -Path "templates\partials\admin_menu_edit_card.html" -Destination $backupDir -Force
Copy-Item -Path "static\css\new_user.css" -Destination $backupDir -Force

Write-Host "Backup criado em: $backupDir"

# ###################################################################################
# (2) VALIDAR DIVERGENCIAS GIT
# ###################################################################################
Write-Host "Executando git diff --check..."
git diff --check

Write-Host "Visualizando git status..."
git status

# ###################################################################################
# (3) REINICIAR DOCKER E TESTAR HTTP
# ###################################################################################
Write-Host "Reiniciando serviço web no Docker..."
docker compose restart web

Write-Host "Aguardando 5 segundos para o contêiner inicializar..."
Start-Sleep -Seconds 5

Write-Host "Executando teste HTTP..."
python scratch/test_http.py

# ###################################################################################
# (4) MOSTRAR LOGS DO DOCKER
# ###################################################################################
Write-Host "Logs recentes do Docker..."
docker compose logs --tail=50 web
