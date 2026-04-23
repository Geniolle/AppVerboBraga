from __future__ import annotations

import os
from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from membrisia import (
    Department,
    DepartmentMembership,
    DepartmentMembershipOperation,
    DepartmentMembershipRole,
    Entity,
    Member,
    MemberEntity,
    Profile,
    Role,
    User,
    UserProfile,
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///app.db")


def main() -> None:
    load_dotenv()
    engine = create_engine(get_database_url(), future=True)

    with Session(engine) as session:
        existing = session.execute(select(Entity).where(Entity.name == "Igreja Braga")).scalar_one_or_none()
        if existing is not None:
            print("Smoke test data already exists. No changes made.")
            return

        entity = Entity(name="Igreja Braga", acronym="IVB")
        member = Member(
            full_name="Joao Silva",
            primary_phone="+351910000000",
            email="joao.silva@example.com",
            member_status="active",
            is_collaborator=True,
            first_collaboration_date=date.today(),
        )
        member_entity = MemberEntity(
            member=member,
            entity=entity,
            status="active",
            entry_date=date.today(),
        )
        user = User(
            member=member,
            login_email=member.email,
            password_hash="not-a-real-password-hash",
            account_status="active",
        )

        profile = Profile(name="leader", description="Department leader")
        user_profile = UserProfile(user=user, profile=profile)

        department = Department(entity=entity, name="Louvor")
        role = Role(entity=entity, name="Musico")

        department_membership = DepartmentMembership(
            member_entity=member_entity,
            department=department,
            status="active",
            entry_date=date.today(),
        )
        department_membership_op = DepartmentMembershipOperation(
            department_membership=department_membership,
            internal_priority=1,
            eligible_for_auto_schedule=True,
            monthly_schedule_limit=4,
        )
        department_role = DepartmentMembershipRole(
            department_membership=department_membership,
            role=role,
            is_primary=True,
            is_active=True,
            included_in_schedule=True,
        )

        session.add_all(
            [
                entity,
                member,
                member_entity,
                user,
                profile,
                user_profile,
                department,
                role,
                department_membership,
                department_membership_op,
                department_role,
            ]
        )
        session.commit()

    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
