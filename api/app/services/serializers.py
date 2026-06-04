import os
from typing import Optional


def _avatar_filename(avatar_url: Optional[str]) -> Optional[str]:
    if not avatar_url:
        return None
    return os.path.basename(avatar_url)


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
        "source_type": scan.get("source_type", "image"),
        "heatmap_path": scan.get("heatmap_path"),
        "heatmap_raw_path": scan.get("heatmap_raw_path"),
        "doctor_verified": scan.get("doctor_verified"),
        "created_at": scan["created_at"],
        "updated_at": scan.get("updated_at"),
        "confidence": scan.get("confidence"),
        "tumor_detected": scan.get("tumor_detected"),
        "n_slices": scan.get("n_slices"),
        "representative_slice_idx": scan.get("representative_slice_idx"),
    }


def scans_serializer(scans) -> list:
    return [scan_serializer(scan) for scan in scans]


def comment_serializer(comment) -> dict:
    return {
        "_id": comment["_id"],
        "scan_id": comment["scan_id"],
        "author_id": comment["author_id"],
        "author_name": comment["author_name"],
        "message": comment["message"],
        "created_at": comment["created_at"],
    }


def conclusion_serializer(conclusion) -> dict:
    return {
        "_id": conclusion["_id"],
        "scan_id": conclusion["scan_id"],
        "doctor_id": conclusion["doctor_id"],
        "doctor_name": conclusion["doctor_name"],
        "text": conclusion["text"],
        "created_at": conclusion["created_at"],
    }


def user_serializer(user) -> dict:
    return {
        "_id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role"),
        "surname": user.get("surname"),
        "middlename": user.get("middlename"),
        "birthday": user.get("birthday"),
        "position": user.get("position"),
        "phone": user.get("phone"),
        "avatar_url": _avatar_filename(user.get("avatar_url")),
        "clinic_id": user.get("clinic_id"),
        "clinic_name": user.get("clinic_name"),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }
