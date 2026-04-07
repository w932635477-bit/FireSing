"""WeChat OAuth login routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from starlette.responses import RedirectResponse

from ..config import WECHAT_OPEN_APP_ID, WECHAT_MP_APP_ID
from ..database import get_db
from ..dependencies import create_token, get_current_user, require_auth
from ..models import User
from ..services.wechat_service import (
    get_qr_login_url,
    get_mp_authorize_url,
    exchange_code_for_userinfo,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory state store for OAuth flow (key: state, value: user_id or "pending")
_oauth_states: dict[str, str] = {}


@router.get("/wechat/qr-url")
def wechat_qr_url():
    """Get WeChat QR code login URL for PC."""
    if not WECHAT_OPEN_APP_ID:
        return {"url": "", "error": "WECHAT_OPEN_APP_ID not configured"}
    state = uuid.uuid4().hex
    _oauth_states[state] = "pending"
    url = get_qr_login_url(state)
    return {"url": url, "state": state}


@router.get("/wechat/authorize")
def wechat_mp_authorize():
    """Get WeChat MP OAuth URL for in-app login."""
    if not WECHAT_MP_APP_ID:
        return {"url": "", "error": "WECHAT_MP_APP_ID not configured"}
    state = uuid.uuid4().hex
    _oauth_states[state] = "pending"
    url = get_mp_authorize_url(state)
    return {"url": url, "state": state}


@router.get("/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query(...),
    db=Depends(get_db),
):
    """WeChat OAuth callback. Handles both QR scan and MP authorization."""
    if state not in _oauth_states:
        return RedirectResponse(url="/login?error=invalid_state")

    # Determine if this is MP (Official Account) or Open Platform
    is_mp = bool(WECHAT_MP_APP_ID and not WECHAT_OPEN_APP_ID)

    try:
        user_info = await exchange_code_for_userinfo(code, is_mp=is_mp)
    except Exception:
        return RedirectResponse(url="/login?error=wechat_failed")

    openid = user_info["openid"]
    unionid = user_info.get("unionid")

    # Find existing user by openid or unionid
    user = db.execute(select(User).where(User.wechat_openid == openid)).scalar_one_or_none()
    if user is None and unionid:
        user = db.execute(select(User).where(User.wechat_unionid == unionid)).scalar_one_or_none()
        if user:
            # Update openid for this platform
            user.wechat_openid = openid

    if user is None:
        # Create new user
        user = User(
            id=uuid.uuid4().hex[:12],
            wechat_openid=openid,
            wechat_unionid=unionid,
            wechat_nickname=user_info.get("nickname", ""),
            wechat_avatar_url=user_info.get("avatar_url", ""),
            credits=3,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Store user_id in state for polling
    _oauth_states[state] = user.id

    # Create JWT
    token = create_token(user.id)

    # Redirect to frontend with token
    return RedirectResponse(url=f"/login?token={token}")


@router.get("/wechat/poll")
def wechat_poll(state: str):
    """Poll for QR scan login result."""
    user_id = _oauth_states.get(state)
    if user_id and user_id != "pending":
        token = create_token(user_id)
        return {"status": "ok", "token": token}
    return {"status": "pending"}


@router.get("/me")
def get_me(user: Optional[User] = Depends(get_current_user)):
    """Get current user info."""
    if user is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "id": user.id,
        "nickname": user.wechat_nickname,
        "avatar_url": user.wechat_avatar_url,
        "credits": user.credits,
        "plan": user.subscription_plan,
        "has_unlimited": user.has_unlimited,
    }
