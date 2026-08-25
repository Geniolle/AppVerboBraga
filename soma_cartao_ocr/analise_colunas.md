# ANÁLISE DA EXTRAÇÃO DE COLUNAS

## Função split_columns() [linhas 478-483]

```python
def split_columns(row: list[Word], width: int, columns: dict[str, list[float]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for name, bounds in columns.items():
        selected = [word.text for word in row if width * bounds[0] <= word.cx < width * bounds[1]]
        output[name] = " ".join(selected).strip()
    return output
```

## Análise Visual do Extrato

Medindo visualmente as colunas na imagem do extrato:

### Limites Atuais (config.yaml)
```
data_movimento:   [0.00, 0.10]  = 10%
data_valor:       [0.10, 0.17]  = 7%
descricao:        [0.17, 0.52]  = 35%
pais:             [0.52, 0.55]  = 3%
moeda_original:   [0.55, 0.65]  = 10%
taxa_cambio:      [0.65, 0.78]  = 13%
debito_eur:       [0.78, 0.88]  = 10%
credito_eur:      [0.88, 1.00]  = 12%
```

### Limites Observados Visualmente no Extrato Real
```
Data Mov.         ≈ 8-10%  (START ~0px, END ~80-100px approx)
Data Valor        ≈ 8-10%  (START ~80-100px, END ~160-180px)
Descrição         ≈ 38-42% (START ~160-180px, END ~450-500px) ← GRANDE
País              ≈ 3-5%   (START ~450-500px, END ~520-560px)
Moeda Original    ≈ 9-11%  (START ~520-560px, END ~600-660px)
Taxa Câmbio       ≈ 12-15% (START ~600-660px, END ~750-850px)
Débito EUR        ≈ 8-10%  (START ~750-850px, END ~830-930px)
Crédito EUR       ≈ 12-14% (START ~830-930px, END ~960-1020px)
```

## Problemas Identificados

### 1. **Descrição pode estar muito estreita**
   - Atual: 35% (0.17 a 0.52)
   - Observado: Pode ser até 40% (0.17 a 0.57)
   - **Impacto**: Descrições longas podem ser cortadas

### 2. **Limites de País e Moeda podem estar desalinhados**
   - Atual: País [0.52, 0.55], Moeda [0.55, 0.65]
   - Possível: País [0.52, 0.57], Moeda [0.57, 0.68]
   - **Impacto**: País pode absorver palavras que seriam da Moeda

### 3. **Data Valor pode estar muito estreita**
   - Atual: 7% (0.10 a 0.17)
   - Observado: Deveria ser 8-10% (0.10 a 0.18/0.20)
   - **Impacto**: Data Valor pode ser capturada parcialmente

### 4. **Débito EUR e Crédito EUR podem estar desalinhados**
   - Atual: Débito [0.78, 0.88], Crédito [0.88, 1.00]
   - Possível overlap ou gap entre eles

## Recomendações de Correção

### Opção 1: Ajustar baseado em análise visual
```yaml
table:
  columns:
    data_movimento: [0.00, 0.10]   # OK: 10%
    data_valor:     [0.10, 0.19]   # Aumentar de 7% para 9%
    descricao:      [0.19, 0.55]   # Aumentar de 35% para 36%
    pais:           [0.55, 0.58]   # Ajustar limites
    moeda_original: [0.58, 0.68]   # Mover direita
    taxa_cambio:    [0.68, 0.79]   # Ajustar
    debito_eur:     [0.79, 0.89]   # Ajustar
    credito_eur:    [0.89, 1.00]   # Ajustar
```

### Opção 2: Usar análise automática
Implementar função que:
1. Analisa a imagem OCR
2. Detecta automaticamente as posições das colunas
3. Calcula limites dinamicamente

## Testes Necessários

- [ ] Executar com limites atuais e validar saída
- [ ] Comparar descrições extraídas com extrato original
- [ ] Verificar se "MERCADONA BRAGA" é extraído corretamente
- [ ] Verificar limites de País/Moeda com transações USA/IRL
- [ ] Validar alinhamento de valores numéricos (Débito/Crédito)

## Status

- ✓ Estrutura geral correta
- ⚠ Alguns limites podem precisar ajustes finos
- ⚠ Recomenda-se gerar relatório de diagnóstico visual
