import re
import os

filepath = "/app/static/js/modules/process_subprocess_standards_v1.js"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Split ADMINISTRATIVO_SUBPROCESS_TABS_V1
admin_tabs_re = re.search(r'const ADMINISTRATIVO_SUBPROCESS_TABS_V1 = Object\.freeze\(\[([\s\S]*?)\]\);', content)
admin_tabs_content = admin_tabs_re.group(1)

# We want to remove sessoes and menu from ADMINISTRATIVO, and create SESSOES_SUBPROCESS_TABS_V1
sessoes_menu_pattern = r'(\{\s*key:\s*"sessoes"[\s\S]*?\},?\s*\{\s*key:\s*"menu"[\s\S]*?\}(?:,)?\s*)'
match = re.search(sessoes_menu_pattern, admin_tabs_content)
if match:
    sessoes_menu_tabs = match.group(1).rstrip(", \n")
    new_admin_tabs = admin_tabs_content.replace(match.group(1), "")
    
    new_sessoes_def = f"""
  const SESSOES_SUBPROCESS_TABS_V1 = Object.freeze([
    {sessoes_menu_tabs}
  ]);
"""
    content = content.replace(admin_tabs_re.group(0), f"""const ADMINISTRATIVO_SUBPROCESS_TABS_V1 = Object.freeze([{new_admin_tabs}]);\n{new_sessoes_def}""")

# 2. Update SUBPROCESS_TAB_LIBRARY_V1
content = content.replace(
"""  const SUBPROCESS_TAB_LIBRARY_V1 = Object.freeze({
    administrativo: ADMINISTRATIVO_SUBPROCESS_TABS_V1
  });""",
"""  const SUBPROCESS_TAB_LIBRARY_V1 = Object.freeze({
    administrativo: ADMINISTRATIVO_SUBPROCESS_TABS_V1,
    sessoes: SESSOES_SUBPROCESS_TABS_V1
  });"""
)

# 3. Update MENU_TARGET_ALIAS_LIBRARY_V1
content = content.replace(
"""  const MENU_TARGET_ALIAS_LIBRARY_V1 = Object.freeze({
    administrativo: Object.freeze({
      "#admin-menu-form": "#admin-menu-card",
      "#admin-menu-create-card": "#admin-menu-card"
    })
  });""",
"""  const MENU_TARGET_ALIAS_LIBRARY_V1 = Object.freeze({
    administrativo: Object.freeze({}),
    sessoes: Object.freeze({
      "#admin-menu-form": "#admin-menu-card",
      "#admin-menu-create-card": "#admin-menu-card"
    })
  });"""
)

# 4. Update MENU_SCOPED_CARD_GROUP_LIBRARY_V1
menu_group_pattern = r'(\s*Object\.freeze\(\{\s*key:\s*"menu"[\s\S]*?\}\)(?:,)?\s*)'
match_menu_group = re.search(menu_group_pattern, content)
if match_menu_group:
    menu_group_content = match_menu_group.group(1)
    content = content.replace(menu_group_content, "")
    
    # insert sessoes group
    content = content.replace(
"""  const MENU_SCOPED_CARD_GROUP_LIBRARY_V1 = Object.freeze({
    administrativo: Object.freeze([""",
f"""  const MENU_SCOPED_CARD_GROUP_LIBRARY_V1 = Object.freeze({{
    sessoes: Object.freeze([{menu_group_content.rstrip(", ")}]),
    administrativo: Object.freeze(["""
    )

# 5. Update HASH_TARGET_MENU_LIBRARY_V1
for old, new in [
    ('"#admin-menu-card-create": "administrativo"', '"#admin-menu-card-create": "sessoes"'),
    ('"#admin-menu-card": "administrativo"', '"#admin-menu-card": "sessoes"'),
    ('"#admin-menu-card-inactive": "administrativo"', '"#admin-menu-card-inactive": "sessoes"'),
    ('"#admin-sidebar-sections-card": "administrativo"', '"#admin-sidebar-sections-card": "sessoes"'),
    ('"#settings-menu-edit-card": "administrativo"', '"#settings-menu-edit-card": "sessoes"')
]:
    content = content.replace(old, new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("process_subprocess_standards_v1.js updated!")
