#!/usr/bin/env python3
"""PaddleOCR: OCR multilíngue para português e inglês."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
import re

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class PaddleOCREngine:
    """
    Motor OCR PaddleOCR para português + inglês.

    Vantagens sobre Tesseract:
    - Melhor para português
    - Detecta layout automaticamente
    - Melhor precisão para números
    - Suporta múltiplos idiomas
    """

    _instance = None  # Singleton para evitar carregar modelo múltiplas vezes

    def __new__(cls):
        if cls._instance is None and PADDLE_AVAILABLE:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not PADDLE_AVAILABLE:
            return

        if self._initialized:
            return

        # Inicializar com suporte a português + inglês
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=['pt', 'en'],
            use_gpu=False,  # Mudar para True se tiver GPU
            show_log=False
        )
        self._initialized = True

    @staticmethod
    def extract_text(image_array: np.ndarray, lang: str = "pt") -> Dict[str, Any]:
        """
        Extrai texto com PaddleOCR.

        Args:
            image_array: Imagem (BGR ou grayscale)
            lang: Idioma principal ('pt' ou 'en')

        Returns:
            {'text': str, 'confidence': float, 'boxes': list}
        """
        if not PADDLE_AVAILABLE:
            return {"text": "", "confidence": 0.0, "error": "PaddleOCR not installed"}

        try:
            engine = PaddleOCREngine()

            # Converter BGR para RGB se necessário
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image_array

            # Executar OCR
            result = engine.ocr.ocr(image_rgb, cls=True)

            if not result or not result[0]:
                return {"text": "", "confidence": 0.0, "boxes": []}

            # Extrair texto e confiança
            texts = []
            confidences = []
            boxes = []

            for line in result[0]:
                if line:
                    bbox, (text, conf) = line[0], line[1]
                    texts.append(text)
                    confidences.append(conf)
                    boxes.append(bbox)

            full_text = "\n".join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0

            return {
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "boxes": boxes,
                "error": None,
            }

        except Exception as e:
            return {"text": "", "confidence": 0.0, "boxes": [], "error": str(e)}

    @staticmethod
    def extract_numbers(image_array: np.ndarray) -> Dict[str, Any]:
        """
        Extrai números e valores monetários.

        Retorna: {'numbers': str, 'confidence': float, 'source': 'paddle'}
        """
        if not PADDLE_AVAILABLE:
            return {
                "numbers": "",
                "confidence": 0.0,
                "source": "none",
                "error": "PaddleOCR not available",
            }

        try:
            result = PaddleOCREngine.extract_text(image_array, lang="pt")

            if result.get("error"):
                return {
                    "numbers": "",
                    "confidence": 0.0,
                    "source": "error",
                    "error": result["error"],
                }

            full_text = result["text"]

            # Extrair números e valores monetários (1,99 ou 1.99)
            numbers = re.findall(r'\d+[.,]\d+', full_text)

            if numbers:
                # Juntar números encontrados
                result_str = ",".join(numbers)

                return {
                    "numbers": result_str,
                    "confidence": result.get("confidence", 0.7),
                    "source": "paddle",
                    "error": None,
                }

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
    def extract_structured_fields(image_array: np.ndarray) -> Dict[str, str]:
        """
        Tenta extrair campos estruturados (Data, País, Descrição, etc).

        Retorna: {'field_name': value}
        """
        if not PADDLE_AVAILABLE:
            return {}

        try:
            result = PaddleOCREngine.extract_text(image_array, lang="pt")
            full_text = result.get("text", "")

            fields = {}

            # Procurar padrões conhecidos
            # Data (DD/MM)
            dates = re.findall(r'\d{2}/\d{2}', full_text)
            if dates:
                fields['data'] = dates[0]

            # País (2-3 letras maiúsculas, às vezes)
            countries = re.findall(r'\b(USA|EUR|IRL|POR|ESP|FRA|GBR|ALE|ITA)\b', full_text.upper())
            if countries:
                fields['pais'] = countries[0]

            # Números monetários
            amounts = re.findall(r'\d+[.,]\d{2}', full_text)
            if amounts:
                fields['valor'] = amounts[0]

            return fields

        except Exception as e:
            return {}
