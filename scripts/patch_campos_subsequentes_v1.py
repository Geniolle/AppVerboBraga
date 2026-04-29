from pathlib import Path

ROOT = Path.cwd()

def read_file(path):
    return path.read_text(encoding="utf-8")

def write_file(path, content):
    path.write_text(content, encoding="utf-8")

def replace_or_insert_after(content, old_line, new_line, anchor_line):
    if old_line in content:
        content = content.replace(old_line, new_line)
    elif new_line not in content:
        content = content.replace(anchor_line, anchor_line + "\n" + new_line)
    return content

admin_tabs_path = ROOT / "appverbo" / "process_settings" / "admin_tabs.py"
admin_tabs_content = read_file(admin_tabs_path)

admin_tabs_content = replace_or_insert_after(
    admin_tabs_content,
    '    {"key": "subsequentes", "label": "Subsequentes"},',
    '    {"key": "campos_subsequentes", "label": "Campos Subsequentes"},',
    '    {"key": "lista", "label": "Listas"},'
)

write_file(admin_tabs_path, admin_tabs_content)

admin_tabs_js_path = ROOT / "static" / "js" / "process_settings" / "adminProcessTabs_v1.js"
admin_tabs_js_content = read_file(admin_tabs_js_path)

admin_tabs_js_content = replace_or_insert_after(
    admin_tabs_js_content,
    '    { key: "subsequentes", label: "Subsequentes" }',
    '    { key: "campos_subsequentes", label: "Campos Subsequentes" },',
    '    { key: "lista", label: "Listas" },'
)

admin_tabs_js_content = replace_or_insert_after(
    admin_tabs_js_content,
    '    { key: "subsequentes", label: "Subsequentes" },',
    '    { key: "campos_subsequentes", label: "Campos Subsequentes" },',
    '    { key: "lista", label: "Listas" },'
)

write_file(admin_tabs_js_path, admin_tabs_js_content)

new_user_js_path = ROOT / "static" / "js" / "new_user.js"
new_user_js_content = read_file(new_user_js_path)

if '"campos-subsequentes": "campos-subsequentes"' not in new_user_js_content:
    new_user_js_content = new_user_js_content.replace(
        '    "adicionais": "campos-adicionais"',
        '    "adicionais": "campos-adicionais",\n'
        '    "lista": "lista",\n'
        '    "listas": "lista",\n'
        '    "campos-subsequentes": "campos-subsequentes",\n'
        '    "campos_subsequentes": "campos-subsequentes",\n'
        '    "subsequentes": "campos-subsequentes",\n'
        '    "subsequent": "campos-subsequentes",\n'
        '    "subsequent-rules": "campos-subsequentes"'
    )

write_file(new_user_js_path, new_user_js_content)

subsequent_js_path = ROOT / "static" / "js" / "modules" / "subsequent_rules_v1.js"

if subsequent_js_path.exists():
    subsequent_js_content = read_file(subsequent_js_path)

    subsequent_js_content = subsequent_js_content.replace(
        'return settingsTab === "subsequentes";',
        'return settingsTab === "subsequentes" || settingsTab === "campos_subsequentes";'
    )

    subsequent_js_content = subsequent_js_content.replace(
        'settings_tab="subsequentes"',
        'settings_tab="campos_subsequentes"'
    )

    subsequent_js_content = subsequent_js_content.replace(
        'settings_tab: "subsequentes"',
        'settings_tab: "campos_subsequentes"'
    )

    write_file(subsequent_js_path, subsequent_js_content)

settings_handlers_path = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
settings_handlers_content = read_file(settings_handlers_path)

settings_handlers_content = settings_handlers_content.replace(
    'settings_tab="subsequentes"',
    'settings_tab="campos_subsequentes"'
)

write_file(settings_handlers_path, settings_handlers_content)

print("Key campos_subsequentes e label Campos Subsequentes aplicadas com sucesso.")
