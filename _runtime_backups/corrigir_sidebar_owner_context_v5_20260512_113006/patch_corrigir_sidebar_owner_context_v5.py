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

    # Remove import inserido antes do from __future__, que quebra a regra do Python.
    text = re.sub(r"\Afrom sqlmodel import select\s*\n", "", text)

    # Remove qualquer bloco V4 que tenha sido inserido dentro do dicionario de contexto.
    text = re.sub(
        r"\n[ \t]*# APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_START[\s\S]*?# APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V4_END[ \t]*\n",
        "\n",
        text,
    )

    # Remove chaves antigas que apontavam para variaveis inexistentes.
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

    # Remove chaves duplicadas ja corrigidas, para reinserir apenas uma vez.
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

    # Se nao existir contexto owner anterior, cria um bloco seguro antes do retorno.
    if (
        "APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V3_START" not in text
        and "APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V5_START" not in text
    ):
        needle = '    current_entity_scope = ""\n'
        if needle not in text:
            raise RuntimeError("Marcador current_entity_scope nao encontrado para inserir contexto owner.")

        owner_context = '''\
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V5_START
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
    # APPVERBO_SIDEBAR_OWNER_ENTITY_CONTEXT_V5_END

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

    write_text(PAGE, text)
    py_compile.compile(str(PAGE), doraise=True)


def patch_sidebar() -> None:
    text = read_text(SIDEBAR)

    owner_block = '''\
    {# APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V5_START #}
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
        <span class="appverbo-sidebar-owner-label">Entidade owner</span>
        <span class="appverbo-sidebar-owner-name">{{ sidebar_owner_entity_name if sidebar_owner_entity_name else "Owner nao configurado" }}</span>
      </div>
    </div>
    {# APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V5_END #}
'''

    pattern = r"\s*\{# APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V\d+_START #\}[\s\S]*?\{# APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V\d+_END #\}\s*"

    if re.search(pattern, text):
        text = re.sub(pattern, "\n" + owner_block + "\n", text, count=1)
    else:
        if "</aside>" not in text:
            raise RuntimeError("Tag </aside> nao encontrada no sidebar.")
        text = text.replace("</aside>", owner_block + "    </aside>", 1)

    write_text(SIDEBAR, text)


def patch_css() -> None:
    text = read_text(CSS)

    owner_css = '''\

/* APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V5_START */
.appverbo-sidebar-owner-card {
  margin: auto 14px 14px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--sidebar-line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
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

.appverbo-sidebar-owner-label {
  font-size: 10px;
  line-height: 1.1;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
  font-weight: 700;
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
/* APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V5_END */
'''

    pattern = r"/\* APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V\d+_START \*/[\s\S]*?/\* APPVERBO_SIDEBAR_OWNER_ENTITY_LABEL_V\d+_END \*/"

    if re.search(pattern, text):
        text = re.sub(pattern, owner_css.strip(), text, count=1)
    else:
        text = text.rstrip() + "\n" + owner_css

    write_text(CSS, text)


def patch_new_user() -> None:
    text = read_text(NEW_USER)
    text = re.sub(
        r"/static/css/new_user\.css\?v=[^\"]+",
        "/static/css/new_user.css?v=20260512-sidebar-owner-label-logo-v5",
        text,
    )
    write_text(NEW_USER, text)


patch_page()
patch_sidebar()
patch_css()
patch_new_user()

for path in [PAGE, SIDEBAR, CSS, NEW_USER]:
    content = read_text(path)
    if "\ufffd" in content:
        raise RuntimeError(f"Caractere Unicode de substituicao encontrado em {path}")

print("OK: patch V5 aplicado com sucesso.")
