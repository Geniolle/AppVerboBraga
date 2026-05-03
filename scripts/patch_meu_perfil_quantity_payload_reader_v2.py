from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

PROFILE_HANDLERS_PATH = PROJECT_ROOT / "appverbo" / "routes" / "profile" / "profile_handlers.py"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) NOVA FUNCAO ROBUSTA
####################################################################################

NEW_FUNCTION = r'''def _resolve_submitted_process_quantity_items(
    submitted_form: Any,
    rule_key: str,
) -> list[dict[str, str]]:
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_rule_key:
        return []

    payload_field_name = f"process_quantity_payload__{clean_rule_key}"

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

    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_START
    # Pode existir mais de um input process_quantity_payload__<rule_key>.
    # Starlette FormData.get() pode apanhar o primeiro, que por vezes e "[]".
    # Por isso lemos todos os valores e usamos o ultimo payload preenchido valido.
    for raw_payload_value in reversed(raw_payload_values):
        if not raw_payload_value or raw_payload_value == "[]":
            continue

        parsed_quantity_items = parse_menu_process_quantity_values(raw_payload_value)

        if parsed_quantity_items:
            return parsed_quantity_items
    # APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_END

    collected_quantity_items = _collect_process_quantity_items_from_form(
        submitted_form,
        clean_rule_key,
    )

    if collected_quantity_items:
        return collected_quantity_items

    # Se o payload "[]" foi submetido explicitamente, isto significa que o utilizador
    # limpou a quantidade ou removeu todos os pares.
    if any(raw_payload_value == "[]" for raw_payload_value in raw_payload_values):
        return []

    return []
'''


####################################################################################
# (4) PATCH profile_handlers.py
####################################################################################

def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    if "def _resolve_submitted_process_quantity_items(" not in content:
        raise RuntimeError("Funcao _resolve_submitted_process_quantity_items nao encontrada.")

    pattern = re.compile(
        r"def _resolve_submitted_process_quantity_items\(\n"
        r".*?"
        r"\n(?=@router\.post\(\"/users/profile/personal\"\))",
        flags=re.DOTALL,
    )

    if not pattern.search(content):
        raise RuntimeError("Nao foi possivel delimitar a funcao _resolve_submitted_process_quantity_items.")

    content = pattern.sub(NEW_FUNCTION + "\n\n", content)

    required_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_START",
        "submitted_form.getlist(payload_field_name)",
        "for raw_payload_value in reversed(raw_payload_values):",
        "_collect_process_quantity_items_from_form",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes apos patch: " + ", ".join(missing))

    write_text_v1(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (5) PATCH CACHE BUSTER
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-meu-perfil-quantity-payload-reader-v2",
        content,
    )

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDACAO
####################################################################################

def validate_v1() -> None:
    profile_content = read_text_v1(PROFILE_HANDLERS_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_profile = [
        "APPVERBO_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_START",
        "submitted_form.getlist(payload_field_name)",
        "raw_payload_value == \"[]\"",
        "_collect_process_quantity_items_from_form",
    ]

    missing_profile = [
        marker for marker in required_profile
        if marker not in profile_content
    ]

    if missing_profile:
        raise RuntimeError("Marcadores ausentes em profile_handlers.py: " + ", ".join(missing_profile))

    if "new_user.js?v=20260503-meu-perfil-quantity-payload-reader-v2" not in template_content:
        raise RuntimeError("Cache buster do template nao foi atualizado.")

    print("OK: backend agora le todos os payloads repetidos e usa o ultimo preenchido.")
    print("OK: fallback para process_quantity_field__ mantido.")
    print("OK: cache buster atualizado.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(PROFILE_HANDLERS_PATH)
    require_file_v1(TEMPLATE_PATH)

    profile_backup = backup_file_v1(PROFILE_HANDLERS_PATH, "quantity_payload_reader_v2")
    template_backup = backup_file_v1(TEMPLATE_PATH, "quantity_payload_reader_v2")

    print(f"OK: backup criado: {profile_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_profile_handlers_v1()
    patch_template_v1()
    validate_v1()

    print("OK: patch payload reader v2 concluido.")


if __name__ == "__main__":
    main()
