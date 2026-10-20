"""Pydantic-схемы для услуг (services)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    """Запрос: создание услуги."""
    name: str = Field(..., min_length=1, examples=["Полировка"])
    description: Optional[str] = Field(None, examples=["Полировка кузова"])
    price_min: int = Field(0, ge=0)
    price_max: int = Field(..., gt=0)


class ServiceUpdate(BaseModel):
    """Запрос: частичное обновление услуги."""
    name: Optional[str] = None
    description: Optional[str] = None
    price_min: Optional[int] = Field(None, ge=0)
    price_max: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ServiceOut(BaseModel):
    """Ответ: услуга."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    price_min: int
    price_max: int
    is_active: bool
    created_at: datetime