"""论文匹配分数路由。"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import MatchScoreOut
from ..services.matching import enqueue_compute_matches

router = APIRouter(prefix="/matches", tags=["matches"])




@router.get("/paper/{paper_id}", response_model=list[MatchScoreOut])
def paper_matches(paper_id: int, request: Request, min_score: int = 40):
    """获取某篇论文的所有候选 reviewer（按分数降序，过滤 COI）。"""
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                ms.paper_id, ms.reviewer_id,
                r.name as reviewer_name, r.institution as reviewer_institution,
                ms.total_score, ms.topic_score, ms.method_score, ms.recency_score,
                ms.rationale,
                CASE WHEN c.id IS NOT NULL THEN 1 ELSE 0 END as has_conflict
            FROM match_scores ms
            JOIN reviewers r ON r.id = ms.reviewer_id
            LEFT JOIN conflicts c ON c.paper_id = ms.paper_id
                AND c.reviewer_id = ms.reviewer_id
                AND c.status = 'confirmed'
            WHERE ms.paper_id = ? AND ms.total_score >= ?
            ORDER BY ms.total_score DESC
        """, (paper_id, min_score)).fetchall()
    return [dict(r) for r in rows]


@router.post("/compute/{paper_id}", status_code=202)
def compute_paper_matches(paper_id: int, request: Request, background_tasks: BackgroundTasks):
    """触发单篇论文的匹配计算。"""
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT id, analysis_status FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    if row["analysis_status"] != "analyzed":
        raise HTTPException(400, "论文尚未完成分析")
    background_tasks.add_task(enqueue_compute_matches, paper_id)
    return {"message": "已入队"}


@router.post("/compute-all", status_code=202)
def compute_all_matches(request: Request, background_tasks: BackgroundTasks):
    """触发所有已分析论文的匹配计算。"""
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id FROM papers WHERE analysis_status='analyzed'"
        ).fetchall()
    for r in rows:
        background_tasks.add_task(enqueue_compute_matches, r["id"])
    return {"message": f"已入队 {len(rows)} 篇"}
