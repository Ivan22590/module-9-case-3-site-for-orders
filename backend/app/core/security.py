"""
Хеширование паролей и JWT-токены для авторизации администраторов.
"""
import hashlib
import os
import secrets
import time

import jwt

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-me-in-production",
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))


# ────────────────────────────────────────────────────────────
# Хеширование паролей (PBKDF2-HMAC-SHA256)
# ────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Хеширует пароль с помощью PBKDF2-HMAC-SHA256.

    Формат: pbkdf2_sha256$<salt>$<hash>
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, hashed: str) -> bool:
    """Проверяет пароль против захешированного значения."""
    if not hashed or not hashed.startswith("pbkdf2_sha256$"):
        return False
    try:
        _, salt, digest = hashed.split("$", 2)
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200_000,
        ).hex()
        return secrets.compare_digest(expected, digest)
    except (ValueError, IndexError):
        return False


# ────────────────────────────────────────────────────────────
# JWT-токены
# ────────────────────────────────────────────────────────────

def create_access_token(subject: str) -> str:
    """Создаёт JWT-токен для заданного subject (обычно email админа)."""
    expire = time.time() + JWT_EXPIRE_MINUTES * 60
    return jwt.encode(
        {"sub": subject, "exp": expire},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    """Декодирует JWT-токен. Возвращает subject или None при ошибке."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None