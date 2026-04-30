import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(tz=timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    token = jwt.encode(
        claims=payload,
        key=settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    return token


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY.get_secret_value(),
            algorithms=settings.ALGORITHM,
        )
    except JWTError:
        raise ValueError("Token is invalid")
    return payload
