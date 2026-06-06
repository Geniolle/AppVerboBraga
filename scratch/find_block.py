with open('templates/new_user.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = None
for idx, line in enumerate(lines):
    if 'settings_edit_data and admin_tab == "menu"' in line:
        start_line = idx
        break

if start_line is not None:
    depth = 0
    for idx in range(start_line, len(lines)):
        line = lines[idx]
        # Count only if it is a block-level if/endif
        # we can search for {% if and {% endif
        # Simple stack tracking:
        if '{% if' in line and not '{% endif %}' in line:
            depth += 1
        elif '{% endif %}' in line and not '{% if' in line:
            depth -= 1
            if depth == 0:
                print(f'Start: {start_line+1}, End: {idx+1}')
                break
        elif '{% if' in line and '{% endif %}' in line:
            # both on the same line, does not change depth
            pass
