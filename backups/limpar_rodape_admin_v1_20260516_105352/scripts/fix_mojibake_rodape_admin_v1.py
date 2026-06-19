from pathlib import Path

FILES = [
    Path("templates/new_user.html"),
    Path("templates/macros/admin_subprocess.html"),
    Path("static/css/modules/admin_table_footer_standard_v1.css"),
    Path("static/js/modules/admin_table_footer_standard_v1.js"),
]

SUSPICIOUS = [
    "\u00c3",
    "\u00c2",
    "\ufffd",
]

REPLACEMENTS = {
    "\u00c3\u0080": "À",
    "\u00c3\u0081": "Á",
    "\u00c3\u0082": "Â",
    "\u00c3\u0083": "Ã",
    "\u00c3\u0087": "Ç",
    "\u00c3\u0089": "É",
    "\u00c3\u008a": "Ê",
    "\u00c3\u008d": "Í",
    "\u00c3\u0093": "Ó",
    "\u00c3\u0094": "Ô",
    "\u00c3\u0095": "Õ",
    "\u00c3\u009a": "Ú",
    "\u00c3\u00a0": "à",
    "\u00c3\u00a1": "á",
    "\u00c3\u00a2": "â",
    "\u00c3\u00a3": "ã",
    "\u00c3\u00a7": "ç",
    "\u00c3\u00a8": "è",
    "\u00c3\u00a9": "é",
    "\u00c3\u00aa": "ê",
    "\u00c3\u00ad": "í",
    "\u00c3\u00b3": "ó",
    "\u00c3\u00b4": "ô",
    "\u00c3\u00b5": "õ",
    "\u00c3\u00ba": "ú",
    "\u00c3\u00bc": "ü",
    "\u00c2\u00ba": "º",
    "\u00c2\u00aa": "ª",
    "\u00c2\u00ab": "«",
    "\u00c2\u00bb": "»",
    "\u00c2": "",
}

def has_suspicious(text):
    return any(marker in text for marker in SUSPICIOUS)

def print_suspicious_lines(title, text):
    found = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if has_suspicious(line):
            if not found:
                print(f"\n[{title}] linhas suspeitas:")
                found = True
            print(f"  L{line_number}: {line}")
    if not found:
        print(f"\n[{title}] sem linhas suspeitas.")
    return found

def fix_text(text):
    fixed = text
    for source, target in REPLACEMENTS.items():
        fixed = fixed.replace(source, target)
    return fixed

def main():
    any_before = False

    print("===== DIAGNOSTICO ANTES DA CORRECAO =====")
    for path in FILES:
        if not path.exists():
            print(f"\n[{path}] ficheiro nao encontrado.")
            continue

        text = path.read_text(encoding="utf-8-sig")
        any_before = print_suspicious_lines(str(path), text) or any_before

    print("\n===== APLICAR CORRECAO SEGURA =====")
    for path in FILES:
        if not path.exists():
            continue

        original = path.read_text(encoding="utf-8-sig")
        fixed = fix_text(original)

        if fixed != original:
            path.write_text(fixed, encoding="utf-8", newline="")
            print(f"Corrigido: {path}")
        else:
            print(f"Sem alteracao: {path}")

    print("\n===== DIAGNOSTICO DEPOIS DA CORRECAO =====")
    any_after = False
    for path in FILES:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8")
        any_after = print_suspicious_lines(str(path), text) or any_after

    if any_after:
        raise SystemExit("ERRO: ainda existem caracteres suspeitos de mojibake. Corrija manualmente as linhas listadas acima.")

    print("\nOK: sem caracteres suspeitos de mojibake nos ficheiros validados.")

if __name__ == "__main__":
    main()
