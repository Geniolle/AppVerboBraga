from sqlalchemy import text

from appverbo.core import SessionLocal

with SessionLocal() as session:
    result = session.execute(
        text("SELECT COUNT(*) as total FROM process_view_authorization_rules")
    ).first()
    count = result.total if result else 0

    print("\n📊 TABELA: process_view_authorization_rules")
    print("=" * 60)
    print(f"Total de registos: {count}")

    if count == 0:
        print("\n⚠️  A tabela está VAZIA")
        print("\nNenhum perfil de autorização foi criado ainda.")
        print("\nOs perfis serão gravados quando criar em:")
        print("  Menu > Definições > Perfil de autorização > Criar Perfil")
    else:
        print(f"\n✅ Mostrando todos os {count} registos:\n")
        rows = session.execute(
            text("""
            SELECT
                id,
                entity_id,
                profile_name,
                process_label,
                subprocess_label,
                department_name,
                status,
                visibility_scope_mode,
                created_at,
                created_by_user_id
            FROM process_view_authorization_rules
            ORDER BY id
        """)
        ).fetchall()

        for row in rows:
            print(f"ID: {row.id}")
            print(f"  Perfil: {row.profile_name}")
            print(f"  Processo: {row.process_label}")
            print(f"  Subprocesso: {row.subprocess_label}")
            print(f"  Departamento: {row.department_name}")
            print(f"  Status: {row.status}")
            print(f"  Escopo: {row.visibility_scope_mode}")
            print(f"  Entidade ID: {row.entity_id}")
            print(f"  Criado em: {row.created_at}")
            print(f"  Criado por: {row.created_by_user_id}")
            print()
