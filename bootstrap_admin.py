from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from membrisia import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)
from web_app import hash_password

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update an initial admin/login user."
    )
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--phone", required=True, help="Primary phone")
    parser.add_argument("--email", required=True, help="Login email")
    parser.add_argument("--password", required=True, help="Initial password")
    parser.add_argument("--entity", required=True, help="Entity name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
    engine = create_engine(database_url, future=True)

    email = args.email.strip().lower()
    with Session(engine) as session:
        entity = session.scalar(
            select(Entity).where(func.lower(Entity.name) == args.entity.strip().lower())
        )
        if entity is None:
            entity = Entity(name=args.entity.strip(), is_active=True)
            session.add(entity)
            session.flush()

        member = session.scalar(select(Member).where(func.lower(Member.email) == email))
        if member is None:
            member = Member(
                full_name=args.name.strip(),
                primary_phone=args.phone.strip(),
                email=email,
                member_status=MemberStatus.ACTIVE.value,
                is_collaborator=True,
            )
            session.add(member)
            session.flush()
        else:
            member.full_name = args.name.strip()
            member.primary_phone = args.phone.strip()
            member.member_status = MemberStatus.ACTIVE.value
            member.is_collaborator = True

        member_link = session.scalar(
            select(MemberEntity).where(
                MemberEntity.member_id == member.id,
                MemberEntity.entity_id == entity.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        )
        if member_link is None:
            member_link = MemberEntity(
                member_id=member.id,
                entity_id=entity.id,
                status=MemberEntityStatus.ACTIVE.value,
                entry_date=date.today(),
            )
            session.add(member_link)

        user = session.scalar(select(User).where(User.member_id == member.id))
        if user is None:
            user = User(
                member_id=member.id,
                login_email=email,
                password_hash=hash_password(args.password),
                account_status=UserAccountStatus.ACTIVE.value,
            )
            session.add(user)
        else:
            user.login_email = email
            user.password_hash = hash_password(args.password)
            user.account_status = UserAccountStatus.ACTIVE.value

        session.commit()
        print(f"Bootstrap user ready: {email}")


if __name__ == "__main__":
    main()
