from pathlib import Path

ROOT = Path.cwd()
template_path = ROOT / "templates" / "new_user.html"

content = template_path.read_text(encoding="utf-8")
lines = content.splitlines()

clean_lines = []

for line in lines:
    if "additional_fields_header_groups_v3.js" in line:
        continue

    if "additional_fields_header_groups_v4.js" in line:
        continue

    if "additional_fields_header_groups_v5.js" in line:
        continue

    if "additional_fields_header_separators_v1.js" in line:
        continue

    if "additional_fields_header_separators_v2.js" in line:
        continue

    if "additional_fields_compact_layout_v1.js" in line:
        continue

    clean_lines.append(line)

new_script = '  <script src="/static/js/modules/additional_fields_compact_layout_v1.js?v=20260429-compact-layout-v2"></script>'

inserted = False

for index, line in enumerate(clean_lines):
    if "process_lists_runtime_v5.js" in line:
        clean_lines.insert(index + 1, new_script)
        inserted = True
        break

if not inserted:
    for index, line in enumerate(clean_lines):
        if "{% endblock %}" in line:
            clean_lines.insert(index, new_script)
            inserted = True
            break

if not inserted:
    clean_lines.append(new_script)

template_path.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")

print("OK: mantido somente additional_fields_compact_layout_v1.js.")
