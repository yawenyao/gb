# Neo4j 图数据库（Docker）

## 1. 启动 Docker

确保本机 **Docker Desktop**（或 Docker 引擎）已启动。

## 2. 一键：启动 Neo4j 并导入数据

```bash
cd docker
./run_and_import.sh
```

脚本会：启动 Neo4j 容器 → 等待就绪 → 从 `data-extraction/output/all_tables_extracted.json` 导入节点与关系到 Neo4j。

## 3. 分步执行（可选）

```bash
# 仅启动 Neo4j
cd docker
docker compose up -d

# 等待约 15 秒后，在项目 data-extraction 目录下导入
cd ../data-extraction
export NEO4J_PASSWORD=neo4j123
python3 scripts/import_to_neo4j.py
```

## 4. 访问 Neo4j

- 浏览器打开：http://localhost:7474  
- 登录：用户名 `neo4j`，密码 `neo4j123`

## 5. 图模型说明

- **节点**：`Additive`（添加剂）、`FoodCategory`（食品类别）、`FunctionCategory`（功能类别）
- **边**：`ALLOWED_IN`（允许使用）、`EXCLUDED_FROM`（表A.2 除外）、`HAS_FUNCTION`（功能）、`BELONGS_TO`（分类层级）、`MIXED_WITH`（混合使用）

若未先运行过数据提取，请先执行：`cd data-extraction && python3 scripts/run_extraction_to_csv.py`
