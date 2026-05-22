from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.core.deps import get_current_user
from app.db.mongo import db
from app.models.user import UserResponse, UpdateUserSchema
from app.services.serializers import user_serializer
from datetime import datetime
from app.core.config import AVATAR_DIR
import os

os.makedirs(AVATAR_DIR, exist_ok=True)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Получить профиль
@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return user_serializer(user)


# Обновить профиль
@router.put("/me", response_model=UserResponse)
async def update_me(data: UpdateUserSchema, user=Depends(get_current_user)):

    update_data = data.model_dump(exclude_unset=True)

    # Проверяем, есть ли изменения
    if not update_data:
        raise HTTPException(400, "Нет данных для обновления")

    update_data["updated_at"] = datetime.utcnow()

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": update_data}
    )

    updated_user = await db.users.find_one({
        "_id": user["_id"]
    })

    return user_serializer(updated_user)


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user=Depends(get_current_user)):

    if not file.content_type.startswith(
        "image/"
    ):
        raise HTTPException(400, "Только изображения")

    path = f"{AVATAR_DIR}/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "avatar_url": path
            }
        }
    )

    return {
        "avatar_url": path
    }


@router.get("/avatar/{filename}")
async def get_avatar(filename: str, user=Depends(get_current_user)):

    path = f"{AVATAR_DIR}/{filename}"

    if not os.path.exists(path):
        raise HTTPException(404)

    return FileResponse(path)