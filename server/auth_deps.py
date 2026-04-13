import os
from typing import Optional

from fastapi import Header, HTTPException

_APP_KEY = os.getenv("APP_API_KEY", "").strip()


def require_app_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
):
    """当设置了 APP_API_KEY 时，要求请求携带相同密钥（Bearer 或 X-API-Key）。"""
    if not _APP_KEY:
        return
    token = (x_api_key or "").strip()
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token or token != _APP_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
