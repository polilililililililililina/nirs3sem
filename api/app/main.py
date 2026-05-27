from fastapi import FastAPI
from app.routes import auth, users, scans, knowledge
from fastapi.middleware.cors import CORSMiddleware
from app.core.limiter import limiter
from contextlib import asynccontextmanager
from app.services.worker import process_scan_task
import asyncio
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    workers = []

    for _ in range(3):
        task = asyncio.create_task(process_scan_task())
        workers.append(task)

    yield

    for worker in workers:
        worker.cancel()


app = FastAPI(lifespan=lifespan)

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

app.state.limiter = limiter

