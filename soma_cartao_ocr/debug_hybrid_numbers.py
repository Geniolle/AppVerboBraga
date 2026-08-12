#!/usr/bin/env python3
"""Debug: quais números o Tesseract capturou para a linha Google One."""

import sys
import os

# Configurar PATH
if sys.platform == "win32":
    os.environ["PATH"] = r"C:\Program Files\Tesseract-OCR" + os.pathsep + os.environ["PATH"]

import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from pathlib import Path
import cv2
import numpy as np
from ocr_hybrid import HybridOCR
import re

# Carregar a imagem
img_path = Path("output/01_contraste.png")
if not img_path.exists():
    print(f"Imagem não encontrada: {img_path}")
    sys.exit(1)

img = cv2.imread(str(img_path))
print(f"\nImagem carregada: {img.shape}")

# Extrair texto completo
from PIL import Image
pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
full_text = pytesseract.image_to_string(pil_img, lang="eng")

print(f"\n{'='*150}")
print("TEXTO COMPLETO DO TESSERACT:")
print(f"{'='*150}")
print(full_text[:500])

# Procurar por Google One
if "Google One" in full_text:
    print(f"\n{'='*150}")
    print("ENCONTRADO: Google One")
    print(f"{'='*150}")

    # Extrair números
    numbers = re.findall(r'\d+[.,]\d+', full_text)
    print(f"\nNúmeros encontrados: {numbers}")

    # Procurar especificamente ao redor de "Google One"
    google_one_idx = full_text.find("Google One")
    context = full_text[google_one_idx:google_one_idx+100]
    print(f"\nContexto around Google One:")
    print(f"  '{context}'")

    # Números neste contexto
    numbers_near = re.findall(r'\d+[.,]\d+', context)
    print(f"\nNúmeros perto de Google One: {numbers_near}")

print()
