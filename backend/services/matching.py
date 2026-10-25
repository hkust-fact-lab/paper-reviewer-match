"""
匹配分数计算 Service。
三维加权：话题重叠(50%) + 方法相关(30%) + 时近度(20%)，0-100 分。
"""
import json
from datetime import datetime
from ..models.db import get_conn


def enqueue_compute_matches(paper_id: int) -> None:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO async_tasks(type, ref_id, status) VALUES('compute_matches',?,'running')",
            (paper_id,),
        )
        task_id = cur.lastrowid

    try:
        _compute(paper_id)
        with get_conn() as conn:
            conn.execute(
                "UPDATE async_tasks SET status='done', progress=100, finished_at=datetime('now') WHERE id=?",
                (task_id,),
            )
    except Exception as e:
        with get_conn() as conn:
            conn.execute(
                "UPDATE async_tasks SET status='error', error_message=?, finished_at=datetime('now') WHERE id=?",
                (str(e), task_id),
            )


def _compute(paper_id: int) -> None:
    with get_conn() as conn:
        paper = conn.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
        reviewers = conn.execute(
            "SELECT * FROM reviewers WHERE fetch_status='done'"
        ).fetchall()

    if not paper:
        raise ValueError(f"Paper {paper_id} not found")

    if paper["analysis_status"] != "analyzed":
        raise ValueError(f"Paper {paper_id} not yet analyzed (status={paper['analysis_status']})")

    def safe_json(val: str | None) -> list:
        if not val:
            return []
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []

    paper_topics  = set(safe_json(paper["topics"]))
    paper_methods = set(safe_json(paper["methods"]))
    current_year  = datetime.now().year

    for rev in reviewers:
        rev_topics = set(safe_json(rev["expertise_topics"]))
        rev_pubs   = safe_json(rev["publications"])

        # ── 话题重叠 (50%) ───────────────────────────────
        if paper_topics and rev_topics:
            topic_score = int(
                100 * len(paper_topics & rev_topics) / len(paper_topics | rev_topics)
            )
        else:
            topic_score = 0

        # ── 方法相关 (30%) ───────────────────────────────
        # 简化：检查 reviewer 论文 title/venue 中是否含 paper_methods 关键词
        method_hits = 0
        for pub in rev_pubs:
            text = f"{pub.get('title','')} {pub.get('venue','')}".lower()
            if any(m.lower() in text for m in paper_methods):
                method_hits += 1
        method_score = min(100, method_hits * 25)

        # ── 时近度 (20%) ─────────────────────────────────
        # 近 3 年有相关发表 → 100，4-5 年 → 60，更早 → 20
        relevant_years = [
            pub.get("year", 0) for pub in rev_pubs
            if any(t.lower() in pub.get("title", "").lower() for t in paper_topics)
        ]
        if relevant_years:
            most_recent = max(relevant_years)
            gap = current_year - most_recent
            recency_score = 100 if gap <= 3 else (60 if gap <= 5 else 20)
        else:
            recency_score = 0

        # ── 加权总分 ─────────────────────────────────────
        total = int(topic_score * 0.5 + method_score * 0.3 + recency_score * 0.2)

        # ── 生成理由（TODO: 换成 LLM 生成）────────────────
        rationale = _build_rationale(rev["name"], topic_score, method_score, recency_score, rev_pubs)

        with get_conn() as conn:
            conn.execute("""
                INSERT INTO match_scores(paper_id, reviewer_id, total_score, topic_score, method_score, recency_score, rationale)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(paper_id, reviewer_id) DO UPDATE SET
                    total_score=excluded.total_score,
                    topic_score=excluded.topic_score,
                    method_score=excluded.method_score,
                    recency_score=excluded.recency_score,
                    rationale=excluded.rationale,
                    computed_at=datetime('now')
            """, (paper_id, rev["id"], total, topic_score, method_score, recency_score, rationale))


def _build_rationale(name: str, topic: int, method: int, recency: int, pubs: list) -> str:
    recent = [p for p in pubs if p.get("year", 0) >= datetime.now().year - 3]
    lines = []
    if topic >= 70:
        lines.append("研究方向高度吻合")
    elif topic >= 40:
        lines.append("研究方向部分重叠")
    if recent:
        lines.append(f"近 3 年有 {len(recent)} 篇相关发表（含 {recent[0].get('venue','')}）")
    if method >= 50:
        lines.append("技术方法相近")
    return "；".join(lines) if lines else "相关性一般"
