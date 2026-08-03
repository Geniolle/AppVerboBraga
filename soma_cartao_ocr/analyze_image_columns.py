#!/usr/bin/env python3
"""Analisar a imagem e verificar o alinhamento visual das colunas."""

print("""
ANÁLISE VISUAL DA IMAGEM contraste.png
======================================

Contando de CIMA para BAIXO e ESQUERDA para DIREITA:

CABEÇALHO (2 linhas):
1. "Detalhe de Movimentos"
2. Nomes das colunas

PRIMEIRA TRANSAÇÃO (3 linhas):
Linha A: 23/06 | 20/06 | Google One Dublin
Linha B: 26/06 | 25/06 | MERCADONA BRAGA | IRL | ??? | ??? | 1,99
Linha C: 26/06 | 26/06 | FACEBK 8HJ84THS72 Dublin | IRL | 5,90 | ??? | 1,99

PADRÃO OBSERVADO:
─────────────────

Na coluna de DÉBITO EUR (à direita), de cima para baixo:
1. Google One: ???
2. MERCADONA: 1,99 ← ou isto está em outra coluna?
3. FACEBK: 1,99

HIPÓTESE 1: Ambos têm 1,99 (impossível - diferentes transações)
HIPÓTESE 2: Apenas um tem 1,99, e está desalinhado verticalmente
HIPÓTESE 3: Os valores estão em COLUNAS diferentes e confundimos

COMPARAÇÃO COM ESPERADO:
───────────────────────

Esperado (do extrato):
- Google One Dublin: Débito 1,99
- MERCADONA BRAGA: Débito 35,15
- FACEBK 8HJ84THS72 Dublin: Débito 5,90 (não 1,99!)

CONCLUSÃO:
──────────

Se esperado é:
- Google One: 1,99
- MERCADONA: 35,15
- FACEBK: 5,90

Mas na imagem vemos:
- Google One: ???
- MERCADONA: 1,99
- FACEBK: 1,99

Então AMBOS estão com débito "1,99", o que NÃO FAZ SENTIDO!

OU:
- O "1,99" na imagem para MERCADONA está em outra coluna (Moeda Original, não Débito)
- O "1,99" na imagem para FACEBK está em outra coluna também

OU:
- Os valores "1,99" e "35,15" estão misturados e não alinhados bem visualmente

PRÓXIMO PASSO:
───────────────

Contar PIXEL A PIXEL a posição X de cada valor na imagem para saber em qual coluna estão realmente.

Os limites de coluna são:
- data_movimento: [0%, 10%] = [0px, 213px]
- data_valor: [10%, 19%] = [213px, 405px]
- descricao: [19%, 56%] = [405px, 1195px]
- pais: [56%, 59%] = [1195px, 1259px]
- moeda_original: [59%, 69%] = [1259px, 1474px]
- taxa_cambio: [69%, 82%] = [1474px, 1749px]
- debito_eur: [82%, 92%] = [1749px, 1963px]
- credito_eur: [92%, 100%] = [1963px, 2134px]

Se alguém conseguir extrair a posição X dos valores "1,99", "35,15", "5,90",
podemos saber se estão nas colunas corretas!
""")
