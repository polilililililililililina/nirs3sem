import asyncio
import re
import time
import uuid
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from app.core.time import utc_now
from app.db.mongo import db
from app.services.knowledge import DEFAULT_TAGS, PATHOLOGY_TAG, infer_tags_from_text

BASE_URL = "https://neurosurgeru.org"
REQUEST_DELAY_SEC = 1.5
REQUEST_TIMEOUT_SEC = 20
USER_AGENT = "MRI-Analyzer-KnowledgeBot/1.0 (+https://mri-analyzer.cloudpub.ru)"

SECTION_PATHS = [
    "/",
    "/articles/",
    "/blog/",
    "/news/",
    "/publications/",
    "/library/",
    "/biblioteka/",
    "/statyi/",
]

ARTICLE_PATH_HINTS = (
    "/article/",
    "/articles/",
    "/blog/",
    "/news/",
    "/post/",
    "/statya/",
    "/publication/",
)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="", query="")
    return normalized.geturl().rstrip("/")


def _is_article_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in ("neurosurgeru.org", "www.neurosurgeru.org"):
        return False

    path = parsed.path.lower()
    if path in ("/", ""):
        return False

    if any(hint in path for hint in ARTICLE_PATH_HINTS):
        return True

    return bool(re.search(r"/\d{4}/\d{2}/", path))


def _load_robots_parser(session: requests.Session) -> RobotFileParser:
    parser = RobotFileParser()
    robots_url = urljoin(BASE_URL, "/robots.txt")

    try:
        response = session.get(robots_url, timeout=REQUEST_TIMEOUT_SEC)
        if response.ok:
            parser.parse(response.text.splitlines())
        else:
            parser.parse(["User-agent: *", "Allow: /"])
    except requests.RequestException:
        parser.parse(["User-agent: *", "Allow: /"])

    return parser


def _can_fetch(parser: RobotFileParser, url: str) -> bool:
    return parser.can_fetch(USER_AGENT, url)


def _fetch_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    return response.text


def _extract_links(soup: BeautifulSoup, page_url: str) -> set[str]:
    links: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue

        absolute = _normalize_url(urljoin(page_url, href))
        if _is_article_url(absolute):
            links.add(absolute)

    return links


def _extract_article(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title_node = (
        soup.find("h1")
        or soup.select_one(".entry-title")
        or soup.select_one(".post-title")
        or soup.select_one("article h1")
    )
    title = title_node.get_text(" ", strip=True) if title_node else ""

    content_node = (
        soup.select_one("article .entry-content")
        or soup.select_one(".entry-content")
        or soup.select_one("article .post-content")
        or soup.select_one(".post-content")
        or soup.select_one("article")
        or soup.select_one("main")
    )

    if not content_node:
        return None

    for tag in content_node.find_all(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()

    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in content_node.find_all(["p", "li", "h2", "h3"])
        if paragraph.get_text(" ", strip=True)
    ]

    body = "\n\n".join(paragraphs)
    if not title or len(body) < 120:
        return None

    tags = infer_tags_from_text(f"{title}\n{body}")
    pathology_type = PATHOLOGY_TAG if PATHOLOGY_TAG in tags else None

    return {
        "title": title,
        "body": body,
        "tags": tags,
        "pathology_type": pathology_type,
        "source": "external",
        "source_url": url,
        "is_external": True,
    }


def _crawl_articles_sync(existing_urls: set[str], max_articles: int) -> dict:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    robots = _load_robots_parser(session)
    discovered: set[str] = set()
    articles: list[dict] = []
    skipped = 0
    errors: list[str] = []

    for section_path in SECTION_PATHS:
        section_url = _normalize_url(urljoin(BASE_URL, section_path))

        if not _can_fetch(robots, section_url):
            continue

        try:
            html = _fetch_html(session, section_url)
            soup = BeautifulSoup(html, "html.parser")
            discovered.update(_extract_links(soup, section_url))
        except requests.RequestException as exc:
            errors.append(f"{section_url}: {exc}")
        finally:
            time.sleep(REQUEST_DELAY_SEC)

    for url in sorted(discovered):
        if len(articles) >= max_articles:
            break

        if url in existing_urls:
            skipped += 1
            continue

        if not _can_fetch(robots, url):
            skipped += 1
            continue

        try:
            html = _fetch_html(session, url)
            soup = BeautifulSoup(html, "html.parser")
            article = _extract_article(soup, url)

            if not article:
                skipped += 1
                continue

            articles.append(article)
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
        finally:
            time.sleep(REQUEST_DELAY_SEC)

    return {
        "articles": articles,
        "skipped": skipped,
        "discovered": len(discovered),
        "errors": errors[:20],
    }


async def run_import(max_articles: int = 30) -> dict:
    existing = await db.knowledge.find({"source_url": {"$exists": True, "$ne": None}}, {"source_url": 1}).to_list(None)
    existing_urls = {_normalize_url(item["source_url"]) for item in existing if item.get("source_url")}

    crawl_result = await asyncio.to_thread(_crawl_articles_sync, existing_urls, max_articles)

    imported = 0
    now = utc_now()

    for article in crawl_result["articles"]:
        source_url = article.get("source_url")
        if source_url and await db.knowledge.find_one({"source_url": source_url}):
            crawl_result["skipped"] += 1
            continue

        doc = {
            "_id": str(uuid.uuid4()),
            "title": article["title"],
            "body": article["body"],
            "tags": article.get("tags") or DEFAULT_TAGS.copy(),
            "pathology_type": article.get("pathology_type"),
            "source": article.get("source", "external"),
            "source_url": source_url,
            "is_external": article.get("is_external", True),
            "author_id": None,
            "created_at": now,
            "updated_at": now,
        }
        await db.knowledge.insert_one(doc)
        imported += 1

    return {
        "imported": imported,
        "skipped": crawl_result["skipped"],
        "discovered": crawl_result["discovered"],
        "errors": crawl_result["errors"],
    }
