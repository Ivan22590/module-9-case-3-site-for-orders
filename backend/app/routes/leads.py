"""
Роуты заявок: создание единым пакетом (lead + behavior),
чтение и удаление.

POST /leads — вызывается фронтендом через nginx /api/leads.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import lead as lead_crud
from ..schemas.lead import LeadOut, LeadPackage

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(package: LeadPackage, db: Session = Depends(get_db)):
    """Создать заявку: данные формы + поведение (1:1) одной транзакцией."""
    lead = lead_crud.create_lead_with_behavior(
        db,
        **package.lead.model_dump(),
        behavior=package.behavior.model_dump(),
    )
    return lead


@router.get("", response_model=list[LeadOut])
def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Список заявок (новые первыми)."""
    return lead_crud.list_leads(db, skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Заявка по ID, включая поведение."""
    lead = lead_crud.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Удалить заявку (поведение — по CASCADE)."""
    if not lead_crud.delete_lead(db, lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")