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
PAGE_SERVICE_PATH = PROJECT_ROOT / "appverbo" / "services" / "page.py"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"

START_MARKER = "# APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_START"
END_MARKER = "# APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_END"


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
# (3) PATCH profile_handlers.py
####################################################################################

PERSISTENCE_BLOCK = r'''
        # APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_START
        # Reforco de persistencia dos Campos Quantidade do Meu perfil.
        #
        # O frontend envia:
        #   process_quantity_payload__<rule_key> = JSON array
        #
        # O valor deve ficar em Member.profile_custom_fields com a chave:
        #   quantity__meu_perfil__<rule_key>
        #
        # Este bloco e intencionalmente executado imediatamente antes de regravar
        # existing_profile_fields, para garantir que o ultimo payload submetido
        # prevalece sobre valores antigos.
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            if not rule_key:
                continue

            storage_key = build_menu_process_quantity_storage_key(
                MENU_MEU_PERFIL_KEY,
                rule_key,
            )
            if not storage_key:
                continue

            payload_field_name = f"process_quantity_payload__{rule_key}"
            payload_was_submitted = payload_field_name in submitted_form

            parsed_quantity_items = _resolve_submitted_process_quantity_items(
                submitted_form,
                rule_key,
            )

            allowed_repeated_fields = {
                str(field_key or "").strip().lower()
                for field_key in quantity_rule.get("repeated_field_keys", [])
                if str(field_key or "").strip()
            }

            try:
                max_quantity_items = int(str(quantity_rule.get("max_items") or "1").strip())
            except (TypeError, ValueError):
                max_quantity_items = 1

            max_quantity_items = max(1, min(max_quantity_items, 50))

            cleaned_quantity_items: list[dict[str, str]] = []

            for raw_item in parsed_quantity_items[:max_quantity_items]:
                if not isinstance(raw_item, dict):
                    continue

                clean_item: dict[str, str] = {}

                for raw_field_key, raw_field_value in raw_item.items():
                    clean_field_key = str(raw_field_key or "").strip().lower()
                    clean_field_value = str(raw_field_value or "").strip()

                    if not clean_field_key or clean_field_key not in allowed_repeated_fields:
                        continue

                    if not clean_field_value:
                        continue

                    clean_item[clean_field_key] = clean_field_value

                if clean_item:
                    cleaned_quantity_items.append(clean_item)

            serialized_quantity_items = serialize_menu_process_quantity_values(
                cleaned_quantity_items
            )

            if serialized_quantity_items:
                updated_quantity_values[storage_key] = serialized_quantity_items
            elif payload_was_submitted:
                updated_quantity_values.pop(storage_key, None)
        # APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_END

'''


def patch_profile_handlers_v1() -> None:
    content = read_text_v1(PROFILE_HANDLERS_PATH)

    required_markers = [
        "async def update_personal_profile",
        "quantity_rules = _normalize_process_quantity_rules",
        "updated_quantity_values = {",
        "serialize_menu_process_quantity_values",
        "build_menu_process_quantity_storage_key",
    ]

    missing = [
        marker for marker in required_markers
        if marker not in content
    ]

    if missing:
        raise RuntimeError("Marcadores ausentes em profile_handlers.py: " + ", ".join(missing))

    marker_pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?",
        flags=re.DOTALL,
    )

    if marker_pattern.search(content):
        content = marker_pattern.sub(PERSISTENCE_BLOCK, content)
    else:
        insertion_anchor = (
            "        previous_phone = (member.primary_phone or \"\").strip()\n"
        )

        if insertion_anchor not in content:
            raise RuntimeError("Nao encontrei ponto de insercao antes de previous_phone em update_personal_profile.")

        content = content.replace(
            insertion_anchor,
            PERSISTENCE_BLOCK + insertion_anchor,
            1,
        )

    write_text_v1(PROFILE_HANDLERS_PATH, content)


####################################################################################
# (4) PATCH page.py PARA GARANTIR RELOAD DOS VALORES DO MEU PERFIL
####################################################################################

def patch_page_service_v1() -> None:
    content = read_text_v1(PAGE_SERVICE_PATH)

    old_filter = 'if not menu_key or menu_key in {"home", "perfil", "administrativo", MENU_MEU_PERFIL_KEY}:'
    new_filter = 'if not menu_key or menu_key in {"home", "perfil", "administrativo"}:'

    if old_filter in content:
        content = content.replace(old_filter, new_filter, 1)

    if old_filter in content:
        raise RuntimeError("page.py ainda ignora MENU_MEU_PERFIL_KEY no mapa de quantidade.")

    if "menu_process_quantity_values_map" not in content:
        raise RuntimeError("page.py nao contem menu_process_quantity_values_map.")

    if "build_menu_process_quantity_storage_key(menu_key, rule_key)" not in content:
        raise RuntimeError("page.py nao carrega valores por build_menu_process_quantity_storage_key.")

    write_text_v1(PAGE_SERVICE_PATH, content)


####################################################################################
# (5) ATUALIZAR CACHE BUSTER DO TEMPLATE
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "new_user.js" not in content:
        raise RuntimeError("new_user.js nao encontrado no template.")

    content = re.sub(
        r'new_user\.js\?v=[^"]+',
        "new_user.js?v=20260503-meu-perfil-quantity-persistence-v1",
        content,
    )

    if "new_user.js?v=20260503-meu-perfil-quantity-persistence-v1" not in content:
        raise RuntimeError("Cache buster do new_user.js nao foi atualizado.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

def validate_content_v1() -> None:
    profile_content = read_text_v1(PROFILE_HANDLERS_PATH)
    page_content = read_text_v1(PAGE_SERVICE_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_profile_markers = [
        "APPVERBO_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_START",
        "process_quantity_payload__",
        "updated_quantity_values[storage_key]",
        "serialized_quantity_items",
        "payload_was_submitted",
        "allowed_repeated_fields",
    ]

    missing_profile = [
        marker for marker in required_profile_markers
        if marker not in profile_content
    ]

    if missing_profile:
        raise RuntimeError("Marcadores ausentes em profile_handlers.py: " + ", ".join(missing_profile))

    if 'if not menu_key or menu_key in {"home", "perfil", "administrativo", MENU_MEU_PERFIL_KEY}:' in page_content:
        raise RuntimeError("page.py ainda ignora MENU_MEU_PERFIL_KEY.")

    if "new_user.js?v=20260503-meu-perfil-quantity-persistence-v1" not in template_content:
        raise RuntimeError("Template nao contem cache buster esperado.")

    print("OK: profile_handlers.py reforcado para gravar payload de Campos Quantidade.")
    print("OK: page.py ajustado para recarregar valores de quantidade do meu_perfil.")
    print("OK: template atualizado com novo cache buster.")


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(PROFILE_HANDLERS_PATH)
    require_file_v1(PAGE_SERVICE_PATH)
    require_file_v1(TEMPLATE_PATH)

    profile_backup = backup_file_v1(PROFILE_HANDLERS_PATH, "quantity_persistence_v1")
    page_backup = backup_file_v1(PAGE_SERVICE_PATH, "quantity_persistence_v1")
    template_backup = backup_file_v1(TEMPLATE_PATH, "quantity_persistence_v1")

    print(f"OK: backup criado: {profile_backup}")
    print(f"OK: backup criado: {page_backup}")
    print(f"OK: backup criado: {template_backup}")

    patch_profile_handlers_v1()
    patch_page_service_v1()
    patch_template_v1()
    validate_content_v1()

    print("OK: patch de persistencia concluido.")


if __name__ == "__main__":
    main()
