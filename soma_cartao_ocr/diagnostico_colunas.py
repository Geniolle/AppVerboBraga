#!/usr/bin/env python3
"""Diagnóstico visual de extração de colunas."""

import yaml
from pathlib import Path

# Carregar config
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

columns = cfg["table"]["columns"]

print("\n" + "="*100)
print("DIAGNÓSTICO DE EXTRAÇÃO DE COLUNAS")
print("="*100 + "\n")

print("CONFIGURAÇÃO ATUAL (config.yaml):")
print("-" * 100)
print(f"{'COLUNA':<20} {'INÍCIO':<10} {'FIM':<10} {'LARGURA':<10} {'VISUALIZAÇÃO':<50}")
print("-" * 100)

total_width = 0
col_visual = []

for name, bounds in columns.items():
    start = bounds[0]
    end = bounds[1]
    width = end - start
    total_width += width

    # Criar visualização
    bar_length = 40
    bar_start = int(start * bar_length)
    bar_width = max(1, int(width * bar_length))
    bar = " " * bar_start + "█" * bar_width + " " * (bar_length - bar_start - bar_width)

    print(f"{name:<20} {start:<10.2f} {end:<10.2f} {width:<10.2%} {bar:<50}")
    col_visual.append(f"{name}: {width:.1%}")

print("-" * 100)
print(f"{'TOTAL':<20} {'0.00':<10} {'1.00':<10} {total_width:<10.2%}")

print("\n" + "="*100)
print("RESUMO VISUAL (para imagem de ~1200px de largura):")
print("="*100 + "\n")

img_width = 1200
print(f"{'COLUNA':<20} {'PIXELS (1200px)':<20} {'LARGURA PX':<15}")
print("-" * 100)

for name, bounds in columns.items():
    start_px = int(bounds[0] * img_width)
    end_px = int(bounds[1] * img_width)
    width_px = end_px - start_px
    print(f"{name:<20} {start_px:>5}px - {end_px:<5}px  {width_px:>6}px")

print("\n" + "="*100)
print("PROBLEMAS POTENCIAIS:")
print("="*100 + "\n")

problems = []

# Verificar se Descrição é muito estreita
desc_width = columns["descricao"][1] - columns["descricao"][0]
if desc_width < 0.35:
    problems.append(f"⚠ Descrição muito estreita ({desc_width:.1%}), deveria ser ~36-40%")

# Verificar se Data Valor é muito estreita
dv_width = columns["data_valor"][1] - columns["data_valor"][0]
if dv_width < 0.08:
    problems.append(f"⚠ Data Valor muito estreita ({dv_width:.1%}), deveria ser ~8-10%")

# Verificar sobreposições
for i, (name1, bounds1) in enumerate(list(columns.items())):
    for name2, bounds2 in list(columns.items())[i+1:]:
        if bounds1[1] > bounds2[0]:
            overlap = min(bounds1[1], bounds2[1]) - bounds2[0]
            if overlap > 0.01:
                problems.append(f"⚠ Sobreposição entre {name1} e {name2}: {overlap:.1%}")

if not problems:
    print("✓ Nenhum problema óbvio detectado")
else:
    for problem in problems:
        print(problem)

print("\n" + "="*100)
print("RECOMENDAÇÃO:")
print("="*100 + "\n")

print("""
Execute a análise da imagem OCR para validar se as colunas estão sendo extraídas corretamente:

1. Gere o relatório de diagnóstico visual
2. Compare as descrições extraídas com o extrato original
3. Valide especialmente:
   - "MERCADONA BRAGA" (2 palavras distintas)
   - "FACEBK 8HJ84THS72 Dublin" (múltiplas componentes)
   - "RECHEIO CASH & CARRY BRAGA" (com caracteres especiais)

4. Se houver problemas:
   - Ajuste os limites de colunas em config.yaml
   - Re-execute o OCR
   - Valide novamente
""")

print("="*100 + "\n")
