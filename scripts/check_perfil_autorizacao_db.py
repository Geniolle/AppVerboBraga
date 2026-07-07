import sys
sys.path.insert(0, '/app')
from appgenesis.db.session import SessionLocal
from sqlalchemy import text

s = SessionLocal()

# (1) ESTADO ATUAL sidebar_menu_settings para perfil_de_autorizacao
print('=== sidebar_menu_settings (perfil_de_autorizacao) ===')
rows = s.execute(text(
    "SELECT * FROM sidebar_menu_settings WHERE menu_key = 'perfil_de_autorizacao'"
)).fetchall()
for r in rows:
    print(dict(r._mapping))
if not rows:
    print('  (VAZIO - registos nao existem!)')

# (2) VER TODOS os registos da tabela
print('\n=== sidebar_menu_settings COMPLETO ===')
rows2 = s.execute(text(
    "SELECT id, entity_id, menu_key, menu_label, is_active, is_deleted FROM sidebar_menu_settings ORDER BY id"
)).fetchall()
for r in rows2:
    print(dict(r._mapping))

# (3) VERIFICAR sequence/max id
print('\n=== MAX ID ===')
max_id = s.execute(text("SELECT MAX(id) FROM sidebar_menu_settings")).scalar()
print(f'  Max ID: {max_id}')

# (4) VERIFICAR se ids 38 e 65 existem
print('\n=== IDs 38 e 65 existem? ===')
for check_id in [38, 65]:
    row = s.execute(text(f"SELECT id, menu_key FROM sidebar_menu_settings WHERE id = {check_id}")).fetchone()
    if row:
        print(f'  ID {check_id}: SIM - {dict(row._mapping)}')
    else:
        print(f'  ID {check_id}: NAO EXISTE')

s.close()
print('\nFim.')
