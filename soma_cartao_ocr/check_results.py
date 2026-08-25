#!/usr/bin/env python3
import json
from pathlib import Path

result_file = Path("resultado.json")
if result_file.exists():
    with open(result_file) as f:
        data = json.load(f)
    
    movements = data.get("movements", [])
    print(f"\n{'='*150}")
    print(f"Total de transações: {len(movements)}\n")
    
    for i, mov in enumerate(movements[:5], 1):
        print(f"Linha {i}:")
        print(f"  Data: {mov.get('data_movimento', '')}")
        print(f"  Desc: {mov.get('descricao', '')}")
        print(f"  Débito: {mov.get('debito_eur', '')}")
        print(f"  Crédito: {mov.get('credito_eur', '')}")
        print(f"  Status: {mov.get('status', '')}\n")
    
    print(f"{'='*150}")
    print("🔍 Procurando Google One...")
    for i, mov in enumerate(movements, 1):
        if "Google One" in mov.get("descricao", ""):
            print(f"\n✅ Encontrado na linha {i}:")
            print(f"   Data Mov: {mov.get('data_movimento', '')}")
            print(f"   Descrição: {mov.get('descricao', '')}")
            print(f"   Débito EUR: '{mov.get('debito_eur', '')}'")
            print(f"   Crédito EUR: '{mov.get('credito_eur', '')}'")
            print(f"   Status: {mov.get('status', '')}")
            break
else:
    print("resultado.json não encontrado")
