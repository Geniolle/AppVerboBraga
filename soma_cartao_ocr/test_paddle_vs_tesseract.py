#!/usr/bin/env python3
"""Comparar PaddleOCR vs Tesseract na primeira linha (Google One)."""

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
import numpy as np
from ocr_hybrid import HybridOCR

print("\n" + "="*150)
print("COMPARACAO: PaddleOCR vs Tesseract")
print("="*150 + "\n")

# Carregar imagem
img_path = Path("output/01_contraste.png")
if not img_path.exists():
    print(f"Imagem nao encontrada: {img_path}")
    sys.exit(1)

img = cv2.imread(str(img_path))
print(f"Imagem carregada: {img.shape}\n")

# Teste 1: Tesseract
print("1. TESSERACT (Linha completa)")
print("-" * 150)

result_tess = HybridOCR.extract_with_tesseract(img, lang="eng")
print(f"Texto (primeiros 300 chars): {result_tess['text'][:300]}")
print(f"Confiança: {result_tess['confidence']:.2%}\n")

numbers_tess = HybridOCR.extract_numbers_hybrid(img)
print(f"Números: {numbers_tess['numbers']}")
print(f"Confiança: {numbers_tess['confidence']:.2%}\n")

# Teste 2: PaddleOCR
print("\n2. PADDLEOCR (Linha completa)")
print("-" * 150)

try:
    from paddle_ocr import PaddleOCREngine

    result_paddle = PaddleOCREngine.extract_text(img, lang="pt")
    print(f"Texto (primeiros 300 chars): {result_paddle['text'][:300]}")
    print(f"Confiança: {result_paddle['confidence']:.2%}\n")

    numbers_paddle = PaddleOCREngine.extract_numbers(img)
    print(f"Números: {numbers_paddle['numbers']}")
    print(f"Confiança: {numbers_paddle['confidence']:.2%}\n")

except Exception as e:
    print(f"ERRO ao carregar PaddleOCR: {e}")
    print("(Isso é esperado se a instalação ainda não terminou)\n")
    numbers_paddle = None

# Teste 3: Procurar "Google One"
print("\n3. PROCURANDO PADRAO 'GOOGLE ONE'")
print("-" * 150)

if "Google" in result_tess['text'] or "Googte" in result_tess['text']:
    print("✓ Tesseract encontrou 'Google' (ou similar)")
    # Procurar contexto
    for line in result_tess['text'].split('\n'):
        if 'google' in line.lower():
            print(f"  Linha: {line}")
else:
    print("✗ Tesseract NAO encontrou 'Google'")

if numbers_paddle is not None:
    if "Google" in result_paddle['text'] or "google" in result_paddle['text'].lower():
        print("✓ PaddleOCR encontrou 'Google'")
        for line in result_paddle['text'].split('\n'):
            if 'google' in line.lower():
                print(f"  Linha: {line}")
    else:
        print("✗ PaddleOCR NAO encontrou 'Google'")

# Teste 4: Extrair primeira linha (Google One)
print("\n4. TESTE NA PRIMEIRA LINHA (Google One)")
print("-" * 150)

# Estimar y_min, y_max para primeira linha (aproximadamente topo)
y_min = 50
y_max = 150
row_image = img[y_min:y_max, :]

print(f"ROI extraida: {row_image.shape}\n")

print("Tesseract nesta linha:")
tess_row = HybridOCR.extract_with_tesseract(row_image, lang="eng")
print(f"  Texto: {tess_row['text'][:100]}")
print(f"  Confiança: {tess_row['confidence']:.2%}")

if numbers_paddle is not None:
    print("\nPaddleOCR nesta linha:")
    try:
        paddle_row = PaddleOCREngine.extract_text(row_image, lang="pt")
        print(f"  Texto: {paddle_row['text'][:100]}")
        print(f"  Confiança: {paddle_row['confidence']:.2%}")
    except Exception as e:
        print(f"  ERRO: {e}")

# Resumo
print("\n" + "="*150)
print("RESUMO")
print("="*150 + "\n")

print("Tesseract:")
print(f"  - Encontrou 'Google': {'Sim' if 'Google' in result_tess['text'] or 'Googte' in result_tess['text'] else 'Nao'}")
print(f"  - Números capturados: {numbers_tess['numbers']}")
print(f"  - Confiança média: {numbers_tess['confidence']:.2%}")

if numbers_paddle is not None:
    print("\nPaddleOCR:")
    print(f"  - Encontrou 'Google': {'Sim' if 'google' in result_paddle['text'].lower() else 'Nao'}")
    print(f"  - Números capturados: {numbers_paddle['numbers']}")
    print(f"  - Confiança média: {numbers_paddle['confidence']:.2%}")

    print("\nVencedor:")
    if len(numbers_paddle['numbers']) > len(numbers_tess['numbers']):
        print("  PaddleOCR capturou MAIS números ✓")
    elif len(numbers_paddle['numbers']) < len(numbers_tess['numbers']):
        print("  Tesseract capturou MAIS números ✓")
    else:
        print("  Empate em quantidade de números")

print("\n" + "="*150 + "\n")
