"""利益冲突路由（管理员管理，无需 reviewer 登录）。"""
from fastapi import APIRouter, HTTPException, Request
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import ConflictOut, ConflictCreate

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("", response_model=list[ConflictOut])
def list_conflicts(request: Request, status: str = ""):
    require_admin(request)
    with get_conn() as conn:
        if status:
            rows = conn.execute("""
                SELECT c.*, p.title as paper_title, r.name as reviewer_name
                FROM conflicts c
                JOIN papers p ON p.id = c.paper_id
                JOIN reviewers r ON r.id = c.reviewer_id
                WHERE c.status = ?
                ORDER BY c.created_at DESC
            """, (status,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.*, p.title as paper_title, r.name as reviewer_name
                FROM conflicts c
                JOIN papers p ON p.id = c.paper_id
                JOIN reviewers r ON r.id = c.reviewer_id
                ORDER BY c.created_at DESC
            """).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=ConflictOut, status_code=201)
def create_conflict(body: ConflictCreate, request: Request):
    """管理员手动添加 COI。"""
    user = require_admin(request)
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO conflicts(paper_id, reviewer_id, source, detail, reported_by, status)
                VALUES(?,?,?,?,?,'confirmed')
            """, (body.paper_id, body.reviewer_id, body.source, body.detail, user["email"]))
            row = conn.execute("""
                SELECT c.*, p.title as paper_title, r.name as reviewer_name
                FROM conflicts c
                JOIN papers p ON p.id = c.paper_id
                JOIN reviewers r ON r.id = c.reviewer_id
                WHERE c.paper_id=? AND c.reviewer_id=? AND c.source=?
            """, (body.paper_id, body.reviewer_id, body.source)).fetchone()
        except Exception:
            raise HTTPException(409, "已存在该 COI 记录")
    return dict(row)


@router.patch("/{conflict_id}/confirm")
def confirm_conflict(conflict_id: int, request: Request):
    user = require_admin(request)
    with get_conn() as conn:
        conn.execute(
            "UPDATE conflicts SET status='confirmed', confirmed_by=? WHERE id=?",
            (user["email"], conflict_id),
        )
    return {"message": "已确认"}


@router.patch("/{conflict_id}/reject")
def reject_conflict(conflict_id: int, request: Request):
    user = require_admin(request)
    with get_conn() as conn:
        conn.execute(
            "UPDATE conflicts SET status='rejected', confirmed_by=? WHERE id=?",
            (user["email"], conflict_id),
        )
    return {"message": "已驳回"}


@router.delete("/{conflict_id}")
def delete_conflict(conflict_id: int, request: Request):
    require_admin(request)
    with get_conn() as conn:
        conn.execute("DELETE FROM conflicts WHERE id=?", (conflict_id,))
    return {"message": "已删除"}
