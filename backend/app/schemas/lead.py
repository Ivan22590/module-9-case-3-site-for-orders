"""Pydantic-схемы для заявок (leads) и поведения (lead_behavior)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BehaviorData(BaseModel):
    """Поведение пользователя на странице (собирается фронтом)."""
    time_on_page_seconds: int = 0
    clicks_count: int = 0
    cursor_idle_seconds: int = 0
    cursor_hover_stalls: int = 0
    returns_count: int = 0
    scroll_depth_percent: int = 0
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    timezone: Optional[str] = None
    cursor_positions: Optional[str] = None  # JSON-строка [[x,y], ...]
    platform: Optional[str] = None
    touch_points: Optional[int] = None
    device_memory: Optional[float] = None
    hardware_concurrency: Optional[int] = None
    languages: Optional[str] = None
    color_depth: Optional[int] = None
    pixel_ratio: Optional[float] = None


class LeadData(BaseModel):
    """Данные заявки из формы."""
    contact: str = Field(..., min_length=1)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    business_info: Optional[str] = None
    niche: Optional[str] = None
    company_size: Optional[str] = None
    role: Optional[str] = None
    task_type: Optional[str] = None
    product_interest: Optional[str] = None
    budget: Optional[str] = None
    deadline: Optional[str] = None
    contact_channel: Optional[str] = None
    contact_time: Optional[str] = None
    comment: Optional[str] = None


class LeadPackage(BaseModel):
    """Единый пакет от фронта: заявка + поведение."""
    lead: LeadData
    behavior: BehaviorData = Field(default_factory=BehaviorData)


class BehaviorOut(BaseModel):
    """Ответ: запись поведения (PK = lead_id)."""
    model_config = ConfigDict(from_attributes=True)

    lead_id: int
    time_on_page_seconds: int
    clicks_count: int
    cursor_idle_seconds: int
    cursor_hover_stalls: int
    returns_count: int
    scroll_depth_percent: int
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    tz_name: Optional[str] = Field(None, serialization_alias="timezone")
    cursor_positions: Optional[str] = None
    recorded_at: datetime


class LeadOut(BaseModel):
    """Ответ: заявка с поведением и анализом."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    business_info: Optional[str] = None
    niche: Optional[str] = None
    company_size: Optional[str] = None
    role: Optional[str] = None
    task_type: Optional[str] = None
    product_interest: Optional[str] = None
    budget: Optional[str] = None
    deadline: Optional[str] = None
    contact_channel: Optional[str] = None
    contact_time: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    behavior: Optional[BehaviorOut] = None
    analysis: Optional[dict] = None  # AI-анализ (не из БД, а вычисляется)