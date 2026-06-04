from app.db.mongo import db


async def ensure_indexes() -> None:
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.users.create_index("clinic_id")

    await db.scans.create_index("user_id")
    await db.scans.create_index([("is_guest", 1), ("created_at", 1)])
    await db.scans.create_index("status")
    await db.scans.create_index([("is_guest", 1), ("expires_at", 1)], sparse=True)

    await db.knowledge.create_index("tags")
    await db.knowledge.create_index("pathology_type")
    await db.knowledge.create_index("source")
#    await db.knowledge.create_index("source_url", unique=True, sparse=True)

    await db.clinics.create_index("name")

    await db.doctors_comments.create_index("scan_id")
    await db.expert_conclusions.create_index("scan_id")
