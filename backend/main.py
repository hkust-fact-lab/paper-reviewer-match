"""FastAPI 主入口。"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .models.db import init_db
from .routers import auth, papers, reviewers, matches, assignment, conflicts, tasks

app = FastAPI(title="ReviewMatch API", version="0.1.0")

# 初始化数据库
@app.on_event("startup")
def startup():
    init_db()

# API 路由
app.include_router(auth.router,       prefix="/api")
app.include_router(papers.router,     prefix="/api")
app.include_router(reviewers.router,  prefix="/api")
app.include_router(matches.router,    prefix="/api")
app.include_router(assignment.router, prefix="/api")
app.include_router(conflicts.router,  prefix="/api")
app.include_router(tasks.router,      prefix="/api")

# 前端静态文件（生产）
DIST = Path(__file__).parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(DIST / "index.html")
