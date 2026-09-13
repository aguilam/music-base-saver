from __future__ import annotations

from sqlalchemy import func
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
    select,
)

from core.db.models import UserORM
from core.services.server_service import delete_orphans


def admin_create(session: Session):
    statement = select(func.count()).select_from(UserORM)
    users_count = session.exec(statement).one()
    if users_count < 1:
        admin = UserORM(
            username="admin",
            password="admin",
            email="admin@mail.com",
            is_admin=True,
        )
        session.add(admin)


class _DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)
        with self.get_session() as session, session.begin():
            admin_create(session)
            delete_orphans(session)

    def get_session(self) -> Session:
        return Session(self.engine)


DBManager = _DBManager()
