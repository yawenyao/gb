#!/bin/bash
# 启动 Neo4j 并导入 GB 2760 数据（需先确保 Docker 已运行）
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"
echo "启动 Neo4j..."
docker compose up -d
echo "等待 Neo4j 就绪（约 15 秒）..."
sleep 15
cd "$PROJECT_ROOT/data-extraction"
export NEO4J_PASSWORD=neo4j123
echo "导入数据到 Neo4j..."
python3 scripts/import_to_neo4j.py
echo "完成。浏览器打开 http://localhost:7474 登录 neo4j / neo4j123 查看图数据。"
