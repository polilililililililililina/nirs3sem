from fastapi import APIRouter
from app.db.mongo import db

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/")
async def list_articles():
    return await db.knowledge.find().to_list(100)


@router.get("/{id}")
async def get_article(id: str):
    return await db.knowledge.find_one({"_id": id})