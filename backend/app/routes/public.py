"""
Публичные роуты: healthcheck и список услуг для фронтенда.

Доступны извне только через nginx (/api/...).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import service as svc_crud
from ..schemas.service import ServiceOut

router = APIRouter(tags=["public"])


@router.get("/health")
def health():
    """Проверка живости сервиса."""
    return {"status": "ok"}


@router.get("/services", response_model=list[ServiceOut])
def get_services(db: Session = Depends(get_db)):
    """Список активных услуг — фронт строит интерфейс по ним."""
    return svc_crud.list_services(db, active_only=True)