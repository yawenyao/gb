# GB 2760 食品添加剂使用标准查询

GB 2760-2024 综合查询：按添加剂或按食品分类双向查询，支持本级/上级/GMP 分组展示。

## 克隆即可运行（数据已入库）

**本仓库已包含全部运行所需数据**，换电脑后只需：

```bash
git clone https://github.com/yawenyao/gb.git && cd gb
```

无需再跑爬虫或生成数据集，可直接启动应用。仓库内已提交：

| 数据 | 路径 | 用途 |
|------|------|------|
| 爬虫产出 | `data-extraction/output/foodmate/*.json` | 构建 dataset 的输入（可复现 dataset） |
| **基础数据集** | `data-extraction/output/foodmate_dataset/` | 后端、导入脚本、Docker 挂载均用此目录 |
| ├ 实体 | `entities/additives.json`, `categories.json` | 添加剂与分类节点 |
| ├ 关系 | `relations/additive_usage.json` | USED_IN 边（含 source/unit） |
| ├ 索引 | `index/by_additive.json`, `by_category.json` | 按添加剂/分类查询 |
| └ 参考 | `reference/*.json` | 加工助剂、酶制剂、香精、附录D 等 |

后端默认 `dataset.path=../data-extraction/output/foodmate_dataset`（相对 gb-backend 目录），克隆后路径一致，可直接运行。

## 项目结构

| 目录 | 说明 |
|------|------|
| **gb-web** | 前端（Vue 3 + Vite） |
| **gb-backend** | 后端（Spring Boot + Neo4j） |
| **data-extraction** | 数据提取与数据集构建（爬虫、foodmate_dataset） |
| **deploy** | Docker 部署（Neo4j + 后端 + 前端） |
| **gb-standalone** | 独立包（内嵌数据集，一键启动） |
| **scripts** | 一键导入 Neo4j 等脚本 |

## 快速开始（换机克隆后）

1. **克隆**：`git clone https://github.com/yawenyao/gb.git && cd gb`
2. **导入图库**（需 Neo4j）：`./scripts/import-to-neo4j.sh`（会按需启动 Neo4j 并导入上述 dataset）
3. **启动后端**：`cd gb-backend && mvn spring-boot:run`
4. **启动前端**：`cd gb-web && npm install && npm run dev`
5. 或 **Docker 一键**：在项目根目录执行 `docker compose -f deploy/docker-compose.yml up -d --build`（会挂载本仓库内的 `foodmate_dataset`，无需额外生成）

详见各子目录 README。
