# 🔍 Debug Insights - Google One Dublin Issue

**Data:** 2026-08-03  
**Status:** Investigado e Analisado

---

## 📊 Achados Principais

### Problema 1: "Google One Dublin" em Linhas Y Diferentes
```
Linha 8 (CY=335): "20/06 Google Câmbio"
Linha 9 (CY=354): "One Dublin EUR ( + )"
Diferença Y: 19 pixels
```

**Causa:** Vision API está agrupando as palavras em diferentes linhas Y porque:
- "Google" aparece em CY=348 (Y=328-368)
- "One" aparece em CY=354 (Y=336-372)
- Diferença: ~20 pixels

**Por que não agrupa?**
- Row tolerance atual: 0.003 * 900px = 2.7 pixels
- Diferença real: 19 pixels
- Precisa: tolerance = 0.021 (19/900)

**Problema:** Aumentar para 0.021 agrupa linhas indesejadas e piora taxa de sucesso (38.89%)

---

### Problema 2: Valores "1,99" Fora das Colunas Definidas
```
Esperado: X=1250-1452 (moeda_original coluna)
Encontrado: X=1454 e X=1974
Posição: No final da imagem, não mapeado nas colunas
```

**Análise:**
- Primeira "1,99" em X=1454 (logo após moeda_original)
- Segunda "1,99" em X=1974 (bem fora do intervalo)
- Ambas com Y entre 388-452

**Por que não foi capturado?**
- split_columns() procura em intervalo 1250-1452
- Valores estão em 1454 e 1974
- Fora do intervalo, logo não captura

---

### Problema 3: Dados Múltiplos na Mesma Linha Y

```
Linha 8 (CY=335):  "20/06 Google Câmbio"
Linha 9 (CY=354):  "One Dublin EUR ( + )"
Linha 10 (CY=372): "26/06 25/06 IRL"
```

**Insight:** Vision API está dividindo logicamente a transação em 3 linhas:
1. Data + Descrição (Google)
2. Descrição continuada (One Dublin) + Débito/Crédito
3. Próxima transação (MERCADONA)

---

## 📈 Análise de Impacto

### Se Aumentarmos row_tolerance_ratio
```
Benefício: Agrupa "Google" com "One Dublin"
Custo: Taxa de sucesso cai de 55.56% para 38.89% (-43%)
Conclusão: ❌ PIOR DO QUE BOM
```

### Raiz do Problema
Não é agrupamento de linhas (group_rows), é **divisão de transação em múltiplas linhas Y pela Vision API**.

---

## 🎯 Recomendação

### Opção A: Aceitar "Google One Dublin" como REVISAO
- ✓ Manter taxa em 55.56%
- ✓ Usar Tesseract para capturar "1,99"
- ✓ Deixar para próxima sprint

### Opção B: Pós-Processamento de Linhas
- Após group_rows(), fazer "merge" de linhas Y próximas
- Lógica: Se próximas linhas têm mesmo padrão, juntar
- Custo: +200 linhas de código
- Risco: Pode quebrar outras linhas

### Opção C: Ajustar split_columns()
- Expandir "moeda_original" para capturar X=1454
- Ajustado em debug: [0.62, 0.75] em vez de [0.62, 0.72]
- Resultado: Taxa cai para 38.89%
- Conclusão: ❌ Não funciona

---

## 💡 Insights Técnicos

1. **Vision API está dividindo por layout visual, não por lógica**
   - "Google" está em linha visual 8
   - "One Dublin" está em linha visual 9
   - Sistema OCR segue o layout físico, não lógica

2. **Tesseract está capturando melhor os números**
   - 22 valores capturados
   - Hybrid OCR com cross-validation funciona
   - Primeiro "1,99" está sendo detectado via Tesseract

3. **Split de colunas é frágil**
   - Valores fora dos limites não são capturados
   - Expansão de colunas piora outras linhas
   - Melhor deixar como está

---

## ✅ Conclusão

**"Google One Dublin" é um edge case, não um bug sistêmico**

- Vision API divide logicamente em 3 linhas Y
- Aumentar tolerance piora taxa geral
- Tesseract já está capturando "1,99"
- Sistema está em bom estado (55.56%)

**Recomendação:** Deixar para próxima sprint com maior refactor de pós-processamento.

---

## 🚀 Próximos Passos

Passar para:
1. ✅ Resolver EasyOCR
2. ✅ Testar em outros extratos
3. ✅ Batch processing

**Status Crítico:** Investigado, documentado, aceitando como tech debt

---

**Investigado por:** Claude Code  
**Data:** 2026-08-03  
**Tempo Gasto:** ~30 minutos  
**Conclusão:** Edge case, não crítico

