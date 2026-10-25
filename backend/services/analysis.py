"""
论文分析 Service。
用大模型从 PDF 提取：研究主题、具体问题、技术方法、所需审稿专业知识。
API: OpenAI-compatible (sub2api.megahit.ai)
"""
import json
import os
import httpx
import pymupdf as fitz  # PyMuPDF
from ..models.db import get_conn

API_BASE  = os.getenv("LLM_BASE_URL", "https://sub2api.megahit.ai")
API_KEY   = os.getenv("LLM_API_KEY", "")   # 必须在 .env 中配置，不设置则禁用 LLM 调用
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-6-astra")

ANALYSIS_PROMPT = """\
你是一位计算机体系结构领域的资深学者，正在帮助分析一篇学术论文。

请仔细阅读以下论文内容，然后以 JSON 格式输出分析结果。

论文标题：{title}

论文摘要（若有）：
{abstract}

论文正文（前4000字）：
{body}

请输出以下 JSON（不要输出任何其他内容）：
{{
  "title": "论文标题（若摘要中更完整则使用摘要中的）",
  "abstract": "一句话总结这篇论文做了什么",
  "topics": ["研究方向1", "研究方向2", ...],
  "methods": ["技术方法1", "技术方法2", ...],
  "required_expertise": ["审稿需要的专业知识1", "专业知识2", ...]
}}

要求：
- topics：3-6 个，使用英文，如 "Cache Coherence"、"DRAM Architecture"
- methods：2-5 个，使用英文，如 "Cycle-accurate simulation"、"FPGA prototype"
- required_expertise：3-5 个，描述审稿人需要具备的专业背景，英文
- 所有字符串简洁，不超过 5 个词
"""


def enqueue_analyze_paper(paper_id: int) -> None:
    """在后台线程里运行论文分析，更新数据库状态。"""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO async_tasks(type, ref_id, status) VALUES('analyze_paper',?,'running')",
            (paper_id,),
        )
        task_id = cur.lastrowid
        conn.execute(
            "UPDATE papers SET analysis_status='analyzing' WHERE id=?", (paper_id,)
        )

    try:
        result = _analyze(paper_id)
        with get_conn() as conn:
            conn.execute("""
                UPDATE papers SET
                    analysis_status='analyzed',
                    topics=?, methods=?, required_expertise=?,
                    title=COALESCE(NULLIF(?, ''), title),
                    abstract=COALESCE(NULLIF(?, ''), abstract)
                WHERE id=?
            """, (
                json.dumps(result["topics"]),
                json.dumps(result["methods"]),
                json.dumps(result["required_expertise"]),
                result.get("title", ""),
                result.get("abstract", ""),
                paper_id,
            ))
            conn.execute(
                "UPDATE async_tasks SET status='done', progress=100, finished_at=datetime('now') WHERE id=?",
                (task_id,),
            )
    except Exception as e:
        with get_conn() as conn:
            conn.execute(
                "UPDATE papers SET analysis_status='error', analysis_error=? WHERE id=?",
                (str(e), paper_id),
            )
            conn.execute(
                "UPDATE async_tasks SET status='error', error_message=?, finished_at=datetime('now') WHERE id=?",
                (str(e), task_id),
            )


def _extract_pdf_text(pdf_path: str, max_chars: int = 4000) -> str:
    """用 PyMuPDF 提取 PDF 前几页的文本。"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) >= max_chars:
                break
        doc.close()
        return text[:max_chars]
    except Exception as e:
        return f"[PDF 提取失败: {e}]"


def _call_llm(prompt: str) -> str:
    """调用 OpenAI-compatible API。"""
    if not API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置，请在 .env 中设置")
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{API_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _analyze(paper_id: int) -> dict:
    """读取 PDF → 调用 LLM → 解析 JSON 结果。"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT title, abstract, pdf_path FROM papers WHERE id=?", (paper_id,)
        ).fetchone()

    if not row:
        raise ValueError(f"Paper {paper_id} not found")

    # 提取 PDF 文本
    body = ""
    if row["pdf_path"]:
        body = _extract_pdf_text(row["pdf_path"])

    prompt = ANALYSIS_PROMPT.format(
        title=row["title"] or "(unknown)",
        abstract=row["abstract"] or "(not provided)",
        body=body or "(not available)",
    )

    raw = _call_llm(prompt)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试从响应中提取 JSON 块
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            result = json.loads(m.group())
        else:
            raise ValueError(f"LLM 返回了无效 JSON: {raw[:200]}")

    # 确保字段存在且是列表
    for field in ("topics", "methods", "required_expertise"):
        if not isinstance(result.get(field), list):
            result[field] = []

    return result
