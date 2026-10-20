"""
Точка входа FastAPI-приложения.

Здесь собираются все роуты, инициализируются таблицы БД.
Backend доступен только внутри машины (через nginx /api/...).
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy import inspect, text

from .core.db import Base, engine
# Импортируем модели, чтобы create_all увидел все таблицы
from .models import lead as _lead_models  # noqa: F401
from .models import service as _service_models  # noqa: F401
from .routes import admin, leads, public


def _migrate_legacy_leads() -> None:
    """Миграция MVP-таблицы leads (v1) → leads_legacy_v1.

    Старая схема (metrics/tech JSONB) несовместима с новой —
    переименовываем старую таблицу, новая создаётся через create_all.
    """
    insp = inspect(engine)
    if "leads" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("leads")}
    if "first_name" not in cols:  # это старая v1-таблица
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE leads RENAME TO leads_legacy_v1"
            ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте: миграция старой таблицы + создание недостающих
    _migrate_legacy_leads()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    root_path="/api",
    title="Orders Backend",
    description=(
        "Приватный backend сайта заявок.\n\n"
        "Доступен только через nginx: `http://<server>:8088/api/...`\n\n"
        "- **public** — healthcheck и список услуг для фронта\n"
        "- **leads** — приём заявок единым пакетом (данные + поведение)\n"
        "- **admin** — управление услугами и диапазонами цен"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Единый роутер приложения: сюда подключаются все модули
api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(leads.router)
api_router.include_router(admin.router)

app.include_router(api_router)