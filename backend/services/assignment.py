"""
分配算法 Service。
贪心 + 约束满足：在满足每篇篇数、每人上下限、COI 排除的前提下，最大化总匹配分数。
"""
import json
from ..models.db import get_conn


def run_assignment() -> None:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO async_tasks(type, status) VALUES('run_assignment','running')"
        )
        task_id = cur.lastrowid

    try:
        result = _assign()
        with get_conn() as conn:
            conn.execute(
                "UPDATE async_tasks SET status='done', progress=100, result_summary=?, finished_at=datetime('now') WHERE id=?",
                (json.dumps(result), task_id),
            )
    except Exception as e:
        with get_conn() as conn:
            conn.execute(
                "UPDATE async_tasks SET status='error', error_message=?, finished_at=datetime('now') WHERE id=?",
                (str(e), task_id),
            )


def _assign() -> dict:
    with get_conn() as conn:
        cfg = conn.execute("SELECT * FROM assignment_config WHERE id=1").fetchone()
        papers = conn.execute(
            "SELECT id FROM papers WHERE analysis_status='analyzed'"
        ).fetchall()
        reviewers = conn.execute(
            "SELECT id, load_min, load_max FROM reviewers WHERE fetch_status='done'"
        ).fetchall()
        # 已确认的 COI（排除用）
        conflicts = conn.execute(
            "SELECT paper_id, reviewer_id FROM conflicts WHERE status='confirmed'"
        ).fetchall()
        # 匹配分数
        scores = conn.execute(
            "SELECT paper_id, reviewer_id, total_score FROM match_scores WHERE total_score >= ?",
            (cfg["min_score_threshold"],),
        ).fetchall()

    conflict_set = {(c["paper_id"], c["reviewer_id"]) for c in conflicts}
    per_paper    = cfg["reviewers_per_paper"]
    max_load     = cfg["max_papers_per_reviewer"]
    min_load     = cfg["min_papers_per_reviewer"]

    # 按论文分组，过滤 COI，按分数降序排列候选
    paper_candidates: dict[int, list[tuple[int, int]]] = {}
    for s in scores:
        pid, rid, score = s["paper_id"], s["reviewer_id"], s["total_score"]
        if (pid, rid) not in conflict_set:
            paper_candidates.setdefault(pid, []).append((score, rid))
    for pid in paper_candidates:
        paper_candidates[pid].sort(reverse=True)

    load: dict[int, int] = {r["id"]: 0 for r in reviewers}
    assignments: list[tuple[int, int]] = []
    infeasible: list[int] = []

    # 贪心：先处理候选少的论文（避免难论文被挤占）
    paper_ids = sorted(
        [p["id"] for p in papers],
        key=lambda pid: len(paper_candidates.get(pid, [])),
    )

    for pid in paper_ids:
        candidates = paper_candidates.get(pid, [])
        assigned = 0
        for score, rid in candidates:
            if assigned >= per_paper:
                break
            if load[rid] < max_load:
                assignments.append((pid, rid))
                load[rid] += 1
                assigned += 1
        if assigned < per_paper:
            infeasible.append(pid)

    # ── min_load 补足：若有 reviewer 未达最低要求，尝试补分配 ──
    if min_load > 0:
        underloaded = [rid for rid, cnt in load.items() if cnt < min_load]
        for rid in underloaded:
            # 找该 reviewer 分数最高、尚未超配额的论文
            extra_candidates = sorted(
                [(s, pid) for pid, cands in paper_candidates.items()
                 for s, r in cands if r == rid and (pid, rid) not in set(assignments)],
                reverse=True,
            )
            for score, pid in extra_candidates:
                if load[rid] >= min_load:
                    break
                if load[rid] < max_load and (pid, rid) not in set(assignments):
                    assignments.append((pid, rid))
                    load[rid] += 1

    # 写入数据库（先清除旧的 auto 分配）
    with get_conn() as conn:
        conn.execute("DELETE FROM assignments WHERE source='auto'")
        conn.executemany(
            "INSERT OR IGNORE INTO assignments(paper_id, reviewer_id, source) VALUES(?,?,'auto')",
            assignments,
        )

    return {
        "assigned_pairs": len(assignments),
        "infeasible_papers": infeasible,
        "message": f"分配完成，{len(assignments)} 对，{len(infeasible)} 篇论文无法满足配额",
    }
