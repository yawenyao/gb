#!/usr/bin/env bash
# 自动导入：启动 Neo4j（若未运行）并将 foodmate_dataset 导入图库，完成后退出。
# 在项目根目录执行：./scripts/import-to-neo4j.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATASET_PATH="${PROJECT_ROOT}/data-extraction/output/foodmate_dataset"

if [ ! -d "$DATASET_PATH" ]; then
  echo "错误：数据集目录不存在: $DATASET_PATH"
  echo "请先运行: python3 data-extraction/scripts/build_foodmate_dataset.py"
  exit 1
fi

echo ">>> 检查 Neo4j..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null | grep -q 200; then
  echo ">>> 启动 Neo4j（deploy/docker-compose）..."
  cd "$PROJECT_ROOT"
  docker compose -f deploy/docker-compose.yml up -d neo4j
  echo ">>> 等待 Neo4j 就绪（约 20 秒）..."
  sleep 20
  for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null | grep -q 200; then
      break
    fi
    sleep 2
  done
fi

echo ">>> 导入数据到 Neo4j（仅导入模式，完成后自动退出）..."
cd "$PROJECT_ROOT/gb-backend"
export DATASET_PATH
mvn -q spring-boot:run \
  -Dspring-boot.run.profiles=import \
  -Dspring-boot.run.arguments="--gb2760.import-only=true --spring.main.web-application-type=none"

echo ">>> 导入完成。可启动后端与前端进行查询。"
