import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    subject_id: int,
    subject_type: str,  # "client" | "employee"
    role: str | None = None,  # None для клиента; "admin" | "courier" для сотрудника
) -> str:
    """
    subject_type разделяет два потока аутентификации:
      - "client"   → токен клиента (POST /auth/login)
      - "employee" → токен сотрудника (POST /auth/staff/login)

    Это позволяет get_current_client и get_current_employee
    на уровне dependencies отклонять чужие токены (status 401),
    а не падать с 500 при попытке найти employee по client.id.
    """
    payload: dict = {
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
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY.get_secret_value(),
            algorithms=settings.ALGORITHM,
        )
    except JWTError:
        raise AuthError("Token is invalid")
    return payload
