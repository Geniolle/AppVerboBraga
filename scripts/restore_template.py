from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"

def main() -> None:
    # 1) Encontrar e restaurar o backup feito pelo v4
    backups = sorted(TEMPLATE_PATH.parent.glob("new_user.html.bak_*"))
    if not backups:
        print("ERRO: Nenhum backup encontrado! (new_user.html.bak_*)")
        return
    
    latest_backup = backups[-1]
    print(f"Restaurando backup: {latest_backup.name}")
    shutil.copy2(latest_backup, TEMPLATE_PATH)
    
    content = TEMPLATE_PATH.read_text(encoding="utf-8-sig")
    
    # 2) Remover scripts antigos
    for script_name in ["force_lista_tab_v1.js", "process_lists_v1.js", "process_lists_runtime_v2.js"]:
        content = re.sub(
            rf'\s*<script\b[^>]*{re.escape(script_name)}[^>]*></script>\s*',
            "\n",
            content,
            flags=re.IGNORECASE,
        )
        
    # 3) Injetar script v3
    runtime_tag = '<script src="/static/js/modules/process_lists_runtime_v3.js?v=20260428c"></script>'
    if "process_lists_runtime_v3.js" not in content:
        marker = '<script src="/static/js/new_user.js'
        idx = content.find(marker)
        if idx >= 0:
            insert_at = content.find("</script>", idx) + 9
            content = content[:insert_at] + "\n  " + runtime_tag + content[insert_at:]
        else:
            idx = content.rfind("{% endblock %}")
            if idx >= 0:
                content = content[:idx] + "  " + runtime_tag + "\n" + content[idx:]
                
    # 4) Encontrar tags "Campos adicionais" de forma SEGURA (sem engolir o ficheiro todo)
    tab_pattern = re.compile(
        r'<(?P<tag>a|button)\b(?P<attrs>[^>]*)>(?P<body>(?:(?!</?(?:a|button)\b)[\s\S])*?Campos adicionais(?:(?!</?(?:a|button)\b)[\s\S])*?)</(?P=tag)>',
        flags=re.IGNORECASE,
    )
    
    matches = list(tab_pattern.finditer(content))
    if len(matches) >= 2:
        replacements = []
        for match in matches[1:]:
            tag_name = match.group("tag")
            attrs = match.group("attrs")
            
            attrs = attrs.replace("campos-adicionais", "lista").replace("campos_adicionais", "lista")
            attrs = attrs.replace("Campos adicionais", "Listas").replace("campos adicionais", "Listas")
            
            new_tag = f"<{tag_name}{attrs}>Listas</{tag_name}>"
            replacements.append((match.start(), match.end(), new_tag))
            
        for start, end, new_value in reversed(replacements):
            content = content[:start] + new_value + content[end:]
        print(f"OK: {len(replacements)} aba(s) duplicada(s) corrigida(s) para Listas.")

    elif len(matches) == 1 and "settings_tab=lista" not in content and 'data-settings-tab="lista"' not in content:
        match = matches[0]
        tag_name = match.group("tag")
        attrs = match.group("attrs")
        
        attrs = attrs.replace("campos-adicionais", "lista").replace("campos_adicionais", "lista")
        attrs = attrs.replace("Campos adicionais", "Listas").replace("campos adicionais", "Listas")
        
        lista_tag = f"<{tag_name}{attrs}>Listas</{tag_name}>"
        content = content[:match.end()] + "\n              " + lista_tag + content[match.end()]
        print("OK: aba Listas criada após Campos adicionais.")
        
    # 5) Corrigir texto "Lista" em abas de "Listas" já existentes (de forma SEGURA)
    def corrigir_tag_lista(match: re.Match[str]) -> str:
        tag = match.group(0)
        tag = re.sub(r">(.*?)</a>", ">Listas</a>", tag, flags=re.IGNORECASE | re.DOTALL)
        tag = re.sub(r">(.*?)</button>", ">Listas</button>", tag, flags=re.IGNORECASE | re.DOTALL)
        tag = tag.replace("Campos adicionais", "Listas").replace("campos adicionais", "Listas")
        return tag

    content = re.sub(
        r'<(?P<tag>a|button)\b[^>]*(?:settings_tab=lista|data-settings-tab=[\'"]lista[\'"])[^>]*>(?:(?!</?(?:a|button)\b)[\s\S])*?</(?P=tag)>',
        corrigir_tag_lista,
        content,
        flags=re.IGNORECASE,
    )
        
    TEMPLATE_PATH.write_text(content, encoding="utf-8", newline="\n")
    print("OK: new_user.html restaurado e corrigido com sucesso!")

if __name__ == "__main__":
    main()