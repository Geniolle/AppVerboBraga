#!/usr/bin/env python3
"""Teste do OCR Híbrido para capturar números."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocr_hybrid import HybridOCR
import cv2

print("\n" + "="*150)
print("TESTE: OCR HÍBRIDO PARA NÚMEROS")
print("="*150 + "\n")

# Testar com a imagem otimizada para dígitos
test_images = [
    ("temp_cleaned_digits.jpg", "Dígitos Limpos (Melhor)"),
    ("temp_fused_digits.jpg", "Dígitos Fusão"),
    ("temp_adaptive_digits.jpg", "Dígitos Adaptativo"),
    ("output/01_contraste.png", "Contraste Original"),
]

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
    print(f"   Confiança: {result_direct['confidence']:.2%}\n")

    # Teste 2: Hybrid para números
    print("2️⃣  HYBRID OCR (com pré-processamento):")
    result_hybrid = HybridOCR.extract_numbers_hybrid(img)
    print(f"   Números: '{result_hybrid['numbers']}'")
    print(f"   Confiança: {result_hybrid['confidence']:.2%}")
    print(f"   Fonte: {result_hybrid['source']}")
    if result_hybrid.get("error"):
        print(f"   Erro: {result_hybrid['error']}")
    print()

print("\n" + "="*150)
print("PRÓXIMO PASSO: Usar best em main.py")
print("="*150 + "\n")

print("""
✅ Se temp_cleaned_digits.jpg consegue capturar números:
   → Integrar HybridOCR em build_movements()
   → Quando debito_eur está vazio, tentar Tesseract
   → Testar na primeira linha (Google One: 1,99)

❌ Se nenhuma funciona:
   → Problema é no Vision API ou preprocessing
   → Tesseract não consegue ver os números nem com otimização
   → Pode ser necessário revisar a qualidade original da imagem
""")

print("="*150 + "\n")
