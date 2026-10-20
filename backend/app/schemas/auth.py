"""Pydantic-схемы для авторизации администраторов."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminRegister(BaseModel):
    """Регистрация администратора."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = None


class AdminLogin(BaseModel):
    """Вход администратора."""
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    """Ответ: данные администратора."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Ответ: JWT-токен."""
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut