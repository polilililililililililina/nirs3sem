import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import require_role
from app.core.time import utc_now
from app.db.mongo import db
from app.models.admin import (
    AdminUserListResponse,
    ClinicCreate,
    ClinicUpdate,
    RoleUpdate,
)
from app.models.user import UserRole
from app.services.clinics import clinic_serializer, clinics_serializer
from app.services.users import user_response

router = APIRouter(prefix="/admin", tags=["Admin"])


async def _ensure_not_last_admin(user_id: str, new_role: UserRole) -> None:
    user = await db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(404, "Пользователь не найден")

    if user.get("role") != "admin" or new_role == UserRole.admin:
        return

    admin_count = await db.users.count_documents({"role": "admin"})

    if admin_count <= 1:
        raise HTTPException(400, "Нельзя понизить последнего администратора")


@router.get("/users", response_model=AdminUserListResponse, summary="Список пользователей")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    user=Depends(require_role("admin")),
):
    query: dict = {}

    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"surname": {"$regex": search, "$options": "i"}},
            {"middlename": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * limit
    users = await db.users.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents(query)

    items = [await user_response(item) for item in users]

    return {
        "items": items,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.patch("/users/{user_id}/role", summary="Изменить роль пользователя")
async def update_user_role(
    user_id: str,
    data: RoleUpdate,
    user=Depends(require_role("admin")),
):
    target = await db.users.find_one({"_id": user_id})

    if not target:
        raise HTTPException(404, "Пользователь не найден")

    await _ensure_not_last_admin(user_id, data.role)

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"role": data.role.value, "updated_at": utc_now()}},
    )

    updated = await db.users.find_one({"_id": user_id})

    return await user_response(updated)


@router.get("/clinics", summary="Список клиник (админ)")
async def list_clinics(user=Depends(require_role("admin"))):
    clinics = await db.clinics.find().sort("name", 1).to_list(None)
    return {"items": clinics_serializer(clinics)}


@router.post("/clinics", summary="Создать клинику")
async def create_clinic(
    data: ClinicCreate,
    user=Depends(require_role("admin")),
):
    name = data.name.strip()

    if not name:
        raise HTTPException(400, "Название клиники обязательно")

    existing = await db.clinics.find_one({"name": name})

    if existing:
        raise HTTPException(400, "Клиника с таким названием уже существует")

    now = utc_now()
    doc = {
        "_id": str(uuid.uuid4()),
        "name": name,
        "address": data.address.strip() if data.address else None,
        "description": data.description.strip() if data.description else None,
        "created_at": now,
    }

    await db.clinics.insert_one(doc)

    return clinic_serializer(doc)


@router.put("/clinics/{clinic_id}", summary="Обновить клинику")
async def update_clinic(
    clinic_id: str,
    data: ClinicUpdate,
    user=Depends(require_role("admin")),
):
    clinic = await db.clinics.find_one({"_id": clinic_id})

    if not clinic:
        raise HTTPException(404, "Клиника не найдена")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "Нет данных для обновления")

    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()
        if not update_data["name"]:
            raise HTTPException(400, "Название клиники обязательно")

        duplicate = await db.clinics.find_one(
            {"name": update_data["name"], "_id": {"$ne": clinic_id}}
        )
        if duplicate:
            raise HTTPException(400, "Клиника с таким названием уже существует")

    if "address" in update_data and update_data["address"]:
        update_data["address"] = update_data["address"].strip()

    if "description" in update_data and update_data["description"]:
        update_data["description"] = update_data["description"].strip()

    await db.clinics.update_one({"_id": clinic_id}, {"$set": update_data})

    updated = await db.clinics.find_one({"_id": clinic_id})

    return clinic_serializer(updated)


@router.delete("/clinics/{clinic_id}", summary="Удалить клинику")
async def delete_clinic(
    clinic_id: str,
    user=Depends(require_role("admin")),
):
    clinic = await db.clinics.find_one({"_id": clinic_id})

    if not clinic:
        raise HTTPException(404, "Клиника не найдена")

    linked_users = await db.users.count_documents({"clinic_id": clinic_id})

    if linked_users > 0:
        raise HTTPException(
            400,
            f"Нельзя удалить клинику: к ней привязано пользователей: {linked_users}",
        )

    await db.clinics.delete_one({"_id": clinic_id})

    return {"ok": True}
