from __future__ import annotations

import re
from pathlib import Path


START_MARKER = "APPVERBO_ENTITY_DELETE_INACTIVE_ONLY_V1_START"
END_MARKER = "APPVERBO_ENTITY_DELETE_INACTIVE_ONLY_V1_END"


def read_text_v1(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v1(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v1(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_template_v1() -> None:
    path = "templates/new_user.html"
    content = read_text_v1(path)

    form_pattern = re.compile(
        r'(?P<form><form\b(?=[^>]*\baction=(["\'])/entities/delete\2)[\s\S]*?</form>)',
        re.IGNORECASE,
    )

    matches = list(form_pattern.finditer(content))
    require_v1(matches, "ERRO: nenhum formulário /entities/delete encontrado no template.")

    result_parts: list[str] = []
    last_index = 0
    wrapped_count = 0
    already_wrapped_count = 0

    for match in matches:
        start = match.start()
        end = match.end()
        form_html = match.group("form")

        before_window = content[max(0, start - 250):start]
        after_window = content[end:end + 250]
        is_already_wrapped = (
            START_MARKER in before_window
            or "{% if not row.is_active %}" in before_window
            or "{% if row.is_active == false %}" in before_window
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
                "{% if not row.is_active %}\n"
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
        "ERRO: validação falhou. Nenhum formulário /entities/delete encontrado após patch.",
    )

    for validation_match in validation_matches:
        start = validation_match.start()
        end = validation_match.end()
        before_window = new_content[max(0, start - 300):start]
        after_window = new_content[end:end + 300]

        guarded = (
            "{% if not row.is_active %}" in before_window
            or "{% if row.is_active == false %}" in before_window
            or START_MARKER in before_window
        ) and (
            "{% endif %}" in after_window
            or END_MARKER in after_window
        )

        require_v1(
            guarded,
            "ERRO: existe formulário /entities/delete sem guarda de entidade inativa.",
        )

    write_text_v1(path, new_content)

    print(f"OK: formulários de delete envolvidos agora: {wrapped_count}")
    print(f"OK: formulários de delete já protegidos: {already_wrapped_count}")


def patch_delete_handler_v1() -> None:
    path = "appverbo/routes/entities/delete_handler.py"
    content = read_text_v1(path)

    if "APPVERBO_DELETE_ONLY_INACTIVE_ENTITY_V1_START" in content:
        write_text_v1(path, content)
        print("OK: backend já tinha bloqueio para entidades ativas.")
        return

    guard_block = '''        # APPVERBO_DELETE_ONLY_INACTIVE_ENTITY_V1_START
        if entity.is_active:
            return RedirectResponse(
                url=build_users_new_url(
                    entity_error="Só é permitido eliminar entidades inativas.",
                    menu="administrativo",
                    admin_tab="entidade",
                    entity_edit_id=str(parsed_entity_id),
                )
                + "#edit-entity-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        # APPVERBO_DELETE_ONLY_INACTIVE_ENTITY_V1_END

'''

    pattern = re.compile(
        r'(?P<entity_none_block>'
        r'        entity = session\.get\(Entity, parsed_entity_id\)\n'
        r'        if entity is None:\n'
        r'[\s\S]*?'
        r'            \)\n'
        r'\n'
        r')'
        r'(?P<next_block>        linked_users_count = session\.scalar\()',
        re.MULTILINE,
    )

    new_content, count = pattern.subn(
        lambda match: match.group("entity_none_block") + guard_block + match.group("next_block"),
        content,
        count=1,
    )

    require_v1(
        count == 1,
        "ERRO: não foi possível inserir bloqueio backend antes de linked_users_count.",
    )

    require_v1(
        "if entity.is_active:" in new_content,
        "ERRO: validação falhou. Bloqueio entity.is_active não foi inserido.",
    )

    write_text_v1(path, new_content)
    print("OK: backend agora bloqueia delete de entidade ativa.")


def validate_v1() -> None:
    template = read_text_v1("templates/new_user.html")
    delete_handler = read_text_v1("appverbo/routes/entities/delete_handler.py")

    require_v1(
        '/entities/delete' in template,
        "ERRO: template não contém formulário /entities/delete.",
    )

    require_v1(
        "{% if not row.is_active %}" in template or START_MARKER in template,
        "ERRO: template não contém regra para mostrar delete apenas em entidades inativas.",
    )

    require_v1(
        "if entity.is_active:" in delete_handler,
        "ERRO: backend não bloqueia delete de entidade ativa.",
    )

    require_v1(
        "Só é permitido eliminar entidades inativas." in delete_handler,
        "ERRO: mensagem de bloqueio backend não encontrada.",
    )


def main_v1() -> None:
    patch_template_v1()
    patch_delete_handler_v1()
    validate_v1()


if __name__ == "__main__":
    main_v1()
