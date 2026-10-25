"""分配路由：配置、运行、调整、导出。"""
import csv, io, json
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import AssignmentConfig, AssignmentOut
from ..services.assignment import run_assignment

router = APIRouter(prefix="/assignment", tags=["assignment"])




@router.get("/config", response_model=AssignmentConfig)
def get_config(request: Request):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM assignment_config WHERE id=1").fetchone()
    d = dict(row)
    d["coi_same_institution"] = bool(d["coi_same_institution"])
    return d


@router.put("/config", response_model=AssignmentConfig)
@router.patch("/config", response_model=AssignmentConfig)
def update_config(body: AssignmentConfig, request: Request):
    require_admin(request)
    with get_conn() as conn:
        conn.execute("""
            UPDATE assignment_config SET
                reviewers_per_paper=?, max_papers_per_reviewer=?,
                min_papers_per_reviewer=?, min_score_threshold=?,
                coi_same_institution=?, coi_coauthor_years=?,
                updated_at=datetime('now')
            WHERE id=1
        """, (
            body.reviewers_per_paper, body.max_papers_per_reviewer,
            body.min_papers_per_reviewer, body.min_score_threshold,
            int(body.coi_same_institution), body.coi_coauthor_years,
        ))
    return body


@router.post("/run", status_code=202)
def trigger_assignment(request: Request, background_tasks: BackgroundTasks):
    """触发分配算法（贪心 + 约束满足）。"""
    require_admin(request)
    background_tasks.add_task(run_assignment)
    return {"message": "分配任务已启动"}


@router.get("", response_model=list[AssignmentOut])
def list_assignments(request: Request):
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT a.*, p.title as paper_title, r.name as reviewer_name
            FROM assignments a
            JOIN papers p ON p.id = a.paper_id
            JOIN reviewers r ON r.id = a.reviewer_id
            ORDER BY a.paper_id, a.reviewer_id
        """).fetchall()
    return [dict(r) for r in rows]


@router.post("/{paper_id}/add/{reviewer_id}", status_code=201)
def add_assignment(paper_id: int, reviewer_id: int, request: Request):
    """手动添加分配。"""
    user = require_admin(request)
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO assignments(paper_id, reviewer_id, source, assigned_by) VALUES(?,?,'manual',?)",
                (paper_id, reviewer_id, user["email"]),
            )
        except Exception:
            raise HTTPException(409, "已存在该分配")
    return {"message": "已添加"}


@router.delete("/{paper_id}/remove/{reviewer_id}")
def remove_assignment(paper_id: int, reviewer_id: int, request: Request):
    """移除分配。"""
    require_admin(request)
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM assignments WHERE paper_id=? AND reviewer_id=?",
            (paper_id, reviewer_id),
        )
    return {"message": "已移除"}


@router.get("/export")
def export_csv(request: Request):
    """导出分配结果为 CSV。"""
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.hotcrp_id, p.title, r.email as reviewer_email, r.name as reviewer_name
            FROM assignments a
            JOIN papers p ON p.id = a.paper_id
            JOIN reviewers r ON r.id = a.reviewer_id
            ORDER BY p.id, r.name
        """).fetchall()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["paper_id", "paper_title", "reviewer_email", "reviewer_name"])
    for r in rows:
        w.writerow([r["hotcrp_id"] or "", r["title"], r["reviewer_email"], r["reviewer_name"]])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assignment.csv"},
    )
