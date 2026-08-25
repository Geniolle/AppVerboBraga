#!/usr/bin/env python3
"""Solução 3: Pré-processamento específico para números."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

print("\n" + "="*150)
print("SOLUÇÃO 3: PRÉ-PROCESSAMENTO ESPECÍFICO PARA NÚMEROS")
print("="*150 + "\n")

img_path = Path("output/01_contraste.png")
if not img_path.exists():
    print(f"❌ Imagem não encontrada: {img_path}")
    sys.exit(1)

print(f"Carregando: {img_path}\n")
img = cv2.imread(str(img_path))
if img is None:
    print("❌ Erro ao carregar imagem")
    sys.exit(1)

height, width = img.shape[:2]
print(f"Dimensões: {width}x{height}\n")

print("="*150)
print("ESTRATÉGIAS DE REALCE DE DÍGITOS")
print("="*150 + "\n")

# Converter para escala de cinza
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 1. MORPHOLOGICAL OPERATIONS (para realçar dígitos pequenos)
print("1️⃣  MORPHOLOGICAL OPERATIONS")
print("-" * 150)

kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

# Erosão seguida de dilatação (abre a imagem)
opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_small, iterations=1)
print("   ✓ MORPH_OPEN: Remove pixels pequenos (ruído)\n")

# Dilatação seguida de erosão (fecha buracos)
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_small, iterations=1)
print("   ✓ MORPH_CLOSE: Fecha buracos dentro de dígitos\n")

cv2.imwrite("temp_morphological.jpg", closed)

# 2. EDGE DETECTION (detectar bordas de dígitos)
print("2️⃣  EDGE DETECTION")
print("-" * 150)

edges = cv2.Canny(closed, 50, 150)
print("   ✓ Canny Edge Detection")
print("     Realça bordas de dígitos\n")

cv2.imwrite("temp_edges.jpg", edges)

# 3. DILATE EDGES (aumentar visibilidade de dígitos)
edges_dilated = cv2.dilate(edges, kernel_small, iterations=2)
print("   ✓ Dilate Edges: Aumenta espessura dos dígitos\n")

cv2.imwrite("temp_edges_dilated.jpg", edges_dilated)

# 4. THRESHOLDING ADAPTATIVO AGRESSIVO (binarizar dígitos)
print("3️⃣  BINARIZAÇÃO PARA DÍGITOS")
print("-" * 150)

# Método 1: Otsu (automático)
_, otsu = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print("   ✓ Otsu Threshold: Binarização automática\n")

cv2.imwrite("temp_otsu.jpg", otsu)

# Método 2: Adaptive com parâmetros pequenos (ideal para números)
adaptive = cv2.adaptiveThreshold(closed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)  # blockSize pequeno
print("   ✓ Adaptive Threshold: Para números pequenos")
print("     blockSize=11 (pequeno), constant=2 (mínimo)\n")

cv2.imwrite("temp_adaptive_digits.jpg", adaptive)

# 5. FUSION: Combinar diferentes técnicas
print("4️⃣  FUSÃO INTELIGENTE")
print("-" * 150)

# Combinar Otsu + Adaptive
fused = cv2.addWeighted(otsu, 0.6, adaptive, 0.4, 0)
print("   ✓ Fusão: Otsu(60%) + Adaptive(40%)\n")

cv2.imwrite("temp_fused_digits.jpg", fused)

# 6. POST-PROCESSING: Limpar artefatos
print("5️⃣  PÓS-PROCESSAMENTO")
print("-" * 150)

# Remover pequenas componentes (ruído)
contours, _ = cv2.findContours(fused, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cleaned = np.zeros_like(fused)

min_area = 20  # Mínimo de pixels para manter
for contour in contours:
    if cv2.contourArea(contour) > min_area:
        cv2.drawContours(cleaned, [contour], 0, 255, -1)

print(f"   ✓ Removido ruído: < {min_area} pixels")
print(f"     Total de contornos: {len(contours)} → {len([c for c in contours if cv2.contourArea(c) > min_area])}\n")

cv2.imwrite("temp_cleaned_digits.jpg", cleaned)

print("="*150)
print("RESULTADO FINAL")
print("="*150 + "\n")

print(f"""
✅ Imagens especializadas em DÍGITOS:
   • temp_morphological.jpg      - Morfologia (remove ruído)
   • temp_edges.jpg              - Detecção de bordas
   • temp_edges_dilated.jpg      - Bordas dilatadas
   • temp_otsu.jpg               - Binarização Otsu
   • temp_adaptive_digits.jpg    - Adaptativa para dígitos
   • temp_fused_digits.jpg       - Fusão inteligente (MELHOR)
   • temp_cleaned_digits.jpg     - Após limpeza

🎯 Melhor para OCR de Números:
   📌 Use: temp_cleaned_digits.jpg

   Razões:
   ✓ Dígitos realçados e claros
   ✓ Artefatos removidos
   ✓ Alto contraste
   ✓ Bordas definidas

⚠️  Próximo passo:
   1. Usar "temp_cleaned_digits.jpg" com Tesseract (configurado para dígitos)
   2. Ou usar com Vision API como fallback
   3. Implementar em pipeline de OCR para campos monetários
""")

print("="*150 + "\n")

print("CÓDIGO DE INTEGRAÇÃO:")
print("-" * 150)
print("""
def extract_digits_with_preprocessing(image_path):
    '''Extrai números com pré-processamento especializado'''
    import cv2

    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Aplicar pipeline de dígitos
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Binarização especializada
    _, otsu = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(closed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)

    # Fusão
    fused = cv2.addWeighted(otsu, 0.6, adaptive, 0.4, 0)

    # Usar Tesseract com configuração de dígitos
    import pytesseract
    text = pytesseract.image_to_string(
        fused,
        lang='eng',  # Apenas inglês (mais preciso para números)
        config='--psm 8 -c tessedit_char_whitelist=0123456789,.'
    )

    return text
""")

print("-" * 150 + "\n")
