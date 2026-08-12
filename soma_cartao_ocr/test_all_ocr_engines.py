#!/usr/bin/env python3
"""Comparar todos os motores OCR: Vision API vs Tesseract vs EasyOCR."""

import sys
import os
from pathlib import Path

# Configurar Tesseract PATH
if sys.platform == "win32":
    os.environ["PATH"] = r"C:\Program Files\Tesseract-OCR" + os.pathsep + os.environ["PATH"]
    try:
        import pytesseract
        pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    except:
        pass

sys.stdout.reconfigure(encoding='utf-8')

import cv2
from ocr_hybrid import HybridOCR

print("\n" + "="*150)
print("COMPARACAO: Vision API vs Tesseract vs EasyOCR")
print("="*150 + "\n")

# Carregar imagem
img_path = Path("output/01_contraste.png")
if not img_path.exists():
    print(f"Imagem nao encontrada: {img_path}")
    sys.exit(1)

img = cv2.imread(str(img_path))
print(f"Imagem carregada: {img.shape}\n")

# Teste 1: Vision API (simulado com Tesseract geral)
print("1. VISION API (simulado com OCR geral)")
print("-" * 150)

result_vision = HybridOCR.extract_with_tesseract(img, lang="eng")
print(f"Texto (primeiros 200 chars): {result_vision['text'][:200]}")
print(f"Confiança: {result_vision['confidence']:.2%}")

# Teste 2: Tesseract
print("\n2. TESSERACT (otimizado para números)")
print("-" * 150)

numbers_tess = HybridOCR.extract_numbers_hybrid(img)
print(f"Números: {numbers_tess['numbers']}")
print(f"Confiança: {numbers_tess['confidence']:.2%}")
print(f"Quantidade: {len(numbers_tess['numbers'].split(',')) if numbers_tess['numbers'] else 0}")

# Teste 3: EasyOCR
print("\n3. EASYOCR (multilíngue)")
print("-" * 150)

try:
    from easy_ocr import EasyOCREngine

    result_easy = EasyOCREngine.extract_text(img)
    print(f"Texto (primeiros 200 chars): {result_easy['text'][:200]}")
    print(f"Confiança: {result_easy['confidence']:.2%}")

    numbers_easy = EasyOCREngine.extract_numbers(img)
    print(f"\nNúmeros: {numbers_easy['numbers']}")
    print(f"Confiança: {numbers_easy['confidence']:.2%}")
    print(f"Quantidade: {len(numbers_easy['numbers'].split(',')) if numbers_easy['numbers'] else 0}")

except Exception as e:
    print(f"ERRO ao usar EasyOCR: {e}")
    print("(Isso pode ser esperado se EasyOCR ainda está inicializando)\n")
    numbers_easy = None

# Comparação
print("\n" + "="*150)
print("RESUMO COMPARATIVO")
print("="*150 + "\n")

print("Tesseract:")
print(f"  - Números capturados: {numbers_tess['numbers'][:50]}...")
print(f"  - Confiança: {numbers_tess['confidence']:.2%}")
print(f"  - Quantidade: {len(numbers_tess['numbers'].split(',')) if numbers_tess['numbers'] else 0}")

if numbers_easy:
    print("\nEasyOCR:")
    print(f"  - Números capturados: {numbers_easy['numbers'][:50]}...")
    print(f"  - Confiança: {numbers_easy['confidence']:.2%}")
    print(f"  - Quantidade: {len(numbers_easy['numbers'].split(',')) if numbers_easy['numbers'] else 0}")

print("\n" + "="*150)
print("RECOMENDACAO")
print("="*150 + "\n")

if numbers_easy and numbers_easy['numbers']:
    print("✓ EasyOCR é uma alternativa viável ao Tesseract")
    print("✓ Próximo passo: Integrar EasyOCR em main.py como fallback adicional")
else:
    print("✓ Tesseract continua como melhor opção por enquanto")
    print("✓ EasyOCR será testado em próxima oportunidade")

print("\n" + "="*150 + "\n")
