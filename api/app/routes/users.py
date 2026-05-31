from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.core.deps import get_current_user
from app.db.mongo import db
from app.models.user import UserResponse, UpdateUserSchema
from app.services.users import user_response
from app.core.time import utc_now
from app.core.config import AVATAR_DIR
import os
import uuid

os.makedirs(AVATAR_DIR, exist_ok=True)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Профиль текущего пользователя")
async def me(user=Depends(get_current_user)):
    return await user_response(user)


@router.put("/me", response_model=UserResponse, summary="Обновить профиль")
async def update_me(data: UpdateUserSchema, user=Depends(get_current_user)):
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "Нет данных для обновления")

    if "clinic_id" in update_data and update_data["clinic_id"]:
        clinic = await db.clinics.find_one({"_id": update_data["clinic_id"]})
        if not clinic:
            raise HTTPException(400, "Клиника не найдена")

    update_data["updated_at"] = utc_now()

    await db.users.update_one({"_id": user["_id"]}, {"$set": update_data})

    updated_user = await db.users.find_one({"_id": user["_id"]})

    return await user_response(updated_user)


@router.post("/avatar", summary="Загрузить аватар")
async def upload_avatar(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Только изображения")

    extension = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4()}{extension}"
    path = os.path.join(AVATAR_DIR, filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    old_avatar = user.get("avatar_url")
    if old_avatar:
        old_path = old_avatar if os.path.isabs(old_avatar) else os.path.join(AVATAR_DIR, os.path.basename(old_avatar))
        if os.path.isfile(old_path) and old_path != path:
            os.remove(old_path)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"avatar_url": filename}},
    )

    return {"avatar_url": filename}


@router.get("/avatar/{filename}", summary="Получить файл аватара")
async def get_avatar(filename: str, user=Depends(get_current_user)):
    safe_name = os.path.basename(filename)
    path = os.path.join(AVATAR_DIR, safe_name)

    if not os.path.isfile(path):
        raise HTTPException(404)

    if os.path.basename(user.get("avatar_url") or "") != safe_name and user.get("role") != "admin":
        raise HTTPException(403)

    return FileResponse(path)
