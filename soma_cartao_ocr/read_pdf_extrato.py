#!/usr/bin/env python3
"""Converter PDF para imagem e exibir."""

import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
    import os

    pdf_path = r"c:\Users\clayton.silva\OneDrive - Salsajeans\Desktop\Adobe Scan 03_08_2026.pdf"

    print("\n" + "="*80)
    print("CONVERTENDO PDF PARA IMAGEM")
    print("="*80 + "\n")

    if not os.path.exists(pdf_path):
        print(f"✗ Arquivo não encontrado: {pdf_path}")
        sys.exit(1)

    print(f"Lendo: {pdf_path}\n")

    # Converter PDF para imagens
    images = convert_from_path(pdf_path, dpi=200)

    print(f"✓ Total de páginas: {len(images)}\n")

    # Salvar cada página como imagem
    output_dir = Path("output/pdf_extrato")
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, image in enumerate(images, 1):
        output_path = output_dir / f"pagina_{idx}.png"
        image.save(str(output_path), "PNG")
        print(f"✓ Página {idx} salva: {output_path}")

    print("\n" + "="*80 + "\n")

except ImportError:
    print("✗ Erro: pdf2image não consegue encontrar poppler")
    print("  Instalando poppler-utils via choco...")
    os.system("choco install poppler -y")
