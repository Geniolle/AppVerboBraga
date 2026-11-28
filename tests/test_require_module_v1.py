"""Etapa 6: rota de modulo pago devolve 403 pelo backend quando a entidade da sessao nao o tem ativo."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

import appgenesis.web.dependencies as dependencies_module
from appgenesis.models import Base, Entity, Member, MemberEntity, MemberEntityStatus, User
from appgenesis.models.modules import AppModule, EntityModuleEntitlement
from appgenesis.web.dependencies import require_module


def _factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Entity.__table__,
            Member.__table__,
            MemberEntity.__table__,
            User.__table__,
            AppModule.__table__,
            EntityModuleEntitlement.__table__,
        ],
    )
    return sessionmaker(bind=engine, future=True)


def _seed(factory):
    with factory() as session:
        a = Entity(entity_number=1001, name="A", is_active=True, profile_scope="legado")
        b = Entity(entity_number=1002, name="B", is_active=True, profile_scope="legado")
        session.add_all([a, b])
        session.flush()
        users = {}
        for email, entity in (("a@t.test", a), ("b@t.test", b)):
            member = Member(full_name=email, primary_phone="900", email=email)
            session.add(member)
            session.flush()
            session.add(MemberEntity(member_id=member.id, entity_id=entity.id, status=MemberEntityStatus.ACTIVE.value))
            user = User(member_id=member.id, login_email=email, password_hash="x", account_status="active")
            session.add(user)
            session.flush()
            users[email] = user.id
        session.add_all(
            [
                AppModule(module_key="home", module_name="Home", is_core=True, is_active=True),
                AppModule(module_key="tesouraria", module_name="Tesouraria", is_core=False, is_active=True),
                AppModule(module_key="eventos", module_name="Eventos", is_core=False, is_active=True),
            ]
        )
        session.flush()
        expired = datetime.now(timezone.utc) - timedelta(days=1)
        session.add_all(
            [
                # B tem tesouraria ativa; A nao tem. A tem eventos, mas expirado.
                EntityModuleEntitlement(entity_id=b.id, module_key="tesouraria", status="active"),
                EntityModuleEntitlement(entity_id=a.id, module_key="tesouraria", status="inactive"),
                EntityModuleEntitlement(entity_id=a.id, module_key="eventos", status="active", expires_at=expired),
            ]
        )
        session.commit()
        return a.id, b.id, users


def _client(factory):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.post("/test-login")
    def test_login(request: Request, user_id: int, entity_id: int):
        request.session["user_id"] = user_id
        request.session["entity_id"] = entity_id  # pode ser "forjado": get_current_user revalida
        return {}

    for key in ("tesouraria", "eventos", "home", "inexistente"):
        app.add_api_route(f"/{key}", lambda: {"ok": True}, dependencies=[Depends(require_module(key))])
    return TestClient(app)


def test_module_routes_by_entity_and_status():
    factory = _factory()
    a_id, b_id, users = _seed(factory)
    with patch.object(dependencies_module, "SessionLocal", factory):
        client = _client(factory)
        assert client.get("/tesouraria").status_code == 401  # sem login

        client.post("/test-login", params={"user_id": users["b@t.test"], "entity_id": b_id})
        assert client.get("/tesouraria").status_code == 200  # B com o modulo ativo
        assert client.get("/eventos").status_code == 403  # B sem entitlement
        assert client.get("/home").status_code == 200  # modulo core
        assert client.get("/inexistente").status_code == 403  # modulo nao registado

        client.post("/test-login", params={"user_id": users["a@t.test"], "entity_id": a_id})
        assert client.get("/tesouraria").status_code == 403  # A com entitlement inativo
        response = client.get("/eventos")
        assert response.status_code == 403 and "expirou" in response.json()["detail"]


def test_user_cannot_borrow_module_from_another_entity():
    factory = _factory()
    _a_id, b_id, users = _seed(factory)
    with patch.object(dependencies_module, "SessionLocal", factory):
        client = _client(factory)
        # Utilizador so de A forca entity_id=B (que tem tesouraria): a sessao volta a A e recusa.
        client.post("/test-login", params={"user_id": users["a@t.test"], "entity_id": b_id})
        assert client.get("/tesouraria").status_code == 403
