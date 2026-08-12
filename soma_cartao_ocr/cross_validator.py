#!/usr/bin/env python3
"""Validação cruzada inteligente: Vision API vs Tesseract OCR."""

import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OCRResult:
    """Resultado de OCR de uma fonte."""
    source: str  # 'vision' ou 'tesseract'
    text: str
    confidence: float
    numbers: list[float] = None


class CrossValidator:
    """Validação cruzada entre múltiplas fontes OCR."""

    @staticmethod
    def extract_numbers(text: str) -> list[float]:
        """Extrai números de um texto."""
        if not text:
            return []

        numbers_str = re.findall(r'\d+[.,]\d+', text)
        numbers = []

        for num_str in numbers_str:
            try:
                num = float(num_str.replace(',', '.'))
                if 0.01 <= num <= 999.99:
                    numbers.append(num)
            except:
                pass

        return sorted(numbers)

    @staticmethod
    def compare_results(
        vision_result: Optional[OCRResult],
        tesseract_result: Optional[OCRResult]
    ) -> Dict[str, Any]:
        """
        Compara resultados de Vision vs Tesseract.

        Retorna:
        {
            'best_source': 'vision'|'tesseract'|'conflict',
            'recommended_value': str,
            'confidence': float,
            'divergence': float (0-1),
            'reasoning': str
        }
        """

        if not vision_result and not tesseract_result:
            return {
                'best_source': 'none',
                'recommended_value': '',
                'confidence': 0.0,
                'divergence': 0.0,
                'reasoning': 'Nenhuma fonte disponível'
            }

        if not vision_result:
            return {
                'best_source': 'tesseract',
                'recommended_value': tesseract_result.text,
                'confidence': tesseract_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Vision API não retornou resultado'
            }

        if not tesseract_result:
            return {
                'best_source': 'vision',
                'recommended_value': vision_result.text,
                'confidence': vision_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Tesseract não retornou resultado'
            }

        # Ambas retornaram
        vision_nums = CrossValidator.extract_numbers(vision_result.text)
        tess_nums = CrossValidator.extract_numbers(tesseract_result.text)

        # Caso 1: Ambas capturaram números
        if vision_nums and tess_nums:
            # Comparar primeiro número de cada
            if abs(vision_nums[0] - tess_nums[0]) < 0.01:
                # Concordam dentro de 1 centavo
                best_conf = max(vision_result.confidence, tesseract_result.confidence)
                return {
                    'best_source': 'agreement',
                    'recommended_value': f"{vision_nums[0]:.2f}",
                    'confidence': best_conf,
                    'divergence': 0.0,
                    'reasoning': 'Vision e Tesseract concordam'
                }
            else:
                # Divergem
                divergence = abs(vision_nums[0] - tess_nums[0]) / max(vision_nums[0], tess_nums[0])
                best_source = 'vision' if vision_result.confidence > tesseract_result.confidence else 'tesseract'
                best_result = vision_result if best_source == 'vision' else tesseract_result
                best_nums = vision_nums if best_source == 'vision' else tess_nums

                return {
                    'best_source': best_source,
                    'recommended_value': f"{best_nums[0]:.2f}",
                    'confidence': best_result.confidence,
                    'divergence': divergence,
                    'reasoning': f'Divergência de {divergence:.1%} - usando {best_source} com confiança {best_result.confidence:.2%}'
                }

        # Caso 2: Apenas Vision capturou
        if vision_nums:
            return {
                'best_source': 'vision',
                'recommended_value': f"{vision_nums[0]:.2f}",
                'confidence': vision_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Apenas Vision capturou número'
            }

        # Caso 3: Apenas Tesseract capturou
        if tess_nums:
            return {
                'best_source': 'tesseract',
                'recommended_value': f"{tess_nums[0]:.2f}",
                'confidence': tesseract_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Apenas Tesseract capturou número'
            }

        # Caso 4: Nenhuma capturou números
        if vision_result.confidence > tesseract_result.confidence:
            return {
                'best_source': 'vision',
                'recommended_value': vision_result.text,
                'confidence': vision_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Nenhuma capturou números - usando Vision por confiança'
            }
        else:
            return {
                'best_source': 'tesseract',
                'recommended_value': tesseract_result.text,
                'confidence': tesseract_result.confidence,
                'divergence': 0.0,
                'reasoning': 'Nenhuma capturou números - usando Tesseract por confiança'
            }

    @staticmethod
    def score_result(
        field_name: str,
        result: Dict[str, Any],
        expected_format: Optional[str] = None
    ) -> Tuple[float, list[str]]:
        """
        Pontua resultado da validação cruzada.

        Args:
            field_name: Nome do campo ('debito_eur', 'descricao', etc)
            result: Resultado da comparação
            expected_format: Padrão esperado ('MONEY', 'DATE', 'TEXT', etc)

        Returns:
            (score: 0-1, warnings: list[str])
        """

        warnings = []
        score = result.get('confidence', 0.0)

        # Penalizar divergências
        divergence = result.get('divergence', 0.0)
        if divergence > 0.1:
            score *= (1 - divergence)
            warnings.append(f"Alta divergência entre fontes ({divergence:.1%})")

        # Validar formato
        if expected_format == 'MONEY':
            if not re.match(r'^\d+[.,]\d{2}$', result.get('recommended_value', '')):
                score *= 0.8
                warnings.append("Valor monetário não está em formato correto")

        elif expected_format == 'DATE':
            if not re.match(r'^\d{2}/\d{2}', result.get('recommended_value', '')):
                score *= 0.8
                warnings.append("Data não está em formato correto")

        # Avisar se confiança baixa
        if score < 0.6:
            warnings.append(f"Confiança baixa ({score:.2%}) - requer revisão")

        return min(1.0, score), warnings


# Função helper para integração em main.py
def get_best_value_cross_validated(
    field_name: str,
    vision_text: str,
    vision_confidence: float,
    tesseract_text: str,
    tesseract_confidence: float,
    expected_format: Optional[str] = None
) -> Tuple[str, float, str]:
    """
    Helper para obter melhor valor com validação cruzada.

    Returns:
        (value, confidence, source)
    """

    vision_result = OCRResult(
        source='vision',
        text=vision_text,
        confidence=vision_confidence
    ) if vision_text else None

    tess_result = OCRResult(
        source='tesseract',
        text=tesseract_text,
        confidence=tesseract_confidence
    ) if tesseract_text else None

    comparison = CrossValidator.compare_results(vision_result, tess_result)

    return (
        comparison['recommended_value'],
        comparison['confidence'],
        comparison['best_source']
    )
