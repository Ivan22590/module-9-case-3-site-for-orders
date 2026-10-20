"""
Backend-заглушка MVP: healthcheck и приём заявок.
Запись в PostgreSQL. Позже заменяется на реальный код.
"""
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://orders_user:orders@postgres:5432/orders_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицу заявок при старте
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                contact TEXT NOT NULL,
                business TEXT,
                budget TEXT,
                channel TEXT,
                comment TEXT,
                metrics JSONB DEFAULT '{}',
                tech JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """))
    yield


app = FastAPI(title="Orders Backend", lifespan=lifespan)


class LeadPayload(BaseModel):
    contact: str = Field(..., min_length=1)
    business: str | None = None
    budget: str | None = None
    channel: str | None = None
    comment: str | None = None
    metrics: dict = Field(default_factory=dict)
    tech: dict = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/leads")
def create_lead(lead: LeadPayload):
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO leads
                        (contact, business, budget, channel, comment, metrics, tech)
                    VALUES
                        (:contact, :business, :budget, :channel, :comment,
                         CAST(:metrics AS jsonb), CAST(:tech AS jsonb))
                """),
                {
                    "contact": lead.contact,
                    "business": lead.business,
                    "budget": lead.budget,
                    "channel": lead.channel,
                    "comment": lead.comment,
                    "metrics": json.dumps(lead.metrics, ensure_ascii=False),
                    "tech": json.dumps(lead.tech, ensure_ascii=False),
                },
            )
        return {"ok": True, "message": "Lead saved"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"DB error: {exc}") from exc