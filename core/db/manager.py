from __future__ import annotations
from sqlmodel import (
    SQLModel,
    create_engine,
    Session,
    select,
)
from sqlalchemy import func
from core.db.models import UserORM


def admin_create(engine):
    with Session(engine) as session:
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
            session.commit()


class _DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)
        admin_create(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)


DBManager = _DBManager()
