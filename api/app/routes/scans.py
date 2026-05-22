from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from app.db.mongo import db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.scan import Scan, ScanStatus, ScanListResponse
from app.services.serializers import scans_serializer
import uuid
from datetime import datetime
from typing import Optional
import os
from app.services.queue import scan_queue
from fastapi import WebSocket
from app.sockets.manager import manager
from app.core.config import INPUT_DIR

router = APIRouter(prefix="/scans", tags=["Scans"])

os.makedirs(INPUT_DIR, exist_ok=True)

@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user_optional)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Можно загружать только изображения")

    scan_id = str(uuid.uuid4())

    extension = file.filename.split(".")[-1]
    path = f"{INPUT_DIR}/{scan_id}.{extension}"    

    with open(path, "wb") as f:
        f.write(await file.read())

    doc = {
        "_id": scan_id,
        "user_id": user["_id"] if user else None,
        "is_guest": user is None,
        "filename": file.filename,
        "file_path": path,
        "status": ScanStatus.queued,
        "created_at": datetime.utcnow(),
    }

    await db.scans.insert_one(doc)

    await scan_queue.put({ "scan_id": scan_id, "path": path })

    return {"id": scan_id}


@router.get("/", response_model=ScanListResponse)
async def get_scans(
    page: int = 1,
    limit: int = 10,
    status: Optional[ScanStatus] = None,
    search: Optional[str] = None,
    user=Depends(get_current_user)
):
    skips = (page - 1) * limit

    query = {
        "user_id": user["_id"]
    }

    # Фильтр по статусу
    if status:
        query["status"] = status

    # Фильтр по имени файла
    if search:
        query["filename"] = {
            "$regex": search,
            "$options": "i"
        }

    scans_cursor = db.scans.find(query).sort("created_at", -1).skip(skips).limit(limit)
    scans = await scans_cursor.to_list(limit)
    total = await db.scans.count_documents(query)

    return {
        "items": scans_serializer(scans),
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/result/{scan_id}")
async def get_result(scan_id: str, user=Depends(get_current_user_optional)):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404)

    # scan принадлежит пользователю
    if scan["user_id"]:

        if not user:
            raise HTTPException(401)

        if scan["user_id"] != user["_id"]:
            raise HTTPException(403)

    return FileResponse(scan["result"])


@router.get("/{scan_id}")
async def get_scan(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({
        "_id": scan_id,
        "user_id": user["_id"]
    })

    if not scan:
        raise HTTPException(404)
    
    return {"status": scan["status"]}


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, user=Depends(get_current_user)):
    scan = await db.scans.find_one({
        "_id": scan_id,
        "user_id": user["_id"]
    })

    if not scan:
        raise HTTPException(404)

    await db.scans.delete_one({
        "_id": scan_id
    })

    return {"ok": True}


@router.websocket("/ws/{scan_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    scan_id: str
):
    await manager.connect(scan_id,websocket)

    try:
        while True:
            await websocket.receive_text()

    except:
        manager.disconnect(scan_id)