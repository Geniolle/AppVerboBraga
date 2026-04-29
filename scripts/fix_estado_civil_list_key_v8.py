from pathlib import Path

ROOT = Path.cwd()
MENU_SETTINGS_PATH = ROOT / "appverbo" / "menu_settings.py"

content = MENU_SETTINGS_PATH.read_text(encoding="utf-8")

patch_marker = "# (LISTAS V8) PRESERVAR LIST_KEY NOS CAMPOS ADICIONAIS"

patch_content = r'''

####################################################################################
# (LISTAS V8) PRESERVAR LIST_KEY NOS CAMPOS ADICIONAIS
####################################################################################

def _normalize_process_list_key_v8(raw_key: Any) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    return clean_value


def normalize_menu_process_additional_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    seen_keys: set[str] = set()

    for raw_item in raw_fields:
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        item_list_key = ""

        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
            item_size = _normalize_additional_field_size(
                raw_item.get("size", raw_item.get("max_length")),
                item_type,
            )
            item_is_required = _normalize_additional_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
            item_list_key = _normalize_process_list_key_v8(
                raw_item.get("list_key")
                or raw_item.get("listKey")
                or raw_item.get("process_list_key")
                or raw_item.get("processListKey")
            )
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
            item_size = _normalize_additional_field_size(
                ADDITIONAL_FIELD_DEFAULT_SIZE,
                item_type,
            )
            item_is_required = False

        if not item_label:
            continue

        normalized_label_key = item_label.lower()

        if normalized_label_key in seen_labels:
            continue

        seen_labels.add(normalized_label_key)

        candidate_key = item_key or _build_custom_field_key_from_label(item_label)
        unique_key = candidate_key
        suffix_index = 2

        while unique_key in seen_keys:
            unique_key = f"{candidate_key}_{suffix_index}"
            suffix_index += 1

        seen_keys.add(unique_key)

        if item_type == "list" and not item_list_key:
            item_list_key = _normalize_process_list_key_v8(item_label)

        normalized_item: dict[str, Any] = {
            "key": unique_key,
            "label": item_label,
            "field_type": item_type,
            "is_required": bool(item_is_required and item_type != "header"),
        }

        if item_size is not None:
            normalized_item["size"] = item_size

        if item_type == "list":
            normalized_item["list_key"] = item_list_key

        normalized.append(normalized_item)

    return normalized
'''

if patch_marker not in content:
    content = content.rstrip() + "\n" + patch_content + "\n"

MENU_SETTINGS_PATH.write_text(content, encoding="utf-8")

print("OK: normalize_menu_process_additional_fields agora preserva list_key.")
