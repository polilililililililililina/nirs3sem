def scan_serializer(scan) -> dict:
    return {
        "_id": scan["_id"],
        "filename": scan["filename"],
        "file_path": scan["file_path"],
        "status": scan["status"],
        "user_id": str(scan["user_id"]) if scan.get("user_id") else None,
        "result": scan.get("result"),
        "is_guest": scan.get("is_guest", False),
        "result_desc": scan.get("result_desc"),
        "created_at": scan["created_at"]
    }


def scans_serializer(scans) -> list:
    return [scan_serializer(scan) for scan in scans]


def user_serializer(user) -> dict:
    return {
        "_id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "surname": user.get("surname"),
        "middlename": user.get("middlename"),
        "birthday": user.get("birthday"),
        "job": user.get("job"),
        "position": user.get("position"),
        "phone": user.get("phone"),
        "avatar_url": user.get("avatar_url"),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"]
    }