"""
Модель и CRUD-операции для услуг (админ-данные).

Фронтенд динамически строит интерфейс по этому списку:
название услуги + диапазон цен (min / max).

SQL для генерации таблицы:

    CREATE TABLE services (
        id          SERIAL PRIMARY KEY,
        name        TEXT NOT NULL UNIQUE,
        description TEXT,
        price_min   INTEGER NOT NULL DEFAULT 0,
        price_max   INTEGER NOT NULL,
        is_active   BOOLEAN NOT NULL DEFAULT TRUE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..core.db import Base


class Service(Base):
    """Услуга, доступная для выбора клиентом."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_max: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# ──────────────────────────────────────────────────────── CRUD-операции
def create_service(db: Session, *, name: str, price_max: int,
                   description: str | None = None,
                   price_min: int = 0) -> Service:
    """Создать услугу."""
    svc = Service(name=name, description=description,
                  price_min=price_min, price_max=price_max)
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def get_service(db: Session, service_id: int) -> Service | None:
    """Получить услугу по ID."""
    return db.get(Service, service_id)


def list_services(db: Session, *, skip: int = 0, limit: int = 100,
                  active_only: bool = True) -> list[Service]:
    """Список услуг (по умолчанию — только активные)."""
    q = db.query(Service)
    if active_only:
        q = q.filter(Service.is_active.is_(True))
    return q.offset(skip).limit(limit).all()


def update_service(db: Session, service_id: int, *,
                   name: str | None = None,
                   description: str | None = None,
                   price_min: int | None = None,
                   price_max: int | None = None,
                   is_active: bool | None = None) -> Service | None:
    """Частичное обновление услуги. None-поля не меняются."""
    svc = db.get(Service, service_id)
    if svc is None:
        return None
    if name is not None:
        svc.name = name
    if description is not None:
        svc.description = description
    if price_min is not None:
        svc.price_min = price_min
    if price_max is not None:
        svc.price_max = price_max
    if is_active is not None:
        svc.is_active = is_active
    db.commit()
    db.refresh(svc)
    return svc


def delete_service(db: Session, service_id: int) -> bool:
    """Удалить услугу. True — если найдена и удалена."""
    svc = db.get(Service, service_id)
    if svc is None:
        return False
    db.delete(svc)
    db.commit()
    return True