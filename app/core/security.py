from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthError

_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    if len(password.encode()) > _MAX_PASSWORD_BYTES:
        raise ValueError("Пароль слишком длинный")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    if len(plain.encode()) > _MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    subject_id: int,
    subject_type: str,
    role: str | None = None,
) -> str:
    payload = {
        "sub": str(subject_id),
        "sub_type": subject_type,
        "exp": datetime.now(tz=timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if role is not None:
        payload["role"] = role

    return jwt.encode(
        claims=payload,
        key=settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(
            token=token,
            key=settings.SECRET_KEY.get_secret_value(),
            algorithms=settings.ALGORITHM,
        )
    except JWTError:
        raise AuthError("Token is invalid")
