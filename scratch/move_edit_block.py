import os
import re

file_path = 'templates/new_user.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Find the edit block start
start_idx = None
for idx, line in enumerate(lines):
    if '{% if settings_edit_data and admin_tab == "menu" %}' in line:
        start_idx = idx
        break

if start_idx is None:
    raise ValueError("Start of edit block not found")

# 2. Track depth to find the correct matching endif
depth = 0
end_idx = None
for idx in range(start_idx, len(lines)):
    line = lines[idx]
    if '{% if' in line and not '{% endif %}' in line:
        depth += 1
    elif '{% endif %}' in line and not '{% if' in line:
        depth -= 1
        if depth == 0:
            end_idx = idx
            break

if end_idx is None:
    raise ValueError("Matching endif not found")

print(f"Edit block found from line {start_idx+1} to {end_idx+1}")

# 3. Extract the edit block
edit_block = lines[start_idx : end_idx+1]

# 4. Remove the edit block from lines
del lines[start_idx : end_idx+1]

# 5. Find the insert position: right before '<section id="admin-menu-card"'
insert_idx = None
for idx, line in enumerate(lines):
    if '<section id="admin-menu-card"' in line:
        insert_idx = idx
        break

if insert_idx is None:
    raise ValueError("Insertion target <section id=\"admin-menu-card\" not found")

print(f"Insertion target found at line {insert_idx+1}")

# 6. Insert the edit block at the new position
lines[insert_idx:insert_idx] = edit_block

# Reconstruct HTML string
html_content = "".join(lines)

# 7. Add data attributes to the 4 cards:
# - settings-menu-edit-card
# - admin-menu-card-create
# - admin-menu-card
# - admin-menu-card-inactive

# For admin-menu-card-create
create_target = r'(<section\s+id="admin-menu-card-create"\s+class="[^"]+")(\s*>|[^>]*>)'
def replace_create(match):
    prefix = match.group(1)
    rest = match.group(2)
    if 'data-admin-card-group' not in prefix and 'data-admin-card-group' not in rest:
        return prefix + ' data-admin-card-group="menu" data-admin-card-role="create"' + rest
    return match.group(0)
html_content = re.sub(create_target, replace_create, html_content)

# For settings-menu-edit-card
edit_target = r'(<section\s+id="settings-menu-edit-card"\s+class="[^"]+")(\s*>|[^>]*>)'
def replace_edit(match):
    prefix = match.group(1)
    rest = match.group(2)
    if 'data-admin-card-group' not in prefix and 'data-admin-card-group' not in rest:
        return prefix + ' data-admin-card-group="menu" data-admin-card-role="edit"' + rest
    return match.group(0)
html_content = re.sub(edit_target, replace_edit, html_content)

# For admin-menu-card
active_target = r'(<section\s+id="admin-menu-card"\s+class="[^"]+")(\s*>|[^>]*>)'
def replace_active(match):
    prefix = match.group(1)
    rest = match.group(2)
    if 'data-admin-card-group' not in prefix and 'data-admin-card-group' not in rest:
        return prefix + ' data-admin-card-group="menu" data-admin-card-role="active"' + rest
    return match.group(0)
html_content = re.sub(active_target, replace_active, html_content)

# For admin-menu-card-inactive
inactive_target = r'(<section\s+id="admin-menu-card-inactive"\s+class="[^"]+")(\s*>|[^>]*>)'
def replace_inactive(match):
    prefix = match.group(1)
    rest = match.group(2)
    if 'data-admin-card-group' not in prefix and 'data-admin-card-group' not in rest:
        return prefix + ' data-admin-card-group="menu" data-admin-card-role="inactive"' + rest
    return match.group(0)
html_content = re.sub(inactive_target, replace_inactive, html_content)

# 8. Save the modified file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Block moved and attributes updated successfully!")
