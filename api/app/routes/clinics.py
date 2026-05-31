from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.mongo import db

router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.get("/", summary="Список клиник для выбора в профиле")
async def list_clinics(user=Depends(get_current_user)):
    clinics = await db.clinics.find().sort("name", 1).to_list(None)

    return {
        "items": [
            {
                "_id": clinic["_id"],
                "name": clinic["name"],
                "address": clinic.get("address"),
            }
            for clinic in clinics
        ]
    }
