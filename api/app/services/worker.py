import asyncio
import shutil
from app.services.queue import scan_queue, processing_semaphore
from app.db.mongo import db
from app.models.scan import ScanStatus
from app.sockets.manager import manager
from app.core.config import OUTPUT_DIR
import os
from datetime import datetime
from app.ai.services.predict import predict_scan

os.makedirs(OUTPUT_DIR, exist_ok=True)

async def process_scan_task():

    while True:
        task = await scan_queue.get()

        scan_id = task["scan_id"]
        path = task["path"]

        async with processing_semaphore:
            try:
                await db.scans.update_one({ "_id": scan_id },{ "$set": { "status": ScanStatus.processing }})
                await manager.send_message(scan_id, {"status": ScanStatus.processing})

                result = predict_scan(path)

                await db.scans.update_one(
                    {"_id": scan_id},
                    {
                        "$set": {
                            "status": "done",
                            "result": result["result_path"],
                            "confidence": result["confidence"],
                            "tumor_detected": result["tumor_detected"],
                            "result_desc": "Обработка завершена",
                            "updated_at": datetime.utcnow(),
                        }
                    }
                )


                # await asyncio.to_thread(
                #     shutil.copy,
                #     path,
                #     #result_path
                #     result
                # )

                await manager.send_message(scan_id, {"status": ScanStatus.done, "result": result["result_path"]})

            except Exception as e:
                await db.scans.update_one(
                    {"_id": scan_id},
                    {
                        "$set": {
                            "status":
                                ScanStatus.error,
                            "result_desc":
                                str(e)
                        }
                    }
                )

                await manager.send_message(scan_id, {"status": ScanStatus.error, "message": str(e)})

        scan_queue.task_done()