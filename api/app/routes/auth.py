from fastapi import APIRouter, HTTPException, Request
from app.db.mongo import db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, create_reset_token, decode_token
from app.models.auth import RegisterSchema, LoginSchema, ForgotPasswordSchema, ResetPasswordSchema
from datetime import datetime, timedelta
from app.services.email import send_reset_email
from fastapi import BackgroundTasks
from app.core.config import FRONTEND_URL
from app.core.limiter import limiter
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(data: RegisterSchema):
    try:
        # Проверяем, есть ли пользователь с таким email
        if await db.users.find_one({"email": data.email}):
            raise HTTPException(400, "Пользователь с таким email уже существует")

        user = {
            "_id": str(uuid.uuid4()),
            "email": data.email,
            "password": hash_password(data.password),
            "name": data.name,
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.users.insert_one(user)
        return {"message": "ok"}

    except HTTPException:
        # Если это уже HTTPException (например, пользователь существует), пробрасываем дальше
        raise
    except Exception as e:
        # Любая другая ошибка (например, база недоступна)
        raise HTTPException(500, f"Произошла ошибка при регистрации: {str(e)}")


@router.post("/login")
async def login(data: LoginSchema):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(400, "Неверный адрес электронной почты или пароль")

    try:
        access_token = create_access_token({"_id": user["_id"], "email": user["email"]})
        refresh_token = create_refresh_token({"_id": user["_id"], "email": user["email"]})
    except Exception as e:
        raise HTTPException(500, f"Произошла ошибка при входе: {str(e)}")

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks
):
    user = await db.users.find_one({"email": data.email})

    if not user:
        return {
            "message":
            "Если email существует, письмо отправлено"
        }

    token = create_reset_token({"_id": user["_id"], "email": user["email"]})

    expires = datetime.utcnow() + timedelta(minutes=30)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token": token,
                "password_reset_expires": expires
            }
        }
    )

    reset_link = (
        f"{FRONTEND_URL}/reset-password"
        f"?token={token}"
    )

    background_tasks.add_task(
        send_reset_email,
        user["email"],
        reset_link
    )

    return {
        "message":
        "Если email существует, письмо отправлено"
    }


@router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema):

    user = await db.users.find_one({
        "password_reset_token": data.token
    })

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Неверный токен"
        )

    if (
        not user.get("password_reset_expires")
        or
        user["password_reset_expires"]
        < datetime.utcnow()
    ):
        raise HTTPException(400, "Токен истёк")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hash_password(
                    data.new_password
                ),
                "updated_at": datetime.utcnow()
            },

            "$unset": {
                "password_reset_token": "",
                "password_reset_expires": ""
            }
        }
    )

    return { "message": "Пароль изменён" }


@router.post("/refresh")
async def refresh_token(data: dict):

    refresh_token = data.get("refresh_token")
    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(401, "Invalid refresh token")

    access_token = access_token({
        "_id": payload["_id"],
        "email": payload["email"]
    })

    return {"access_token": access_token}

