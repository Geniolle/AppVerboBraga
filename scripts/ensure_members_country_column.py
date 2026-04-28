from __future__ import annotations

from sqlalchemy import inspect, text

from appverbo.db.session import engine


# ###################################################################################
# (1) VALIDAR / CRIAR COLUNA members.country
# ###################################################################################

with engine.begin() as connection:
    inspector = inspect(connection)
    columns = {
        column["name"]
        for column in inspector.get_columns("members")
    }

    if "country" not in columns:
        connection.execute(text("ALTER TABLE members ADD COLUMN country VARCHAR(120)"))
        print("OK: coluna members.country criada.")
    else:
        print("INFO: coluna members.country ja existe.")
