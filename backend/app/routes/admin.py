"""
Админ-роуты: CRUD услуг.

Через эти эндпоинты админ задаёт услуги и диапазоны цен,
по которым фронтенд динамически строит форму заявки.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import service as svc_crud
from ..schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/admin/services", tags=["admin"])


@router.post("", response_model=ServiceOut, status_code=201)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    """Создать услугу (например: Полировка, 5000–15000)."""
    if payload.price_min > payload.price_max:
        raise HTTPException(422, "price_min не может превышать price_max")
    try:
        return svc_crud.create_service(db, **payload.model_dump())
    except Exception as exc:  # noqa: BLE001
        # UNIQUE-конфликт по name
        raise HTTPException(409, f"Услуга уже существует: {exc}") from exc


@router.get("", response_model=list[ServiceOut])
def list_all_services(include_inactive: bool = False,
                      db: Session = Depends(get_db)):
    """Список всех услуг (include_inactive=true — и отключённые)."""
    return svc_crud.list_services(db, active_only=not include_inactive)


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Услуга по ID."""
    svc = svc_crud.get_service(db, service_id)
    if svc is None:
        raise HTTPException(404, "Service not found")
    return svc


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(service_id: int, payload: ServiceUpdate,
                   db: Session = Depends(get_db)):
    """Частичное обновление услуги."""
    svc = svc_crud.update_service(db, service_id, **payload.model_dump())
    if svc is None:
        raise HTTPException(404, "Service not found")
    return svc


@router.delete("/{service_id}", status_code=204)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Удалить услугу."""
    if not svc_crud.delete_service(db, service_id):
        raise HTTPException(404, "Service not found")