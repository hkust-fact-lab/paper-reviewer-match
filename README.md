# ReviewMatch

**ISCA 2027 审稿人匹配系统** — 用大模型辅助论文与审稿人匹配和分配。

## 演示视频

https://github.com/user-attachments/assets/1e80df6d-9f30-4ac7-8aac-dfab07f62641

## 功能

1. **分析论文** — 用大模型读取 PDF，提取研究主题、方法、所需审稿专业知识
2. **分析审稿人** — 从 Semantic Scholar 抓取 PC 成员论文，建立研究专长画像
3. **计算匹配分数** — 三维加权（话题 50% + 方法 30% + 时近度 20%），生成 0-100 分和自然语言理由
4. **生成完整分配** — 满足每篇篇数、每人上限、利益冲突等约束，可配置
5. **可操作界面** — 导入、查看推荐、运行分配、人工调整、导出

## 快速启动

### 依赖

- Python 3.12+
- Node.js 18+

### 安装

```sh
git clone https://github.com/hkust-fact-lab/paper-reviewer-match.git
cd paper-reviewer-match

# 后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 前端
cd frontend && npm install && npm run build && cd ..
```

### 配置

```sh
cp .env.example .env
# 编辑 .env，填写 ADMIN_PASSWORD 和 LLM_API_KEY
```

### 启动

```sh
./dev.sh
```

浏览器打开 `http://localhost:8000`，使用 `.env` 中配置的管理员账号登录。

### 插入演示数据

```sh
source .venv/bin/activate
python scripts/seed_demo.py
```

插入 12 篇 ISCA 论文、12 位真实 PC 成员、30 条匹配分数和 24 对分配结果。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 · Vite · TanStack Router · Tailwind CSS v4 |
| 后端 | Python · FastAPI · SQLite |
| 大模型 | OpenAI-compatible API（支持 Claude、GPT、Qwen 等） |
| 数据来源 | Semantic Scholar API · Google Scholar |

## 目录

```
paper-reviewer-match/
├── backend/
│   ├── routers/        # API 路由（auth / papers / reviewers / matches / assignment / conflicts）
│   ├── services/       # 论文分析 · Scholar 抓取 · 匹配计算 · 分配算法
│   └── models/         # SQLite schema · Pydantic schemas
├── frontend/
│   └── src/
│       ├── routes/     # 页面（TanStack Router 文件路由）
│       ├── components/ # UI 组件 · 布局
│       └── lib/        # API 客户端 · i18n · 认证
└── scripts/
    └── seed_demo.py    # 演示数据种子脚本
```
