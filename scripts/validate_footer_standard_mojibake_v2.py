from pathlib import Path

FILES = [
    "static/css/modules/admin_table_footer_standard_v1.css",
    "static/js/modules/admin_table_footer_standard_v1.js",
    "templates/new_user.html",
    "templates/partials/admin_table_footer_standard_v1.html",
    "templates/partials/admin_user_table_v1.html",
    "templates/macros/admin_subprocess.html",
]

BAD_TOKENS = ("Ã", "Â", "\ufffd")

for relative_path in FILES:
    path = Path(relative_path)
    text = path.read_text(encoding="utf-8")
    bad_lines = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(token in line for token in BAD_TOKENS):
            bad_lines.append((line_number, line))

    if bad_lines:
        print(f"ERRO: possivel mojibake em {relative_path}")
        for line_number, line in bad_lines:
            print(f"Linha {line_number}: {line}")
        raise SystemExit(1)

    print(f"OK: sem mojibake em {relative_path}")
