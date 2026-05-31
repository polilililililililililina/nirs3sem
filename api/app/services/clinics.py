def clinic_serializer(clinic: dict) -> dict:
    return {
        "_id": clinic["_id"],
        "name": clinic["name"],
        "address": clinic.get("address"),
        "description": clinic.get("description"),
        "created_at": clinic["created_at"],
    }


def clinics_serializer(clinics: list) -> list:
    return [clinic_serializer(clinic) for clinic in clinics]
