#!/usr/bin/env python3
"""OCR Alternativo: Tesseract + comparação com Google Vision API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*150)
print("SOLUÇÃO 1: OCR ALTERNATIVO (TESSERACT)")
print("="*150 + "\n")

try:
    import pytesseract
    from PIL import Image
    print("✅ Tesseract está instalado!\n")
except ImportError:
    print("❌ Tesseract NÃO está instalado.\n")
    print("INSTALAÇÃO NECESSÁRIA:")
    print("-" * 150)
    print("""
Windows:
  1. Download: https://github.com/UB-Mannheim/tesseract/wiki
  2. Instalar com idiomas: Portuguese, English
  3. Adicionar ao PATH ou configurar em pytesseract:

     pytesseract.pytesseract.pytesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

Linux:
  sudo apt-get install tesseract-ocr
  sudo apt-get install libtesseract-dev
  pip install pytesseract

macOS:
  brew install tesseract
  pip install pytesseract
""")
    print("-" * 150)
    print("\nDEPOIS DE INSTALAR, você pode usar:\n")
    print("""
import pytesseract
from PIL import Image

# Extrair texto da imagem
image = Image.open('output/01_contraste.png')
text = pytesseract.image_to_string(image, lang='por+eng')

# Extrair com caixa de dados (posições)
data = pytesseract.image_to_data(image, lang='por+eng', output_type='dict')

# Extrair com confiança
data = pytesseract.image_to_data(image, lang='por+eng', output_type='dict')
for i, conf in enumerate(data['conf']):
    if int(conf) > 0:
        print(f"{data['text'][i]}: {conf}% confiança")
""")
    sys.exit(1)

print("\n" + "="*150)
print("COMPARAÇÃO: Google Vision API vs Tesseract")
print("="*150 + "\n")

comparison = {
    "Aspecto": ["Suporte Linguagem", "Números", "Textos Pequenos", "Velocidade", "Custo", "Instalação"],
    "Google Vision": ["Excelente", "Bom", "Excelente", "Rápido", "Caro", "API"],
    "Tesseract": ["Bom", "Muito Bom", "Razoável", "Lento", "Grátis", "Local"],
}

# Tabela manual (tabulate não disponível)
print(f"{'Aspecto':<20} | {'Google Vision':<20} | {'Tesseract':<20}")
print("-" * 65)
for i, aspecto in enumerate(comparison["Aspecto"]):
    google = comparison["Google Vision"][i]
    tesseract = comparison["Tesseract"][i]
    print(f"{aspecto:<20} | {google:<20} | {tesseract:<20}")

print("\n" + "="*150)
print("RECOMENDAÇÃO")
print("="*150 + "\n")

print("""
✅ HÍBRIDO (MELHOR SOLUÇÃO):
   1. Usar Google Vision API para extração inicial (mais preciso)
   2. Usar Tesseract para validação/recuperação de números
   3. Comparar resultados e usar o melhor de cada

Implementação:
  - Se Google Vision falha com números → Tesseract preenche
  - Se Tesseract falha com texto complexo → Google Vision completa
  - Fusão de resultados com confiança combinada
""")

print("="*150 + "\n")
