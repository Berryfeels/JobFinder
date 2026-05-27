from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_finder.config import load_config
from job_finder.db.models import Base


class DatabaseManager:
    def __init__(self, database_url: str | None = None):
        config = load_config()
        url = database_url or config.get("database", {}).get("url", "sqlite:///jobfinder.db")
        self.engine = create_engine(url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self) -> None:
        self.engine.dispose()


_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.init_db()
    return _db_manager


def get_session() -> Session:
    return get_db_manager().get_session()
