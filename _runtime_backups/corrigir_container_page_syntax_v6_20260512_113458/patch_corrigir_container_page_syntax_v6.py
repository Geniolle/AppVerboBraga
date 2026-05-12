from pathlib import Path
import py_compile
import re

ROOT = Path.cwd()

PAGE = ROOT / "appverbo" / "services" / "page.py"
SIDEBAR = ROOT / "templates" / "partials" / "new_user_sidebar.html"
CSS = ROOT / "static" / "css" / "new_user.css"
NEW_USER = ROOT / "templates" / "new_user.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in content.split("\n")]

    while lines and lines[-1] == "":
        lines.pop()

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def patch_page() -> None:
    text = read_text(PAGE)

    text = re.sub(r"\Afrom sqlmodel import select\s*\n", "", text)

    text = re.sub(
        r"[ \t]*# APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_START[\s\S]*?# APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_END[ \t]*\n?",
        "",
        text,
    )

    text = re.sub(
        r'^[ \t]*"sidebar_owner_entity_name":\s*sidebar_owner_entity_name,\n',
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^[ \t]*"sidebar_owner_entity_logo_url":\s*sidebar_owner_entity_logo_url,\n',
        "",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r'^[ \t]*"sidebar_owner_entity_name":\s*sidebar_owner_entity\.get\("name", ""\),\n',
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^[ \t]*"sidebar_owner_entity_logo_url":\s*sidebar_owner_entity\.get\("logo_url", ""\),\n',
        "",
        text,
        flags=re.MULTILINE,
    )

    if "sidebar_owner_entity = {" not in text:
        needle = '    current_entity_scope = ""\n'
        if needle not in text:
            raise RuntimeError("Marcador current_entity_scope nao encontrado.")

        owner_context = '''\
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V6_START
    sidebar_owner_entity = {"name": "", "logo_url": ""}
    try:
        from sqlalchemy import select as _appverbo_sidebar_select
        from appverbo.models.entity import Entity as _AppverboSidebarEntity

        _appverbo_owner_stmt = (
            _appverbo_sidebar_select(_AppverboSidebarEntity)
            .where(_AppverboSidebarEntity.profile_scope == "owner")
            .order_by(_AppverboSidebarEntity.id)
        )

        if hasattr(session, "exec"):
            _appverbo_owner_entity = session.exec(_appverbo_owner_stmt).first()
        else:
            _appverbo_owner_result = session.execute(_appverbo_owner_stmt)
            _appverbo_owner_entity = _appverbo_owner_result.scalars().first()

        if _appverbo_owner_entity is not None:
            sidebar_owner_entity = {
                "name": str(getattr(_appverbo_owner_entity, "name", "") or "").strip(),
                "logo_url": str(getattr(_appverbo_owner_entity, "logo_url", "") or "").strip(),
            }
    except Exception:
        sidebar_owner_entity = {"name": "", "logo_url": ""}
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V6_END

'''
        text = text.replace(needle, needle + owner_context, 1)

    marker = '        "current_entity_scope": current_entity_scope,'
    if marker not in text:
        raise RuntimeError("Chave current_entity_scope nao encontrada.")

    replacement = (
        '        "current_entity_scope": current_entity_scope,\n'
        '        "sidebar_owner_entity_name": sidebar_owner_entity.get("name", ""),\n'
        '        "sidebar_owner_entity_logo_url": sidebar_owner_entity.get("logo_url", ""),'
    )

    text = text.replace(marker, replacement, 1)

    if "APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_START" in text:
        raise RuntimeError("Bloco V4 invalido ainda existe em page.py.")

    write_text(PAGE, text)
    py_compile.compile(str(PAGE), doraise=True)


def patch_new_user_cache() -> None:
    text = read_text(NEW_USER)
    text = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        "/static/css/new_user.css?v=20260512-sidebar-owner-label-logo-v6",
        text,
    )
    write_text(NEW_USER, text)


patch_page()
patch_new_user_cache()

for path in [PAGE, SIDEBAR, CSS, NEW_USER]:
    content = read_text(path)
    if "\ufffd" in content:
        raise RuntimeError(f"Caractere Unicode de substituicao encontrado em {path}")

print("OK: patch V6 aplicado com sucesso.")
