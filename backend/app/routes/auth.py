"""
Роуты авторизации: регистрация (только если нет админов),
вход (login), статус (проверка токена), информация о текущем админе.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import create_access_token, decode_access_token, verify_password
from ..models import admin as admin_crud
from ..schemas.auth import AdminLogin, AdminOut, AdminRegister, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AdminOut, status_code=201)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """Регистрация первого администратора.

    Доступна ТОЛЬКО если в базе ещё нет активных админов.
    После создания первого админа endpoint автоматически блокируется.
    """
    if admin_crud.admin_exists(db):
        raise HTTPException(
            status_code=403,
            detail="Регистрация закрыта: уже есть администраторы",
        )
    if admin_crud.get_admin_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Админ с таким email уже существует")
    admin = admin_crud.create_admin(db, **payload.model_dump())
    return admin


@router.post("/login", response_model=TokenResponse)
def login(payload: AdminLogin, db: Session = Depends(get_db)):
    """Вход администратора. Возвращает JWT-токен."""
    admin = admin_crud.get_admin_by_email(db, payload.email)
    if admin is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    if not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(admin.email)
    return TokenResponse(access_token=token, admin=AdminOut.model_validate(admin))


@router.get("/status")
def check_status(db: Session = Depends(get_db)):
    """Проверка: есть ли уже администраторы.

    Возвращает is_first_admin=True, если можно зарегистрироваться.
    """
    return {"is_first_admin": not admin_crud.admin_exists(db)}


@router.get("/me", response_model=AdminOut)
def get_current_admin_info(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Получить данные текущего администратора.

    Токен передаётся в заголовке: Authorization: Bearer <token>.
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
    admin = admin_crud.get_admin_by_email(db, email)
    if admin is None:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    return AdminOut.model_validate(admin)