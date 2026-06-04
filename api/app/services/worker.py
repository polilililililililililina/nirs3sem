import asyncio
import os

from app.ai.services.predict import predict_scan, predict_scan_volume
from app.ai.services.result_text import build_result_desc
from app.core.time import utc_now
from app.db.mongo import db
from app.models.scan import ScanStatus
from app.services.queue import processing_semaphore, scan_queue
from app.sockets.manager import manager

os.makedirs("storage/output", exist_ok=True)


def _user_friendly_error(exc: Exception) -> str:
    text = str(exc)
    if "Lambda layer" in text or "safe_mode" in text:
        return (
            "Не удалось загрузить модель нейросети. "
            "Перезапустите сервер API (после обновления) или переобучите модель командой "
            "python -m app.ai.train.train_aa_unet"
        )
    if len(text) > 500:
        return text[:500] + "…"
    return text


async def process_scan_task():
    while True:
        task = await scan_queue.get()

        scan_id = task["scan_id"]
        mode = task.get("mode", "image")
        path = task.get("path")

        async with processing_semaphore:
            try:
                await db.scans.update_one(
                    {"_id": scan_id},
                    {"$set": {"status": ScanStatus.processing}},
                )
                await manager.send_message(scan_id, {"status": ScanStatus.processing})

                if mode == "dicom_zip":
                    dicom_folder = task["dicom_folder"]
                    preview_path = path or task.get("preview_path")
                    result = await asyncio.to_thread(
                        predict_scan_volume,
                        dicom_folder,
                        preview_path,
                    )
                else:
                    result = await asyncio.to_thread(predict_scan, path)

                update_fields = {
                    "status": "done",
                    "result": result["result_path"],
                    "confidence": result["confidence"],
                    "tumor_detected": result["tumor_detected"],
                    "result_desc": build_result_desc(
                        result["tumor_detected"],
                        volume_stats=result.get("volume_stats"),
                    ),
                    "updated_at": utc_now(),
                }

                if result.get("preview_path"):
                    update_fields["file_path"] = result["preview_path"]

                if result.get("n_slices") is not None:
                    update_fields["n_slices"] = result["n_slices"]

                if result.get("representative_slice_idx") is not None:
                    update_fields["representative_slice_idx"] = result[
                        "representative_slice_idx"
                    ]

                if result.get("heatmap_path"):
                    update_fields["heatmap_path"] = result["heatmap_path"]

                if result.get("heatmap_raw_path"):
                    update_fields["heatmap_raw_path"] = result["heatmap_raw_path"]

                await db.scans.update_one({"_id": scan_id}, {"$set": update_fields})

                ws_payload = {
                    "status": ScanStatus.done,
                    "result": result["result_path"],
                    "heatmap_path": result.get("heatmap_path"),
                    "tumor_detected": result["tumor_detected"],
                    "confidence": result["confidence"],
                }
                if update_fields.get("result_desc"):
                    ws_payload["result_desc"] = update_fields["result_desc"]

                await manager.send_message(scan_id, ws_payload)

            except Exception as e:
                error_message = _user_friendly_error(e)
                await db.scans.update_one(
                    {"_id": scan_id},
                    {
                        "$set": {
                            "status": ScanStatus.error,
                            "result_desc": error_message,
                            "updated_at": utc_now(),
                        }
                    },
                )

                await manager.send_message(
                    scan_id,
                    {"status": ScanStatus.error, "message": error_message},
                )

        scan_queue.task_done()
