"""
Админ-роуты: CRUD услуг, управление заявками, статистика, heatmap.

Все эндпоинты защищены JWT — заголовок Authorization: Bearer <token>.
Токен выдаётся после входа через POST /api/auth/login.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.scoring import analyze_lead
from ..core.security import decode_access_token
from ..models import service as svc_crud
from ..models import lead as lead_crud
from ..models.lead import LeadBehavior
from ..schemas.lead import LeadOut
from ..schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

# ────────────────────────────────────────────────────────────
# Зависимость: проверка JWT из заголовка Authorization
# ────────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Извлекает токен из заголовка Authorization: Bearer <token>.

    Проверяет подпись и срок действия, возвращает админа из БД.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Не передан токен авторизации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = decode_access_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Недействительный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from ..models.admin import get_admin_by_email
    admin = get_admin_by_email(db, email)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return admin


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


# ────────────────────────────────────────────────────────────
# Заявки с AI-анализом
# (объявлены раньше /{service_id}, иначе FastAPI перехватит
#  путь /admin/leads шаблоном /admin/{service_id})
# ────────────────────────────────────────────────────────────
def _build_lead_out(lead) -> LeadOut:
    """LeadOut + вычисляемый AI-анализ."""
    b = lead.behavior
    analysis = analyze_lead(
        niche=lead.niche,
        company_size=lead.company_size,
        role=lead.role,
        task_type=lead.task_type,
        product_interest=lead.product_interest,
        budget=lead.budget,
        deadline=lead.deadline,
        time_on_page=b.time_on_page_seconds if b else 0,
        clicks=b.clicks_count if b else 0,
        returns=b.returns_count if b else 0,
    )
    out = LeadOut.model_validate(lead)
    out.analysis = analysis
    return out


@router.get("/leads", response_model=list[LeadOut])
def list_leads_with_analysis(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Список заявок с AI-анализом, отсортированный по score (горячие сверху)."""
    leads = lead_crud.list_leads(db, skip=skip, limit=limit)
    result = [_build_lead_out(lead) for lead in leads]
    result.sort(key=lambda x: x.analysis["score"] if x.analysis else 0, reverse=True)
    return result


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead_with_analysis(lead_id: int, db: Session = Depends(get_db)):
    """Заявка по ID с анализом."""
    lead = lead_crud.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(404, "Lead not found")
    return _build_lead_out(lead)


@router.delete("/leads/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Удалить заявку (поведение удаляется по CASCADE)."""
    if not lead_crud.delete_lead(db, lead_id):
        raise HTTPException(404, "Lead not found")


# ────────────────────────────────────────────────────────────
# Статистика и Heatmap
# ────────────────────────────────────────────────────────────
@router.get("/stats/overview")
def stats_overview(db: Session = Depends(get_db)):
    """Общая статистика: заявки, услуги, avg/max time за день/неделю/месяц."""
    now = datetime.now(timezone.utc)
    total_leads = db.query(func.count(lead_crud.Lead.id)).scalar() or 0
    total_services = db.query(func.count(svc_crud.Service.id)).scalar() or 0
    total_behaviors = db.query(func.count()).select_from(LeadBehavior).scalar() or 0

    def _agg(days: int) -> dict:
        def _inner(func_agg):
            return db.query(func_agg(
                LeadBehavior.time_on_page_seconds
            )).filter(
                LeadBehavior.recorded_at >= now - timedelta(days=days)
            ).scalar() or 0
        return {
            "avg": int(_inner(func.avg)),
            "max": int(_inner(func.max)),
        }

    return {
        "total_leads": total_leads,
        "total_services": total_services,
        "total_behaviors": total_behaviors,
        "avg_time": {
            "day": _agg(1)["avg"],
            "week": _agg(7)["avg"],
            "month": _agg(30)["avg"],
        },
        "max_time": {
            "day": _agg(1)["max"],
            "week": _agg(7)["max"],
            "month": _agg(30)["max"],
        },
    }


@router.get("/stats/heatmap")
def heatmap_data(db: Session = Depends(get_db)):
    """Кластеризованные координаты курсора для heatmap.

    Фронт сохраняет позиции курсора в процентах (0–100), поэтому
    кластеризация идёт сеткой 5%.
    Возвращает [[x, y, count], ...].
    """
    rows = db.query(
        LeadBehavior.cursor_positions
    ).filter(
        LeadBehavior.cursor_positions.isnot(None),
        LeadBehavior.cursor_positions != "",
    ).all()

    points = []
    for (pos,) in rows:
        if not pos:
            continue
        try:
            coords = json.loads(pos)
            if isinstance(coords, list):
                for p in coords:
                    if isinstance(p, (list, tuple)) and len(p) == 2:
                        points.append([float(p[0]), float(p[1])])
        except (json.JSONDecodeError, ValueError):
            continue

    # Кластеризация сеткой 5% (координаты 0–100 от фронтенда)
    clusters: dict[tuple[int, int], int] = {}
    for x, y in points:
        key = (int(round(x / 5) * 5), int(round(y / 5) * 5))
        clusters[key] = clusters.get(key, 0) + 1

    result = [{"x": k[0], "y": k[1], "count": v} for k, v in clusters.items()]
    result.sort(key=lambda p: p["count"], reverse=True)
    return {"points": result}


# ────────────────────────────────────────────────────────────
# CRUD услуг
# ────────────────────────────────────────────────────────────
@router.post("", response_model=ServiceOut, status_code=201)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    """Создать услугу."""
    if payload.price_min > payload.price_max:
        raise HTTPException(422, "price_min не может превышать price_max")
    try:
        return svc_crud.create_service(db, **payload.model_dump())
    except Exception as exc:
        raise HTTPException(409, f"Услуга уже существует: {exc}") from exc


@router.get("", response_model=list[ServiceOut])
def list_all_services(include_inactive: bool = False,
                      db: Session = Depends(get_db)):
    """Список всех услуг."""
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
