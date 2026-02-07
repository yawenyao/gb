# GB 2760 食品添加剂使用标准查询

GB 2760-2024 综合查询：按添加剂或按食品分类双向查询，支持本级/上级/GMP 分组展示。

## 项目结构

| 目录 | 说明 |
|------|------|
| **gb-web** | 前端（Vue 3 + Vite） |
| **gb-backend** | 后端（Spring Boot + Neo4j） |
| **data-extraction** | 数据提取与数据集构建（爬虫、foodmate_dataset） |
| **deploy** | Docker 部署（Neo4j + 后端 + 前端） |
| **gb-standalone** | 独立包（内嵌数据集，一键启动） |
| **scripts** | 一键导入 Neo4j 等脚本 |

## 快速开始

1. **导入图库**（需 Neo4j）：`./scripts/import-to-neo4j.sh`
2. **启动后端**：`cd gb-backend && mvn spring-boot:run`
3. **启动前端**：`cd gb-web && npm run dev`
4. 或使用 **Docker**：`docker compose -f deploy/docker-compose.yml up -d`

详见各子目录 README。
