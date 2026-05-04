from __future__ import annotations

import re
from pathlib import Path


def read_text_v10(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v10(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v10(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_template_cache_v10() -> None:
    path = "templates/new_user.html"
    content = read_text_v10(path)

    content = re.sub(
        r'/static/css/new_user\.css\?v=[^"]+',
        '/static/css/new_user.css?v=20260504-users-footer-entity-like-v10',
        content,
        count=1,
    )

    require_v10(
        "new_user.css?v=20260504-users-footer-entity-like-v10" in content,
        "ERRO: cache bust do CSS V10 não foi aplicado no template.",
    )

    require_v10(
        '<section id="admin-users-created-card" class="card"' in content,
        "ERRO: card Utilizadores criados não encontrado.",
    )

    require_v10(
        '<section id="inactive-users-card" class="card"' in content,
        "ERRO: card Utilizadores inativos não encontrado.",
    )

    require_v10(
        "SuperUsers de Entidade" not in content,
        "ERRO: bloco SuperUsers de Entidade ainda existe no template.",
    )

    require_v10(
        "entity-status-inactive{% else %}" not in content,
        "ERRO: ainda existe Jinja quebrado no template.",
    )

    write_text_v10(path, content)


def patch_css_v10() -> None:
    path = "static/css/new_user.css"
    content = read_text_v10(path)

    content = re.sub(
        r'/\* APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_START \*/[\s\S]*?/\* APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_END \*/',
        "",
        content,
        flags=re.S,
    )

    block = '''
/* APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_START */
#admin-users-created-card table,
#inactive-users-card table {
  margin-bottom: 0;
}

#admin-users-created-card .admin-users-table-footer,
#inactive-users-card .admin-users-table-footer {
  align-items: center;
  border-top: 1px solid #d7deeb;
  display: flex;
  gap: 8px;
  justify-content: flex-start;
  margin-top: 12px;
  padding-top: 10px;
}

#admin-users-created-card .admin-users-table-footer select,
#inactive-users-card .admin-users-table-footer select {
  height: 34px;
  margin: 0;
  max-width: 72px;
  min-width: 64px;
  padding: 4px 10px;
  width: auto;
}

#admin-users-created-card .admin-users-table-footer > span,
#inactive-users-card .admin-users-table-footer > span {
  line-height: 34px;
}

#admin-users-created-card .admin-users-table-footer .pagination,
#inactive-users-card .admin-users-table-footer .pagination {
  align-items: center;
  display: flex;
  gap: 6px;
  margin-left: auto;
}

#admin-users-created-card .admin-users-table-footer .pagination button,
#inactive-users-card .admin-users-table-footer .pagination button {
  align-items: center;
  background: #f8fbff;
  border: 1px solid #d8e1ef;
  border-radius: 999px;
  color: #a9b5c7;
  cursor: pointer;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  height: 26px;
  justify-content: center;
  line-height: 1;
  min-width: 26px;
  padding: 0 8px;
}

#admin-users-created-card .admin-users-table-footer .pagination button.active,
#inactive-users-card .admin-users-table-footer .pagination button.active {
  background: #2f66bb;
  border-color: #2f66bb;
  color: #ffffff;
  min-width: 28px;
}

#admin-users-created-card .admin-users-table-footer .pagination button:disabled,
#inactive-users-card .admin-users-table-footer .pagination button:disabled {
  background: #f8fbff;
  border-color: #d8e1ef;
  color: #c4cedb;
  cursor: not-allowed;
  opacity: 1;
}
/* APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_END */
'''

    content = content.rstrip() + "\n\n" + block.strip() + "\n"

    require_v10(
        "APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_START" in content,
        "ERRO: bloco CSS V10 não foi inserido.",
    )

    require_v10(
        "#inactive-users-card .admin-users-table-footer" in content,
        "ERRO: CSS do footer dos inativos não foi inserido.",
    )

    require_v10(
        "margin-top: 12px;" in content,
        "ERRO: espaçamento superior do footer não foi aplicado.",
    )

    write_text_v10(path, content)


def validate_v10() -> None:
    template = read_text_v10("templates/new_user.html")
    css = read_text_v10("static/css/new_user.css")

    checks = {
        "template css cache v10": "new_user.css?v=20260504-users-footer-entity-like-v10" in template,
        "template active card": '<section id="admin-users-created-card" class="card"' in template,
        "template inactive card": '<section id="inactive-users-card" class="card"' in template,
        "template sem SuperUsers": "SuperUsers de Entidade" not in template,
        "template sem Jinja quebrado": "entity-status-inactive{% else %}" not in template,
        "css layout V10": "APPVERBO_ADMIN_USERS_TABLE_FOOTER_LAYOUT_V10_START" in css,
        "css footer ativos": "#admin-users-created-card .admin-users-table-footer" in css,
        "css footer inativos": "#inactive-users-card .admin-users-table-footer" in css,
        "css espacamento": "margin-top: 12px;" in css,
        "css paginacao circular": "border-radius: 999px;" in css,
    }

    failed = [name for name, ok in checks.items() if not ok]
    require_v10(not failed, "Falha na validação: " + ", ".join(failed))


def main_v10() -> None:
    patch_template_cache_v10()
    patch_css_v10()
    validate_v10()


if __name__ == "__main__":
    main_v10()
