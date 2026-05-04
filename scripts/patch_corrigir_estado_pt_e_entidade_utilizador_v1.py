from __future__ import annotations

import re
from pathlib import Path


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_account_status_select_labels_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    status_labels = {
        "active": "Ativo",
        "pending": "Pendente",
        "inactive": "Inativo",
        "blocked": "Bloqueado",
    }

    select_pattern = re.compile(
        r'(?P<select><select\b(?=[^>]*\bname=(["\'])account_status\2)[\s\S]*?</select>)',
        re.IGNORECASE,
    )

    option_pattern_template = (
        r'(?P<open><option\b(?=[^>]*\bvalue=(["\']){value}\2)[^>]*>)'
        r'(?P<label>[\s\S]*?)'
        r'(?P<close></option>)'
    )

    select_count = 0

    def patch_select(match: re.Match[str]) -> str:
        nonlocal select_count
        select_count += 1
        select_html = match.group("select")

        for value, label in status_labels.items():
            option_pattern = re.compile(
                option_pattern_template.format(value=re.escape(value)),
                re.IGNORECASE,
            )

            select_html = option_pattern.sub(
                lambda option_match: (
                    option_match.group("open")
                    + label
                    + option_match.group("close")
                ),
                select_html,
            )

        return select_html

    content = select_pattern.sub(patch_select, content)

    require_v1(
        select_count > 0,
        "ERRO: nenhum select name='account_status' encontrado no template.",
    )

    for select_match in select_pattern.finditer(content):
        select_html = select_match.group("select")
        for raw_value in ("active", "pending", "inactive", "blocked"):
            raw_option_text_pattern = re.compile(
                r'<option\b(?=[^>]*\bvalue=(["\'])'
                + re.escape(raw_value)
                + r'\1)[^>]*>\s*'
                + re.escape(raw_value)
                + r'\s*</option>',
                re.IGNORECASE,
            )
            require_v1(
                not raw_option_text_pattern.search(select_html),
                f"ERRO: select account_status ainda mostra texto técnico: {raw_value}",
            )

    write_text_v1(path, content)


def ensure_page_status_labels_v1() -> None:
    path = "appverbo/services/page.py"
    content = read_text_v1(path)

    if "APPVERBO_USER_STATUS_LABEL_PT_V1_START" not in content:
        helper_block = '''    # APPVERBO_USER_STATUS_LABEL_PT_V1_START
    def normalize_user_account_status_v1(raw_status: Any) -> str:
        return str(raw_status or "").strip().lower()

    def user_account_status_label_pt_v1(raw_status: Any) -> str:
        normalized_status = normalize_user_account_status_v1(raw_status)
        status_label_map = {
            UserAccountStatus.ACTIVE.value: "Ativo",
            UserAccountStatus.PENDING.value: "Pendente",
            UserAccountStatus.INACTIVE.value: "Inativo",
            UserAccountStatus.BLOCKED.value: "Bloqueado",
        }
        return status_label_map.get(normalized_status, normalized_status or "-")
    # APPVERBO_USER_STATUS_LABEL_PT_V1_END

'''
        content = content.replace(
            "    all_users = [\n",
            helper_block + "    all_users = [\n",
            1,
        )

    if '"account_status_label": user_account_status_label_pt_v1(row.account_status),' not in content:
        content = content.replace(
            '            "account_status": row.account_status,\n',
            '            "account_status": normalize_user_account_status_v1(row.account_status),\n'
            '            "account_status_label": user_account_status_label_pt_v1(row.account_status),\n'
            '            "account_status_is_inactive": normalize_user_account_status_v1(row.account_status) == UserAccountStatus.INACTIVE.value,\n',
            1,
        )

    write_text_v1(path, content)


def patch_update_user_keep_current_entity_v1() -> None:
    path = "appverbo/routes/users/update_handler.py"
    content = read_text_v1(path)

    if "APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_START" in content:
        write_text_v1(path, content)
        return

    fallback_block = '''        # APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_START
        if selected_entity is None:
            fallback_entity_stmt = (
                select(Entity)
                .join(MemberEntity, MemberEntity.entity_id == Entity.id)
                .where(
                    MemberEntity.member_id == member.id,
                    MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                    Entity.is_active.is_(True),
                )
                .order_by(MemberEntity.id.asc())
            )

            if not entity_permissions.get("can_manage_all_entities"):
                allowed_entity_ids = sorted(
                    set(entity_permissions.get("allowed_entity_ids") or set())
                )

                if allowed_entity_ids:
                    fallback_entity_stmt = fallback_entity_stmt.where(
                        Entity.id.in_(allowed_entity_ids)
                    )
                else:
                    fallback_entity_stmt = fallback_entity_stmt.where(Entity.id == -1)

            selected_entity = session.execute(
                fallback_entity_stmt.limit(1)
            ).scalar_one_or_none()

            if selected_entity is not None:
                entity_resolution_error = ""
        # APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_END

'''

    pattern = re.compile(
        r'(?P<resolve>'
        r'        selected_entity, entity_resolution_error = _resolve_entity_from_user_email\(\n'
        r'[\s\S]*?'
        r'        \)\n'
        r')'
        r'(?P<error_check>'
        r'        if selected_entity is None and entity_resolution_error:\n'
        r'            errors\.append\(entity_resolution_error\)\n'
        r')',
        re.MULTILINE,
    )

    new_content, count = pattern.subn(
        lambda match: match.group("resolve") + fallback_block + match.group("error_check"),
        content,
        count=1,
    )

    require_v1(
        count == 1,
        "ERRO: não foi possível inserir fallback para manter entidade atual no update_user.",
    )

    require_v1(
        "entity_resolution_error = \"\"" in new_content,
        "ERRO: validação falhou. O fallback não limpa o erro de resolução da entidade.",
    )

    write_text_v1(path, new_content)


def validate_v1() -> None:
    template = read_text_v1("templates/new_user.html")
    page_service = read_text_v1("appverbo/services/page.py")
    update_handler = read_text_v1("appverbo/routes/users/update_handler.py")

    require_v1(
        "Ativo" in template and "Inativo" in template and "Pendente" in template and "Bloqueado" in template,
        "ERRO: labels PT do select de estado não foram encontrados no template.",
    )

    require_v1(
        "user_account_status_label_pt_v1" in page_service,
        "ERRO: labels PT da listagem não existem no page.py.",
    )

    require_v1(
        "APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_START" in update_handler,
        "ERRO: fallback de entidade atual não existe no update_handler.py.",
    )

    require_v1(
        "entity_resolution_error = \"\"" in update_handler,
        "ERRO: fallback não remove o erro de determinação da entidade.",
    )


def main_v1() -> None:
    patch_account_status_select_labels_v1()
    ensure_page_status_labels_v1()
    patch_update_user_keep_current_entity_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
