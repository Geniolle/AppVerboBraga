from appverbo.db.session import SessionLocal
from appverbo.admin_subprocesses.repositories.definition_repository import DefinitionAdminRepository
from appverbo.admin_subprocesses.definicoes.configuracao import DEFINICOES_CONFIG

def main():
    repo = DefinitionAdminRepository(DEFINICOES_CONFIG)
    with SessionLocal() as session:
        rows = repo.list_rows(session)
        print(f"Total rows retrieved: {len(rows)}")
        print("First 15 rows with their internal numbers and scope labels:")
        for idx, row in enumerate(rows[:15]):
            print(f"[{idx+1}] Parameter: {row.get('parameter_name')} | Entity ID: {row.get('entity_id')} | Nº Entidade: {row.get('entity_internal_number')} | Entity Scope Label: {row.get('entity_scope_label')}")

if __name__ == '__main__':
    main()
