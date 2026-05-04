from __future__ import annotations

import re
from pathlib import Path


def read_text_v9(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v9(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v9(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_template_cache_v9() -> None:
    path = "templates/new_user.html"
    content = read_text_v9(path)

    content = re.sub(
        r'/static/js/new_user\.js\?v=[^"]+',
        '/static/js/new_user.js?v=20260504-users-inactive-visible-v9',
        content,
        count=1,
    )

    require_v9(
        "new_user.js?v=20260504-users-inactive-visible-v9" in content,
        "ERRO: versão do JS V9 não foi aplicada no template.",
    )

    require_v9(
        '<section id="inactive-users-card" class="card"' in content,
        "ERRO: section inactive-users-card não existe no template.",
    )

    require_v9(
        "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_START" in content,
        "ERRO: bloco de inativos V7 não existe no template.",
    )

    write_text_v9(path, content)


def patch_new_user_js_v9() -> None:
    path = "static/js/new_user.js"
    content = read_text_v9(path)

    old_block = '''        card.id === "create-user-card" ||
        card.id === "edit-user-card" ||
        card.id === "admin-users-created-card"'''

    new_block = '''        card.id === "create-user-card" ||
        card.id === "edit-user-card" ||
        card.id === "admin-users-created-card" ||
        card.id === "inactive-users-card"'''

    if old_block in content and new_block not in content:
        content = content.replace(old_block, new_block, 1)

    require_v9(
        'card.id === "inactive-users-card"' in content,
        "ERRO: inactive-users-card não foi incluído na regra principal do JS.",
    )

    require_v9(
        "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" in content,
        "ERRO: guard V8 não existe no JS.",
    )

    write_text_v9(path, content)


def validate_v9() -> None:
    template = read_text_v9("templates/new_user.html")
    js = read_text_v9("static/js/new_user.js")
    page_service = read_text_v9("appverbo/services/page.py")
    delete_handler = read_text_v9("appverbo/routes/users/delete_handler.py")

    checks = {
        "template js cache v9": "new_user.js?v=20260504-users-inactive-visible-v9" in template,
        "template inactive card": '<section id="inactive-users-card" class="card"' in template,
        "template active section": "APPVERBO_ADMIN_USERS_ACTIVE_SECTION_V7_START" in template,
        "template inactive section": "APPVERBO_ADMIN_USERS_INACTIVE_SECTION_V7_START" in template,
        "template sem SuperUsers": "SuperUsers de Entidade" not in template,
        "template sem Jinja quebrado": "entity-status-inactive{% else %}" not in template,
        "js regra principal inactive card": 'card.id === "inactive-users-card"' in js,
        "js guard V8 presente": "APPVERBO_ADMIN_INACTIVE_USERS_VISIBILITY_V8_START" in js,
        "page inactive_users": "inactive_users = [" in page_service,
        "page context inactive_users": '"inactive_users": inactive_users,' in page_service,
        "backend delete inactive only": "Só é permitido eliminar utilizadores inativos." in delete_handler,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v9(not failed, "Falha na validação: " + ", ".join(failed))


def main_v9() -> None:
    patch_template_cache_v9()
    patch_new_user_js_v9()
    validate_v9()


if __name__ == "__main__":
    main_v9()
