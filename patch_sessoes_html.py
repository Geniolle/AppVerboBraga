import re

path = 'templates/new_user.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update data-menu-scope="administrativo" for the menu cards
# Since we know exactly which IDs are for "menu" tab:
for target_id in [
    'admin-menu-card-create',
    'admin-menu-card',
    'admin-menu-card-inactive',
    'settings-menu-edit-card',
    'admin-account-create-card',
    'admin-account-status-card',
    'admin-menu-inactive-card'
]:
    # Replace data-menu-scope="administrativo" -> data-menu-scope="sessoes"
    # Also replace data-menu-scope="administrativo,configuracao" -> data-menu-scope="sessoes,configuracao"
    pattern1 = rf'(<section id="{target_id}"[^>]*data-menu-scope=")administrativo(")'
    content = re.sub(pattern1, r'\g<1>sessoes\g<2>', content)
    
    pattern2 = rf'(<section id="{target_id}"[^>]*data-menu-scope=")administrativo,configuracao(")'
    content = re.sub(pattern2, r'\g<1>sessoes,configuracao\g<2>', content)

# 2. Update hrefs and redirect_menu inputs
# We want to change redirect_menu="administrativo" to "sessoes" but ONLY inside the menu-related blocks.
# Let's replace the global redirect_menu values inside the forms related to menu.
# Actually, the forms are: action="/settings/menu/save", action="/settings/menu/move", action="/settings/menu/edit", action="/settings/menu/delete", action="/settings/menu/create"
def replace_redirect_menu(match):
    block = match.group(0)
    block = block.replace('value="administrativo"', 'value="sessoes"')
    return block

content = re.sub(r'<form[^>]*action=\"/settings/menu/.*?</form>', replace_redirect_menu, content, flags=re.DOTALL)

# 3. Update hrefs pointing to /users/new?menu=administrativo&admin_tab=menu...
# We will just replace menu=administrativo with menu=sessoes inside the hrefs that contain admin_tab=menu
def replace_hrefs(match):
    href = match.group(0)
    href = href.replace('menu=administrativo', 'menu=sessoes')
    return href

content = re.sub(r'href=\"/users/new\?menu=administrativo&admin_tab=menu[^\"]*\"', replace_hrefs, content)

# 4. Same for admin_tab=sessoes and admin_tab=definicoes (if they exist)
content = re.sub(r'href=\"/users/new\?menu=administrativo&admin_tab=sessoes[^\"]*\"', replace_hrefs, content)
content = re.sub(r'href=\"/users/new\?menu=administrativo&admin_tab=definicoes[^\"]*\"', replace_hrefs, content)

# 5. One more specific spot: settings_edit_origin_menu and settings_edit_cancel_url inside admin_tab == "menu" block
content = content.replace('{% set settings_edit_origin_menu = "administrativo" %}', '{% set settings_edit_origin_menu = "sessoes" %}')
content = content.replace('{% set settings_edit_cancel_url = "/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card" %}', '{% set settings_edit_cancel_url = "/users/new?menu=sessoes&admin_tab=menu&target=admin-menu-card#admin-menu-card" %}')


with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch aplicado com sucesso!')
