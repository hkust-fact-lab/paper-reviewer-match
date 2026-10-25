"""简单密码认证。管理员用用户名+密码登录，无需 OAuth。"""
import hashlib
import hmac
import os
import secrets
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from ..models.db import get_conn

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")

# ── 管理员账号从环境变量读 ──────────────────────────────────────────────────
# ADMIN_USERNAME / ADMIN_PASSWORD 在 .env 里配置
# 默认值仅用于本地开发
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def _sign(value: str) -> str:
    """对 session uid 做 HMAC 签名，防止伪造。"""
    sig = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{sig}"


def _verify(signed: str) -> str | None:
    """验证签名，返回原始 uid；签名无效返回 None。"""
    if "." not in signed:
        return None
    value, sig = signed.rsplit(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected):
        return value
    return None


def get_current_user(request: Request) -> dict:
    """从 cookie 里取当前登录用户，未登录抛 401。"""
    signed = request.cookies.get("session")
    if not signed:
        raise HTTPException(401, "未登录")
    uid = _verify(signed)
    if not uid:
        raise HTTPException(401, "会话无效")
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    return dict(row)


def require_admin(request: Request) -> dict:
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user


# ── API ────────────────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginBody, response: Response):
    if body.username != ADMIN_USERNAME or body.password != ADMIN_PASSWORD:
        raise HTTPException(401, "用户名或密码错误")

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users(hotcrp_user_id, email, name, role)
            VALUES(?, ?, ?, 'admin')
            ON CONFLICT(hotcrp_user_id) DO NOTHING
        """, (ADMIN_USERNAME, f"{ADMIN_USERNAME}@local", ADMIN_USERNAME))
        row = conn.execute(
            "SELECT id FROM users WHERE hotcrp_user_id=?", (ADMIN_USERNAME,)
        ).fetchone()

    signed = _sign(str(row["id"]))
    response.set_cookie("session", signed, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    user = get_current_user(request)
    return {
        "id":    str(user["id"]),
        "name":  user["name"],
        "email": user["email"],
        "role":  user["role"],
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me/reviewer-id")
def me_reviewer_id(request: Request):
    """返回当前登录用户对应的 reviewer id（按 email 匹配）。"""
    user = get_current_user(request)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM reviewers WHERE email=?", (user["email"],)
        ).fetchone()
    return {"reviewer_id": row["id"] if row else None}
