from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from api.routers import organizations, roles, tasks, dataflows, knowledge, skills, systems, generator, rag


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIST_DIR = os.path.join(BASE_DIR, "web", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data/organizations", exist_ok=True)
    os.makedirs("data/knowledge", exist_ok=True)
    os.makedirs("data/skills", exist_ok=True)
    os.makedirs("openclaw_workspace", exist_ok=True)
    os.makedirs("data/organizations/systems", exist_ok=True)
    os.makedirs("data/rag/documents", exist_ok=True)
    os.makedirs("data/rag/chunks", exist_ok=True)
    os.makedirs("data/rag/embeddings", exist_ok=True)
    yield


app = FastAPI(
    title="ClawFlow",
    description="Agent 组织动态构建平台",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(roles.router, prefix="/api/v1/organizations", tags=["Roles"])
app.include_router(tasks.router, prefix="/api/v1/organizations", tags=["Tasks"])
app.include_router(dataflows.router, prefix="/api/v1/organizations", tags=["DataFlows"])
app.include_router(knowledge.router, prefix="/api/v1/organizations", tags=["Knowledge"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(systems.router, prefix="/api/v1/organizations", tags=["Systems"])
app.include_router(generator.router, prefix="/api/v1/generator", tags=["Generator"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])

app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST_DIR, "assets")), name="assets")


@app.get("/")
async def root():
    return FileResponse(os.path.join(WEB_DIST_DIR, "index.html"))


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "message": "ClawFlow API is running"}
