import asyncio

from app.services.queue import scan_queue, processing_semaphore
from app.db.mongo import db
from app.models.scan import ScanStatus
from app.sockets.manager import manager
from app.core.config import OUTPUT_DIR
from app.core.time import utc_now
from app.ai.services.predict import predict_scan
from app.ai.services.result_text import build_result_desc
import os

os.makedirs(OUTPUT_DIR, exist_ok=True)


async def process_scan_task():
    while True:
        task = await scan_queue.get()

        scan_id = task["scan_id"]
        path = task["path"]

        async with processing_semaphore:
            try:
                await db.scans.update_one(
                    {"_id": scan_id},
                    {"$set": {"status": ScanStatus.processing}},
                )
                await manager.send_message(scan_id, {"status": ScanStatus.processing})

                result = await asyncio.to_thread(predict_scan, path)

                update_fields = {
                    "status": "done",
                    "result": result["result_path"],
                    "confidence": result["confidence"],
                    "tumor_detected": result["tumor_detected"],
                    "result_desc": build_result_desc(result["tumor_detected"]),
                    "updated_at": utc_now(),
                }

                if result.get("heatmap_path"):
                    update_fields["heatmap_path"] = result["heatmap_path"]

                if result.get("heatmap_raw_path"):
                    update_fields["heatmap_raw_path"] = result["heatmap_raw_path"]

                await db.scans.update_one({"_id": scan_id}, {"$set": update_fields})

                await manager.send_message(
                    scan_id,
                    {
                        "status": ScanStatus.done,
                        "result": result["result_path"],
                        "heatmap_path": result.get("heatmap_path"),
                        "tumor_detected": result["tumor_detected"],
                        "confidence": result["confidence"],
                    },
                )

            except Exception as e:
                await db.scans.update_one(
                    {"_id": scan_id},
                    {
                        "$set": {
                            "status": ScanStatus.error,
                            "result_desc": str(e),
                        }
                    },
                )

                await manager.send_message(
                    scan_id,
                    {"status": ScanStatus.error, "message": str(e)},
                )

        scan_queue.task_done()
