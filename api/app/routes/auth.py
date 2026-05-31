from fastapi import APIRouter, HTTPException, Request
from app.db.mongo import db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
)
from app.models.auth import (
    RegisterSchema,
    LoginSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    RefreshTokenSchema,
)
from datetime import timedelta
from app.core.time import utc_now
from app.services.email import send_reset_email
from fastapi import BackgroundTasks
from app.core.config import FRONTEND_URL
from app.core.limiter import limiter
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", summary="Регистрация пользователя")
async def register(data: RegisterSchema):
    try:
        if await db.users.find_one({"email": data.email}):
            raise HTTPException(400, "Пользователь с таким email уже существует")

        user = {
            "_id": str(uuid.uuid4()),
            "email": data.email,
            "password": hash_password(data.password),
            "name": data.name,
            "role": "user",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        await db.users.insert_one(user)
        return {"message": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Произошла ошибка при регистрации: {str(e)}")


@router.post("/login", summary="Вход и получение JWT токенов")
async def login(data: LoginSchema):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(400, "Неверный адрес электронной почты или пароль")

    try:
        access_token = create_access_token({
            "_id": user["_id"],
            "email": user["email"],
            "role": user.get("role", "user"),
        })
        refresh_token = create_refresh_token({
            "_id": user["_id"],
            "email": user["email"],
            "role": user.get("role", "user"),
        })
    except Exception as e:
        raise HTTPException(500, f"Произошла ошибка при входе: {str(e)}")

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/forgot-password", summary="Запрос ссылки для сброса пароля")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
):
    user = await db.users.find_one({"email": data.email})

    if not user:
        return {"message": "Если email существует, письмо отправлено"}

    token = create_reset_token({"_id": user["_id"], "email": user["email"]})
    expires = utc_now() + timedelta(minutes=30)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token": token,
                "password_reset_expires": expires,
            }
        },
    )

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    background_tasks.add_task(send_reset_email, user["email"], reset_link)

    return {"message": "Если email существует, письмо отправлено"}


@router.post("/reset-password", summary="Сброс пароля по токену")
async def reset_password(data: ResetPasswordSchema):
    user = await db.users.find_one({"password_reset_token": data.token})

    if not user:
        raise HTTPException(status_code=400, detail="Неверный токен")

    if not user.get("password_reset_expires") or user["password_reset_expires"] < utc_now():
        raise HTTPException(400, "Токен истёк")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hash_password(data.new_password),
                "updated_at": utc_now(),
            },
            "$unset": {
                "password_reset_token": "",
                "password_reset_expires": "",
            },
        },
    )

    return {"message": "Пароль изменён"}


@router.post("/refresh", summary="Обновить access token")
async def refresh_token(data: RefreshTokenSchema):
    payload = decode_token(data.refresh_token)

    if not payload:
        raise HTTPException(401, "Invalid refresh token")

    user = await db.users.find_one({"email": payload["email"]})

    if not user:
        raise HTTPException(401, "User not found")

    new_access_token = create_access_token(
        {
            "_id": user["_id"],
            "email": user["email"],
            "role": user.get("role", "user"),
        }
    )

    return {"access_token": new_access_token}
