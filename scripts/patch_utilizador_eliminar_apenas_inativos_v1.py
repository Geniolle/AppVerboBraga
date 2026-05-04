from __future__ import annotations

import re
from pathlib import Path


START_MARKER = "APPVERBO_USER_DELETE_INACTIVE_ONLY_V1_START"
END_MARKER = "APPVERBO_USER_DELETE_INACTIVE_ONLY_V1_END"


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_page_service_v1() -> None:
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

    if '"account_status_label": row.get("account_status_label", user_account_status_label_pt_v1(row["account_status"])),' not in content:
        content = content.replace(
            '                "account_status": row["account_status"],\n',
            '                "account_status": row["account_status"],\n'
            '                "account_status_label": row.get("account_status_label", user_account_status_label_pt_v1(row["account_status"])),\n',
            1,
        )

    write_text_v1(path, content)


def patch_template_status_text_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    content = content.replace(
        "{{ row.account_status }}",
        "{{ row.account_status_label if row.account_status_label is defined else row.account_status }}",
    )

    content = content.replace(
        "{{ row.account_status_label if row.account_status_label is defined else row.account_status_label if row.account_status_label is defined else row.account_status }}",
        "{{ row.account_status_label if row.account_status_label is defined else row.account_status }}",
    )

    write_text_v1(path, content)


def patch_template_delete_button_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    form_pattern = re.compile(
        r'(?P<form><form\b(?=[^>]*\baction=(["\'])/users/delete\2)[\s\S]*?</form>)',
        re.IGNORECASE,
    )

    matches = list(form_pattern.finditer(content))
    require_v1(matches, "ERRO: nenhum formulário /users/delete encontrado no template.")

    result_parts: list[str] = []
    last_index = 0
    wrapped_count = 0
    already_wrapped_count = 0

    for match in matches:
        start = match.start()
        end = match.end()
        form_html = match.group("form")

        before_window = content[max(0, start - 500):start]
        after_window = content[end:end + 500]
        is_already_wrapped = (
            START_MARKER in before_window
            or "row.account_status_is_inactive" in before_window
            or "UserAccountStatus.INACTIVE" in before_window
        ) and (
            END_MARKER in after_window
            or "{% endif %}" in after_window
        )

        result_parts.append(content[last_index:start])

        if is_already_wrapped:
            result_parts.append(form_html)
            already_wrapped_count += 1
        else:
            wrapped_form = (
                "{% if row is defined and (row.account_status_is_inactive or row.account_status == 'inactive') %}\n"
                f"<!-- {START_MARKER} -->\n"
                f"{form_html}\n"
                f"<!-- {END_MARKER} -->\n"
                "{% endif %}"
            )
            result_parts.append(wrapped_form)
            wrapped_count += 1

        last_index = end

    result_parts.append(content[last_index:])
    new_content = "".join(result_parts)

    validation_matches = list(form_pattern.finditer(new_content))
    require_v1(
        validation_matches,
        "ERRO: validação falhou. Nenhum formulário /users/delete encontrado após patch.",
    )

    for validation_match in validation_matches:
        start = validation_match.start()
        end = validation_match.end()
        before_window = new_content[max(0, start - 600):start]
        after_window = new_content[end:end + 600]

        guarded = (
            "row.account_status_is_inactive" in before_window
            or START_MARKER in before_window
        ) and (
            "{% endif %}" in after_window
            or END_MARKER in after_window
        )

        require_v1(
            guarded,
            "ERRO: existe formulário /users/delete sem regra de utilizador inativo.",
        )

    write_text_v1(path, new_content)

    print(f"OK: formulários de delete envolvidos agora: {wrapped_count}")
    print(f"OK: formulários de delete já protegidos: {already_wrapped_count}")


def patch_delete_handler_v1() -> None:
    path = "appverbo/routes/users/delete_handler.py"
    content = read_text_v1(path)

    if "APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_START" in content:
        write_text_v1(path, content)
        print("OK: backend já tinha bloqueio para utilizadores ativos/não inativos.")
        return

    guard_block = '''        # APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_START
        if str(user.account_status or "").strip().lower() != UserAccountStatus.INACTIVE.value:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Só é permitido eliminar utilizadores inativos.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        # APPVERBO_DELETE_ONLY_INACTIVE_USER_V1_END

'''

    pattern = re.compile(
        r'(?P<permission_block>'
        r'        if not _member_is_within_permissions\(\n'
        r'[\s\S]*?'
        r'            \)\n'
        r'\n'
        r')'
        r'(?P<next_block>        target_is_active_admin = \()',
        re.MULTILINE,
    )

    new_content, count = pattern.subn(
        lambda match: match.group("permission_block") + guard_block + match.group("next_block"),
        content,
        count=1,
    )

    require_v1(
        count == 1,
        "ERRO: não foi possível inserir bloqueio backend antes de target_is_active_admin.",
    )

    require_v1(
        "Só é permitido eliminar utilizadores inativos." in new_content,
        "ERRO: validação falhou. Mensagem de bloqueio não foi inserida.",
    )

    write_text_v1(path, new_content)
    print("OK: backend agora bloqueia delete de utilizador não inativo.")


def validate_v1() -> None:
    template = read_text_v1("templates/new_user.html")
    page_service = read_text_v1("appverbo/services/page.py")
    delete_handler = read_text_v1("appverbo/routes/users/delete_handler.py")

    require_v1(
        "user_account_status_label_pt_v1" in page_service,
        "ERRO: função de label português do estado não existe no page.py.",
    )

    require_v1(
        '"account_status_label"' in page_service,
        "ERRO: account_status_label não existe nos dados dos utilizadores.",
    )

    require_v1(
        '"account_status_is_inactive"' in page_service,
        "ERRO: account_status_is_inactive não existe nos dados dos utilizadores.",
    )

    require_v1(
        "row.account_status_label" in template,
        "ERRO: template não usa o texto português do estado.",
    )

    require_v1(
        '/users/delete' in template,
        "ERRO: template não contém formulário /users/delete.",
    )

    require_v1(
        "row.account_status_is_inactive" in template,
        "ERRO: template não contém regra para mostrar delete apenas em utilizadores inativos.",
    )

    require_v1(
        "UserAccountStatus.INACTIVE.value" in delete_handler,
        "ERRO: backend não compara com UserAccountStatus.INACTIVE.",
    )

    require_v1(
        "Só é permitido eliminar utilizadores inativos." in delete_handler,
        "ERRO: backend não contém mensagem de bloqueio.",
    )


def main_v1() -> None:
    patch_page_service_v1()
    patch_template_status_text_v1()
    patch_template_delete_button_v1()
    patch_delete_handler_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
