#!/usr/bin/env python3
"""Analisar os dados já extraídos para identificar o padrão de desalinhamento."""

import json
from pathlib import Path

resultado_json = Path("output/resultado.json")

if not resultado_json.exists():
    print(f"❌ Arquivo não encontrado: {resultado_json}")
    exit(1)

print("\n" + "="*140)
print("ANÁLISE DE DESALINHAMENTO - Dados Extraídos vs Esperado")
print("="*140 + "\n")

with open(resultado_json, encoding="utf-8") as f:
    data = json.load(f)

movimentos = data.get("movimentos", [])

# Dados esperados do extrato (CORRIGIDO BASEADO NA IMAGEM REAL - LEITURA FINAL)
esperado = [
    {"desc": "Google One Dublin", "pais": "", "taxa": "", "debito": ""},
    {"desc": "MERCADONA BRAGA", "pais": "IRL", "taxa": "", "debito": ""},
    {"desc": "FACEBK 8HJ84THS72 Dublin", "pais": "IRL", "taxa": "5.90", "debito": "1.99"},
    {"desc": "OPUS CLIP OPUS.PRO", "pais": "IRL", "taxa": "", "debito": "35.15"},
    {"desc": "COMISSAO ESTRANGEIRO", "pais": "USA", "taxa": "29.00", "debito": "5.90"},
    {"desc": "IS-TGIS 17.3.4.", "pais": "", "taxa": "", "debito": "29.00"},
    {"desc": "LEVANT. NUMERÁRIO A CRÉDITO", "pais": "", "taxa": "", "debito": "1.09"},
    {"desc": "COMISSAO CASH", "pais": "", "taxa": "", "debito": "160.00"},
    {"desc": "IS-TGIS 17.3.4.", "pais": "", "taxa": "", "debito": "11.20"},
    {"desc": "CANVA 104920-25183857 CANVA.CO", "pais": "USA", "taxa": "12.00", "debito": "12.00"},
]

print("COMPARAÇÃO LINHA POR LINHA:")
print("-" * 140)
print(f"{'LN':<3} {'DESCRIÇÃO EXTRAÍDA':<40} {'PAÍS':<8} {'TAXA':<12} {'DÉBITO':<12} | {'DESC ESP':<40} | MATCH")
print("-" * 140)

mismatches = []

for idx, (mov, esp) in enumerate(zip(movimentos[:10], esperado[:10]), 1):
    desc_obs = mov.get("descricao", "")[:38]
    pais_obs = mov.get("pais", "")
    taxa_obs = str(mov.get("taxa_cambio", ""))
    debito_obs = str(mov.get("debito_eur", ""))

    desc_esp = esp["desc"][:38]
    pais_esp = esp["pais"]
    taxa_esp = esp["taxa"]
    debito_esp = esp["debito"]

    # Verificar matches
    desc_match = desc_obs.lower() in desc_esp.lower() or desc_esp.lower() in desc_obs.lower()
    pais_match = pais_obs == pais_esp
    taxa_match = taxa_obs == taxa_esp
    debito_match = debito_obs == debito_esp

    overall_match = "✓" if (desc_match and pais_match and taxa_match and debito_match) else "✗"

    print(f"{idx:<3} {desc_obs:<40} {pais_obs:<8} {taxa_obs:<12} {debito_obs:<12} | {desc_esp:<40} | {overall_match}")

    if not (pais_match and taxa_match and debito_match):
        mismatches.append({
            "linha": idx,
            "desc": desc_obs,
            "pais": {"obs": pais_obs, "esp": pais_esp, "match": pais_match},
            "taxa": {"obs": taxa_obs, "esp": taxa_esp, "match": taxa_match},
            "debito": {"obs": debito_obs, "esp": debito_esp, "match": debito_match},
        })

print("\n" + "="*140)
print("ANÁLISE DE DISCREPÂNCIAS")
print("="*140 + "\n")

if mismatches:
    for m in mismatches:
        print(f"LINHA {m['linha']}: {m['desc']}")
        if not m['pais']['match']:
            print(f"  País: obs='{m['pais']['obs']}' esp='{m['pais']['esp']}' ✗")
        if not m['taxa']['match']:
            print(f"  Taxa: obs='{m['taxa']['obs']}' esp='{m['taxa']['esp']}' ✗")
        if not m['debito']['match']:
            print(f"  Débito: obs='{m['debito']['obs']}' esp='{m['debito']['esp']}' ✗")
        print()

print("="*140)
print("PADRÃO IDENTIFICADO")
print("="*140 + "\n")

# Procura padrão
debito_matches = sum(1 for m in mismatches if m['debito']['match'])
debito_mismatches = len(mismatches) - debito_matches

if debito_mismatches > 0:
    print(f"⚠️  Débitos DESALINHADOS: {debito_mismatches}/{len(mismatches)}")
    print("\nPadrão de desalinhamento:")
    for idx in range(min(3, len(mismatches))):
        m = mismatches[idx]
        # Verificar se o débito desta linha corresponde ao da linha anterior
        if idx > 0 and movimentos[idx-1].get("debito_eur", "") == m['debito']['esp']:
            print(f"  Linha {m['linha']}: Débito '{m['debito']['obs']}' = Débito esperado da linha {m['linha']-1} '{esperado[m['linha']-2]['debito']}'")
        elif idx < len(movimentos) - 1 and movimentos[idx+1].get("debito_eur", "") == m['debito']['esp']:
            print(f"  Linha {m['linha']}: Débito '{m['debito']['obs']}' = Débito esperado da linha {m['linha']+1}")

print("\n" + "="*140 + "\n")
