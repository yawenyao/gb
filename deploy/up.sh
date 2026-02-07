#!/usr/bin/env bash
# 在项目根目录执行：./deploy/up.sh
set -e
cd "$(dirname "$0")/.."
docker compose -f deploy/docker-compose.yml up -d --build
echo "前端: http://localhost  后端: http://localhost:8080  Neo4j: http://localhost:7474"
echo "首次使用请执行一次导入: docker compose -f deploy/docker-compose.yml run --rm backend java -jar /app/app.jar --spring.profiles.active=import"
