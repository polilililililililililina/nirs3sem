from app.db.mongo import db
from app.services.serializers import user_serializer


async def user_response(user: dict) -> dict:
    data = user_serializer(user)

    clinic_id = user.get("clinic_id")
    if clinic_id:
        clinic = await db.clinics.find_one({"_id": clinic_id})
        if clinic:
            data["clinic_name"] = clinic["name"]

    return data
