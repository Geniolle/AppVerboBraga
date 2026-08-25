#!/usr/bin/env python3
"""Tabela temporária para visualizar e validar dados ANTES de escrever na Sheet."""

import sys
import os
from pathlib import Path
import json

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import vision
import yaml

print("\n" + "="*200)
print("PREVIEW: TABELA TEMPORARIA DE VALIDACAO (ANTES DE ESCREVER NA SHEET)")
print("="*200 + "\n")

# Carregar config
with open("config.yaml", encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# Carregar resultado.json para ver o que foi extraído
with open("output/resultado.json", encoding='utf-8') as f:
    resultado = json.load(f)

# Preparar dados para tabela
rows_data = []

for movimento in resultado.get('movimentos', []):
    rows_data.append({
        'ID': f"CAR{movimento.get('id', '').replace('CAR', '')}",
        'Line': movimento.get('line', ''),
        'Data Mov.': movimento.get('data_movimento', ''),
        'Data Valor': movimento.get('data_valor', ''),
        'Descrição': movimento.get('descricao', '')[:50],  # Truncar para exibição
        'País': movimento.get('pais', ''),
        'Moeda Original': movimento.get('moeda_original', ''),
        'Taxa de Câmbio': movimento.get('taxa_cambio', ''),
        'Débito EUR': movimento.get('debito_eur', ''),
        'Crédito EUR': movimento.get('credito_eur', ''),
        'Status': movimento.get('status', ''),
        'Confiança': f"{movimento.get('confidence', 0):.2%}",
    })

# Criar DataFrame
df = pd.DataFrame(rows_data)

print("📋 TABELA TEMPORARIA - TODOS OS MOVIMENTOS EXTRAIDOS\n")
print(f"Total de movimentos: {len(df)}\n")

# Exibir com pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 30)

print(df.to_string(index=False))

print("\n" + "="*200)
print("VALIDACAO: VERIFICACOES DE INTEGRIDADE")
print("="*200 + "\n")

# Validações
issues = []

# 1. Verificar datas
for idx, row in df.iterrows():
    data_mov = row['Data Mov.'].strip()
    data_valor = row['Data Valor'].strip()
    status = row['Status']

    if status == 'válido':
        # Verificar formato DD/MM/YYYY
        if data_mov and '/' not in data_mov:
            issues.append(f"Linha {idx+1}: Data Movimento sem barra: '{data_mov}'")
        if data_valor and '/' not in data_valor:
            issues.append(f"Linha {idx+1}: Data Valor sem barra: '{data_valor}'")

        # Verificar ordem (Data Mov <= Data Valor)
        if data_mov and data_valor:
            try:
                dm = data_mov.split('/')[1] + data_mov.split('/')[0]  # Converte DD/MM para MMDD para comparação
                dv = data_valor.split('/')[1] + data_valor.split('/')[0]
                if dm > dv:
                    issues.append(f"Linha {idx+1}: Data Movimento > Data Valor ({data_mov} > {data_valor})")
            except:
                pass

# 2. Verificar valores monetários
for idx, row in df.iterrows():
    if row['Status'] == 'válido':
        debito = row['Débito EUR'].strip()
        credito = row['Crédito EUR'].strip()

        # Deve ter exatamente um ou outro
        has_debito = debito and debito not in ['0', '0.00', '0,00', '']
        has_credito = credito and credito not in ['0', '0.00', '0,00', '']

        if not has_debito and not has_credito:
            issues.append(f"Linha {idx+1}: Nem débito nem crédito preenchidos")
        if has_debito and has_credito:
            issues.append(f"Linha {idx+1}: Ambos débito e crédito preenchidos")

# 3. Verificar descrições vazias
for idx, row in df.iterrows():
    if row['Status'] == 'válido':
        desc = row['Descrição'].strip()
        if not desc or desc == '':
            issues.append(f"Linha {idx+1}: Descrição vazia")

# 4. Verificar país
for idx, row in df.iterrows():
    if row['Status'] == 'válido':
        pais = row['País'].strip()
        if pais and len(pais) > 3:
            issues.append(f"Linha {idx+1}: País muito longo: '{pais}'")

if issues:
    print("❌ PROBLEMAS ENCONTRADOS:\n")
    for issue in issues:
        print(f"  • {issue}")
else:
    print("✅ NENHUM PROBLEMA ENCONTRADO!")

print("\n" + "="*200)
print("RESUMO ESTATISTICO")
print("="*200 + "\n")

valid_count = len(df[df['Status'] == 'válido'])
review_count = len(df[df['Status'] == 'revisão'])
rejected_count = len(df[df['Status'] == 'rejeitado'])

print(f"Total de movimentos:      {len(df)}")
print(f"  ✅ Válidos (a escrever):  {valid_count}")
print(f"  ⚠️  Revisão:              {review_count}")
print(f"  ❌ Rejeitados:            {rejected_count}")
print(f"Taxa de sucesso:          {valid_count/len(df)*100:.1f}%")
print(f"Confiança média:          {df['Confiança'].str.rstrip('%').astype(float).mean():.1f}%")

print("\n" + "="*200)
print("DETALHE: MOVIMENTOS VALIDOS (O QUE SERA ESCRITO)")
print("="*200 + "\n")

valid_df = df[df['Status'] == 'válido'].copy()

if len(valid_df) > 0:
    print(valid_df[['Data Mov.', 'Data Valor', 'Descrição', 'País', 'Débito EUR', 'Status']].to_string(index=False))
else:
    print("❌ Nenhum movimento válido para escrever!")

print("\n" + "="*200)
print("DETALHE: MOVIMENTOS PARA REVISAO")
print("="*200 + "\n")

review_df = df[df['Status'] == 'revisão'].copy()

if len(review_df) > 0:
    print(review_df[['Data Mov.', 'Data Valor', 'Descrição', 'Confiança', 'Status']].to_string(index=False))
else:
    print("Nenhum movimento para revisão")

print("\n" + "="*200 + "\n")

# Salvar em CSV temporário para análise
output_csv = Path("output/preview_temporario.csv")
df.to_csv(output_csv, index=False, encoding='utf-8')
print(f"✅ Tabela temporária salva em: {output_csv}\n")
