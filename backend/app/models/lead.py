"""
Модели и CRUD-операции для заявок (leads) и поведения (lead_behavior).

Связь 1:1: primary key таблицы lead_behavior одновременно является
внешним ключом на leads.id.

SQL для генерации таблиц:

    CREATE TABLE leads (
        id               SERIAL PRIMARY KEY,
        first_name       TEXT,
        last_name        TEXT,
        middle_name      TEXT,
        contact          TEXT NOT NULL,
        business_info    TEXT,
        niche            TEXT,
        company_size     TEXT,
        role             TEXT,
        task_type        TEXT,
        product_interest TEXT,
        budget           TEXT,
        deadline         TEXT,
        contact_channel  TEXT,
        contact_time     TEXT,
        comment          TEXT,
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE lead_behavior (
        lead_id               INTEGER PRIMARY KEY REFERENCES leads(id)
                              ON DELETE CASCADE,
        time_on_page_seconds  INTEGER NOT NULL DEFAULT 0,
        clicks_count          INTEGER NOT NULL DEFAULT 0,
        cursor_idle_seconds   INTEGER NOT NULL DEFAULT 0,
        cursor_hover_stalls   INTEGER NOT NULL DEFAULT 0,
        returns_count         INTEGER NOT NULL DEFAULT 0,
        scroll_depth_percent  INTEGER NOT NULL DEFAULT 0,
        user_agent            TEXT,
        referrer              TEXT,
        utm_source            TEXT,
        utm_medium            TEXT,
        utm_campaign          TEXT,
        screen_width          INTEGER,
        screen_height         INTEGER,
        timezone              TEXT,
        recorded_at           TIMESTAMPTZ NOT NULL DEFAULT now()
    );
"""
from datetime import datetime, timezone as dt_tz
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, Session, relationship

from ..core.db import Base


# ──────────────────────────────────────────────────────────── Lead
class Lead(Base):
    """Заявка клиента: контакты + информация о бизнесе."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Контакты: имя, фамилия, отчество, способ связи
    first_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[Optional[str]] = mapped_column(Text)
    middle_name: Mapped[Optional[str]] = mapped_column(Text)
    contact: Mapped[str] = mapped_column(Text, nullable=False)

    # Бизнес: ниша, размер компании, роль, тип задачи, продукт
    business_info: Mapped[Optional[str]] = mapped_column(Text)
    niche: Mapped[Optional[str]] = mapped_column(Text)
    company_size: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[Optional[str]] = mapped_column(Text)  # сотрудник / руководитель
    task_type: Mapped[Optional[str]] = mapped_column(Text)
    product_interest: Mapped[Optional[str]] = mapped_column(Text)

    # Бюджет (строка, на фронте — ползунок) и срок результата
    budget: Mapped[Optional[str]] = mapped_column(Text)
    deadline: Mapped[Optional[str]] = mapped_column(Text)

    # Предпочтительный способ и удобное время связи, комментарий
    contact_channel: Mapped[Optional[str]] = mapped_column(Text)
    contact_time: Mapped[Optional[str]] = mapped_column(Text)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(dt_tz.utc),
    )

    # Связь 1:1 с поведением
    behavior: Mapped[Optional["LeadBehavior"]] = relationship(
        back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────────────── LeadBehavior
class LeadBehavior(Base):
    """Поведение пользователя на странице заявки (1:1 с Lead).

    PK lead_id — одновременно FK на leads.id.
    """

    __tablename__ = "lead_behavior"

    lead_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("leads.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Метрики поведения
    time_on_page_seconds: Mapped[int] = mapped_column(Integer, default=0)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0)
    cursor_idle_seconds: Mapped[int] = mapped_column(Integer, default=0)
    cursor_hover_stalls: Mapped[int] = mapped_column(Integer, default=0)
    returns_count: Mapped[int] = mapped_column(Integer, default=0)
    scroll_depth_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Техническая информация
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    referrer: Mapped[Optional[str]] = mapped_column(Text)
    utm_source: Mapped[Optional[str]] = mapped_column(Text)
    utm_medium: Mapped[Optional[str]] = mapped_column(Text)
    utm_campaign: Mapped[Optional[str]] = mapped_column(Text)
    screen_width: Mapped[Optional[int]] = mapped_column(Integer)
    screen_height: Mapped[Optional[int]] = mapped_column(Integer)
    tz_name: Mapped[Optional[str]] = mapped_column("timezone", Text)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(dt_tz.utc),
    )

    lead: Mapped["Lead"] = relationship(back_populates="behavior")


# ──────────────────────────────────────────────────────── CRUD-операции
def create_lead_with_behavior(db: Session, *,
                              contact: str,
                              first_name: str | None = None,
                              last_name: str | None = None,
                              middle_name: str | None = None,
                              business_info: str | None = None,
                              niche: str | None = None,
                              company_size: str | None = None,
                              role: str | None = None,
                              task_type: str | None = None,
                              product_interest: str | None = None,
                              budget: str | None = None,
                              deadline: str | None = None,
                              contact_channel: str | None = None,
                              contact_time: str | None = None,
                              comment: str | None = None,
                              behavior: dict | None = None) -> Lead:
    """Создать заявку и связанную запись поведения (одна транзакция)."""
    lead = Lead(
        contact=contact,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        business_info=business_info,
        niche=niche,
        company_size=company_size,
        role=role,
        task_type=task_type,
        product_interest=product_interest,
        budget=budget,
        deadline=deadline,
        contact_channel=contact_channel,
        contact_time=contact_time,
        comment=comment,
    )
    db.add(lead)
    db.flush()  # генерируем lead.id до вставки behavior

    b = behavior or {}
    db.add(LeadBehavior(
        lead_id=lead.id,
        time_on_page_seconds=b.get("time_on_page_seconds", 0),
        clicks_count=b.get("clicks_count", 0),
        cursor_idle_seconds=b.get("cursor_idle_seconds", 0),
        cursor_hover_stalls=b.get("cursor_hover_stalls", 0),
        returns_count=b.get("returns_count", 0),
        scroll_depth_percent=b.get("scroll_depth_percent", 0),
        user_agent=b.get("user_agent"),
        referrer=b.get("referrer"),
        utm_source=b.get("utm_source"),
        utm_medium=b.get("utm_medium"),
        utm_campaign=b.get("utm_campaign"),
        screen_width=b.get("screen_width"),
        screen_height=b.get("screen_height"),
        tz_name=b.get("timezone"),
    ))
    db.commit()
    db.refresh(lead)
    return lead


def get_lead(db: Session, lead_id: int) -> Lead | None:
    """Получить заявку по ID (включая behavior через relationship)."""
    return db.get(Lead, lead_id)


def list_leads(db: Session, *, skip: int = 0, limit: int = 100) -> list[Lead]:
    """Список заявок (новые первыми)."""
    return db.query(Lead).order_by(Lead.id.desc()).offset(skip).limit(limit).all()


def update_lead(db: Session, lead_id: int, **fields) -> Lead | None:
    """Частичное обновление заявки."""
    lead = db.get(Lead, lead_id)
    if lead is None:
        return None
    for key, value in fields.items():
        if value is not None and hasattr(lead, key):
            setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, lead_id: int) -> bool:
    """Удалить заявку (поведение удалится по CASCADE)."""
    lead = db.get(Lead, lead_id)
    if lead is None:
        return False
    db.delete(lead)
    db.commit()
    return True