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


def patch_page_context() -> None:
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
            raise RuntimeError("Marcador current_entity_scope nao encontrado em page.py.")

        owner_context = '''\
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V7_START
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
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V7_END

'''
        text = text.replace(needle, needle + owner_context, 1)

    marker = '        "current_entity_scope": current_entity_scope,'
    if marker not in text:
        raise RuntimeError("Chave current_entity_scope nao encontrada no dicionario de contexto.")

    replacement = (
        '        "current_entity_scope": current_entity_scope,\n'
        '        "sidebar_owner_entity_name": sidebar_owner_entity.get("name", ""),\n'
        '        "sidebar_owner_entity_logo_url": sidebar_owner_entity.get("logo_url", ""),'
    )

    text = text.replace(marker, replacement, 1)

    if "APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_START" in text:
        raise RuntimeError("Bloco V4 invalido ainda existe em page.py.")

    if "sidebar_owner_entity = None" in text:
        raise RuntimeError("Residuo invalido encontrado em page.py: sidebar_owner_entity = None")

    write_text(PAGE, text)
    py_compile.compile(str(PAGE), doraise=True)


def patch_sidebar_footer() -> None:
    text = read_text(SIDEBAR)

    owner_footer = '''\
    {# APPVERBO_SIDEBAR_OWNER_ENTITY_FOOTER_V7_START #}
    <footer class="appverbo-sidebar-owner-footer" aria-label="Rodape da entidade owner">
      <div class="appverbo-sidebar-owner-card" aria-label="Entidade owner">
        <div class="appverbo-sidebar-owner-logo-wrap">
          {% if sidebar_owner_entity_logo_url %}
            <img class="appverbo-sidebar-owner-logo" src="{{ sidebar_owner_entity_logo_url }}" alt="Logo da entidade owner">
          {% else %}
            <span class="appverbo-sidebar-owner-logo appverbo-sidebar-owner-logo-fallback" aria-hidden="true">
              {{ (sidebar_owner_entity_name[:1] if sidebar_owner_entity_name else "A")|upper }}
            </span>
          {% endif %}
        </div>
        <div class="appverbo-sidebar-owner-text">
          <span class="appverbo-sidebar-owner-name">{{ sidebar_owner_entity_name if sidebar_owner_entity_name else "Owner nao configurado" }}</span>
        </div>
      </div>
    </footer>
    {# APPVERBO_SIDEBAR_OWNER_ENTITY_FOOTER_V7_END #}
'''

    old_block_pattern = (
        r"\s*\{# APPVERBO_SIDEBAR_OWNER_ENTITY_(?:LABEL|FOOTER)_V\d+_START #\}"
        r"[\s\S]*?"
        r"\{# APPVERBO_SIDEBAR_OWNER_ENTITY_(?:LABEL|FOOTER)_V\d+_END #\}\s*"
    )

    if re.search(old_block_pattern, text):
        text = re.sub(old_block_pattern, "\n" + owner_footer + "\n", text, count=1)
    else:
        if "</aside>" not in text:
            raise RuntimeError("Tag </aside> nao encontrada no sidebar.")
        text = text.replace("</aside>", owner_footer + "    </aside>", 1)

    if "</footer>" not in text:
        raise RuntimeError("Footer da logo owner nao foi aplicado no sidebar.")

    write_text(SIDEBAR, text)


def patch_css_footer() -> None:
    text = read_text(CSS)

    owner_css = '''\

/* APPVERBO_SIDEBAR_OWNER_ENTITY_FOOTER_V7_START */
.sidebar {
  display: flex;
  flex-direction: column;
}

.appverbo-sidebar-owner-footer {
  margin-top: auto;
  padding: 12px 14px 14px;
  flex: 0 0 auto;
}

.appverbo-sidebar-owner-card {
  margin: 0;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--sidebar-line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
}

.appverbo-sidebar-owner-logo-wrap {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.appverbo-sidebar-owner-logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
  border: 1px solid var(--sidebar-line);
  background: #fff;
}

.appverbo-sidebar-owner-logo-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 14px;
  color: #334155;
}

.appverbo-sidebar-owner-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.appverbo-sidebar-owner-name {
  font-size: 13px;
  line-height: 1.2;
  color: #0f172a;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* APPVERBO_SIDEBAR_OWNER_ENTITY_FOOTER_V7_END */
'''

    old_css_pattern = (
        r"/\* APPVERBO_SIDEBAR_OWNER_ENTITY_(?:LABEL|FOOTER)_V\d+_START \*/"
        r"[\s\S]*?"
        r"/\* APPVERBO_SIDEBAR_OWNER_ENTITY_(?:LABEL|FOOTER)_V\d+_END \*/"
    )

    if re.search(old_css_pattern, text):
        text = re.sub(old_css_pattern, owner_css.strip(), text, count=1)
    else:
        text = text.rstrip() + "\n" + owner_css

    write_text(CSS, text)


def patch_new_user_cache() -> None:
    text = read_text(NEW_USER)
    text = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        "/static/css/new_user.css?v=20260512-sidebar-owner-footer-logo-v7",
        text,
    )
    write_text(NEW_USER, text)


patch_page_context()
patch_sidebar_footer()
patch_css_footer()
patch_new_user_cache()

for path in [PAGE, SIDEBAR, CSS, NEW_USER]:
    content = read_text(path)
    if "\ufffd" in content:
        raise RuntimeError(f"Caractere Unicode de substituicao encontrado em {path}")

print("OK: patch V7 aplicado. Logo owner movida para o rodape do sidebar.")
