from typing import Optional

from app.db.mongo import db


async def can_access_scan(scan: dict, user: Optional[dict]) -> bool:
    scan_user_id = scan.get("user_id")

    if not scan_user_id:
        return True

    if not user:
        return False

    if scan_user_id == user["_id"]:
        return True

    role = user.get("role")

    if role == "admin":
        return True

    if role == "doctor" and user.get("clinic_id"):
        patient = await db.users.find_one({"_id": scan_user_id})
        if patient and patient.get("clinic_id") == user["clinic_id"]:
            return True

    return False
