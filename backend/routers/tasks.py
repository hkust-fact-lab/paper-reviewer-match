"""异步任务状态查询（仅管理员）。"""
from fastapi import APIRouter, HTTPException, Request
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(request: Request, limit: int = 20):
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM async_tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, request: Request):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM async_tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return dict(row)
