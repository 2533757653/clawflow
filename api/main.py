import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from api.logging_config import setup_logging, LOG_DIR
from api.routers import organizations, roles, tasks, dataflows, knowledge, skills, rag, memory, agency, execution, role_suggestions

setup_logging()
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIST_DIR = os.path.join(BASE_DIR, "web", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ClawFlow API starting up...")
    logger.info(f"Log directory: {LOG_DIR}")

    dirs = [
        "data/organizations",
        "data/knowledge",
        "data/skills",
        "data/roles",
        "data/memory",
        "agents",
        "data/rag/documents",
        "data/rag/chunks",
        "data/rag/embeddings",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Ensured directory exists: {d}")

    logger.info(f"ClawFlow API ready — serving at port 8000")
    yield
    logger.info("ClawFlow API shutting down.")


app = FastAPI(
    title="ClawFlow",
    description="Agent 组织动态构建平台",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Request logging middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info(f"→ {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        status = response.status_code
        if status >= 500:
            logger.error(f"← {request.method} {request.url.path} {status} ({elapsed:.1f}ms)")
        elif status >= 400:
            logger.warning(f"← {request.method} {request.url.path} {status} ({elapsed:.1f}ms)")
        else:
            logger.info(f"← {request.method} {request.url.path} {status} ({elapsed:.1f}ms)")
        return response
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(f"✗ {request.method} {request.url.path} 500 ({elapsed:.1f}ms) — {e}")
        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(tasks.router, prefix="/api/v1/organizations", tags=["Tasks"])
app.include_router(dataflows.router, prefix="/api/v1/organizations", tags=["DataFlows"])
app.include_router(knowledge.router, prefix="/api/v1/organizations", tags=["Knowledge"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
app.include_router(agency.router, prefix="/api/v1/agency", tags=["Agency"])
app.include_router(execution.router, prefix="/api/v1", tags=["Execution"])
app.include_router(role_suggestions.router, prefix="/api/v1/roles", tags=["Role Suggestions"])

app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST_DIR, "assets")), name="assets")


@app.get("/")
async def root():
    return FileResponse(os.path.join(WEB_DIST_DIR, "index.html"))


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "message": "ClawFlow API is running"}
