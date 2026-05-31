from app.db.mongo import db


async def can_doctor_access_patient(actor: dict, patient_id: str) -> bool:
    role = actor.get("role")

    if role == "admin":
        return True

    if role != "doctor":
        return False

    clinic_id = actor.get("clinic_id")
    if not clinic_id:
        return False

    patient = await db.users.find_one({"_id": patient_id})
    return bool(patient and patient.get("clinic_id") == clinic_id)


def patient_summary(user: dict) -> dict:
    parts = [user.get("surname"), user.get("name"), user.get("middlename")]
    full_name = " ".join(part for part in parts if part)

    return {
        "_id": user["_id"],
        "email": user["email"],
        "name": user.get("name"),
        "surname": user.get("surname"),
        "middlename": user.get("middlename"),
        "full_name": full_name or user.get("email"),
        "birthday": user.get("birthday"),
        "phone": user.get("phone"),
        "clinic_id": user.get("clinic_id"),
    }
