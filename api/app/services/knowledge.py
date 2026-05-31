PATHOLOGY_TAG = "опухоль головного мозга"
DEFAULT_TAGS = ["МРТ", "нейрохирургия", PATHOLOGY_TAG]


def knowledge_serializer(article: dict) -> dict:
    return {
        "_id": article["_id"],
        "title": article["title"],
        "body": article["body"],
        "tags": article.get("tags", []),
        "pathology_type": article.get("pathology_type"),
        "source": article.get("source", "manual"),
        "source_url": article.get("source_url"),
        "is_external": article.get("is_external", False),
        "author_id": article.get("author_id"),
        "created_at": article["created_at"],
        "updated_at": article.get("updated_at"),
    }


def knowledge_list_serializer(articles: list) -> list:
    return [knowledge_serializer(article) for article in articles]


def infer_pathology_type(tags: list[str]) -> str | None:
    if PATHOLOGY_TAG in tags:
        return PATHOLOGY_TAG
    return None


def infer_tags_from_text(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []

    if any(word in lowered for word in ("мрт", "mri", "магнитно-резонанс")):
        tags.append("МРТ")

    if any(word in lowered for word in ("нейрохирург", "нейрохирургия", "операц")):
        tags.append("нейрохирургия")

    if any(
        word in lowered
        for word in (
            "опухол",
            "глиом",
            "менингиом",
            "метастаз",
            "новообразован",
            "внутричерепн",
        )
    ):
        tags.append(PATHOLOGY_TAG)

    return tags or ["МРТ"]
