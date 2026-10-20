"""Модель администратора и CRUD-операции для него."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..core.db import Base


class Admin(Base):
    """Администратор системы."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ──────────────────────────────────────────────────────── CRUD
    def __repr__(self):
        return f"<Admin {self.email}>"


def create_admin(db: Session, *, email: str, password: str,
                 full_name: str | None = None) -> Admin:
    """Создать администратора с захешированным паролем."""
    from ..core.security import hash_password
    admin = Admin(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def get_admin_by_email(db: Session, email: str) -> Admin | None:
    """Получить админа по email."""
    return db.query(Admin).filter(Admin.email == email).first()


def get_admin_by_id(db: Session, admin_id: int) -> Admin | None:
    """Получить админа по ID."""
    return db.get(Admin, admin_id)


def list_admins(db: Session, *, skip: int = 0, limit: int = 100) -> list[Admin]:
    """Список администраторов."""
    return db.query(Admin).offset(skip).limit(limit).all()


def update_admin(db: Session, admin_id: int, **fields) -> Admin | None:
    """Частичное обновление админа."""
    admin = db.get(Admin, admin_id)
    if admin is None:
        return None
    for key, value in fields.items():
        if value is not None and hasattr(admin, key):
            setattr(admin, key, value)
    db.commit()
    db.refresh(admin)
    return admin


def delete_admin(db: Session, admin_id: int) -> bool:
    """Удалить админа."""
    admin = db.get(Admin, admin_id)
    if admin is None:
        return False
    db.delete(admin)
    db.commit()
    return True


def admin_exists(db: Session) -> bool:
    """Проверить, есть ли хотя бы один админ."""
    return db.query(Admin).filter(Admin.is_active.is_(True)).first() is not None