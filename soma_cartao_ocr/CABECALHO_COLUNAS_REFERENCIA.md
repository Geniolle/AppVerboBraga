# 📋 Referência Permanente: Cabeçalho e Colunas do Extrato

**Data:** 2026-08-03  
**Status:** REFERÊNCIA PERMANENTE - COLUNAS NUNCA MUDAM  
**Atualizado:** Sim, documentado para todos os projetos

---

## ⚡ Quick Reference: As 8 Colunas

```
Posição    Coluna                     Largura  Formato            Importante
─────────────────────────────────────────────────────────────────────────────
0%-10%     DATA MOVIMENTO             10%      DD/MM              ⭐⭐⭐
10%-19%    DATA VALOR                 9%       DD/MM              ⭐⭐⭐
19%-56%    DESCRIÇÃO                  37%      Texto livre        ⭐⭐⭐
56%-62%    PAÍS                       6%       Código ISO         ⭐⭐
62%-72%    MOEDA ORIGINAL             10%      Valor decimal      ⭐⭐⭐
72%-82%    TAXA DE CÂMBIO             10%      Taxa decimal       ⭐⭐
82%-92%    DÉBITO EUR (+)             10%      Valor decimal      ⭐⭐⭐
92%-100%   CRÉDITO EUR (-)            8%       Valor decimal      ⭐⭐⭐
```

---

## 1. DATA MOVIMENTO (10%)
- **X Range:** 0.00 - 0.10
- **Formato:** DD/MM (ex: 23/06)
- **Significado:** Quando a transação foi realizada
- **Importância:** CRÍTICA
- **OCR Difficulty:** ⭐ Muito fácil (números simples)
- **Validação:** 
  - Deve estar entre 01/01 e 31/12
  - Mês deve estar em [6, 7] (junho, julho de 2026)

---

## 2. DATA VALOR (9%)
- **X Range:** 0.10 - 0.19
- **Formato:** DD/MM (ex: 20/06)
- **Significado:** Quando o valor saiu da conta
- **Importância:** CRÍTICA
- **OCR Difficulty:** ⭐ Muito fácil (números simples)
- **Validação:**
  - Geralmente Data Valor ≈ Data Movimento ou depois (0-7 dias)
  - Mês deve estar em [6, 7]

---

## 3. DESCRIÇÃO (37%)
- **X Range:** 0.19 - 0.56
- **Formato:** Texto livre (comerciante, local, referência)
- **Significado:** Identifica quem recebeu o dinheiro e onde
- **Importância:** CRÍTICA (ajuda na categorização)
- **OCR Difficulty:** ⭐⭐ Médio (texto longo, acentos)
- **Desafios:**
  - Pode quebrar em 1-3 linhas Y diferentes
  - Contém acentos (ç, ã, â, é)
  - Algumas descrições podem parecer códigos
- **Exemplos:**
  - "Google One Dublin" (quebra em 2 linhas)
  - "FACEBOOK IRELAND LIMITED"
  - "MERCADONA BRAGA"
  - "COMISSÃO ANUAL"

---

## 4. PAÍS (6%)
- **X Range:** 0.56 - 0.62
- **Formato:** Código ISO 2-3 letras (IRL, USA, POR, GBP)
- **Significado:** País onde a transação ocorreu
- **Importância:** MÉDIA-ALTA (ajuda validação)
- **OCR Difficulty:** ⭐ Muito fácil (apenas 2-3 caracteres)
- **Validação:**
  - Deve ser código país válido (IRL, USA, DEU, FRA, etc)
  - Nunca deve estar vazio em transações internacionais
- **Exemplos Comuns:**
  - IRL (Irlanda)
  - USA (Estados Unidos)
  - POR (Portugal)
  - GBR (Reino Unido)

---

## 5. MOEDA ORIGINAL (10%)
- **X Range:** 0.62 - 0.72
- **Formato:** Valor decimal com vírgula (ex: 1,99)
- **Significado:** Valor na moeda original da transação
- **Importância:** CRÍTICA (base para todas as conversões)
- **OCR Difficulty:** ⭐ Muito fácil (números)
- **Desafios:**
  - Alguns valores podem sair do intervalo X (bug: X=1454, X=1974)
  - Separadores: vírgula (PT) vs ponto (EN)
  - Tesseract capta bem quando Vision falha
- **Validação:**
  - Deve ser > 0
  - Deve ter até 2 casas decimais
  - Nunca vazio

---

## 6. TAXA DE CÂMBIO (10%)
- **X Range:** 0.72 - 0.82
- **Formato:** Taxa decimal (ex: 1.0, 0.95)
- **Significado:** Taxa de câmbio aplicada pela instituição
- **Importância:** MÉDIA (afeta cálculo final)
- **OCR Difficulty:** ⭐ Muito fácil (números simples)
- **Padrões:**
  - 1.0 quando transação é em EUR
  - 0.8-1.2 para câmbios internacionais
- **Validação:**
  - Geralmente está entre 0.5 e 2.0

---

## 7. DÉBITO EUR (+) (10%)
- **X Range:** 0.82 - 0.92
- **Formato:** Valor decimal (ex: 1,99)
- **Significado:** Valor DEBITADO (saída de dinheiro)
- **Importância:** CRÍTICA
- **OCR Difficulty:** ⭐ Muito fácil (números)
- **Regra de Ouro:**
  - ✓ Débito ou Crédito, NUNCA ambos
  - ✓ Se débito tem valor, crédito = vazio
  - ✗ Se débito = vazio, crédito DEVE ter valor
- **Validação:**
  - Se preenchido: > 0
  - Aproximadamente igual a Moeda Original * Taxa Câmbio

---

## 8. CRÉDITO EUR (-) (8%)
- **X Range:** 0.92 - 1.00
- **Formato:** Valor decimal (ex: vazio ou valor)
- **Significado:** Valor CREDITADO (entrada de dinheiro)
- **Importância:** CRÍTICA
- **OCR Difficulty:** ⭐ Muito fácil (números) mas RARO
- **Padrões:**
  - Aparece em <5% das transações (reembolsos, devoluções)
  - Na maioria das vezes ESTÁ VAZIO
- **Regra de Ouro:**
  - ✓ Se crédito tem valor, débito = vazio
  - ✗ Nunca ambos preenchidos

---

## 🎯 Validação Cruzada (Regras Críticas)

```python
# Regra 1: Débito XOR Crédito (mutuamente excludentes)
def validate_debit_credit(débito, crédito):
    assert (débito > 0 and crédito == 0) or (débito == 0 and crédito > 0)
    # Uma transação é OU débito OU crédito, NUNCA ambas

# Regra 2: Valores devem estar corretos
def validate_amounts(moeda_original, taxa_cambio, débito_eur):
    assert abs(débito_eur - (moeda_original * taxa_cambio)) < 0.01
    # Débito EUR deve ser aproximadamente Moeda Original * Taxa

# Regra 3: Datas devem ser válidas
def validate_dates(data_mov, data_valor):
    assert data_mov.month in [6, 7]
    assert data_valor.month in [6, 7]
    assert data_valor >= data_mov  # Data valor é depois do movimento

# Regra 4: País e País devem ser válidos
def validate_country(pais):
    valid_codes = ["IRL", "USA", "POR", "DEU", "FRA", "GBR", ...]
    assert pais in valid_codes
```

---

## 📊 Mapeamento para Config.yaml

```yaml
table:
  columns:
    data_movimento: [0.00, 0.10]     # 10%
    data_valor: [0.10, 0.19]         # 9%
    descricao: [0.19, 0.56]          # 37%
    pais: [0.56, 0.62]               # 6%
    moeda_original: [0.62, 0.72]     # 10%
    taxa_cambio: [0.72, 0.82]        # 10%
    debito_eur: [0.82, 0.92]         # 10%
    credito_eur: [0.92, 1.00]        # 8%
  row_tolerance_ratio: 0.003
```

---

## 🔍 Header Terms (Detecção do Cabeçalho)

```yaml
validation:
  header_terms: 
    - data
    - movimento
    - descrição
    - descricao
    - país
    - pais
    - moeda
    - câmbio
    - cambio
    - débito
    - debito
    - crédito
    - credito
```

**Nota:** Colunas nunca mudam, mas header_terms podem precisar de ajustes se o layout mudar drasticamente.

---

## ⚠️ Problemas Conhecidos (Tech Debt)

| Problema | Afeta | Status | Próxima Sprint |
|----------|-------|--------|----------------|
| "Google One Dublin" quebra em 2 linhas Y | Descrição | ✅ Aceito | Refactor pós-proc |
| Alguns valores moeda_original fora do X | Moeda Original | ✅ Tesseract capta | Edge case |
| Acentos em nomes de colunas | Detecção header | ✅ Handled | Documentado |

---

## 📝 Como Usar Este Documento

1. **Desenvolvimento:** Consulte as especificações de cada coluna
2. **Debug:** Se OCR falha, verifique se é problema de coluna ou de OCR
3. **Validação:** Use as regras de validação cruzada
4. **Testes:** Compare contra estes valores esperados
5. **Futuro:** As colunas NÃO mudam, reutilize este documento sempre

---

**IMPORTÂNCIA:** Este é um documento PERMANENTE do projeto. As colunas nunca mudam entre extratos. Use como referência universal.

**Última Atualização:** 2026-08-03  
**Próxima Revisão:** Somente se houver mudança de formato do banco
