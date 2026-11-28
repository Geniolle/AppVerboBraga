from __future__ import annotations

from typing import Any
from fastapi import (
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from appgenesis.db.session import SessionLocal
from appgenesis.domains.meu_perfil.use_cases import (
    UpdateWhatsappVerificationFailure,
    execute_verify_whatsapp_profile,
)
from appgenesis.menu_settings import (
    MENU_MEU_PERFIL_FIELD_LABELS,
    MENU_MEU_PERFIL_KEY,
    get_sidebar_menu_settings,
    resolve_menu_key_alias,
)
from appgenesis.services.page import build_users_new_url
from appgenesis.services.session import get_current_user
from appgenesis.services.profile_photo import (
    delete_profile_photo_file,
    save_profile_photo_upload,
)
from appgenesis.services.profile import (
    mirror_meu_perfil_custom_fields_to_member_columns,
    build_menu_process_quantity_storage_key,
    filter_process_fields_by_hidden_targets,
    get_hidden_process_targets_from_rules,
    get_menu_process_quantity_repeated_field_keys,
    is_meu_perfil_builtin_duplicate_field,
    parse_member_profile_fields,
    parse_optional_date_pt,
    serialize_member_profile_fields,
    parse_menu_process_quantity_values,
    serialize_menu_process_quantity_values,
)
from appgenesis.models import (
    Member,
    User,
)
from appgenesis.routes.profile.router import router
from appgenesis.routes.profile.handlers.profile_common import (
    _build_post_save_redirect_url_v6,
    _menu_action_denied_v1,
    _normalize_process_field_required,
    _normalize_process_quantity_rules,
)
MEU_PERFIL_BUILTIN_DUPLICATE_LABELS = {
    **dict(MENU_MEU_PERFIL_FIELD_LABELS),
    "pais": "País",
}



# APPGENESIS_MEU_PERFIL_SUBSEQUENT_RULES_RESOLVER_V1_START
def _resolve_process_subsequent_rules_from_setting_v1(
    process_setting: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(process_setting, dict):
        return []

    resolved_rules: list[dict[str, Any]] = []

    for storage_key in (
        "process_subsequent_fields",
        "subsequent_fields",
        "process_subsequent_rules",
    ):
        raw_rules = process_setting.get(storage_key)

        if not isinstance(raw_rules, list):
            continue

        for raw_rule in raw_rules:
            if isinstance(raw_rule, dict):
                resolved_rules.append(raw_rule)

    return resolved_rules


def _collect_process_quantity_items_from_form(
    submitted_form: Any,
    rule_key: str,
) -> list[dict[str, str]]:
    clean_rule_key = str(rule_key or "").strip().lower()
    if not clean_rule_key:
        return []

    prefix = f"process_quantity_field__{clean_rule_key}__"
    indexed_items: dict[int, dict[str, str]] = {}
    if hasattr(submitted_form, "multi_items"):
        raw_items = list(submitted_form.multi_items())
    else:
        raw_items = list((submitted_form or {}).items())

    for raw_name, raw_value in raw_items:
        clean_name = str(raw_name or "").strip().lower()
        if not clean_name.startswith(prefix):
            continue
        suffix = clean_name[len(prefix):]
        index_part, separator, field_key = suffix.partition("__")
        if not separator:
            continue
        try:
            item_index = int(index_part)
        except (TypeError, ValueError):
            continue
        clean_field_key = str(field_key or "").strip().lower()
        clean_field_value = str(raw_value or "").strip()
        if item_index < 0 or not clean_field_key or not clean_field_value:
            continue
        indexed_items.setdefault(item_index, {})[clean_field_key] = clean_field_value

    return [
        indexed_items[item_index]
        for item_index in sorted(indexed_items.keys())
        if indexed_items.get(item_index)
    ]


def _resolve_submitted_process_quantity_items(
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

    # APPGENESIS_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_START
    # Pode existir mais de um input process_quantity_payload__<rule_key>.
    # Starlette FormData.get() pode apanhar o primeiro, que por vezes e "[]".
    # Por isso lemos todos os valores e usamos o ultimo payload preenchido valido.
    for raw_payload_value in reversed(raw_payload_values):
        if not raw_payload_value or raw_payload_value == "[]":
            continue

        parsed_quantity_items = parse_menu_process_quantity_values(raw_payload_value)

        if parsed_quantity_items:
            return parsed_quantity_items
    # APPGENESIS_MEU_PERFIL_QUANTITY_PAYLOAD_READER_V2_END

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


@router.post("/users/profile/personal")
async def update_personal_profile(request: Request) -> RedirectResponse:
    submitted_form = await request.form()
    if _menu_action_denied_v1(request, MENU_MEU_PERFIL_KEY, ("editar",)):
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Sem permissão para editar Meus dados."),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    # APPGENESIS_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START
    # Este endpoint grava sempre dados do Meu perfil. Depois de gravar,
    # o utilizador deve continuar no Meu perfil e na aba onde estava.
    redirect_menu = MENU_MEU_PERFIL_KEY
    redirect_target = str(submitted_form.get("target") or "#perfil-pessoal-card").strip() or "#perfil-pessoal-card"
    redirect_profile_section = str(submitted_form.get("profile_section") or "").strip().lower()
    # APPGENESIS_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_END
    clean_full_name = str(submitted_form.get("full_name") or "").strip()
    clean_primary_phone = str(submitted_form.get("primary_phone") or "").strip()
    clean_login_email = str(submitted_form.get("login_email") or submitted_form.get("email") or "").strip().lower()
    clean_country = str(submitted_form.get("country") or "").strip()
    clean_birth_date = str(submitted_form.get("birth_date") or "").strip()
    whatsapp_notice_opt_in = str(submitted_form.get("whatsapp_notice_opt_in") or "").strip()

    if not clean_birth_date:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Data de nascimento é obrigatória.", profile_tab="pessoal"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        parsed_birth_date = parse_optional_date_pt(clean_birth_date)
    except ValueError:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Data de nascimento inválida. Use o formato dd/mm/aaaa.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    parsed_whatsapp_notice_opt_in = whatsapp_notice_opt_in == "1"

    if not clean_full_name:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Nome completo é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if not clean_primary_phone:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Telefone principal é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not clean_login_email:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Email é obrigatório.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if "@" not in clean_login_email:
        return RedirectResponse(
            url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Email inválido.",
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        member = session.execute(
            select(Member).join(User, User.member_id == Member.id).where(User.id == current_user["id"])
        ).scalar_one_or_none()
        if member is None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Membro associado ao utilizador não encontrado.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user_account = session.get(User, current_user["id"])
        if user_account is None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Conta de utilizador não encontrada.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        email_already_exists = session.execute(
            select(User.id)
            .join(Member, Member.id == User.member_id)
            .where(
                func.lower(User.login_email) == clean_login_email,
                User.id != current_user["id"],
            )
            .limit(1)
        ).scalar_one_or_none()

        member_email_already_exists = session.execute(
            select(Member.id)
            .where(
                func.lower(Member.email) == clean_login_email,
                Member.id != member.id,
            )
            .limit(1)
        ).scalar_one_or_none()

        if email_already_exists is not None or member_email_already_exists is not None:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Este email já está associado a outro utilizador.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sidebar_menu_settings = get_sidebar_menu_settings(session)
        meu_perfil_setting = next(
            (
                row
                for row in sidebar_menu_settings
                if resolve_menu_key_alias(row.get("key")) == MENU_MEU_PERFIL_KEY
            ),
            None,
        )
        process_options = (meu_perfil_setting or {}).get("process_field_options", [])
        quantity_rules = _normalize_process_quantity_rules(
            (meu_perfil_setting or {}).get("process_quantity_fields")
        )
        quantity_repeated_field_keys = get_menu_process_quantity_repeated_field_keys(quantity_rules)
        option_keys = {
            str(item.get("key") or "").strip().lower()
            for item in process_options
            if str(item.get("key") or "").strip()
        }
        option_labels_by_key = {
            str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
            for item in process_options
            if str(item.get("key") or "").strip()
        }
        custom_field_meta: dict[str, dict[str, Any]] = {}
        for raw_item in (meu_perfil_setting or {}).get("process_additional_fields", []):
            clean_key = str(raw_item.get("key") or "").strip().lower()
            if not clean_key.startswith("custom_"):
                continue
            if clean_key not in option_keys:
                continue
            if is_meu_perfil_builtin_duplicate_field(
                clean_key,
                raw_item.get("label"),
                MEU_PERFIL_BUILTIN_DUPLICATE_LABELS,
            ):
                continue
            field_type = str(raw_item.get("field_type") or "text").strip().lower()
            if field_type not in {"text", "number", "email", "phone", "date", "flag", "header"}:
                field_type = "text"
            size_value: int | None = None
            if field_type in {"text", "number", "email", "phone"}:
                try:
                    parsed_size = int(str(raw_item.get("size") or "").strip())
                except (TypeError, ValueError):
                    parsed_size = 30
                size_value = max(1, min(parsed_size, 255))
            is_required = _normalize_process_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
            if field_type == "header":
                is_required = False
            custom_field_meta[clean_key] = {
                "field_type": field_type,
                "size": size_value,
                "is_required": is_required,
            }
        visible_field_section_map: dict[str, str] = {}
        for raw_row in (meu_perfil_setting or {}).get("process_visible_field_rows", []):
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            visible_field_section_map[field_key] = str(raw_row.get("header_key") or "").strip().lower()
        visible_custom_keys = [
            clean_key
            for clean_key in (
                str(raw_key or "").strip().lower()
                for raw_key in (meu_perfil_setting or {}).get("process_visible_fields", [])
            )
            if clean_key.startswith("custom_")
            and clean_key in option_keys
            and clean_key in custom_field_meta
            and clean_key not in quantity_repeated_field_keys
            and str((custom_field_meta.get(clean_key) or {}).get("field_type") or "") != "header"
        ]
        current_meu_perfil_values: dict[str, str] = {
            "nome": clean_full_name,
            "telefone": clean_primary_phone,
            "email": clean_login_email,
            "pais": clean_country,
            "data_nascimento": clean_birth_date,
            "autorizacao_whatsapp": "1" if parsed_whatsapp_notice_opt_in else "0",
        }
        for custom_key in visible_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            if field_type == "flag":
                current_meu_perfil_values[custom_key] = (
                    "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                )
                continue
            if hasattr(submitted_form, "getlist"):
                raw_submitted_values = submitted_form.getlist(field_name)
            else:
                raw_submitted_values = [submitted_form.get(field_name)]
            submitted_values = [
                str(raw_value or "").strip()
                for raw_value in raw_submitted_values
            ]
            clean_values = [value for value in submitted_values if value]
            current_meu_perfil_values[custom_key] = ", ".join(clean_values)
        meu_perfil_subsequent_rules = _resolve_process_subsequent_rules_from_setting_v1(
            meu_perfil_setting
        )
        hidden_meu_perfil_targets = get_hidden_process_targets_from_rules(
            meu_perfil_subsequent_rules,
            current_meu_perfil_values,
        )
        visible_custom_keys_set = set(visible_custom_keys)
        active_custom_keys = filter_process_fields_by_hidden_targets(
            visible_custom_keys,
            hidden_meu_perfil_targets,
            visible_field_section_map,
        )
        active_custom_keys_set = set(active_custom_keys)

        existing_profile_fields = parse_member_profile_fields(member.profile_custom_fields)
        existing_custom_fields = {
            key: value
            for key, value in existing_profile_fields.items()
            if key.startswith("custom_")
        }
        updated_custom_fields = {
            key: value
            for key, value in existing_custom_fields.items()
            if key not in visible_custom_keys_set
        }
        existing_quantity_values = {
            key: value
            for key, value in existing_profile_fields.items()
            if key.startswith(f"quantity__{MENU_MEU_PERFIL_KEY}__")
        }
        updated_quantity_values = {
            key: value
            for key, value in existing_quantity_values.items()
        }
        missing_required_custom_labels: list[str] = []
        for custom_key in active_custom_keys:
            field_name = f"custom_field__{custom_key}"
            field_meta = custom_field_meta.get(custom_key) or {}
            field_type = str(field_meta.get("field_type") or "text").strip().lower()
            field_size = field_meta.get("size")
            field_required = bool(field_meta.get("is_required"))
            if field_type == "flag":
                updated_custom_fields[custom_key] = "1" if str(submitted_form.get(field_name) or "").strip() == "1" else "0"
                continue

            if hasattr(submitted_form, "getlist"):
                raw_submitted_values = submitted_form.getlist(field_name)
            else:
                raw_submitted_values = [submitted_form.get(field_name)]
            submitted_values = [
                str(raw_value or "").strip()
                for raw_value in raw_submitted_values
            ]
            clean_values = [value for value in submitted_values if value]
            if isinstance(field_size, int) and field_size > 0:
                clean_values = [value[:field_size] for value in clean_values]
            clean_custom_value = ", ".join(clean_values)
            # Obrigatorios validam so a aba que esta a ser gravada (profile_section), nao as outras abas.
            in_saved_section = not redirect_profile_section or visible_field_section_map.get(custom_key, "") == redirect_profile_section
            if field_required and not clean_custom_value and in_saved_section:
                field_label = option_labels_by_key.get(custom_key) or custom_key
                if field_label not in missing_required_custom_labels:
                    missing_required_custom_labels.append(field_label)
                continue
            if clean_custom_value:
                updated_custom_fields[custom_key] = clean_custom_value

        # APPGENESIS_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_START
        # Quando um campo fica oculto por regra de Campos Subsequentes,
        # o valor antigo deve ser removido para não apresentar informação incorreta.
        for hidden_custom_key in visible_custom_keys:
            if hidden_custom_key in active_custom_keys_set:
                continue

            updated_custom_fields.pop(hidden_custom_key, None)
        # APPGENESIS_MEU_PERFIL_CLEAR_HIDDEN_SUBSEQUENT_VALUES_V1_END

        active_quantity_rule_keys: set[str] = set()
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            quantity_field_key = str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            if not rule_key or not quantity_field_key:
                continue

            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)

                if storage_key:
                    updated_quantity_values.pop(storage_key, None)

                continue

            parsed_quantity_items = _resolve_submitted_process_quantity_items(
                submitted_form,
                rule_key,
            )
            active_quantity_rule_keys.add(rule_key)

            storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)
            if not storage_key:
                continue

            serialized_quantity_items = serialize_menu_process_quantity_values(parsed_quantity_items)
            if serialized_quantity_items:
                updated_quantity_values[storage_key] = serialized_quantity_items
            else:
                updated_quantity_values.pop(storage_key, None)

        # Campos origem de quantidade sao contagens: so inteiros nao negativos.
        quantity_origin_keys = {
            str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            for quantity_rule in quantity_rules
        }
        invalid_quantity_labels: list[str] = []
        for custom_key in active_custom_keys:
            if custom_key not in quantity_origin_keys:
                continue
            origin_value = str(current_meu_perfil_values.get(custom_key) or "").strip()
            if origin_value and not (origin_value.isascii() and origin_value.isdigit()):
                origin_label = option_labels_by_key.get(custom_key) or custom_key
                if origin_label not in invalid_quantity_labels:
                    invalid_quantity_labels.append(origin_label)
        if invalid_quantity_labels:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(
                    submitted_form,
                    profile_error=" ".join(f"{label} só aceita números inteiros não negativos." for label in invalid_quantity_labels),
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if missing_required_custom_labels:
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Preencha os campos obrigatórios: " + ", ".join(missing_required_custom_labels) + ".",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )


        # Validacao: nao diminuir a quantidade enquanto os itens que deixam de existir tiverem dados gravados.
        # O utilizador limpa esses itens, grava, e so depois diminui a quantidade.
        for quantity_rule in quantity_rules:
            rule_key = str(quantity_rule.get("key") or "").strip().lower()
            quantity_field_key = str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            if not rule_key or not quantity_field_key:
                continue
            if (
                quantity_field_key in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key) in hidden_meu_perfil_targets
            ):
                continue
            try:
                new_quantity_count = int(str(current_meu_perfil_values.get(quantity_field_key) or "").strip())
            except ValueError:
                continue

            validation_storage_key = build_menu_process_quantity_storage_key(MENU_MEU_PERFIL_KEY, rule_key)
            stored_quantity_items = parse_menu_process_quantity_values(
                existing_profile_fields.get(validation_storage_key)
            )
            blocked_item_numbers = [
                str(item_index + 1)
                for item_index, stored_item in enumerate(stored_quantity_items)
                if item_index >= new_quantity_count
                and any(str(stored_value or "").strip() for stored_value in stored_item.values())
            ]
            if blocked_item_numbers:
                origin_label = option_labels_by_key.get(quantity_field_key) or quantity_field_key
                rule_label = quantity_rule.get("label") or rule_key
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(
                        submitted_form,
                        profile_error=(
                            f"Antes de diminuir '{origin_label}' para {new_quantity_count}, "
                            f"limpe os dados do(s) Item(ns) {', '.join(blocked_item_numbers)} "
                            f"em '{rule_label}' e grave."
                        ),
                        profile_tab="pessoal",
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        # APPGENESIS_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_START
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

            quantity_field_key_hidden = str(quantity_rule.get("quantity_field_key") or "").strip().lower()
            if (
                quantity_field_key_hidden in hidden_meu_perfil_targets
                or visible_field_section_map.get(quantity_field_key_hidden) in hidden_meu_perfil_targets
            ):
                # Campo origem oculto por regra: os itens do grupo nao podem ficar guardados.
                updated_quantity_values.pop(storage_key, None)
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
        # APPGENESIS_MEU_PERFIL_QUANTITY_PERSISTENCE_V1_END

        # Foto de perfil (campo fixo): nova foto substitui a anterior; "remover" limpa a foto.
        photo_upload = submitted_form.get("profile_photo")
        if hasattr(photo_upload, "filename") and photo_upload.filename:
            new_photo_url, photo_error = save_profile_photo_upload(photo_upload)
            if photo_error:
                return RedirectResponse(
                    url=_build_post_save_redirect_url_v6(submitted_form, profile_error=photo_error, profile_tab="pessoal"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            delete_profile_photo_file(member.photo_url)
            member.photo_url = new_photo_url
        elif str(submitted_form.get("remove_profile_photo") or "") == "1":
            delete_profile_photo_file(member.photo_url)
            member.photo_url = None

        previous_phone = (member.primary_phone or "").strip()
        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_login_email
        user_account.login_email = clean_login_email
        member.country = clean_country or None
        member.birth_date = parsed_birth_date
        member.whatsapp_notice_opt_in = parsed_whatsapp_notice_opt_in
        for existing_key in list(existing_profile_fields.keys()):
            if existing_key.startswith("custom_"):
                existing_profile_fields.pop(existing_key, None)
            if existing_key.startswith(f"quantity__{MENU_MEU_PERFIL_KEY}__"):
                existing_profile_fields.pop(existing_key, None)
        existing_profile_fields.update(updated_custom_fields)
        existing_profile_fields.update(updated_quantity_values)
        member.profile_custom_fields = serialize_member_profile_fields(existing_profile_fields)
        mirror_meu_perfil_custom_fields_to_member_columns(member, existing_profile_fields)
        if previous_phone != clean_primary_phone:
            member.whatsapp_verification_status = "unknown"
            member.whatsapp_last_check_at = None
            member.whatsapp_last_error = None
            member.whatsapp_last_wa_id = None
            member.whatsapp_last_message_id = None

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=_build_post_save_redirect_url_v6(submitted_form, profile_error="Falha ao gravar dados pessoais.",
                    profile_tab="pessoal",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    request.session["user_name"] = clean_full_name
    request.session["login_email"] = clean_login_email
    request.session["user_email"] = clean_login_email
    return RedirectResponse(
        url=_build_post_save_redirect_url_v6(submitted_form, profile_success="Dados pessoais atualizados com sucesso.",
            profile_tab="pessoal",
            menu=redirect_menu,
            target=redirect_target,
            profile_section=redirect_profile_section,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/users/profile/whatsapp/verify")
def verify_whatsapp_profile(request: Request) -> RedirectResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        result = execute_verify_whatsapp_profile(session, current_user["id"])

    if isinstance(result, UpdateWhatsappVerificationFailure):
        return RedirectResponse(
            url=build_users_new_url(
                profile_error=result.error,
                profile_tab="pessoal",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=build_users_new_url(
            profile_success=result.success,
            profile_tab="pessoal",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
