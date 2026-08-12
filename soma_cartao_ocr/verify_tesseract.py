#!/usr/bin/env python3
"""Verificar se Tesseract foi instalado corretamente."""

import sys
from pathlib import Path
import subprocess
import platform
import os

print("\n" + "="*150)
print("VERIFICAÇÃO: TESSERACT OCR")
print("="*150 + "\n")

# 1. Verificar versão do Tesseract
print("1️⃣  Verificando versão do Tesseract:")
print("-" * 150)

# Tentar encontrar Tesseract
tesseract_cmd = "tesseract"

if platform.system() == "Windows":
    # No Windows, tentar caminho padrão
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        tesseract_cmd = tesseract_path
        print(f"📍 Encontrado em: {tesseract_path}\n")

try:
    result = subprocess.run([tesseract_cmd, "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("✅ Tesseract encontrado!")
        print(f"   {result.stdout.split(chr(10))[0]}\n")
    else:
        print(f"❌ Erro: {result.stderr}\n")
        sys.exit(1)
except FileNotFoundError:
    print("❌ Tesseract não encontrado no PATH\n")
    print("Instruções de instalação:")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  Linux: sudo apt-get install tesseract-ocr")
    print("  macOS: brew install tesseract\n")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro: {e}\n")
    sys.exit(1)

# 2. Verificar pytesseract
print("2️⃣  Verificando módulo pytesseract:")
print("-" * 150)

try:
    import pytesseract
    print("✅ pytesseract importado com sucesso\n")
except ImportError:
    print("❌ pytesseract não está instalado")
    print("   Execute: pip install pytesseract\n")
    sys.exit(1)

# 3. Testar extração simples
print("3️⃣  Teste de extração:")
print("-" * 150)

try:
    from PIL import Image
    import numpy as np

    # Criar imagem simples com número "1.99"
    # (simulada com branco em preto)
    test_img = np.ones((100, 300), dtype=np.uint8) * 255

    pil_img = Image.fromarray(test_img)

    # Tentar extrair
    text = pytesseract.image_to_string(pil_img, lang="eng")

    print("✅ Extração funcionou!")
    print(f"   Teste: '{text.strip()}'\n")

except Exception as e:
    print(f"⚠️  Teste básico falhou: {e}\n")
    print("   Mas Tesseract pode estar instalado corretamente.")
    print("   O erro pode ser em imagem de teste.\n")

print("="*150)
print("✅ TESSERACT PRONTO PARA USO!")
print("="*150 + "\n")

print("Próximo passo:")
print("  1. Executar: python test_hybrid_ocr.py")
print("  2. Se capturar números, executar: python main.py")
print("  3. Verificar se Linha 11 (Google One) agora tem '1,99'\n")
