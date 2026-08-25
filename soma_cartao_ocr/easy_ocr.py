#!/usr/bin/env python3
"""EasyOCR: OCR multilíngue para português (alternativa ao PaddleOCR)."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import numpy as np
import re

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class EasyOCREngine:
    """Motor OCR EasyOCR para português + inglês."""

    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None and EASYOCR_AVAILABLE:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not EASYOCR_AVAILABLE:
            return

        if self._initialized:
            return

        print("Inicializando EasyOCR (primeira vez demora)...")
        self.reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
        self._initialized = True
        print("✓ EasyOCR pronto")

    @staticmethod
    def extract_text(image_array: np.ndarray) -> Dict[str, Any]:
        """
        Extrai texto com EasyOCR.

        Returns:
            {'text': str, 'confidence': float}
        """
        if not EASYOCR_AVAILABLE:
            return {"text": "", "confidence": 0.0, "error": "EasyOCR not installed"}

        try:
            engine = EasyOCREngine()

            # Converter BGR para RGB
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image_array

            # Executar OCR
            results = engine.reader.readtext(image_rgb, detail=1)

            if not results:
                return {"text": "", "confidence": 0.0}

            # Extrair texto e confiança
            texts = [detection[1] for detection in results]
            confidences = [detection[2] for detection in results]

            full_text = " ".join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0

            return {
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "error": None,
            }

        except Exception as e:
            return {"text": "", "confidence": 0.0, "error": str(e)}

    @staticmethod
    def extract_numbers(image_array: np.ndarray) -> Dict[str, Any]:
        """Extrai números e valores monetários."""

        if not EASYOCR_AVAILABLE:
            return {
                "numbers": "",
                "confidence": 0.0,
                "source": "none",
                "error": "EasyOCR not available",
            }

        try:
            result = EasyOCREngine.extract_text(image_array)

            if result.get("error"):
                return {
                    "numbers": "",
                    "confidence": 0.0,
                    "source": "error",
                    "error": result["error"],
                }

            full_text = result["text"]

            # Extrair números
            numbers = re.findall(r'\d+[.,]\d+', full_text)

            if numbers:
                result_str = ",".join(numbers)
                return {
                    "numbers": result_str,
                    "confidence": result.get("confidence", 0.7),
                    "source": "easyocr",
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
