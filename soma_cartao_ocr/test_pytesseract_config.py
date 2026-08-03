#!/usr/bin/env python3
"""Testar configuração do pytesseract com caminho do Tesseract."""

import sys
import os
import platform

print("\n" + "="*150)
print("TESTE: CONFIGURAÇÃO DO PYTESSERACT")
print("="*150 + "\n")

# 1. Detectar plataforma e configurar PATH
print("1️⃣  Configurando caminho do Tesseract:")
print("-" * 150)

if platform.system() == "Windows":
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        print(f"✅ Encontrado: {tesseract_path}")
        # Adicionar ao PATH do sistema
        os.environ["PATH"] = r"C:\Program Files\Tesseract-OCR" + os.pathsep + os.environ["PATH"]
        print(f"✅ PATH configurado\n")
    else:
        print(f"❌ Não encontrado: {tesseract_path}\n")
        sys.exit(1)

# 2. Importar e configurar pytesseract
print("2️⃣  Importando pytesseract:")
print("-" * 150)

try:
    import pytesseract
    print("✅ pytesseract importado\n")
except ImportError as e:
    print(f"❌ Erro: {e}\n")
    sys.exit(1)

# 3. Configurar caminho no pytesseract
print("3️⃣  Configurando pytesseract.pytesseract_cmd:")
print("-" * 150)

pytesseract.pytesseract.pytesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
print(f"✅ Caminho configurado: {pytesseract.pytesseract.pytesseract_cmd}\n")

# 4. Testar extração
print("4️⃣  Testando extração com imagem simples:")
print("-" * 150)

try:
    from PIL import Image
    import numpy as np

    # Criar imagem simples (branca)
    test_img = np.ones((100, 300), dtype=np.uint8) * 255
    pil_img = Image.fromarray(test_img)

    result = pytesseract.image_to_string(pil_img, lang="eng")
    print(f"✅ Extração funcionou! Resultado: '{result.strip()}'\n")

except Exception as e:
    print(f"❌ Erro na extração: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*150)
print("✅ PYTESSERACT FUNCIONAL!")
print("="*150 + "\n")

print("Agora testando com ocr_hybrid.py...\n")

# 5. Testar ocr_hybrid
print("5️⃣  Carregando ocr_hybrid:")
print("-" * 150)

try:
    from ocr_hybrid import HybridOCR, TESSERACT_AVAILABLE
    print(f"✅ ocr_hybrid carregado")
    print(f"   TESSERACT_AVAILABLE = {TESSERACT_AVAILABLE}\n")

    # Teste com a mesma imagem
    result = HybridOCR.extract_with_tesseract(test_img, lang="eng")
    print(f"✅ HybridOCR.extract_with_tesseract funcionou!")
    print(f"   Texto: '{result['text']}'")
    print(f"   Confiança: {result['confidence']:.2%}")
    if result.get("error"):
        print(f"   Erro: {result['error']}")
    print()

except Exception as e:
    print(f"❌ Erro: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*150)
print("✅ TUDO FUNCIONAL!")
print("="*150 + "\n")
