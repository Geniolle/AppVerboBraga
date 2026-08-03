#!/usr/bin/env python3
"""Solução 2: Melhorar qualidade da imagem (Upsampling + Denoise)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np
from PIL import Image

print("\n" + "="*150)
print("SOLUÇÃO 2: MELHORAR QUALIDADE DA IMAGEM")
print("="*150 + "\n")

# Carregar imagem original
img_path = Path("output/00_download.jpg")
if not img_path.exists():
    print(f"❌ Imagem não encontrada: {img_path}")
    sys.exit(1)

print(f"Carregando: {img_path}\n")
img = cv2.imread(str(img_path))
if img is None:
    print("❌ Erro ao carregar imagem")
    sys.exit(1)

height, width = img.shape[:2]
print(f"Dimensões originais: {width}x{height}\n")

print("="*150)
print("TÉCNICAS DE MELHORIA")
print("="*150 + "\n")

# 1. UPSAMPLING com interpolação de qualidade
print("1️⃣  UPSAMPLING (aumentar resolução)")
print("-" * 150)

scale_factor = 3.0  # 3x de aumento
new_width = int(width * scale_factor)
new_height = int(height * scale_factor)

upsampled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
print(f"   Original: {width}x{height}")
print(f"   Upsampled: {new_width}x{new_height} (Lanczos4)\n")

cv2.imwrite("temp_upsampled.jpg", upsampled)

# 2. DENOISE (remover ruído)
print("2️⃣  DENOISE (remover ruído)")
print("-" * 150)

# Método 1: FastNlMeansDenoisingColored (melhor qualidade)
denoised1 = cv2.fastNlMeansDenoisingColored(upsampled, None, h=10, templateWindowSize=7, searchWindowSize=21)
print("   ✓ Aplicado: fastNlMeansDenoisingColored")
print(f"     h=10, template=7, search=21\n")

cv2.imwrite("temp_denoised.jpg", denoised1)

# 3. SUPER-RESOLUTION (reconstrução de detalhe)
print("3️⃣  SUPER-RESOLUTION (reconstruir detalhes)")
print("-" * 150)

# Criar kernel de sharpening suave
kernel = np.array([[-0.5, -0.5, -0.5],
                    [-0.5,  5.0, -0.5],
                    [-0.5, -0.5, -0.5]]) / 1.0

enhanced = cv2.filter2D(denoised1, -1, kernel)
print("   ✓ Aplicado: Sharpening kernel")
print("     Realça detalhes sem artefatos\n")

cv2.imwrite("temp_enhanced.jpg", enhanced)

# 4. AUMENTAR CONTRASTE (CLAHE suave)
print("4️⃣  AUMENTAR CONTRASTE")
print("-" * 150)

gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
contrast_enhanced = clahe.apply(gray)
print("   ✓ Aplicado: CLAHE")
print("     clipLimit=1.5, tileGridSize=(8,8)\n")

cv2.imwrite("temp_contrast.jpg", contrast_enhanced)

# Converter de volta para BGR
contrast_enhanced_bgr = cv2.cvtColor(contrast_enhanced, cv2.COLOR_GRAY2BGR)

print("="*150)
print("RESULTADO FINAL")
print("="*150 + "\n")

print(f"""
✅ Imagens geradas:
   • temp_upsampled.jpg      ({new_width}x{new_height}) - Aumento de resolução
   • temp_denoised.jpg       - Remoção de ruído
   • temp_enhanced.jpg       - Sharpening de detalhes
   • temp_contrast.jpg       - Realce de contraste

📊 Comparação:
   Original:   {width}x{height} (baixa resolução, ruído)
   Processada: {new_width}x{new_height} (alta resolução, limpo, detalhes realçados)

🎯 Benefício para OCR:
   ✓ Texto menor fica legível
   ✓ Números ficam mais claros
   ✓ Ruído removido
   ✓ Contraste melhorado

⚠️  Próximo passo:
   1. Usar "temp_enhanced.jpg" como input para Vision API
   2. Ou treinar Tesseract com estas imagens
""")

print("="*150 + "\n")
