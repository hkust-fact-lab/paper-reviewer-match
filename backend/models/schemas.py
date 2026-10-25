"""Pydantic 模型，用于 API 请求/响应校验。"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    hotcrp_user_id: str
    email: str
    name: str
    role: Literal["admin", "reviewer"]
    reviewer_id: Optional[int] = None


# ── Papers ────────────────────────────────────────
class PaperOut(BaseModel):
    id: int
    hotcrp_id: Optional[str]
    title: str
    abstract: Optional[str]
    authors: Optional[list[dict]]
    topics: Optional[list[str]]
    methods: Optional[list[str]]
    required_expertise: Optional[list[str]]
    analysis_status: str
    analysis_error: Optional[str]
    created_at: str


class PaperCreate(BaseModel):
    hotcrp_id: Optional[str] = None
    title: str
    abstract: Optional[str] = None
    authors: Optional[list[dict]] = None


# ── Reviewers ─────────────────────────────────────
class ReviewerOut(BaseModel):
    id: int
    hotcrp_user_id: Optional[str]
    name: str
    email: str
    institution: Optional[str]
    scholar_url: Optional[str]
    scholar_confirmed: bool
    fetch_status: str
    expertise_topics: Optional[list[str]]
    publications: Optional[list[dict]]
    load_min: int
    load_max: int


class ReviewerCreate(BaseModel):
    name: str
    email: EmailStr
    institution: Optional[str] = None
    scholar_url: Optional[str] = None
    hotcrp_user_id: Optional[str] = None


# ── Match Scores ──────────────────────────────────
class MatchScoreOut(BaseModel):
    paper_id: int
    reviewer_id: int
    reviewer_name: str
    reviewer_institution: Optional[str]
    total_score: int
    topic_score: int
    method_score: int
    recency_score: int
    rationale: Optional[str]
    has_conflict: bool


# ── Assignments ───────────────────────────────────
class AssignmentOut(BaseModel):
    id: int
    paper_id: int
    reviewer_id: int
    paper_title: str
    reviewer_name: str
    source: str
    status: str
    assigned_at: str


# ── Conflicts ─────────────────────────────────────
class ConflictOut(BaseModel):
    id: int
    paper_id: int
    reviewer_id: int
    paper_title: str
    reviewer_name: str
    source: str
    detail: Optional[str]
    status: str
    created_at: str


class ConflictCreate(BaseModel):
    paper_id: int
    reviewer_id: int
    source: Literal["institution", "coauthor", "self_reported", "manual"]
    detail: Optional[str] = None


# ── Assignment Config ─────────────────────────────
class AssignmentConfig(BaseModel):
    reviewers_per_paper: int = 3
    max_papers_per_reviewer: int = 15
    min_papers_per_reviewer: int = 0
    min_score_threshold: int = 40
    coi_same_institution: bool = True
    coi_coauthor_years: int = 5


# ── Async Tasks ───────────────────────────────────
class TaskOut(BaseModel):
    id: int
    type: str
    ref_id: Optional[int]
    status: str
    progress: int
    result_summary: Optional[str]
    error_message: Optional[str]
    created_at: str
    finished_at: Optional[str]
