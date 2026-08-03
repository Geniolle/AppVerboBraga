#!/usr/bin/env python3
"""Converter PDF para imagem usando PyMuPDF (fitz)."""

import sys
import fitz
from pathlib import Path

pdf_path = r"c:\Users\clayton.silva\OneDrive - Salsajeans\Desktop\Adobe Scan 03_08_2026.pdf"

print("\n" + "="*80)
print("CONVERTENDO PDF PARA IMAGEM (PyMuPDF)")
print("="*80 + "\n")

try:
    # Abrir PDF
    doc = fitz.open(pdf_path)
    print(f"✓ PDF aberto: {pdf_path}")
    print(f"✓ Total de páginas: {doc.page_count}\n")

    # Criar diretório de saída
    output_dir = Path("output/pdf_extrato")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Converter cada página para imagem
    for page_num in range(doc.page_count):
        page = doc[page_num]

        # Renderizar página como imagem
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom

        # Salvar como PNG
        output_path = output_dir / f"pagina_{page_num + 1}.png"
        pix.save(str(output_path))

        print(f"✓ Página {page_num + 1} salva: {output_path}")

    doc.close()
    print("\n" + "="*80)
    print("✓ CONVERSÃO CONCLUÍDA")
    print("="*80 + "\n")

except Exception as e:
    print(f"✗ Erro: {e}\n")
    sys.exit(1)
