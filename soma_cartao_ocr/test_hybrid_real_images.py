#!/usr/bin/env python3
"""Testar OCR Híbrido com imagens reais."""

import sys
import os
from pathlib import Path

# Configurar PATH ANTES de importar pytesseract
if sys.platform == "win32":
    os.environ["PATH"] = r"C:\Program Files\Tesseract-OCR" + os.pathsep + os.environ["PATH"]

import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, str(Path(__file__).parent))

from ocr_hybrid import HybridOCR
import cv2

print("\n" + "="*150)
print("TESTE: OCR HÍBRIDO COM IMAGENS REAIS")
print("="*150 + "\n")

test_images = [
    ("temp_cleaned_digits.jpg", "Dígitos Limpos (Melhor)"),
    ("temp_fused_digits.jpg", "Dígitos Fusão"),
    ("temp_adaptive_digits.jpg", "Dígitos Adaptativo"),
    ("output/01_contraste.png", "Contraste Original"),
]

results = []

print("Testando diferentes pré-processamentos:\n")

for img_path, description in test_images:
    if not Path(img_path).exists():
        print(f"❌ {description}: {img_path} NÃO ENCONTRADO\n")
        continue

    print(f"{'='*150}")
    print(f"📌 {description}: {img_path}")
    print(f"{'='*150}\n")

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"❌ Erro ao carregar imagem\n")
        continue

    # Teste 1: Tesseract direto
    print("1️⃣  TESSERACT DIRETO (sem otimização):")
    result_direct = HybridOCR.extract_with_tesseract(img, lang="eng")
    print(f"   Texto: '{result_direct['text']}'")
    print(f"   Confiança: {result_direct['confidence']:.2%}")
    if result_direct.get("error"):
        print(f"   Erro: {result_direct['error']}")
    print()

    # Teste 2: Hybrid para números
    print("2️⃣  HYBRID OCR (com pré-processamento para dígitos):")
    result_hybrid = HybridOCR.extract_numbers_hybrid(img)
    print(f"   Números: '{result_hybrid['numbers']}'")
    print(f"   Confiança: {result_hybrid['confidence']:.2%}")
    print(f"   Fonte: {result_hybrid['source']}")
    if result_hybrid.get("error"):
        print(f"   Erro: {result_hybrid['error']}")
    print()

    results.append({
        "description": description,
        "path": img_path,
        "direct": result_direct['text'],
        "hybrid": result_hybrid['numbers'],
        "confidence": result_hybrid['confidence']
    })

print("\n" + "="*150)
print("RESUMO DOS RESULTADOS")
print("="*150 + "\n")

for r in results:
    print(f"📌 {r['description']}: {r['path']}")
    if r['direct'] or r['hybrid']:
        print(f"   ✅ Texto direto: '{r['direct']}'")
        print(f"   ✅ Números hybrid: '{r['hybrid']}' (confiança: {r['confidence']:.2%})")
    else:
        print(f"   ❌ Nada capturado")
    print()

# Verificar se conseguiu capturar algo
captured_any = any(r['hybrid'] for r in results)

print("\n" + "="*150)
if captured_any:
    print("✅ SUCESSO! Tesseract capturou números!")
    print("="*150 + "\n")
    print("Próximo passo: Integrar em main.py para capturar 'Débito EUR'")
else:
    print("⚠️  Nenhum número foi capturado")
    print("="*150 + "\n")
    print("Possíveis causas:")
    print("  1. Imagens de teste não têm números visíveis")
    print("  2. Tesseract precisa de imagens com melhor contraste")
    print("  3. Números na imagem original são muito pequenos")
print()
