import re

content = open('templates/new_user.html', encoding='utf-8').read()

print('Cards with data-menu-scope="administrativo":')
matches = re.findall(r'<section id="([^"]+)"[^>]*data-menu-scope="administrativo"', content)
for m in matches: print(' -', m)

print('\nCards with data-menu-scope="administrativo,configuracao":')
matches = re.findall(r'<section id="([^"]+)"[^>]*data-menu-scope="administrativo,configuracao"', content)
for m in matches: print(' -', m)
