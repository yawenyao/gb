#!/bin/sh
set -e
# 首次启动时自动导入 Neo4j，之后仅启动应用
if [ ! -f /data/import_done ]; then
  echo "首次运行：正在导入数据到 Neo4j，约需 2～5 分钟…"
  if java -jar /app/app.jar --spring.profiles.active=import; then
    touch /data/import_done
    echo "数据导入完成。"
  fi
fi
exec java -jar /app/app.jar
