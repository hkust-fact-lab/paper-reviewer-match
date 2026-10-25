"""
Google Scholar / Semantic Scholar 抓取 Service。
多源策略（按优先级）：
  1. Semantic Scholar API（有 API key 时，最稳定）
  2. scholarly + Google Scholar（有代理时）
  3. arXiv 作者搜索（兜底，论文覆盖有限）

同名去重：多个候选时标记 needs_confirmation，等管理员确认。
"""
import json
import os
import time
import httpx
from ..models.db import get_conn

S2_API_KEY   = os.getenv("S2_API_KEY", "")          # Semantic Scholar API key（可选）
S2_BASE      = "https://api.semanticscholar.org/graph/v1"
SCHOLAR_PROXY = os.getenv("SCHOLAR_PROXY", "")       # http://host:port
S2_DELAY     = float(os.getenv("S2_DELAY", "1.5"))   # 礼貌延迟（秒）


def enqueue_fetch_reviewer(reviewer_id: int) -> None:
    """在后台线程里抓取 reviewer 数据，更新数据库。"""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO async_tasks(type, ref_id, status) VALUES('fetch_reviewer',?,'running')",
            (reviewer_id,),
        )
        task_id = cur.lastrowid
        conn.execute(
            "UPDATE reviewers SET fetch_status='fetching' WHERE id=?", (reviewer_id,)
        )

    try:
        result = _fetch(reviewer_id)
        status = result.get("status", "done")

        with get_conn() as conn:
            if status == "needs_confirmation":
                conn.execute(
                    "UPDATE reviewers SET fetch_status='needs_confirmation', fetch_error=? WHERE id=?",
                    (json.dumps(result.get("candidates", [])), reviewer_id),
                )
            elif status == "no_data":
                conn.execute(
                    "UPDATE reviewers SET fetch_status='no_data' WHERE id=?", (reviewer_id,)
                )
            else:
                conn.execute("""
                    UPDATE reviewers SET
                        fetch_status='done',
                        expertise_topics=?,
                        publications=?,
                        scholar_url=COALESCE(NULLIF(?, ''), scholar_url)
                    WHERE id=?
                """, (
                    json.dumps(result["expertise_topics"]),
                    json.dumps(result["publications"]),
                    result.get("scholar_url", ""),
                    reviewer_id,
                ))
            conn.execute(
                "UPDATE async_tasks SET status='done', progress=100, finished_at=datetime('now') WHERE id=?",
                (task_id,),
            )
    except Exception as e:
        with get_conn() as conn:
            conn.execute(
                "UPDATE reviewers SET fetch_status='error', fetch_error=? WHERE id=?",
                (str(e), reviewer_id),
            )
            conn.execute(
                "UPDATE async_tasks SET status='error', error_message=?, finished_at=datetime('now') WHERE id=?",
                (str(e), task_id),
            )


def _fetch(reviewer_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT name, email, institution, scholar_url, scholar_confirmed FROM reviewers WHERE id=?",
            (reviewer_id,),
        ).fetchone()

    if not row:
        raise ValueError(f"Reviewer {reviewer_id} not found")

    name        = row["name"]
    institution = row["institution"] or ""
    scholar_url = row["scholar_url"] or ""
    confirmed   = bool(row["scholar_confirmed"])

    # 策略1：Semantic Scholar（推荐，稳定；无 key 时有速率限制）
    try:
        return _fetch_via_s2(name, institution, scholar_url, confirmed)
    except Exception as e:
        if "429" not in str(e) and "Too Many" not in str(e):
            raise  # 非限速错误直接抛出

    # 策略2：scholarly + Google Scholar（被限速时降级，需要代理）
    if SCHOLAR_PROXY or scholar_url:
        try:
            return _fetch_via_scholarly(name, institution, scholar_url, confirmed)
        except Exception:
            pass

    raise RuntimeError(
        "所有数据源均不可用。"
        "请设置 S2_API_KEY（Semantic Scholar）或 SCHOLAR_PROXY（Google Scholar 代理）。"
    )


# ── Semantic Scholar ────────────────────────────────────────────────────────

def _s2_headers() -> dict:
    h: dict[str, str] = {"Accept": "application/json"}
    if S2_API_KEY:
        h["x-api-key"] = S2_API_KEY
    return h


def _fetch_via_s2(name: str, institution: str, scholar_url: str, confirmed: bool) -> dict:
    """用 Semantic Scholar API 抓取。"""
    with httpx.Client(timeout=30) as client:
        # 搜索作者
        resp = client.get(
            f"{S2_BASE}/author/search",
            params={"query": f"{name} {institution}".strip(), "fields": "name,affiliations,paperCount,externalIds", "limit": 5},
            headers=_s2_headers(),
        )
        if resp.status_code == 429:
            raise RuntimeError("429 Too Many Requests")
        resp.raise_for_status()
        data = resp.json()

    candidates_raw = data.get("data", [])
    if not candidates_raw:
        return {"status": "no_data"}

    candidates = [
        {
            "name":        c.get("name", ""),
            "affiliation": (c.get("affiliations") or [{"name": ""}])[0].get("name", ""),
            "s2_id":       c.get("authorId", ""),
            "paper_count": c.get("paperCount", 0),
        }
        for c in candidates_raw
    ]

    # 单一候选或有明确匹配
    if len(candidates) == 1 or _is_clear_match(candidates[0], name, institution):
        return _s2_fetch_profile(candidates[0]["s2_id"])

    # 多个候选，需管理员确认
    return {"status": "needs_confirmation", "candidates": candidates}


def _s2_fetch_profile(author_id: str) -> dict:
    """抓取某个 S2 作者的完整 profile。"""
    time.sleep(S2_DELAY)
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{S2_BASE}/author/{author_id}/papers",
            params={"fields": "title,year,venue,citationCount", "limit": 50},
            headers=_s2_headers(),
        )
        resp.raise_for_status()
        papers_data = resp.json().get("data", [])

    publications = [
        {
            "title":   p.get("title", ""),
            "year":    p.get("year") or 0,
            "venue":   p.get("venue") or "",
            "citedby": p.get("citationCount") or 0,
            "url":     f"https://www.semanticscholar.org/paper/{p.get('paperId','')}",
        }
        for p in papers_data
    ]

    from collections import Counter
    venues = [p["venue"] for p in publications if p["venue"]]
    top_venues = [v for v, _ in Counter(venues).most_common(5)]
    expertise_topics = _infer_topics_from_venues(top_venues)

    return {
        "status":           "done",
        "scholar_url":      f"https://www.semanticscholar.org/author/{author_id}",
        "expertise_topics": expertise_topics,
        "publications":     publications,
    }


# ── scholarly (Google Scholar) ──────────────────────────────────────────────

def _fetch_via_scholarly(name: str, institution: str, scholar_url: str, confirmed: bool) -> dict:
    from scholarly import scholarly as sc, ProxyGenerator

    if SCHOLAR_PROXY:
        pg = ProxyGenerator()
        pg.SingleProxy(http=SCHOLAR_PROXY, https=SCHOLAR_PROXY)
        sc.use_proxy(pg)

    # 有确认的 URL 直接用
    if scholar_url and confirmed:
        return _scholarly_by_url(sc, scholar_url)

    query = f"{name} {institution}".strip()
    time.sleep(1)
    search_gen = sc.search_author(query)

    candidates = []
    for _ in range(4):
        try:
            author = next(search_gen)
            candidates.append({
                "name":        author.get("name", ""),
                "affiliation": author.get("affiliation", ""),
                "scholar_id":  author.get("scholar_id", ""),
                "scholar_url": f"https://scholar.google.com/citations?user={author.get('scholar_id','')}",
                "citedby":     author.get("citedby", 0),
            })
        except StopIteration:
            break
        time.sleep(0.5)

    if not candidates:
        return {"status": "no_data"}

    if len(candidates) == 1 or _is_clear_match(candidates[0], name, institution):
        sid = candidates[0]["scholar_id"]
        url = candidates[0]["scholar_url"]
        return _scholarly_by_id(sc, sid, url)

    return {"status": "needs_confirmation", "candidates": candidates}


def _scholarly_by_url(sc, url: str) -> dict:
    import re
    m = re.search(r'user=([A-Za-z0-9_-]+)', url)
    if not m:
        raise ValueError(f"无法从 URL 提取 scholar_id: {url}")
    return _scholarly_by_id(sc, m.group(1), url)


def _scholarly_by_id(sc, scholar_id: str, url: str) -> dict:
    author = sc.search_author_id(scholar_id)
    author = sc.fill(author, sections=["basics", "publications"])

    pubs_raw = author.get("publications", [])[:30]
    publications = []
    for pub in pubs_raw:
        bib = pub.get("bib", {})
        publications.append({
            "title":   bib.get("title", ""),
            "year":    int(bib.get("pub_year", 0) or 0),
            "venue":   bib.get("venue", "") or bib.get("journal", "") or bib.get("booktitle", ""),
            "citedby": pub.get("num_citations", 0),
            "url":     url,
        })

    interests = author.get("interests", [])
    from collections import Counter
    venues = [p["venue"] for p in publications if p["venue"]]
    top_venues = [v for v, _ in Counter(venues).most_common(5)]
    expertise_topics = interests[:6] if interests else _infer_topics_from_venues(top_venues)

    return {
        "status":           "done",
        "scholar_url":      url,
        "expertise_topics": expertise_topics,
        "publications":     publications,
    }


# ── 通用工具 ────────────────────────────────────────────────────────────────

def _is_clear_match(candidate: dict, name: str, institution: str | None) -> bool:
    cand_name = candidate.get("name", "").lower()
    target    = name.lower()
    name_ok   = cand_name == target or target in cand_name
    if not institution:
        return name_ok
    aff = (candidate.get("affiliation") or candidate.get("affiliation", "")).lower()
    inst_ok = any(w in aff for w in institution.lower().split() if len(w) > 3)
    return name_ok and inst_ok


VENUE_TOPIC_MAP = {
    "ISCA": "Computer Architecture", "MICRO": "Microarchitecture",
    "ASPLOS": "Systems Architecture", "HPCA": "High-Performance Computing",
    "DAC": "Design Automation", "ICCAD": "Design Automation",
    "PLDI": "Programming Languages", "POPL": "Programming Languages",
    "OSDI": "Operating Systems", "SOSP": "Operating Systems",
    "EuroSys": "Systems", "ATC": "Systems", "FAST": "Storage Systems",
    "VLDB": "Database Systems", "SIGMOD": "Database Systems",
    "NeurIPS": "Machine Learning", "ICML": "Machine Learning",
    "ICLR": "Deep Learning", "CVPR": "Computer Vision",
    "ACL": "Natural Language Processing", "EMNLP": "Natural Language Processing",
    "SC": "High-Performance Computing", "ICS": "High-Performance Computing",
    "PPoPP": "Parallel Computing", "SPAA": "Parallel Computing",
}

def _infer_topics_from_venues(venues: list[str]) -> list[str]:
    topics: list[str] = []
    for v in venues:
        for key, topic in VENUE_TOPIC_MAP.items():
            if key.lower() in v.lower() and topic not in topics:
                topics.append(topic)
    return topics[:5] if topics else ["Computer Science"]
