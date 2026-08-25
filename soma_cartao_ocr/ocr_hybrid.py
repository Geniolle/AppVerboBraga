#!/usr/bin/env python3
"""OCR Híbrido: Google Vision + Tesseract para máxima precisão."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np

try:
    import pytesseract
    TESSERACT_AVAILABLE = True

    # Configurar caminho do Tesseract (Windows)
    import platform
    if platform.system() == "Windows":
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        import os
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
except ImportError:
    TESSERACT_AVAILABLE = False


class HybridOCR:
    """
    OCR Híbrido que combina Google Vision e Tesseract.

    - Google Vision: Melhor para texto complexo
    - Tesseract: Melhor para números
    - Fusão: Usa o melhor de cada um
    """

    @staticmethod
    def enhance_for_digits(image_array: np.ndarray) -> np.ndarray:
        """Pré-processamento especializado para números."""
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_array

        # Morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Binarização dual
        _, otsu = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            closed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Fusão
        fused = cv2.addWeighted(otsu, 0.6, adaptive, 0.4, 0)

        # Limpeza
        contours, _ = cv2.findContours(fused, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cleaned = np.zeros_like(fused)
        for contour in contours:
            if cv2.contourArea(contour) > 20:
                cv2.drawContours(cleaned, [contour], 0, 255, -1)

        return cleaned

    @staticmethod
    def extract_with_tesseract(image_array: np.ndarray, lang: str = "eng") -> Dict[str, Any]:
        """
        Extrai texto com Tesseract.

        Args:
            image_array: Imagem (BGR ou grayscale)
            lang: Idioma ('eng', 'por', 'eng+por')

        Returns:
            {'text': str, 'confidence': float}
        """
        if not TESSERACT_AVAILABLE:
            return {"text": "", "confidence": 0.0, "error": "Tesseract not installed"}

        try:
            # Converter para PIL Image
            from PIL import Image

            if len(image_array.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image_array)

            # Extrair texto
            text = pytesseract.image_to_string(pil_image, lang=lang)

            # Extrair com confiança
            data = pytesseract.image_to_data(pil_image, lang=lang, output_type="dict")
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            confidence = (
                np.mean(confidences) / 100.0 if confidences else 0.0
            )

            return {
                "text": text.strip(),
                "confidence": confidence,
                "error": None,
            }
        except Exception as e:
            return {"text": "", "confidence": 0.0, "error": str(e)}

    @staticmethod
    def extract_numbers_hybrid(image_array: np.ndarray, use_best_psm: bool = True) -> Dict[str, Any]:
        """
        Extrai números com pipeline híbrido otimizado.

        Retorna: {'numbers': str, 'confidence': float, 'source': 'tesseract'|'fallback'}
        """
        if not TESSERACT_AVAILABLE:
            return {
                "numbers": "",
                "confidence": 0.0,
                "source": "none",
                "error": "Tesseract not available",
            }

        try:
            from PIL import Image
            import re

            # Estratégia 1: Tentar com PSM 6 (estrutura uniforme) - melhor para tabelas
            if len(image_array.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image_array)

            # Versão 1: PSM 6 (assume coluna de texto)
            full_text_psm6 = pytesseract.image_to_string(
                pil_image,
                lang="eng",
                config="--psm 6"
            )

            # Versão 2: Tesseract padrão
            full_text = pytesseract.image_to_string(pil_image, lang="eng")

            # Combinar resultados
            combined_text = full_text + "\n" + full_text_psm6

            # Extrair números e valores monetários (1,99 ou 1.99)
            numbers = re.findall(r'\d+[.,]\d+', combined_text)

            if numbers:
                # Remover duplicatas mantendo ordem
                seen = set()
                unique_numbers = []
                for n in numbers:
                    if n not in seen:
                        unique_numbers.append(n)
                        seen.add(n)

                result = ",".join(unique_numbers)

                # Extrair confiança
                data = pytesseract.image_to_data(pil_image, lang="eng", output_type="dict")
                confidences = [int(c) for c in data["conf"] if int(c) > 0]
                confidence = (
                    np.mean(confidences) / 100.0 if confidences else 0.7
                )

                return {
                    "numbers": result,
                    "confidence": confidence,
                    "source": "tesseract",
                    "error": None,
                }

            # Estratégia 2: Se regex não encontrou, tentar com enhance
            enhanced = HybridOCR.enhance_for_digits(image_array)
            pil_enhanced = Image.fromarray(enhanced)

            # Tentar múltiplos PSM modes
            numbers_found = ""
            best_confidence = 0.0

            for psm in [6, 8, 11]:  # 6=uniform block, 8=single line, 11=sparse text
                try:
                    numbers_enhanced = pytesseract.image_to_string(
                        pil_enhanced,
                        lang="eng",
                        config=f"--psm {psm} -c tessedit_char_whitelist=0123456789,."
                    )
                    numbers_enhanced = numbers_enhanced.strip().replace("\n", "").replace(" ", "")

                    if any(c.isdigit() for c in numbers_enhanced):
                        data = pytesseract.image_to_data(pil_enhanced, lang="eng", output_type="dict")
                        confidences = [int(c) for c in data["conf"] if int(c) > 0]
                        confidence = np.mean(confidences) / 100.0 if confidences else 0.5

                        if confidence > best_confidence:
                            numbers_found = numbers_enhanced
                            best_confidence = confidence
                except:
                    pass

            if numbers_found:
                return {
                    "numbers": numbers_found,
                    "confidence": best_confidence,
                    "source": "tesseract",
                    "error": None,
                }

            # Se nada funcionou
            return {
                "numbers": "",
                "confidence": 0.0,
                "source": "none",
                "error": "No digits found",
            }

        except Exception as e:
            return {
                "numbers": "",
                "confidence": 0.0,
                "source": "error",
                "error": str(e),
            }

    @staticmethod
    def merge_ocr_results(
        google_result: Dict[str, Any],
        tesseract_result: Dict[str, Any],
        field_type: str = "mixed",
    ) -> Dict[str, Any]:
        """
        Mescla resultados de Google Vision e Tesseract.

        field_type: 'text' (preferir Google), 'numeric' (preferir Tesseract), 'mixed'
        """
        if field_type == "numeric":
            # Preferir Tesseract para números
            if tesseract_result.get("numbers"):
                return {
                    "text": tesseract_result["numbers"],
                    "confidence": tesseract_result.get("confidence", 0.7),
                    "source": "tesseract",
                }
            else:
                # Fallback para Google Vision
                return {
                    "text": google_result.get("text", ""),
                    "confidence": google_result.get("confidence", 0.0),
                    "source": "google",
                }
        else:
            # Preferir Google Vision (mais preciso para texto)
            if google_result.get("text"):
                return {
                    "text": google_result["text"],
                    "confidence": google_result.get("confidence", 0.0),
                    "source": "google",
                }
            else:
                # Fallback para Tesseract
                return {
                    "text": tesseract_result.get("text", ""),
                    "confidence": tesseract_result.get("confidence", 0.0),
                    "source": "tesseract",
                }


# ============================================================================
# FUNÇÃO DE INTEGRAÇÃO PARA main.py
# ============================================================================


def extract_field_hybrid(
    text_value: str,
    field_name: str,
    image_region: Optional[np.ndarray] = None,
) -> str:
    """
    Valida e melhora um campo extraído usando OCR Híbrido se necessário.

    Args:
        text_value: Valor extraído pelo Google Vision
        field_name: Nome do campo ('debito_eur', 'credito_eur', 'moeda_original', etc)
        image_region: Região da imagem correspondente ao campo (opcional)

    Returns:
        Valor melhorado ou original
    """
    # Campos numéricos que precisam de Tesseract
    numeric_fields = {"debito_eur", "credito_eur", "moeda_original"}

    # Se o campo numérico está vazio E temos a imagem, tentar Tesseract
    if field_name in numeric_fields and not text_value.strip() and image_region is not None:
        result = HybridOCR.extract_numbers_hybrid(image_region)

        if result.get("numbers"):
            return result["numbers"]

    return text_value
