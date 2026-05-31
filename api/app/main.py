from contextlib import asynccontextmanager

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routes import auth, users, scans, knowledge, clinics, admin
from app.core.limiter import limiter
from app.core.openapi import OPENAPI_TAGS, configure_openapi
from app.services.worker import process_scan_task
from app.services.guest_cleanup import cleanup_expired_guest_scans
from app.db.indexes import ensure_indexes

API_DESCRIPTION = """
REST API сервиса **MRI Analyzer** — загрузка и анализ МРТ-снимков,
история исследований, база знаний и администрирование.

## Аутентификация

Большинство защищённых эндпоинтов требуют JWT access token в заголовке:

`Authorization: Bearer <access_token>`

Токен выдаётся через `POST /auth/login` и обновляется через `POST /auth/refresh`.

## Роли

- **guest** — без токена (гостевые загрузки, база знаний)
- **user** — обычный пользователь
- **doctor** — врач клиники
- **admin** — администратор
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()

    workers = []
    background_tasks = []

    for _ in range(3):
        task = asyncio.create_task(process_scan_task())
        workers.append(task)

    async def daily_knowledge_import():
        while True:
            await asyncio.sleep(24 * 3600)
            try:
                from app.services.knowledge_import import run_import

                await run_import(max_articles=30)
            except Exception:
                pass

    async def guest_cleanup_loop():
        while True:
            await asyncio.sleep(300)
            try:
                await cleanup_expired_guest_scans()
            except Exception:
                pass

    background_tasks.append(asyncio.create_task(daily_knowledge_import()))
    background_tasks.append(asyncio.create_task(guest_cleanup_loop()))

    yield

    for worker in workers:
        worker.cancel()

    for task in background_tasks:
        task.cancel()


app = FastAPI(
    title="MRI Analyzer API",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

configure_openapi(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://mri-analyzer.cloudpub.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(knowledge.router)
app.include_router(clinics.router)
app.include_router(admin.router)
