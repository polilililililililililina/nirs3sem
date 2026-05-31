from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.security import decode_token
from app.db.mongo import db


async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid token")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    user = await db.users.find_one({"email": payload["email"]})

    if not user:
        raise HTTPException(401, "User not found")

    return user


async def get_current_user_optional(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        return None

    user = await db.users.find_one({"email": payload["email"]})

    if not user:
        return None

    return user


async def get_user_from_token(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None

    payload = decode_token(token)

    if not payload:
        return None

    return await db.users.find_one({"email": payload["email"]})


def require_role(*roles: str) -> Callable:
    async def role_checker(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
        return user

    return role_checker
