# 📊 Análise de Validação - Processo Entradas

## Simulação com Dados de Exemplo

Data da Análise: 2026-08-24

---

## 📋 Dados Simulados de DÍZIMOS/OFERTAS

| Linha | DATA | TIPO | DOC.SOMA | FINANCE | VALOR | ID_INTERNO | Status |
|-------|------|------|----------|---------|-------|------------|--------|
| 2 | 2024-08-15 | DÍZIMOS/OFERTAS | (vazio) | (vazio) | 35,50 | ENT0000000001 | ✅ VÁLIDA |
| 3 | 2024-08-16 | DÍZIMOS/OFERTAS | (vazio) | (vazio) | 100,00 | ENT0000000002 | ✅ VÁLIDA |
| 4 | 2024-08-17 | SAÍDA | (vazio) | (vazio) | 50,00 | ENT0000000003 | ❌ INVÁLIDA |
| 5 | 2024-08-18 | DÍZIMOS/OFERTAS | 4606815 | (vazio) | 75,00 | ENT0000000004 | ❌ INVÁLIDA |
| 6 | 2024-08-19 | DÍZIMOS/OFERTAS | (vazio) | Transferido | 25,00 | ENT0000000005 | ❌ INVÁLIDA |
| 7 | 2024-08-20 | DÍZIMOS/OFERTAS | (vazio) | (vazio) | 0 | ENT0000000006 | ❌ INVÁLIDA |
| 8 | (vazio) | DÍZIMOS/OFERTAS | (vazio) | (vazio) | 45,50 | ENT0000000007 | ❌ INVÁLIDA |
| 9 | 2024-08-22 | DIA VERBO MISSÔES | (vazio) | (vazio) | 60,00 | ENT0000000008 | ✅ VÁLIDA |
| 10 | 2024-08-23 | DÍZIMOS/OFERTAS | (vazio) | (vazio) | ABC | ENT0000000009 | ❌ INVÁLIDA |
| 11 | 2024-08-24 | DÍZIMOS/OFERTAS | (vazio) | (vazio) | -15,00 | ENT0000000010 | ❌ INVÁLIDA |

---

## ✅ ANÁLISE DETALHADA POR LINHA

### **LINHA 2: ✅ VÁLIDA - SERÁ TRANSFERIDA**

```
DATA:          2024-08-15        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido (um dos 2 aceitáveis)
DOC.SOMA:      (vazio)           ✓ Vazio conforme requerido
FINANCE:       (vazio)           ✓ Vazio conforme requerido
VALOR:         35,50             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000001     ✓ Presente
```

**RESULTADO:** ✅ **ACEITA** → Segue para Deduplicação e Transferência
**PRÓXIMA AÇÃO:** Verificar se é duplicata em CONTAORDEM

---

### **LINHA 3: ✅ VÁLIDA - SERÁ TRANSFERIDA**

```
DATA:          2024-08-16        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         100,00            ✓ > 0 e numérico
ID_INTERNO:    ENT0000000002     ✓ Presente
```

**RESULTADO:** ✅ **ACEITA** → Segue para Deduplicação e Transferência

---

### **LINHA 4: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-17        ✓ Preenchida
TIPO:          SAÍDA             ✗ INVÁLIDO - Deve ser "DÍZIMOS/OFERTAS" ou "DIA VERBO MISSÔES"
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         50,00             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000003     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"TIPO inválido: SAÍDA"`
**AÇÃO:** Pula linha, registra erro no log

---

### **LINHA 5: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-18        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      4606815           ✗ NÃO ESTÁ VAZIO - Indica já processado em outro sistema
FINANCE:       (vazio)           ✓ Vazio
VALOR:         75,00             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000004     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"DOC.SOMA não está vazio"`
**AÇÃO:** Pula linha, registra erro no log
**INTERPRETAÇÃO:** Já foi criado documento SOMA para essa entrada → não re-processa

---

### **LINHA 6: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-19        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       Transferido       ✗ NÃO ESTÁ VAZIO - Indica já processado
VALOR:         25,00             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000005     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"FINANCE não está vazio"`
**AÇÃO:** Pula linha, reconhece como já processado
**INTERPRETAÇÃO:** Em execução anterior foi marcado como "Transferido" → não re-processa (IDEMPOTÊNCIA)

---

### **LINHA 7: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-20        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         0                 ✗ NÃO É MAIOR QUE ZERO - Rejeita valores = 0
ID_INTERNO:    ENT0000000006     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"VALOR <= 0: 0"`
**AÇÃO:** Pula linha, não permite doações de valor zero

---

### **LINHA 8: ❌ INVÁLIDA - REJEITADA**

```
DATA:          (vazio)           ✗ VAZIA - Critério obrigatório
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         45,50             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000007     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"DATA vazia"`
**AÇÃO:** Pula linha, data é obrigatória para rastreabilidade

---

### **LINHA 9: ✅ VÁLIDA - SERÁ TRANSFERIDA**

```
DATA:          2024-08-22        ✓ Preenchida
TIPO:          DIA VERBO MISSÔES ✓ Válido (um dos 2 aceitáveis)
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         60,00             ✓ > 0 e numérico
ID_INTERNO:    ENT0000000008     ✓ Presente
```

**RESULTADO:** ✅ **ACEITA** → Segue para Deduplicação e Transferência
**NOTA:** TIPO é "DIA VERBO MISSÔES" (tipo alternativo válido)

---

### **LINHA 10: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-23        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         ABC               ✗ NÃO-NUMÉRICO - Não é um número válido
ID_INTERNO:    ENT0000000009     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"VALOR inválido: ABC"`
**AÇÃO:** Pula linha, valor não é conversível para número

---

### **LINHA 11: ❌ INVÁLIDA - REJEITADA**

```
DATA:          2024-08-24        ✓ Preenchida
TIPO:          DÍZIMOS/OFERTAS   ✓ Válido
DOC.SOMA:      (vazio)           ✓ Vazio
FINANCE:       (vazio)           ✓ Vazio
VALOR:         -15,00            ✗ NEGATIVO - Deve ser > 0
ID_INTERNO:    ENT0000000010     ✓ Presente
```

**RESULTADO:** ❌ **REJEITADA**
**MOTIVO:** `"VALOR <= 0: -15,00"`
**AÇÃO:** Pula linha, não permite valores negativos (não são doações)

---

## 📊 RESUMO DA ANÁLISE

| Critério | Total | Atende | Falha | % Sucesso |
|----------|-------|--------|-------|-----------|
| **DATA** | 10 | 9 | 1 | 90% |
| **TIPO** | 10 | 9 | 1 | 90% |
| **DOC.SOMA** | 10 | 9 | 1 | 90% |
| **FINANCE** | 10 | 9 | 1 | 90% |
| **VALOR** | 10 | 7 | 3 | 70% |
| **TODAS (E)** | 10 | 3 | 7 | **30%** |

### **Resultado Geral:**

```
Total de linhas analisadas:      10
✅ Linhas VÁLIDAS (5 critérios ok): 3 (30%)
❌ Linhas INVÁLIDAS:              7 (70%)

Linhas que serão transferidas:    3 (Linhas 2, 3, 9)
Linhas rejeitadas:                7
```

---

## 🔍 Motivos de Rejeição (Contagem)

| Motivo | Ocorrências | Linhas |
|--------|-------------|--------|
| TIPO inválido | 1 | 4 |
| DOC.SOMA não vazio | 1 | 5 |
| FINANCE não vazio | 1 | 6 |
| VALOR <= 0 | 1 | 7 |
| DATA vazia | 1 | 8 |
| VALOR não-numérico | 1 | 10 |
| VALOR negativo | 1 | 11 |

**Total de rejeições:** 7 (uma rejeição por linha inválida)

---

## 📤 Linhas Que Serão Transferidas para CONTAORDEM

### **Entrada 1: Linha 2**
```
DATA MOV.:              2024-08-15
DESCRIÇÃO:              DÍZIMOS E OFERTAS (CULTO)
IMPORTÂNCIA:            35,50
TIPO:                   Entrada
PLANO DE CONTA:         DOAÇÕES - DÍZIMOS E OFERTAS
CENTRO DE CUSTO:        10.10.01 - DÍZIMOS E OFERTAS
PROCESSO:               DÍZIMOS/OFERTAS
PERÍODO:                AGOSTO
FORMA DE PAGAMENTO:     DINHEIRO
CAIXA:                  CAIXA DIÁRIO
ID_INTERNO:             ENT0000000001
```

### **Entrada 2: Linha 3**
```
DATA MOV.:              2024-08-16
DESCRIÇÃO:              DÍZIMOS E OFERTAS (CULTO)
IMPORTÂNCIA:            100,00
TIPO:                   Entrada
PLANO DE CONTA:         DOAÇÕES - DÍZIMOS E OFERTAS
CENTRO DE CUSTO:        10.10.01 - DÍZIMOS E OFERTAS
PROCESSO:               DÍZIMOS/OFERTAS
PERÍODO:                AGOSTO
FORMA DE PAGAMENTO:     DINHEIRO
CAIXA:                  CAIXA DIÁRIO
ID_INTERNO:             ENT0000000002
```

### **Entrada 3: Linha 9**
```
DATA MOV.:              2024-08-22
DESCRIÇÃO:              DÍZIMOS E OFERTAS (CULTO)
IMPORTÂNCIA:            60,00
TIPO:                   Entrada
PLANO DE CONTA:         DOAÇÕES - DÍZIMOS E OFERTAS
CENTRO DE CUSTO:        10.10.01 - DÍZIMOS E OFERTAS
PROCESSO:               DIA VERBO MISSÔES
PERÍODO:                AGOSTO
FORMA DE PAGAMENTO:     DINHEIRO
CAIXA:                  CAIXA DIÁRIO
ID_INTERNO:             ENT0000000008
```

---

## 🔄 Próxima Fase: Deduplicação

As 3 linhas válidas serão verificadas contra CONTAORDEM:

| Entrada | Chave Dedup | Existe em CONTAORDEM? | Ação |
|---------|-------------|----------------------|------|
| 1 | 2024-08-15 + 35,50 + DESC | Verifica... | Se NÃO → Transfere |
| 2 | 2024-08-16 + 100,00 + DESC | Verifica... | Se NÃO → Transfere |
| 3 | 2024-08-22 + 60,00 + DESC | Verifica... | Se NÃO → Transfere |

---

## 📝 Log de Execução Esperado

```
[INFO] Starting Entradas process pipeline
[INFO] [1/6] Authenticating with Google Sheets...
[INFO]       Sheets authenticated
[INFO] [2/6] Loading and validating entries from DÍZIMOS/OFERTAS...
[INFO]       Loaded 10 rows
[DEBUG] Row 2 valid
[DEBUG] Row 3 valid
[DEBUG] Row 4 invalid: TIPO inválido: SAÍDA
[DEBUG] Row 5 invalid: DOC.SOMA não está vazio
[DEBUG] Row 6 invalid: FINANCE não está vazio
[DEBUG] Row 7 invalid: VALOR <= 0: 0
[DEBUG] Row 8 invalid: DATA vazia
[DEBUG] Row 9 valid
[DEBUG] Row 10 invalid: VALOR inválido: ABC
[DEBUG] Row 11 invalid: VALOR <= 0: -15,00
[INFO]       Valid: 3, Invalid: 7
[INFO] [3/6] Deduplicating entries...
[INFO]       After deduplication: 3 entries (assuming no duplicates)
[INFO] [4/6] Transferring to CONTAORDEM...
[INFO]       Transferred: 3 entries
[INFO] [5/6] Updating status...
[INFO]       Updated: 3 entries (FINANCE="Transferido")
[INFO] [6/6] Sorting CONTAORDEM...
[INFO]       Sorted by DATA MOV. descending
[INFO] ========================================================================
[INFO] Entradas process completed successfully!
[INFO]   - Total entries processed: 3
[INFO]   - Invalid entries: 7
[INFO]   - Transferred: 3
[INFO]   - Duplicates: 0 (assumido)
[INFO]   - Status updated: 3
[INFO] ========================================================================
```

---

## 🎯 Conclusões

### ✅ Linhas Aceitas (3):
1. **Linha 2** - Todos critérios atendidos
2. **Linha 3** - Todos critérios atendidos
3. **Linha 9** - Todos critérios atendidos (TIPO alternativo)

### ❌ Linhas Rejeitadas (7):
1. **Linha 4** - TIPO inválido
2. **Linha 5** - DOC.SOMA preenchido
3. **Linha 6** - FINANCE preenchido (idempotência)
4. **Linha 7** - VALOR = 0 (não positivo)
5. **Linha 8** - DATA vazia
6. **Linha 10** - VALOR não-numérico
7. **Linha 11** - VALOR negativo

### 📈 Taxa de Aceitação:
- **30%** de aceitação (3 de 10)
- **70%** de rejeição (7 de 10)

### 🔑 Critério Mais Crítico:
- **VALOR** (causou 3 rejeições: linha 7, 10, 11)
- **TIPO** (causou 1 rejeição: linha 4)
- **Outros** (1 rejeição cada)

---

## 💡 Recomendações para Melhorar Taxa de Aceitação

1. **Validação de TIPO** no formulário de entrada (dropdown com 2 opções)
2. **Validação de VALOR** no formulário (campo numérico, valor > 0)
3. **Validação de DATA** no formulário (date picker, obrigatório)
4. **Limpeza automática** de DOC.SOMA e FINANCE antes de transferência
5. **Alertas** para usuários sobre registos rejeitados

---

Análise realizada: 24 de Agosto de 2026
