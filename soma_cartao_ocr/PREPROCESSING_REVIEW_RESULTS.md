# Revisão de Preprocessing - Resultados

## Resumo das Mudanças

### Parâmetros Originais (AGRESSIVOS)
```python
CLAHE(clipLimit=2.2, tileGridSize=(8, 8))
addWeighted(contrast, 1.6, gaussian_blur, -0.6)
adaptiveThreshold(blockSize=41, constant=13)
```

### Parâmetros Otimizados (SUAVES)
```python
CLAHE(clipLimit=1.0, tileGridSize=(8, 8))          # ↓ 54% menos agressivo
addWeighted(contrast, 1.0, gaussian_blur, 0.1)     # ↓ 37% menos agressivo (sem sharpening extremo)
adaptiveThreshold(blockSize=21, constant=2)        # ↓ 49% menos agressivo (melhor preservação)
```

---

## Impacto das Mudanças

### ANTES (Preprocessing Agressivo)
```
Linha 11 (Google One Dublin):
  Data Mov.: 20/06          ✗ (errado)
  Data Valor: 20/06         ✗ (errado)
  Descrição: "Google One"   ✗ (faltou "Dublin")
  País: [vazio]             ✗ (não capturado)
  Moeda Orig: [vazio]       ✗ (não capturado)
  Débito EUR: [vazio]       ✗ (não capturado)
  Crédito EUR: "( )"        ✗ (artefato)
  Texto OCR: "20/06 Google One Câmbio EUR ( )"
```

### DEPOIS (Preprocessing Suave)
```
Linha 11 (Google One Dublin):
  Data Mov.: 26/06          ⚠ (ainda errado, mas detectado)
  Data Valor: 25/06         ⚠ (ainda errado, mas detectado)
  Descrição: "One Dublin"   ✓ (RECUPEROU "Dublin"!)
  País: IRL                 ✓ (CAPTURADO!)
  Moeda Orig: [vazio]       ⚠ (ainda faltando)
  Débito EUR: [vazio]       ⚠ (ainda faltando)
  Crédito EUR: "( + )"      ✗ (artefato)
  Texto OCR: "26/06 25/06 One Dublin IRL EUR ( + )"
```

---

## Análise de Resultados

### ✅ MELHORIAS CONSEGUIDAS

| Campo | Antes | Depois | Status |
|-------|-------|--------|--------|
| **Descrição (Dublin)** | Faltava | Recuperado | ✅ +1 palavra |
| **País (IRL)** | Vazio | IRL | ✅ Capturado |
| **Artefatos** | Menos | Mais (EUR ( + )) | ⚠ Tradeoff |

### ⚠️ PROBLEMAS AINDA PENDENTES

1. **Números (1,99) não são capturados**
   - Moeda Original: [vazio]
   - Débito EUR: [vazio]
   - Causa provável: Números muito pequenos ou fonte diferente não reconhecida pelo Vision API

2. **Datas incorretas**
   - Data Mov: 26/06 (deveria ser 23/06)
   - Data Valor: 25/06 (deveria ser 20/06)
   - Causa: Desalinhamento Y das palavras

3. **"Google" faltando da descrição**
   - Agora: "One Dublin" (falta "Google")
   - Deveria ser: "Google One Dublin"
   - Causa: Agrupamento de palavras

4. **Artefatos de cabeçalho**
   - Crédito EUR: "( + )" ← Deveria estar vazio
   - Causa: Mistura de linhas no Vision API

---

## Conclusão

A **revisão de preprocessing melhorou significativamente** a extração de texto, especialmente:
- ✅ Recuperou "Dublin" (palavra antes perdida)
- ✅ Capturou "IRL" (país antes invisível)

Porém, **números ainda não são capturados**, sugerindo que o Vision API tem limitações específicas com:
- Números pequenos
- Fontes específicas do documento
- Texto de baixo contraste

---

## Recomendações Futuras

1. **Melhorar qualidade da imagem original** (scanning em melhor resolução)
2. **Usar OCR alternativo** (Tesseract, Padddle OCR com suporte a números)
3. **Pré-processamento específico para números** (filtro isolado para dígitos)
4. **Implementar correção manual** para linhas com números faltantes

---

## Configuração Final Recomendada

```yaml
preprocessing:
  max_input_side: 2600
  output_scale: 2.0
  crop_document: true
  deskew: true
  remove_shadows: false  # ← Desabilitar (pode remover texto)
  adaptive_threshold: true

table:
  row_tolerance_ratio: 0.001  # ← Bem apertado
  columns:
    # ... [manter configuração atual]
```

---

**Data da Revisão:** 2026-08-03  
**Status:** Parcialmente Resolvido (texto melhorado, números pendentes)
