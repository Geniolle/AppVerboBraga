# Estrutura Esperada - Validação de Dados

**Data:** 2026-08-03  
**Objetivo:** Definir exatamente o que esperar em cada coluna antes de gravar na Sheet

---

## 📋 Estrutura das 8 Colunas (SEMPRE NESTA ORDEM)

### **1. Data Movimento (10%)**
- **Posição:** X = 0-201 pixels (10% da imagem)
- **Formato:** DD/MM/YYYY (ex: 26/06/2026)
- **Conteúdo esperado:** Data quando a transação ocorreu
- **Validação:** 
  - ✓ Deve estar preenchido
  - ✓ Deve ser válido (01-31 para dia, 01-12 para mês)
  - ✓ Deve ser <= Data Valor

### **2. Data Valor (9%)**
- **Posição:** X = 201-383 pixels (9% da imagem)
- **Formato:** DD/MM/YYYY (ex: 20/06/2026)
- **Conteúdo esperado:** Data quando o dinheiro saiu/entrou
- **Validação:**
  - ✓ Deve estar preenchido
  - ✓ Deve ser válido (01-31 para dia, 01-12 para mês)
  - ✓ Deve ser >= Data Movimento

### **3. Descrição (37%)**
- **Posição:** X = 383-1129 pixels (37% da imagem)
- **Formato:** Texto livre
- **Conteúdo esperado:** Nome do comerciante, local, referência
- **Validação:**
  - ✓ Deve estar preenchido
  - ✓ Deve ter sentido comercial
  - ✗ NÃO deve ser vazio

### **4. País (6%)**
- **Posição:** X = 1129-1250 pixels (6% da imagem)
- **Formato:** Código país 2-3 letras (ex: IRL, USA, POR)
- **Conteúdo esperado:** Onde a transação ocorreu
- **Validação:**
  - ✓ Se preenchido, deve ser código válido
  - ✗ NÃO deve ter acentos ou espaços

### **5. Moeda Original (10%)**
- **Posição:** X = 1250-1452 pixels (10% da imagem)
- **Formato:** Valor decimal com vírgula (ex: 29,00)
- **Conteúdo esperado:** Valor na moeda original
- **Validação:**
  - ✓ Deve estar preenchido
  - ✓ Deve ser > 0
  - ✗ NÃO pode vir com símbolo de moeda ($, €, etc)

### **6. Taxa de Câmbio (10%)**
- **Posição:** X = 1452-1653 pixels (10% da imagem)
- **Formato:** Taxa decimal (ex: 1.0, 0.95)
- **Conteúdo esperado:** Taxa de câmbio aplicada
- **Validação:**
  - ✓ Se preenchido, deve estar entre 0.5-2.0
  - ✗ NÃO pode vir com símbolo ou percentual

### **7. Débito EUR (+) (10%)**
- **Posição:** X = 1653-1855 pixels (10% da imagem)
- **Formato:** Valor decimal (ex: 29.00)
- **Conteúdo esperado:** Dinheiro que saiu (em EUR)
- **Validação:**
  - ✓ Ou tem débito OU tem crédito (NUNCA AMBOS)
  - ✓ Se tem débito, deve ser > 0
  - ✓ Deve aproximar ao Moeda Original * Taxa Câmbio

### **8. Crédito EUR (-) (8%)**
- **Posição:** X = 1855-2017 pixels (8% da imagem)
- **Formato:** Valor decimal (ex: 29.00)
- **Conteúdo esperado:** Dinheiro que entrou (reembolsos, devoluções)
- **Validação:**
  - ✓ Ou tem débito OU tem crédito (NUNCA AMBOS)
  - ✓ Se tem crédito, deve ser > 0
  - ✓ Muito raro (< 5% das transações)

---

## ❌ Problemas Detectados na Tabela Temporária

### **Problema 1: Data Movimento > Data Valor**
```
Linha CAR-11:
  Data Movimento: 26/06/2026
  Data Valor:     25/06/2026
  ❌ ERRO: 26 > 25 (impossível)
  Status: REVISÃO (correto)
```

### **Problema 2: Moeda Original ≠ Débito**
```
Linha CAR-14:
  Descrição: OPUS CLIP OPUS . PRO
  Moeda Original: 5,90
  Débito EUR:     35.15
  ❌ ERRO: 5,90 ≠ 35.15 (deveriam ser iguais)
  Taxa Câmbio: (vazio - deveria corrigir)
  Status: REVISÃO
```

### **Problema 3: Valores em Colunas Erradas**
```
Linha CAR-13:
  Descrição: FACEBK 8HJ84THS72 Dublin
  País: (vazio) ← DEVERIA TER "IRL"
  Moeda Original: (vazio) ← DEVERIA TER VALOR
  Débito EUR: 1.99 ← está aqui
  Status: VÁLIDO (mas com dados errados)
```

---

## 🔍 Raiz dos Problemas

1. **Split de colunas errado:** O algoritmo `split_columns()` não está respeitando os limites X corretos
2. **Valores fora do intervalo:** Alguns valores aparecem FORA dos limites definidos (ex: X=1974 em vez de X=1250-1452)
3. **Cabeçalho não sendo pulado:** Algumas linhas do cabeçalho estão sendo interpretadas como dados

---

## ✅ Ações Necessárias

1. ✅ **Verificar limites de X:**
   - data_movimento: [0.00, 0.10]
   - data_valor: [0.10, 0.19]
   - descricao: [0.19, 0.56]
   - pais: [0.56, 0.62]
   - moeda_original: [0.62, 0.72]
   - taxa_cambio: [0.72, 0.82]
   - debito_eur: [0.82, 0.92]
   - credito_eur: [0.92, 1.00]

2. ✅ **Validar antes de escrever:**
   - Data Movimento <= Data Valor
   - Moeda Original × Taxa Câmbio ≈ Débito EUR (ou Crédito EUR)
   - País deve ser código válido ou vazio
   - Descrição não pode ser vazia

3. ✅ **Usar tabela temporária:**
   - Visualizar dados ANTES de gravar
   - Só escrever se passar em validações
   - Marcar para revisão manual se duvidoso

---

**Conclusão:** A tabela temporária mostra que a **estrutura das colunas está incorreta**. Alguns dados estão sendo colocados em colunas erradas devido a problemas de alinhamento no documento PDF/imagem.

**Próximo passo:** Reajustar os limites de X no `config.yaml` baseado em análise visual real da imagem.
