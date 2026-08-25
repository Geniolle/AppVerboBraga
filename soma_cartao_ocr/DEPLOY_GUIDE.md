# 🚀 Guia de Deploy - OCR Híbrido v2.0

**Data:** 2026-08-03  
**Status:** ✅ PRONTO PARA DEPLOY  
**Versão:** 2.0 Production

---

## ✅ Pré-requisitos de Deploy

### Instalado e Funcional
- ✅ Python 3.12+
- ✅ Tesseract v5.5.3 (C:\Program Files\Tesseract-OCR)
- ✅ Todas as dependências Python
- ✅ Google Cloud Vision API (credenciais)
- ✅ Google Sheets API (acesso)

### Verificar Antes de Deploy
```bash
# Tesseract
tesseract --version
# Esperado: tesseract 5.5.3.20260724

# Python modules
python -c "import pytesseract; import cv2; import google.cloud.vision; print('OK')"
# Esperado: OK

# Verificar config
python main.py --dry-run
# Esperado: sem erros
```

---

## 📋 Checklist de Deploy

### Segurança
- [ ] Verificar credenciais (conta-de-servico.json) em .gitignore
- [ ] Verificar config.yaml não expõe dados sensíveis
- [ ] Backup de config.yaml antes de mudanças
- [ ] Logs não contêm dados sensíveis

### Performance
- [ ] main.py executa em < 5min para 1 extrato
- [ ] Tesseract usa < 500MB RAM
- [ ] Google Vision API não ultrapassa quota
- [ ] Sem memory leaks em processamento batch

### Qualidade
- [ ] Taxa de sucesso mantém-se em 55%+
- [ ] Confiança média em 85%+
- [ ] Sem regressions em extratos anteriores
- [ ] Validação cruzada ativa

### Documentação
- [ ] README.md atualizado
- [ ] DEPLOYMENT_GUIDE.md criado
- [ ] Alterações documentadas em CHANGELOG.md
- [ ] Troubleshooting guide disponível

---

## 🔧 Passos de Deploy

### 1. Backup
```bash
# Backup da pasta anterior
cp -r soma_cartao_ocr soma_cartao_ocr.backup.$(date +%Y%m%d)

# Backup do config
cp config.yaml config.yaml.backup
```

### 2. Validação
```bash
# Testar novo código
python main.py --dry-run

# Testar em 1 extrato
python main.py --test 07/2026

# Verificar resultado
cat output/resultado.json | head -20
```

### 3. Deploy Gradual
```bash
# Opção A: Deploy em produção (recomendado)
python main.py

# Opção B: Deploy em staging (se disponível)
python main.py --staging

# Opção C: Deploy em teste manual
python main.py --no-upload  # Processa mas não escreve na sheet
```

### 4. Validação Pós-Deploy
```bash
# Verificar Google Sheet
# Abrir: CARTÃO sheet
# Verificar: Linhas novas com status VALIDO

# Verificar logs
tail -50 output/relatorio_qualidade.txt

# Verificar resultados
python -c "
import json
with open('output/resultado.json') as f:
    data = json.load(f)
    print(f'Taxa de sucesso: {data[\"quality_metrics\"][\"success_rate\"]:.1%}')
"
```

---

## 🎯 Matriz de Decisão

### Se taxa de sucesso > 55%
→ ✅ Continuar com Tesseract
→ Status: Mantém em produção
→ Próximo: Investigar outliers

### Se taxa de sucesso < 50%
→ ⚠️ Rollback para versão anterior
→ Investigar: Qual extrato piorou?
→ Debug: Logs de erro

### Se taxa = 55% (mantida)
→ ✅ Sucesso esperado
→ Próximo: Fixar Google One Dublin

---

## 📊 Monitoramento Pós-Deploy

### Métricas para Monitorar
```
Taxa de Sucesso (esperado: 55%+)
Confiança Média (esperado: 85%+)
Tempo de Processamento (esperado: < 5min)
Erros de Tesseract (esperado: < 5%)
Divergências Vision+Tesseract (esperado: < 10%)
```

### Dashboard Recomendado
```
Criar arquivo: monitor.py
Executar a cada hora:
  - Ler última linha de CARTÃO sheet
  - Verificar status (VALIDO/REVISAO)
  - Log resultado em JSON
  - Alertar se taxa cai < 50%
```

### Alertas
```
CRITICO (reage imediatamente):
  - Taxa de sucesso < 40%
  - Erro em > 20% das linhas
  - Tesseract crash/indisponível

IMPORTANTE (reage dentro de 2h):
  - Taxa 40-50% (degradação)
  - Confiança média < 70%
  - Processamento > 10min

INFORMATIVO (log apenas):
  - Taxa 50-55% (normal)
  - Confiança > 85% (excelente)
```

---

## 🔄 Rollback (Se Necessário)

### Rollback Rápido
```bash
# Se algo deu errado
git checkout main -- main.py config.yaml

# Ou restaurar backup
cp main.py.backup main.py
cp config.yaml.backup config.yaml

# Re-testar
python main.py --dry-run
```

### Investigação
1. Qual extrato piorou?
2. Qual mudança causou?
3. Como corrigir?
4. Testar antes de redeploy

---

## 📝 Após Deploy

### Documentação
- [ ] Atualizar CHANGELOG.md com versão 2.0
- [ ] Documentar resultados em arquivo RESULTS_v2.0.md
- [ ] Criar issue para "Google One Dublin fix"
- [ ] Planejar próxima sprint

### Análise
- [ ] Revisar 10 linhas REVISAO para identificar padrões
- [ ] Comparar com versão anterior (qual piou?)
- [ ] Calcular ROI (tempo economizado vs custo)
- [ ] Preparar apresentação para stakeholders

### Próximos Passos
- [ ] Investigar primeira linha (Google One)
- [ ] Testar em outros extratos (05/2026, 04/2026)
- [ ] Otimizar EasyOCR para fallback
- [ ] Planejar treino de modelo customizado

---

## 🆘 Troubleshooting Comum

### ❌ Tesseract não encontrado
```bash
# Solução
echo $env:PATH | grep Tesseract
# Se vazio, executar:
$env:PATH = "C:\Program Files\Tesseract-OCR;" + $env:PATH
python main.py
```

### ❌ Taxa de sucesso caiu
```bash
# Investigar
python -c "
import json
with open('output/resultado.json') as f:
    data = json.load(f)
    for reason, count in data['quality_metrics']['rejection_reasons'].items():
        print(f'{reason}: {count}')
"
```

### ❌ Google Sheets erro de conexão
```bash
# Verificar credenciais
python -c "
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file('credentials/soma-cartao-ocr.json')
print('Credenciais OK')
"
```

### ❌ Validação cruzada não está ativa
```bash
# Verificar se módulo importou
python -c "from cross_validator import get_best_value_cross_validated; print('OK')"

# Se erro, reinstalar
pip install --upgrade -e .
```

---

## 📞 Suporte

### Contatos
- Desenvolvimento: Claude Code
- Produto: [Nome do PM]
- Ops: [Nome do Ops]

### Repos
- Main: https://github.com/Geniolle/SOMA
- Documentação: /docs
- Issues: /issues

### Logs
- Arquivo: `output/relatorio_qualidade.txt`
- JSON: `output/resultado.json`
- CSV: `output/movimentos.csv`

---

## ✨ Deploy Sucesso!

Se você chegou até aqui, o deploy foi bem-sucedido! 🎉

Próximo passo: Monitorar métricas e planejar melhorias para próxima sprint.

---

**Versão:** 2.0  
**Data:** 2026-08-03  
**Status:** ✅ PRONTO  
**Aprovado por:** [Assinatura]

