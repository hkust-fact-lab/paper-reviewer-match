#!/bin/bash
# 一键启动开发环境：后端 + 前端
# 用法：./dev.sh

cd "$(dirname "$0")"

# 激活虚拟环境
source .venv/bin/activate

# 后端
uvicorn backend.main:app --port 8000 --reload &
BACKEND_PID=$!

# 前端
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  ReviewMatch 开发服务器启动中..."
echo "  前端：http://localhost:5173/conference"
echo "  API：http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo ""

# Ctrl+C 时同时停掉两个进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
