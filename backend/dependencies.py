"""JWT authentication dependency for FastAPI."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import JWT_SECRET, JWT_ALGORITHM
from .database import get_db
from .models import User

security = HTTPBearer(auto_error=False)


def create_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    import uuid
    payload = {
        "sub": user_id,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db=Depends(get_db),
) -> User | None:
    """Get the current authenticated user, or None if not authenticated."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except jwt.InvalidTokenError:
        return None

    from sqlalchemy import select
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    return user


def require_auth(
    user: User | None = Depends(get_current_user),
) -> User:
    """Require authentication. Raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    return user


def require_credits(user: User = Depends(require_auth)) -> User:
    """Require the user to have credits. Raises 402 if insufficient."""
    if not user.has_unlimited and user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="积分不足，请充值",
        )
    return user
