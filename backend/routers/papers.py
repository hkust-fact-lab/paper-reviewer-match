"""论文管理路由。"""
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request
from .auth import require_admin
from ..models.db import get_conn
from ..models.schemas import PaperOut, PaperCreate
from ..services.analysis import enqueue_analyze_paper

router = APIRouter(prefix="/papers", tags=["papers"])




def _row_to_paper(row) -> dict:
    d = dict(row)
    for f in ("authors", "topics", "methods", "required_expertise"):
        if d.get(f):
            d[f] = json.loads(d[f])
    return d


@router.get("", response_model=list[PaperOut])
def list_papers(request: Request):
    require_admin(request)
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM papers ORDER BY id").fetchall()
    return [_row_to_paper(r) for r in rows]


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, request: Request):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return _row_to_paper(row)


@router.post("", response_model=PaperOut, status_code=201)
def create_paper(body: PaperCreate, request: Request, background_tasks: BackgroundTasks):
    require_admin(request)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO papers(hotcrp_id, title, abstract, authors) VALUES(?,?,?,?)",
            (body.hotcrp_id, body.title, body.abstract,
             json.dumps(body.authors) if body.authors else None),
        )
        paper_id = cur.lastrowid
        row = conn.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    background_tasks.add_task(enqueue_analyze_paper, paper_id)
    return _row_to_paper(row)


@router.post("/upload", status_code=202)
async def upload_papers(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """批量上传 PDF，每个文件创建一条论文记录并入队分析。"""
    require_admin(request)
    import os
    from pathlib import Path
    upload_dir = Path(__file__).parent.parent.parent / "data" / "pdfs"
    upload_dir.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    for f in files:
        # 文件类型校验
        fname = f.filename or ""
        if not fname.lower().endswith(".pdf"):
            skipped.append(fname)
            continue
        # 净化文件名，防路径遍历
        from pathlib import PurePosixPath
        safe_name = PurePosixPath(fname).name
        pdf_path = upload_dir / safe_name
        # 同名文件加序号避免覆盖
        stem = pdf_path.stem
        suffix = pdf_path.suffix
        counter = 1
        while pdf_path.exists():
            pdf_path = upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        content = await f.read()
        pdf_path.write_bytes(content)
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO papers(title, pdf_path, analysis_status) VALUES(?,?,'pending')",
                (safe_name, str(pdf_path)),
            )
            paper_id = cur.lastrowid
        background_tasks.add_task(enqueue_analyze_paper, paper_id)
        created.append(paper_id)

    msg = f"{len(created)} 篇论文已入队分析"
    if skipped:
        msg += f"，跳过 {len(skipped)} 个非 PDF 文件"
    return {"created": created, "skipped": skipped, "message": msg}


@router.post("/{paper_id}/retry-analysis", status_code=202)
def retry_analysis(paper_id: int, request: Request, background_tasks: BackgroundTasks):
    require_admin(request)
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM papers WHERE id=?", (paper_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        conn.execute(
            "UPDATE papers SET analysis_status='pending', analysis_error=NULL WHERE id=?",
            (paper_id,),
        )
    background_tasks.add_task(enqueue_analyze_paper, paper_id)
    return {"message": "已重新入队"}
