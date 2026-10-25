# ReviewMatch

ISCA 审稿人匹配系统 — 用大模型辅助论文与审稿人匹配和分配。

## 快速启动

### 后端

```sh
cd paper-reviewer-match
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env   # 填写 HotCRP OAuth 参数
uvicorn backend.main:app --reload --port 8000
```

### 前端（开发）

```sh
cd frontend
npm install
npm run dev   # http://localhost:5173，API 代理到 :8000
```

### 前端（生产构建）

```sh
cd frontend && npm run build
# 再启动后端，访问 http://localhost:8000
```

## 项目结构

```
paper-reviewer-match/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── requirements.txt
│   ├── models/
│   │   ├── db.py            # SQLite 连接 + 建表
│   │   └── schemas.py       # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── auth.py          # HotCRP OAuth 认证
│   │   ├── papers.py        # 论文管理
│   │   ├── reviewers.py     # Reviewer 管理
│   │   ├── matches.py       # 匹配分数
│   │   ├── assignment.py    # 分配配置、运行、导出
│   │   ├── conflicts.py     # COI 管理
│   │   └── tasks.py         # 异步任务状态
│   └── services/
│       ├── analysis.py      # 论文分析（LLM）
│       ├── scholar.py       # Google Scholar 抓取
│       ├── matching.py      # 匹配分数计算
│       └── assignment.py    # 分配算法
├── frontend/
│   ├── src/
│   │   ├── styles/app.css   # Design tokens（Apple 风格）
│   │   ├── components/
│   │   │   ├── ui/          # Button、Badge、Card、Input
│   │   │   └── layout/      # AppShell、PageHeader、EmptyState
│   │   └── routes/          # TanStack Router 文件路由
│   │       ├── login.tsx
│   │       ├── _app.tsx     # 登录保护布局
│   │       └── _app/
│   │           ├── conference.tsx
│   │           ├── papers.tsx / papers.$id.tsx
│   │           ├── reviewers.tsx / reviewers.$id.tsx
│   │           ├── assignment.tsx
│   │           ├── conflicts.tsx
│   │           └── my/ (reviewer 视角)
│   └── vite.config.ts
└── data/                    # SQLite DB + 上传的 PDF（gitignore）
```

## 待接入

- [ ] `services/analysis.py` — 接入 Claude API 读取 PDF 并提取主题
- [ ] `services/scholar.py` — 接入 scholarly / SerpAPI 抓取真实数据
- [ ] `services/matching.py` — 用 LLM 生成自然语言匹配理由
- [ ] HotCRP OAuth 参数 — 需要谢老师提供 client_id / secret
- [ ] 管理员角色初始化 — 在 `.env` 配置 ADMIN_EMAILS
