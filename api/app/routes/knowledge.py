import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.core.deps import get_current_user, require_role
from app.core.time import utc_now
from app.db.mongo import db
from app.models.knowledge import (
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
    KnowledgeListResponse,
)
from app.services.knowledge import (
    PATHOLOGY_TAG,
    infer_pathology_type,
    knowledge_list_serializer,
    knowledge_serializer,
)
from app.services.knowledge_import import run_import

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


async def _can_edit_article(user: dict, article: dict) -> bool:
    if user.get("role") == "admin":
        return True

    if user.get("role") == "doctor" and article.get("author_id") == user["_id"]:
        return True

    return False


@router.get("/", response_model=KnowledgeListResponse, summary="Список статей базы знаний")
async def list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    pathology_type: Optional[str] = None,
    search: Optional[str] = None,
):
    query: dict = {}

    if tag:
        query["tags"] = tag

    if pathology_type:
        query["pathology_type"] = pathology_type

    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"body": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * limit
    cursor = db.knowledge.find(query).sort("created_at", -1).skip(skip).limit(limit)
    articles = await cursor.to_list(limit)
    total = await db.knowledge.count_documents(query)

    return {
        "items": knowledge_list_serializer(articles),
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/suggest", summary="Рекомендуемые статьи по результату анализа")
async def suggest_articles(
    scan_id: str,
    limit: int = Query(5, ge=1, le=20),
):
    scan = await db.scans.find_one({"_id": scan_id})

    if not scan:
        raise HTTPException(404, "Анализ не найден")

    if scan.get("status") != "done":
        raise HTTPException(400, "Анализ ещё не завершён")

    tag = PATHOLOGY_TAG if scan.get("tumor_detected") else "МРТ"
    query = {"tags": tag}

    articles = await db.knowledge.find(query).sort("created_at", -1).limit(limit).to_list(limit)

    return {"items": knowledge_list_serializer(articles)}


@router.post("/import", summary="Импорт статей с neurosurgeru.org")
async def import_articles(
    background_tasks: BackgroundTasks,
    max_articles: int = Query(30, ge=1, le=100),
    run_in_background: bool = True,
    user=Depends(require_role("admin")),
):
    if run_in_background:
        background_tasks.add_task(run_import, max_articles)
        return {"status": "started", "max_articles": max_articles}

    result = await run_import(max_articles=max_articles)
    return {"status": "completed", **result}


@router.get("/{article_id}", summary="Получить статью по ID")
async def get_article(article_id: str):
    article = await db.knowledge.find_one({"_id": article_id})

    if not article:
        raise HTTPException(404, "Статья не найдена")

    return knowledge_serializer(article)


@router.post("/", summary="Создать статью")
async def create_article(
    data: KnowledgeArticleCreate,
    user=Depends(require_role("doctor", "admin")),
):
    title = data.title.strip()
    body = data.body.strip()

    if not title or not body:
        raise HTTPException(400, "Заголовок и текст обязательны")

    tags = data.tags or []
    pathology_type = data.pathology_type or infer_pathology_type(tags)
    now = utc_now()

    doc = {
        "_id": str(uuid.uuid4()),
        "title": title,
        "body": body,
        "tags": tags,
        "pathology_type": pathology_type,
        "source": "manual",
        "source_url": None,
        "is_external": False,
        "author_id": user["_id"],
        "created_at": now,
        "updated_at": now,
    }

    await db.knowledge.insert_one(doc)

    return knowledge_serializer(doc)


@router.put("/{article_id}", summary="Обновить статью")
async def update_article(
    article_id: str,
    data: KnowledgeArticleUpdate,
    user=Depends(require_role("doctor", "admin")),
):
    article = await db.knowledge.find_one({"_id": article_id})

    if not article:
        raise HTTPException(404, "Статья не найдена")

    if not await _can_edit_article(user, article):
        raise HTTPException(403, "Недостаточно прав для редактирования")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "Нет данных для обновления")

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()

    if "body" in update_data:
        update_data["body"] = update_data["body"].strip()

    if "tags" in update_data and "pathology_type" not in update_data:
        update_data["pathology_type"] = infer_pathology_type(update_data["tags"])

    update_data["updated_at"] = utc_now()

    await db.knowledge.update_one({"_id": article_id}, {"$set": update_data})

    updated = await db.knowledge.find_one({"_id": article_id})

    return knowledge_serializer(updated)


@router.delete("/{article_id}", summary="Удалить статью")
async def delete_article(
    article_id: str,
    user=Depends(require_role("doctor", "admin")),
):
    article = await db.knowledge.find_one({"_id": article_id})

    if not article:
        raise HTTPException(404, "Статья не найдена")

    if not await _can_edit_article(user, article):
        raise HTTPException(403, "Недостаточно прав для удаления")

    await db.knowledge.delete_one({"_id": article_id})

    return {"ok": True}
