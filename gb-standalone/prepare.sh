#!/usr/bin/env bash
# 在项目根目录执行：./gb-standalone/prepare.sh
# 将 backend、frontend、dataset 复制到 gb-standalone，便于打包发给他人
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STANDALONE="$(dirname "$0")"
cd "$ROOT"

echo "正在复制到 gb-standalone …"

rm -rf "$STANDALONE/backend" "$STANDALONE/frontend" "$STANDALONE/dataset"
mkdir -p "$STANDALONE/backend" "$STANDALONE/frontend" "$STANDALONE/dataset"

# 后端（排除 target、.idea）
rsync -a --exclude 'target' --exclude '.idea' gb-backend/ "$STANDALONE/backend/" 2>/dev/null || \
  (cp -R gb-backend/* "$STANDALONE/backend/" && rm -rf "$STANDALONE/backend/target" "$STANDALONE/backend/.idea" 2>/dev/null; true)

# 前端（排除 node_modules、dist）
rsync -a --exclude 'node_modules' --exclude 'dist' gb-web/ "$STANDALONE/frontend/" 2>/dev/null || \
  (cp -R gb-web/* "$STANDALONE/frontend/" && rm -rf "$STANDALONE/frontend/node_modules" "$STANDALONE/frontend/dist" 2>/dev/null; true)

# 数据集
cp -R data-extraction/output/foodmate_dataset/* "$STANDALONE/dataset/"

echo "已就绪。可将 gb-standalone 目录打包（zip/tar）发给对方，对方解压后执行："
echo "  docker compose up -d --build"
echo "然后打开 http://localhost 即可查询。"
