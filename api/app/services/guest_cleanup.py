from app.core.time import utc_now
from app.db.mongo import db
from app.services.files import delete_scan_files
from app.sockets.manager import manager


async def cleanup_expired_guest_scans() -> int:
    now = utc_now()
    expired_scans = await db.scans.find(
        {
            "is_guest": True,
            "expires_at": {"$lt": now},
        }
    ).to_list(None)

    removed = 0

    for scan in expired_scans:
        scan_id = scan["_id"]

        try:
            await manager.send_message(
                scan_id,
                {
                    "status": "expired",
                    "message": "Гостевой результат удалён. Войдите, чтобы сохранять анализы.",
                },
            )
        except Exception:
            pass

        delete_scan_files(scan)
        await db.scans.delete_one({"_id": scan_id})
        manager.disconnect(scan_id)
        removed += 1

    return removed
