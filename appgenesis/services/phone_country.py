from __future__ import annotations

import unicodedata


# ###################################################################################
# (1) PAISES E PREFIXOS SUPORTADOS
# ###################################################################################

SUPPORTED_PHONE_COUNTRIES: dict[str, dict[str, str]] = {
    "PT": {
        "label": "Portugal",
        "dial_code": "+351",
        "placeholder": "+351 910 000 000",
    },
    "BR": {
        "label": "Brasil",
        "dial_code": "+55",
        "placeholder": "+55 11 99999-9999",
    },
    "AO": {
        "label": "Angola",
        "dial_code": "+244",
        "placeholder": "+244 923 000 000",
    },
    "MZ": {
        "label": "Moçambique",
        "dial_code": "+258",
        "placeholder": "+258 84 000 0000",
    },
    "CV": {
        "label": "Cabo Verde",
        "dial_code": "+238",
        "placeholder": "+238 991 00 00",
    },
    "GB": {
        "label": "Reino Unido",
        "dial_code": "+44",
        "placeholder": "+44 7700 900123",
    },
    "FR": {
        "label": "França",
        "dial_code": "+33",
        "placeholder": "+33 6 12 34 56 78",
    },
    "ES": {
        "label": "Espanha",
        "dial_code": "+34",
        "placeholder": "+34 612 34 56 78",
    },
    "DE": {
        "label": "Alemanha",
        "dial_code": "+49",
        "placeholder": "+49 1512 3456789",
    },
    "IT": {
        "label": "Itália",
        "dial_code": "+39",
        "placeholder": "+39 312 345 6789",
    },
    "US": {
        "label": "Estados Unidos",
        "dial_code": "+1",
        "placeholder": "+1 202 555 0100",
    },
}

COUNTRY_CODE_ALIASES: dict[str, str] = {
    "UK": "GB",
    "USA": "US",
}


# ###################################################################################
# (2) NORMALIZACAO E LOOKUP
# ###################################################################################

def _normalize_country_lookup(value: str) -> str:
    normalized_value = unicodedata.normalize("NFD", str(value or "").strip().upper())
    without_accents = "".join(
        character
        for character in normalized_value
        if not unicodedata.combining(character)
    )
    return "".join(character for character in without_accents if character.isalnum())


def get_supported_phone_countries() -> list[dict[str, str]]:
    return [
        {
            "value": country_code,
            "label": country_data["label"],
            "calling_code": country_data["dial_code"],
            "placeholder": country_data["placeholder"],
        }
        for country_code, country_data in SUPPORTED_PHONE_COUNTRIES.items()
    ]


def get_supported_phone_country_option(country_code: str) -> dict[str, str] | None:
    normalized_country_code = normalize_country_code(country_code)
    if not normalized_country_code:
        return None

    country_data = SUPPORTED_PHONE_COUNTRIES.get(normalized_country_code)
    if country_data is None:
        return None

    return {
        "value": normalized_country_code,
        "label": country_data["label"],
        "calling_code": country_data["dial_code"],
        "placeholder": country_data["placeholder"],
    }


def normalize_country_code(value: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        return ""

    uppercase_value = clean_value.upper()
    if uppercase_value in SUPPORTED_PHONE_COUNTRIES:
        return uppercase_value
    if uppercase_value in COUNTRY_CODE_ALIASES:
        return COUNTRY_CODE_ALIASES[uppercase_value]

    normalized_lookup = _normalize_country_lookup(clean_value)
    if normalized_lookup in COUNTRY_CODE_ALIASES:
        return COUNTRY_CODE_ALIASES[normalized_lookup]

    for country_code, country_data in SUPPORTED_PHONE_COUNTRIES.items():
        if _normalize_country_lookup(country_data["label"]) == normalized_lookup:
            return country_code

    return uppercase_value


def normalize_phone_value(value: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        return ""

    normalized_characters: list[str] = []
    has_plus_prefix = False
    for character in clean_value:
        if character.isdigit():
            normalized_characters.append(character)
            continue
        if character == "+" and not normalized_characters and not has_plus_prefix:
            normalized_characters.append(character)
            has_plus_prefix = True

    return "".join(normalized_characters)


# ###################################################################################
# (3) VALIDACAO
# ###################################################################################

def validate_phone_prefix_for_country(country_code: str, phone: str) -> str:
    normalized_country_code = normalize_country_code(country_code)
    if not normalized_country_code:
        return "País é obrigatório."

    supported_country = get_supported_phone_country_option(normalized_country_code)
    if supported_country is None:
        return "País inválido."

    normalized_phone = normalize_phone_value(phone)
    if not normalized_phone:
        return "Telefone principal é obrigatório."

    expected_dial_code = supported_country["calling_code"]
    if not normalized_phone.startswith(expected_dial_code):
        return (
            "O telefone deve começar com o prefixo internacional do país selecionado. "
            f"Exemplo para {supported_country['label']}: {expected_dial_code}."
        )

    return ""


__all__ = [
    "SUPPORTED_PHONE_COUNTRIES",
    "get_supported_phone_countries",
    "get_supported_phone_country_option",
    "normalize_country_code",
    "normalize_phone_value",
    "validate_phone_prefix_for_country",
]
