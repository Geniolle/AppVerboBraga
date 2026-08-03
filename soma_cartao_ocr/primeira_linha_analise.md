# Análise da Primeira Linha - Google One Dublin

## Cabeçalho (conforme imagem)
```
Data Mov. | Data Valor | Descrição | País | Moeda Original | Taxa Câmbio | Débito EUR (+) | Crédito EUR (-)
```

## Primeira Linha de Dados
```
23/06 | 20/06 | Google One Dublin | ??? | ??? | ??? | ??? | ???
```

## Campos Identificados Visualmente na Imagem

| Campo | Valor Observado | OCR Capturado | Status |
|-------|-----------------|---------------|--------|
| Data Mov. | 23/06 | 23/06 (não capturado no check_results.py) | ✓ |
| Data Valor | 20/06 | 20/06 (não capturado) | ✓ |
| Descrição | Google One Dublin | Google One (capturado parcialmente) | ⚠️ |
| País | [vazio?] | [vazio] | ? |
| Moeda Original | [vazio?] | [vazio] | ? |
| Taxa Câmbio | [vazio?] | [vazio] | ? |
| **Débito EUR** | **[???]** | [vazio] | **❌ FALTANDO** |
| Crédito EUR | [vazio?] | [vazio] | ? |

## Pergunta ao Utilizador

**Qual é o valor que você vê na coluna "Débito EUR (+)" para a linha "Google One Dublin"?**

- É um número como "1,99" ou "5,90"?
- Em qual intervalo aproximado está na imagem (esquerda, meio, direita da coluna)?
- A fonte é legível ou está desbotada?

Esta informação vai permitir:
1. Ajustar os limites de coluna corretamente
2. Verificar se o Vision API extraiu o valor
3. Implementar a solução apropriada
