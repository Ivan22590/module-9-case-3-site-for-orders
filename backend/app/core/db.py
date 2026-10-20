"""
Драйвер базы данных PostgreSQL.

Строка подключения DATABASE_URL приходит из docker-compose.yml:
    postgresql+psycopg://<user>:<password>@postgres:5432/<db>
Наружу БД не опубликована — только внутренняя сеть backend_net.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://orders_user:orders@postgres:5432/orders_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый декларативный класс для всех моделей."""


def get_db():
    """Зависимость FastAPI: выдаёт сессию БД на время запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()