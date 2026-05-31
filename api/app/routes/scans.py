from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, WebSocketException
from fastapi.responses import FileResponse
from app.db.mongo import db
from app.core.deps import get_current_user, get_current_user_optional, get_user_from_token, require_role
from app.models.scan import ScanStatus, ScanListResponse, CommentCreate, ConclusionCreate, VerifyScanBody
from app.services.serializers import scans_serializer, scan_serializer, comment_serializer, conclusion_serializer
from app.services.scan_access import can_access_scan
from app.services.patient_access import can_doctor_access_patient, patient_summary
from app.services.files import delete_scan_files
from app.core.time import utc_now
import uuid
from typing import Optional, Literal
import os
from datetime import datetime, timedelta
from app.services.queue import scan_queue
from app.sockets.manager import manager
from app.ai.services.dicom_parser import dicom_to_png, is_dicom_file

from app.core.config import INPUT_DIR

router = APIRouter(prefix="/scans", tags=["Scans"])

os.makedirs(INPUT_DIR, exist_ok=True)


async def _build_scans_query(user: dict) -> dict:
    role = user.get("role", "user")

    if role == "user":
        return {"user_id": user["_id"]}

    if role == "doctor":
        clinic_id = user.get("clinic_id")
        if not clinic_id:
            return {"user_id": user["_id"]}

        patient_ids = await db.users.distinct("_id", {"clinic_id": clinic_id})
        return {"user_id": {"$in": patient_ids}}

    if role == "admin":
        return {}

    return {"user_id": user["_id"]}


def _apply_date_filters(query: dict, date_from: Optional[str], date_to: Optional[str]) -> None:
    if date_from:
        start = datetime.fromisoformat(date_from)
        query.setdefault("created_at", {})["$gte"] = start

    if date_to:
        end = datetime.fromisoformat(date_to) + timedelta(days=1)
        query.setdefault("created_at", {})["$lt"] = end


def _doctor_display_name(user: dict) -> str:
    parts = [user.get("surname"), user.get("name")]
    name = " ".join(part for part in parts if part)
    return name or user.get("email", "Врач")


@router.post("/upload", summary="Загрузить изображение МРТ")
async def upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user_optional),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Можно загружать только изображения")

    scan_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename or "")[1].lower().lstrip(".") or "jpg"
    path = f"{INPUT_DIR}/{scan_id}.{extension}"

    with open(path, "wb") as f:
        f.write(await file.read())

    created = utc_now()
    doc = {
        "_id": scan_id,
        "user_id": user["_id"] if user else None,
        "is_guest": user is None,
        "filename": file.filename or f"{scan_id}.{extension}",
        "file_path": path,
        "source_type": "image",
        "status": ScanStatus.queued,
        "created_at": created,
    }

    if user is None:
        doc["expires_at"] = created + timedelta(hours=1)

    await db.scans.insert_one(doc)
    await scan_queue.put({"scan_id": scan_id, "path": path})

    return {"id": scan_id}


@router.post("/upload-dicom", summary="Загрузить DICOM файл (.dcm)")
async def upload_dicom(
    file: UploadFile = File(...),
    user=Depends(get_current_user_optional),
):
    filename = file.filename or ""

    if not is_dicom_file(filename):
        raise HTTPException(400, "Можно загружать только DICOM файлы (.dcm)")

    scan_id = str(uuid.uuid4())
    dicom_path = f"{INPUT_DIR}/{scan_id}.dcm"
    png_path = f"{INPUT_DIR}/{scan_id}.png"

    content = await file.read()

    with open(dicom_path, "wb") as f:
        f.write(content)

    try:
        dicom_to_png(dicom_path, png_path)
    except Exception as exc:
        if os.path.isfile(dicom_path):
            os.remove(dicom_path)
        raise HTTPException(400, f"Не удалось обработать DICOM: {exc}") from exc

    created = utc_now()
    doc = {
        "_id": scan_id,
        "user_id": user["_id"] if user else None,
        "is_guest": user is None,
        "filename": filename or f"{scan_id}.dcm",
        "file_path": png_path,
        "dicom_path": dicom_path,
        "source_type": "dicom",
        "status": ScanStatus.queued,
        "created_at": created,
    }

    if user is None:
        doc["expires_at"] = created + timedelta(hours=1)

    await db.scans.insert_one(doc)
    await scan_queue.put({"scan_id": scan_id, "path": png_path})

    return {"id": scan_id}


@router.get("/", response_model=ScanListResponse, summary="Список анализов текущего пользователя")
async def get_scans(
    page: int = 1,
    limit: int = 10,
    status: Optional[ScanStatus] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user=Depends(get_current_user),
):
    skips = (page - 1) * limit
    query = await _build_scans_query(user)

    if status:
        query["status"] = status

    if search:
        query["filename"] = {"$regex": search, "$options": "i"}

    _apply_date_filters(query, date_from, date_to)

    scans_cursor = db.scans.find(query).sort("created_at", -1).skip(skips).limit(limit)
    scans = await scans_cursor.to_list(limit)
    total = await db.scans.count_documents(query)

    return {
        "items": scans_serializer(scans),
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
        },
    }


@router.get("/patients", summary="Каталог пациентов клиники")
async def get_patients(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    user=Depends(require_role("doctor", "admin")),
):
    if user.get("role") == "doctor" and not user.get("clinic_id"):
        return {
            "items": [],
            "pagination": {"page": page, "limit": limit, "total": 0},
        }

    user_filter: dict = {}
    if user.get("role") == "doctor":
        user_filter["clinic_id"] = user["clinic_id"]

    if search:
        user_filter["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"surname": {"$regex": search, "$options": "i"}},
            {"middlename": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    matching_users = await db.users.find(user_filter, {"_id": 1}).to_list(None)
    user_ids = [item["_id"] for item in matching_users]

    if not user_ids:
        return {
            "items": [],
            "pagination": {"page": page, "limit": limit, "total": 0},
        }

    total_result = await db.scans.aggregate(
        [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {"_id": "$user_id"}},
            {"$count": "total"},
        ]
    ).to_list(1)
    total = total_result[0]["total"] if total_result else 0

    groups = await db.scans.aggregate(
        [
            {"$match": {"user_id": {"$in": user_ids}}},
            {
                "$group": {
                    "_id": "$user_id",
                    "scan_count": {"$sum": 1},
                    "last_scan_at": {"$max": "$created_at"},
                }
            },
            {"$sort": {"last_scan_at": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit},
        ]
    ).to_list(limit)

    items = []
    for group in groups:
        patient = await db.users.find_one({"_id": group["_id"]})
        if not patient:
            continue

        summary = patient_summary(patient)
        summary["scan_count"] = group["scan_count"]
        summary["last_scan_at"] = group["last_scan_at"]
        items.append(summary)

    return {
        "items": items,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/patients/{user_id}", summary="Анализы пациента")
async def get_patient_scans(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    user=Depends(require_role("doctor", "admin")),
):
    if not await can_doctor_access_patient(user, user_id):
        raise HTTPException(403, "Нет доступа к пациенту")

    patient = await db.users.find_one({"_id": user_id})
    if not patient:
        raise HTTPException(404, "Пациент не найден")

    query = {"user_id": user_id}
    skips = (page - 1) * limit

    scans = await db.scans.find(query).sort("created_at", -1).skip(skips).limit(limit).to_list(limit)
    total = await db.scans.count_documents(query)

    return {
        "patient": patient_summary(patient),
        "items": scans_serializer(scans),
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/similar", summary="Похожие завершённые анализы")
async def get_similar_scans(
    scan_id: str,
    limit: int = Query(5, ge=1, le=20),
    user=Depends(get_current_user),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404, "Анализ не найден")

    if not await can_access_scan(scan, user):
        raise HTTPException(403, "Нет доступа к анализу")

    if scan.get("status") != ScanStatus.done:
        raise HTTPException(400, "Анализ ещё не завершён")

    confidence = scan.get("confidence")
    tumor_detected = scan.get("tumor_detected")

    if confidence is None or tumor_detected is None:
        raise HTTPException(400, "Недостаточно данных для поиска похожих случаев")

    scope_query = await _build_scans_query(user)
    query = {
        **scope_query,
        "_id": {"$ne": scan_id},
        "status": ScanStatus.done,
        "tumor_detected": tumor_detected,
        "confidence": {"$gte": confidence - 0.15, "$lte": confidence + 0.15},
    }

    similar = await db.scans.find(query).sort("created_at", -1).limit(limit).to_list(limit)

    return {"items": scans_serializer(similar)}


@router.get("/result/{scan_id}", summary="Получить маску сегментации")
async def get_result(scan_id: str, user=Depends(get_current_user_optional)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan or not scan.get("result"):
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403 if user else 401)

    if not os.path.isfile(scan["result"]):
        raise HTTPException(404)

    return FileResponse(scan["result"])


@router.get("/input/{scan_id}", summary="Получить исходное изображение")
async def get_input(scan_id: str, user=Depends(get_current_user_optional)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan or not scan.get("file_path"):
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403 if user else 401)

    if not os.path.isfile(scan["file_path"]):
        raise HTTPException(404)

    return FileResponse(scan["file_path"])


@router.get("/heatmap/{scan_id}", summary="Получить Grad-CAM heatmap")
async def get_heatmap(
    scan_id: str,
    view: Literal["overlay", "raw"] = "overlay",
    user=Depends(get_current_user_optional),
):
    scan = await db.scans.find_one({"_id": scan_id})

    field = "heatmap_raw_path" if view == "raw" else "heatmap_path"

    if not scan or not scan.get(field):
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403 if user else 401)

    if not os.path.isfile(scan[field]):
        raise HTTPException(404)

    return FileResponse(scan[field])


@router.get("/{scan_id}/comments", summary="Список комментариев врачей")
async def get_scan_comments(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    comments = await db.doctors_comments.find({"scan_id": scan_id}).sort("created_at", 1).to_list(None)

    return {"items": [comment_serializer(comment) for comment in comments]}


@router.post("/{scan_id}/comments", summary="Добавить комментарий врача")
async def add_scan_comment(
    scan_id: str,
    data: CommentCreate,
    user=Depends(require_role("doctor", "admin")),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    message = data.message.strip()
    if not message:
        raise HTTPException(400, "Комментарий не может быть пустым")

    comment_id = str(uuid.uuid4())
    doc = {
        "_id": comment_id,
        "scan_id": scan_id,
        "author_id": user["_id"],
        "author_name": _doctor_display_name(user),
        "message": message,
        "created_at": utc_now(),
    }

    await db.doctors_comments.insert_one(doc)

    return comment_serializer(doc)


@router.get("/{scan_id}/conclusion", summary="Получить экспертное заключение")
async def get_scan_conclusion(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    conclusion = await db.expert_conclusions.find_one({"scan_id": scan_id}, sort=[("created_at", -1)])

    if not conclusion:
        return {"conclusion": None}

    return {"conclusion": conclusion_serializer(conclusion)}


@router.post("/{scan_id}/conclusion", summary="Сохранить экспертное заключение")
async def add_scan_conclusion(
    scan_id: str,
    data: ConclusionCreate,
    user=Depends(require_role("doctor", "admin")),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Заключение не может быть пустым")

    conclusion_id = str(uuid.uuid4())
    doc = {
        "_id": conclusion_id,
        "scan_id": scan_id,
        "doctor_id": user["_id"],
        "doctor_name": _doctor_display_name(user),
        "text": text,
        "created_at": utc_now(),
    }

    await db.expert_conclusions.insert_one(doc)

    return conclusion_serializer(doc)


@router.put("/{scan_id}/verify", summary="Подтвердить или отклонить результат ИИ")
async def verify_scan(
    scan_id: str,
    data: VerifyScanBody,
    user=Depends(require_role("doctor", "admin")),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    await db.scans.update_one(
        {"_id": scan_id},
        {
            "$set": {
                "doctor_verified": data.verified,
                "verified_by": user["_id"],
                "verified_at": utc_now(),
                "updated_at": utc_now(),
            }
        },
    )

    updated = await db.scans.find_one({"_id": scan_id})

    return scan_serializer(updated)


@router.get("/{scan_id}", summary="Детали анализа")
async def get_scan(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if not await can_access_scan(scan, user):
        raise HTTPException(403)

    return scan_serializer(scan)


@router.delete("/{scan_id}", summary="Удалить анализ")
async def delete_scan(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    if scan.get("user_id") != user["_id"] and user.get("role") != "admin":
        raise HTTPException(403)

    delete_scan_files(scan)
    await db.scans.delete_one({"_id": scan_id})

    return {"ok": True}


@router.websocket("/ws/{scan_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    scan_id: str,
    token: Optional[str] = Query(None),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise WebSocketException(code=1008, reason="Scan not found")

    user = await get_user_from_token(token)

    if not await can_access_scan(scan, user):
        raise WebSocketException(code=1008, reason="Access denied")

    await manager.connect(scan_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(scan_id)
