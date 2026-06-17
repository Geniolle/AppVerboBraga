"""
Query para consultar dados de Perfil de Autorização
Tabela: process_view_authorization_rules
"""

from sqlalchemy import text

from appverbo.core import SessionLocal


def query_all_authorization_profiles():
    """Lista todos os perfis de autorização criados"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print("(1) TODOS OS PERFIS DE AUTORIZAÇÃO")
        print("=" * 100)

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
            ORDER BY created_at DESC
        """)
        ).fetchall()

        if not rows:
            print("❌ Nenhum perfil de autorização encontrado")
            return

        print(f"\n✅ Total: {len(rows)} registos\n")
        for row in rows:
            print(f"ID: {row.id}")
            print(f"  Entidade ID: {row.entity_id}")
            print(f"  Perfil: {row.profile_name}")
            print(f"  Processo: {row.process_label}")
            print(f"  Subprocesso: {row.subprocess_label}")
            print(f"  Departamento: {row.department_name}")
            print(f"  Status: {row.status}")
            print(f"  Escopo: {row.visibility_scope_mode}")
            print(f"  Criado em: {row.created_at}")
            print(f"  Criado por: {row.created_by_user_id}")
            print()


def query_by_profile_name(profile_name: str):
    """Consulta perfis por nome específico"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print(f"(2) PERFIS POR NOME: '{profile_name}'")
        print("=" * 100)

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
                created_at
            FROM process_view_authorization_rules
            WHERE LOWER(profile_name) = LOWER(:profile_name)
            ORDER BY created_at DESC
        """),
            {"profile_name": profile_name},
        ).fetchall()

        if not rows:
            print(f"❌ Nenhum perfil encontrado com nome '{profile_name}'")
            return

        print(f"\n✅ Total: {len(rows)} registos\n")
        for row in rows:
            print(f"ID: {row.id} | Perfil: {row.profile_name} | Processo: {row.process_label}")
            print(f"  Status: {row.status} | Escopo: {row.visibility_scope_mode}\n")


def query_by_entity_id(entity_id: int):
    """Consulta perfis por entidade"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print(f"(3) PERFIS POR ENTIDADE ID: {entity_id}")
        print("=" * 100)

        rows = session.execute(
            text("""
            SELECT
                id,
                profile_name,
                process_label,
                subprocess_label,
                department_name,
                status,
                visibility_scope_mode,
                created_at
            FROM process_view_authorization_rules
            WHERE entity_id = :entity_id
            ORDER BY profile_name, process_label
        """),
            {"entity_id": entity_id},
        ).fetchall()

        if not rows:
            print(f"❌ Nenhum perfil encontrado para entidade ID {entity_id}")
            return

        print(f"\n✅ Total: {len(rows)} registos\n")
        for row in rows:
            print(f"ID: {row.id} | Perfil: {row.profile_name} | Processo: {row.process_label}")
            print(f"  Subprocesso: {row.subprocess_label} | Departamento: {row.department_name}")
            print(f"  Status: {row.status}\n")


def query_by_status(status: str = "active"):
    """Consulta perfis por status"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print(f"(4) PERFIS POR STATUS: {status}")
        print("=" * 100)

        rows = session.execute(
            text("""
            SELECT
                id,
                entity_id,
                profile_name,
                process_label,
                subprocess_label,
                status,
                created_at
            FROM process_view_authorization_rules
            WHERE status = :status
            ORDER BY created_at DESC
        """),
            {"status": status},
        ).fetchall()

        if not rows:
            print(f"❌ Nenhum perfil encontrado com status '{status}'")
            return

        print(f"\n✅ Total: {len(rows)} registos\n")
        for row in rows:
            print(
                f"ID: {row.id} | Perfil: {row.profile_name} | Processo: {row.process_label} | Status: {row.status}\n"
            )


def query_statistics():
    """Estatísticas gerais"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print("(5) ESTATÍSTICAS")
        print("=" * 100 + "\n")

        # Total
        total = session.execute(
            text("SELECT COUNT(*) FROM process_view_authorization_rules")
        ).scalar()
        print(f"Total de registos: {total}")

        # Por status
        status_counts = session.execute(
            text("""
            SELECT status, COUNT(*) as total
            FROM process_view_authorization_rules
            GROUP BY status
        """)
        ).fetchall()
        print("\nPor status:")
        for row in status_counts:
            print(f"  {row.status}: {row.total}")

        # Por perfil (top 10)
        profile_counts = session.execute(
            text("""
            SELECT profile_name, COUNT(*) as total
            FROM process_view_authorization_rules
            GROUP BY profile_name
            ORDER BY total DESC
            LIMIT 10
        """)
        ).fetchall()
        print("\nPerfis mais utilizados (top 10):")
        for row in profile_counts:
            print(f"  {row.profile_name}: {row.total}")

        # Por visibilidade
        visibility = session.execute(
            text("""
            SELECT visibility_scope_mode, COUNT(*) as total
            FROM process_view_authorization_rules
            GROUP BY visibility_scope_mode
        """)
        ).fetchall()
        print("\nPor escopo de visibilidade:")
        for row in visibility:
            print(f"  {row.visibility_scope_mode}: {row.total}")


def query_table_structure():
    """Mostra a estrutura da tabela"""
    with SessionLocal() as session:
        print("\n" + "=" * 100)
        print("(6) ESTRUTURA DA TABELA: process_view_authorization_rules")
        print("=" * 100 + "\n")

        cols = session.execute(
            text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'process_view_authorization_rules'
            ORDER BY ordinal_position
        """)
        ).fetchall()

        print(f"{'Coluna':<30} {'Tipo':<20} {'Nullable':<10} {'Default':<30}")
        print("-" * 90)
        for col in cols:
            col_name = col.column_name or ""
            data_type = col.data_type or ""
            nullable = col.is_nullable or "NO"
            default = col.column_default or "-"
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default:<30}")


if __name__ == "__main__":
    print("\n" + "🔍 CONSULTAS - PERFIL DE AUTORIZAÇÃO 🔍")
    print("Tabela: process_view_authorization_rules\n")

    # Executar todas as queries
    query_all_authorization_profiles()
    query_statistics()
    query_table_structure()

    # Exemplos adicionais (descomente conforme necessário)
    # query_by_profile_name("Admin")
    # query_by_entity_id(1)
    # query_by_status("active")
