#!/usr/bin/env python3
"""Pós-processador OCR: filtro e correcção de linhas de cabeçalho e padrões conhecidos."""

import re
from typing import Optional


# Padrões de cabeçalho que aparecem na OCR
HEADER_KEYWORDS = {
    "taxa", "débita", "crédita", "original", "câmbio", "eur",
    "valor", "data", "descrição", "movimento", "comissão taxa",
    "taxa cambio", "débito", "crédito", "moeda"
}

# Palavras de cabeçalho que indicam 100% que é cabeçalho
HEADER_PATTERNS = [
    r"taxa\s+d[eé]bita",
    r"original\s+taxa",
    r"débita\s+eur",
    r"câmbio\s+eur",
    r"taxa\s+câmbio",
]

# Valores errados que parecem cabeçalho ou são artefatos OCR
WRONG_VALUES = {
    "taxa": "",
    "débita": "",
    "crédita": "",
    "débito": "",
    "crédito": "",
    "eur": "",
    "eur ( )": "",
    "eur (": "",      # Artefato do cabeçalho "Débito EUR ("
    "câmbio": "",
    "original": "",
    "( )": "",        # Artefato OCR comum
    "+": "",          # Símbolo extraído como valor
    "-": "",          # Símbolo extraído como valor
    ")": "",          # Parêntese fechado
    "(": "",          # Parêntese aberto
}


def is_header_line(texto_ocr: str, fields: dict) -> bool:
    """
    Detecta se a linha é um cabeçalho.

    Retorna True se:
    - Contém padrões de cabeçalho
    - Valores monetários contêm palavras de cabeçalho
    - Descrição está vazia E valores estão errados
    """
    if not texto_ocr:
        return False

    texto_lower = texto_ocr.lower().strip()

    # Verificar padrões explícitos de cabeçalho
    for pattern in HEADER_PATTERNS:
        if re.search(pattern, texto_lower):
            return True

    # Se debito_eur ou credito_eur contêm palavras de cabeçalho, é cabeçalho
    debito_lower = fields.get("debito_eur", "").lower().strip()
    credito_lower = fields.get("credito_eur", "").lower().strip()

    if debito_lower in ["taxa", "débita", "débito", "crédita", "crédito", "câmbio", "eur", "eur ( )"]:
        return True
    if credito_lower in ["taxa", "débita", "débito", "crédita", "crédito", "câmbio", "eur", "eur ( )"]:
        return True

    # Se taxa_cambio é "Original" (cabeçalho), é cabeçalho
    taxa_lower = fields.get("taxa_cambio", "").lower().strip()
    if taxa_lower == "original":
        return True

    # Se descrição vazia + ambos os valores são palavras de cabeçalho = cabeçalho
    descricao = fields.get("descricao", "").strip()
    if not descricao or len(descricao) < 3:
        if debito_lower in WRONG_VALUES and credito_lower in WRONG_VALUES:
            if debito_lower or credito_lower:  # Pelo menos um está preenchido errado
                return True

    return False


def clean_field_value(value: str) -> str:
    """Remove espaços extras e normaliza valor."""
    if not value:
        return ""

    value = value.strip()

    # Se o valor é uma palavra de cabeçalho, retorna vazio
    if value.lower() in WRONG_VALUES:
        return ""

    return value


def correct_known_patterns(fields: dict) -> tuple[dict, list[str]]:
    """
    Corrige padrões conhecidos de erro na OCR.

    Retorna:
    - dicionário com campos corrigidos
    - lista com razões de correção
    """
    reasons = []
    corrected = fields.copy()

    # Se texto OCR contém artefatos de cabeçalho, limpar campos
    # (linha foi contaminada durante extração)
    texto_ocr = corrected.get("texto_ocr", "").lower()
    if "câmbio" in texto_ocr and "eur" in texto_ocr and ("(" in texto_ocr or ")" in texto_ocr):
        corrected["pais"] = ""
        corrected["moeda_original"] = ""
        corrected["taxa_cambio"] = ""
        corrected["debito_eur"] = ""
        corrected["credito_eur"] = ""
        reasons.append("linha contaminada (artefato de cabeçalho detectado)")

    # Corrigir valores que parecem cabeçalho
    for field in ["debito_eur", "credito_eur", "taxa_cambio"]:
        value = corrected.get(field, "").strip()
        if value.lower() in WRONG_VALUES:
            corrected[field] = ""
            reasons.append(f"{field} corrigido (era palavra-chave: '{value}')")

    # Se ambos débito e crédito estão vazios, marcar para revisão
    debito = corrected.get("debito_eur", "").strip()
    credito = corrected.get("credito_eur", "").strip()
    if not debito and not credito:
        reasons.append("débito/crédito ausente (ambos vazios)")

    # Descrição muito curta
    descricao = corrected.get("descricao", "").strip()
    if descricao and len(descricao) < 3:
        reasons.append("descrição muito curta")
    elif not descricao:
        reasons.append("descrição ausente")

    # Limpar espaços extras em todos os campos
    for field in corrected:
        if isinstance(corrected[field], str):
            corrected[field] = clean_field_value(corrected[field])

    return corrected, reasons


def should_skip_line(texto_ocr: str, fields: dict) -> bool:
    """
    Determina se a linha deve ser IGNORADA completamente (não inserida na sheet).

    Critérios para ignorar:
    - É uma linha de cabeçalho pura (sem dados)
    - Está vazia
    - Todas as datas e valores são vazios
    """
    # Se é cabeçalho E não tem descrição nem montantes, ignorar
    if is_header_line(texto_ocr, fields):
        descricao = fields.get("descricao", "").strip()
        debito = fields.get("debito_eur", "").strip()
        credito = fields.get("credito_eur", "").strip()

        # Se tudo está vazio, é uma linha de cabeçalho pura
        if not descricao and not debito and not credito:
            return True

    return False


def should_mark_for_review(texto_ocr: str, fields: dict, reasons: list) -> tuple[bool, list[str]]:
    """
    Determina se a linha deve ser marcada para REVISÃO.

    Retorna:
    - bool: True se deve revisar
    - list: razões adicionais de revisão
    """
    review_reasons = reasons.copy()

    # Se é cabeçalho, marcar para revisão
    if is_header_line(texto_ocr, fields):
        review_reasons.append("linha de cabeçalho detectada")
        return True, review_reasons

    # Se tem razões de correção, marcar para revisão
    if reasons:
        return True, review_reasons

    return False, review_reasons


def is_description_incomplete(descricao: str) -> bool:
    """
    Detecta se uma descrição parece incompleta.

    Sinais de incompletude:
    - Muito curta (< 5 caracteres)
    - Só contém uma palavra
    - Sem números quando deveria ter (ex: endereço)
    - Padrão típico: uma palavra de localização
    """
    if not descricao or len(descricao.strip()) < 5:
        return True

    palavras = descricao.strip().split()
    if len(palavras) == 1 and len(descricao) < 15:
        return True

    return False


def can_merge_descriptions(desc1: str, desc2: str, pais1: str = "") -> bool:
    """
    Verifica se duas descrições podem ser mescladas.

    Critérios:
    - desc2 é muito curta (incompleta)
    - desc2 não começa com padrões de transação
    - desc1 + desc2 faz sentido semântico
    """
    if not desc2 or len(desc2.strip()) < 3:
        return False

    desc2_lower = desc2.lower().strip()
    desc1_lower = desc1.lower().strip()

    # Se desc2 tem números sozinha, é uma transação independente
    if any(char.isdigit() for char in desc2) and len(desc2.split()) < 2:
        return False

    # Se desc2 é uma palavra de localização comum
    location_keywords = {"braga", "dublin", "portugal", "españa", "ireland", "irlanda", "usa", "eua"}
    if desc2_lower in location_keywords:
        # Se desc1 já tem uma localização (ex: Dublin), pode ser erro de OCR
        # Neste caso, ainda fazer merge porque desc2 é claramente incompleta
        return True

    # Se desc2 completa um padrão comum (ex: "CASH & CARRY" + "BRAGA")
    if any(pattern in desc1_lower for pattern in ["&", "cash", "carry"]):
        if desc2_lower in location_keywords:
            return True

    # Se desc1 é um estabelecimento + localidade incorreta (ex: "MERCADONA DUBLIN")
    # E desc2 é a localidade correta (ex: "BRAGA")
    # Substituir em vez de append
    if len(desc1_lower.split()) == 2:
        word1, word2 = desc1_lower.split()
        # Se palavra 2 é uma localização e desc2 também é localização
        if word2 in location_keywords and desc2_lower in location_keywords:
            # Pode ser erro de OCR, fazer merge
            return True

    return False


def merge_descriptions(desc1: str, desc2: str) -> str:
    """Mescla duas descrições de forma inteligente."""
    if not desc1:
        return desc2
    if not desc2:
        return desc1

    desc1_lower = desc1.lower().strip()
    desc2_lower = desc2.lower().strip()
    location_keywords = {"braga", "dublin", "portugal", "españa", "ireland", "irlanda", "usa", "eua"}

    # Se desc1 tem 2 palavras (estabelecimento + localidade) E desc2 é localidade
    if len(desc1_lower.split()) == 2 and desc2_lower in location_keywords:
        parts = desc1.split()
        # Substituir a segunda parte (localidade errada) pela correta
        return f"{parts[0]} {desc2}"

    # Se desc1 termina com & ou hífen, concatenar direto
    if desc1.rstrip().endswith(("&", "-")):
        return f"{desc1.rstrip()}{desc2}"

    # Senão, adicionar espaço
    return f"{desc1.strip()} {desc2.strip()}"


def postprocess_ocr_line(texto_ocr: str, fields: dict) -> tuple[dict, str, list[str]]:
    """
    Pós-processa uma linha OCR.

    Retorna:
    - campos corrigidos
    - status (VÁLIDO ou REVISÃO)
    - razões de revisão
    """
    # Primeiro, corrigir padrões conhecidos
    corrected_fields, correction_reasons = correct_known_patterns(fields)

    # Depois, verificar se deve revisar
    should_review, all_reasons = should_mark_for_review(texto_ocr, corrected_fields, correction_reasons)

    status = "REVISÃO" if should_review else "VÁLIDO"

    return corrected_fields, status, all_reasons


def detect_broken_descriptions(movimentos: list[dict]) -> list[tuple[int, int]]:
    """
    Detecta pares de linhas que podem ter descrição quebrada.

    Retorna lista de tuplas (índice_linha1, índice_linha2) que devem ser mergeadas.
    """
    merge_pairs = []

    for i in range(len(movimentos) - 1):
        curr = movimentos[i]
        next_mov = movimentos[i + 1]

        curr_desc = curr.get("descricao", "").strip()
        next_desc = next_mov.get("descricao", "").strip()

        # Se a próxima tem descrição incompleta e pode fazer merge
        if is_description_incomplete(next_desc):
            if can_merge_descriptions(curr_desc, next_desc):
                # Verificar se faz sentido: datas próximas ou mesmo dia
                curr_data_mov = curr.get("data_movimento", "")
                next_data_mov = next_mov.get("data_movimento", "")

                if curr_data_mov == next_data_mov or curr_data_mov:  # Mesmo dia ou tem data
                    merge_pairs.append((i, i + 1))

    return merge_pairs


def merge_broken_movement_descriptions(movimentos: list[dict]) -> list[dict]:
    """
    Mescla descrições quebradas detectadas automaticamente.

    Modifica os movimentos em-lugar, removendo linhas que foram mergeadas.
    IMPORTANTE: Apenas mescla descrição, NÃO copia outros campos!
    """
    merge_pairs = detect_broken_descriptions(movimentos)

    if not merge_pairs:
        return movimentos

    # Processar pairs em ordem reversa para não quebrar índices
    for idx1, idx2 in sorted(merge_pairs, reverse=True):
        mov1 = movimentos[idx1]
        mov2 = movimentos[idx2]

        # APENAS mesclar descrição
        # Nunca copiar outros campos, pois estão na coluna correta e já foram extraídos!
        merged_desc = merge_descriptions(
            mov1.get("descricao", ""),
            mov2.get("descricao", "")
        )
        mov1["descricao"] = merged_desc

        # Marcar como mergeado
        mov1["merged"] = True
        mov1["merged_from_line"] = mov2.get("line", idx2)

        # Remover a segunda linha (foi mergeada)
        movimentos.pop(idx2)

    return movimentos
