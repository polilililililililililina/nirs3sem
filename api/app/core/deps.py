from fastapi import Header, HTTPException
from app.core.security import decode_token
from app.db.mongo import db
from typing import Optional


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

    return payload