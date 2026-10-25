"""Reviewer 管理路由。"""
import json, csv, io
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import ReviewerOut, ReviewerCreate
from ..services.scholar import enqueue_fetch_reviewer

router = APIRouter(prefix="/reviewers", tags=["reviewers"])




def _row_to_reviewer(row) -> dict:
    d = dict(row)
    for f in ("expertise_topics", "publications"):
        if d.get(f):
            d[f] = json.loads(d[f])
    d["scholar_confirmed"] = bool(d.get("scholar_confirmed"))
    return d


@router.get("", response_model=list[ReviewerOut])
def list_reviewers(request: Request):
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM reviewers ORDER BY name").fetchall()
    return [_row_to_reviewer(r) for r in rows]


@router.get("/{reviewer_id}", response_model=ReviewerOut)
def get_reviewer(reviewer_id: int, request: Request):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM reviewers WHERE id=?", (reviewer_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return _row_to_reviewer(row)


@router.post("", response_model=ReviewerOut, status_code=201)
def create_reviewer(body: ReviewerCreate, request: Request, background_tasks: BackgroundTasks):
    require_admin(request)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO reviewers(name, email, institution, scholar_url, hotcrp_user_id) VALUES(?,?,?,?,?)",
            (body.name, body.email, body.institution, body.scholar_url, body.hotcrp_user_id),
        )
        rid = cur.lastrowid
        row = conn.execute("SELECT * FROM reviewers WHERE id=?", (rid,)).fetchone()
    if body.scholar_url:
        background_tasks.add_task(enqueue_fetch_reviewer, rid)
    return _row_to_reviewer(row)


@router.post("/upload-csv", status_code=202)
async def upload_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """上传 CSV（列：name, email, institution, scholar_url），批量导入并入队抓取。"""
    require_admin(request)
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "请上传 CSV 文件")
    content = await file.read()
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except Exception:
        raise HTTPException(400, "CSV 文件编码错误，请使用 UTF-8")
    created = []
    skipped_emails: list[str] = []
    for row in reader:
        name  = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        if not name or not email:
            continue
        institution = (row.get("institution") or "").strip() or None
        scholar_url = (row.get("scholar_url") or "").strip() or None
        with get_conn() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO reviewers(name, email, institution, scholar_url) VALUES(?,?,?,?)",
                    (name, email, institution, scholar_url),
                )
                rid = cur.lastrowid
                created.append(rid)
                if scholar_url:
                    background_tasks.add_task(enqueue_fetch_reviewer, rid)
            except Exception as e:
                err_msg = str(e)
                if "UNIQUE" in err_msg or "unique" in err_msg:
                    skipped_emails.append(email)  # 邮箱重复，跳过
                else:
                    raise  # 其他错误向上抛
    return {"created": created, "skipped": skipped_emails, "count": len(created)}


@router.patch("/{reviewer_id}/confirm-scholar")
def confirm_scholar(reviewer_id: int, scholar_url: str, request: Request, background_tasks: BackgroundTasks):
    """管理员确认同名 reviewer 的正确 Scholar profile。"""
    require_admin(request)
    with get_conn() as conn:
        conn.execute(
            "UPDATE reviewers SET scholar_url=?, scholar_confirmed=1, fetch_status='pending' WHERE id=?",
            (scholar_url, reviewer_id),
        )
    background_tasks.add_task(enqueue_fetch_reviewer, reviewer_id)
    return {"message": "已确认，重新入队抓取"}


@router.get("/{reviewer_id}/matches")
def reviewer_matches(reviewer_id: int, request: Request):
    """该 reviewer 在所有论文中的匹配分数。"""
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT ms.*, p.title as paper_title
            FROM match_scores ms
            JOIN papers p ON p.id = ms.paper_id
            WHERE ms.reviewer_id = ?
            ORDER BY ms.total_score DESC
        """, (reviewer_id,)).fetchall()
    return [dict(r) for r in rows]


@router.post("/{reviewer_id}/retry-fetch", status_code=202)
def retry_fetch(reviewer_id: int, request: Request, background_tasks: BackgroundTasks):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM reviewers WHERE id=?", (reviewer_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        conn.execute(
            "UPDATE reviewers SET fetch_status='pending', fetch_error=NULL WHERE id=?",
            (reviewer_id,),
        )
    background_tasks.add_task(enqueue_fetch_reviewer, reviewer_id)
    return {"message": "已重新入队"}
