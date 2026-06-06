import os

file_path = 'templates/new_user.html'
partial_path = 'templates/partials/admin_menu_edit_card.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Locate the block start: '{% if settings_edit_data and admin_tab == "menu" %}'
start_idx = None
for idx, line in enumerate(lines):
    if '{% if settings_edit_data and admin_tab == "menu" %}' in line:
        start_idx = idx
        break

if start_idx is None:
    raise ValueError("Start of edit block not found")

# Track depth to find the correct matching endif
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

print(f"Extracting block from line {start_idx+1} to {end_idx+1}")

# Extract block lines
edit_block = lines[start_idx : end_idx+1]

# Save to partial file
os.makedirs(os.path.dirname(partial_path), exist_ok=True)
with open(partial_path, 'w', encoding='utf-8') as f:
    f.write("".join(edit_block))

# Replace block in original file with {% include %}
replace_line = '        {% include "partials/admin_menu_edit_card.html" %}\n'
del lines[start_idx : end_idx+1]
lines.insert(start_idx, replace_line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write("".join(lines))

print("Extraction completed successfully!")
