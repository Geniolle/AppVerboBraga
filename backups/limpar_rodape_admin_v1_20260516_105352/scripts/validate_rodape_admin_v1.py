from pathlib import Path

FILES = [
    Path("templates/new_user.html"),
    Path("templates/macros/admin_subprocess.html"),
    Path("static/css/modules/admin_table_footer_standard_v1.css"),
    Path("static/js/modules/admin_table_footer_standard_v1.js"),
]

REQUIRED_MARKERS = {
    Path("templates/new_user.html"): [
        "admin_table_footer_standard_v1.css",
        "admin_table_footer_standard_v1.js",
    ],
    Path("templates/macros/admin_subprocess.html"): [
        "APPVERBO_ADMIN_SUBPROCESS_TABLE_FOOTER_STANDARD_V1_START",
        "admin-subprocess-table-footer-v1",
    ],
    Path("static/css/modules/admin_table_footer_standard_v1.css"): [
        "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
        ".table-limiter",
        ".admin-status-table-footer-v1",
        ".admin-subprocess-table-footer-v1",
        "min-width: 84px",
        "height: 34px",
        "font-size: 14px",
    ],
    Path("static/js/modules/admin_table_footer_standard_v1.js"): [
        "APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START",
        "function obterTabelaDoRodapeAdminTableFooterStandard_v1",
        "function instalarRodapesAdminTableFooterStandard_v1",
    ],
}

SUSPICIOUS_CODEPOINTS = {
    0x00C3: "LATIN CAPITAL LETTER A WITH TILDE - sinal comum de mojibake",
    0x00C2: "LATIN CAPITAL LETTER A WITH CIRCUMFLEX - sinal comum de mojibake",
    0xFFFD: "REPLACEMENT CHARACTER - caractere inválido substituído",
}

ALLOWED_CONTEXTS = [
    "Ã©",
    "Ã£",
    "Ã§",
    "Ã³",
    "Ãª",
    "Âº",
    "Âª",
]

def read_text(path):
    return path.read_text(encoding="utf-8-sig")

def validate_exists():
    print("===== VALIDAR EXISTENCIA DOS FICHEIROS =====")
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"ERRO: ficheiro nao encontrado: {path}")
        print(f"OK: {path}")

def validate_markers():
    print("\n===== VALIDAR MARCADORES DO RODAPE PADRAO =====")
    for path, markers in REQUIRED_MARKERS.items():
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                raise SystemExit(f"ERRO: marcador nao encontrado em {path}: {marker}")
            print(f"OK: {path}: {marker}")

def validate_suspicious_chars():
    print("\n===== VALIDAR MOJIBAKE POR CODEPOINT =====")
    found = False

    for path in FILES:
        text = read_text(path)

        for line_number, line in enumerate(text.splitlines(), start=1):
            for char in line:
                codepoint = ord(char)
                if codepoint in SUSPICIOUS_CODEPOINTS:
                    found = True
                    description = SUSPICIOUS_CODEPOINTS[codepoint]
                    print(f"ERRO: {path} L{line_number}: U+{codepoint:04X} {description}")
                    print(f"      {line}")

        if not any(ord(char) in SUSPICIOUS_CODEPOINTS for char in text):
            print(f"OK: {path}: sem codepoints suspeitos")

    if found:
        raise SystemExit("ERRO: foram encontrados caracteres suspeitos de mojibake.")

def main():
    validate_exists()
    validate_markers()
    validate_suspicious_chars()
    print("\nOK: validacao Python concluida sem mojibake real.")

if __name__ == "__main__":
    main()
