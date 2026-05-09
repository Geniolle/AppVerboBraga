from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()
PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


####################################################################################
# (3) BLOCO CORRIGIDO DA FUNCAO _resolve_submitted_process_quantity_items
####################################################################################

NEW_FUNCTION = r'''def _resolve_submitted_process_quantity_items(
    submitted_form: Any,
    rule_key: str,
) -> list[dict[str, str]]:
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_rule_key:
        return []

    payload_field_name = f"process_quantity_payload__{clean_rule_key}"

    # APPVERBO_MEU_PERFIL_QUANTITY_LIVE_FIELDS_PRIORITY_V1_START
    # O formulario pode submeter mais de um input oculto
    # process_quantity_payload__<rule_key>.
    #
    # No caso dos Dados de agregados foi detetado conflito:
    #   1) um payload oculto com valores novos
    #   2) outro payload oculto duplicado com valores antigos
    #
    # Como os campos visiveis process_quantity_field__<rule_key>__<idx>__<field>
    # sao a fonte mais fiel no momento do submit, o backend deve priorizar
    # os campos vivos quando eles existem.
    collected_quantity_items = _collect_process_quantity_items_from_form(
        submitted_form,
        clean_rule_key,
    )

    if collected_quantity_items:
        return collected_quantity_items
    # APPVERBO_MEU_PERFIL_QUANTITY_LIVE_FIELDS_PRIORITY_V1_END

    if hasattr(submitted_form, "getlist"):
        raw_payload_values = [
            str(raw_value or "").strip()
            for raw_value in submitted_form.getlist(payload_field_name)
        ]
    else:
        raw_payload_value = (
            submitted_form.get(payload_field_name)
            if hasattr(submitted_form, "get")
            else ""
        )
        raw_payload_values = [str(raw_payload_value or "").strip()]

    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V3_START
    # Se ainda nao existem campos vivos, tentamos aproveitar os payloads ocultos.
    # Para evitar que um payload antigo sobrescreva um payload novo, percorremos
    # os valores na ordem recebida e escolhemos o primeiro payload preenchido valido.
    for raw_payload_value in raw_payload_values:
        if not raw_payload_value or raw_payload_value == "[]":
            continue

        parsed_quantity_items = parse_menu_process_quantity_values(raw_payload_value)

        if parsed_quantity_items:
            return parsed_quantity_items
    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V3_END

    # Se o payload "[]" foi submetido explicitamente, isto significa que o utilizador
    # limpou a quantidade ou removeu todos os pares.
    if any(raw_payload_value == "[]" for raw_payload_value in raw_payload_values):
        return []

    return []
'''


####################################################################################
# (4) APLICAR PATCH
####################################################################################

def main() -> None:
    if not PROFILE_HANDLERS_PATH.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {PROFILE_HANDLERS_PATH}")

    content = read_text_v1(PROFILE_HANDLERS_PATH)

    function_pattern = re.compile(
        r"def _resolve_submitted_process_quantity_items\(\n"
        r".*?"
        r"\n\n\n# APPVERBO_RETURN_URL_POST_SAVE_V4_START",
        flags=re.DOTALL,
    )

    if not function_pattern.search(content):
        raise RuntimeError("Funcao _resolve_submitted_process_quantity_items nao encontrada no formato esperado.")

    content = function_pattern.sub(
        NEW_FUNCTION + "\n\n\n# APPVERBO_RETURN_URL_POST_SAVE_V4_START",
        content,
        count=1,
    )

    required_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_LIVE_FIELDS_PRIORITY_V1_START",
        "APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V3_START",
        "_collect_process_quantity_items_from_form",
        "return collected_quantity_items",
        "process_quantity_payload__",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes depois do patch: " + ", ".join(missing))

    write_text_v1(PROFILE_HANDLERS_PATH, content)

    print("OK: _resolve_submitted_process_quantity_items corrigida.")
    print("OK: campos vivos process_quantity_field__ agora têm prioridade sobre payload oculto duplicado.")


if __name__ == "__main__":
    main()
