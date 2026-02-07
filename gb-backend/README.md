# GB 2760 后端（Spring Boot + Neo4j）

基于图数据库 Neo4j 的食品添加剂使用标准查询 API，数据来源为 `data-extraction/output/foodmate_dataset`。

## 要求

- JDK 17+
- Maven 3.8+
- Neo4j 5.x（可选 Docker：见项目根目录 `docker/`）

## 配置

- `application.yml`：
  - `spring.neo4j.uri`：默认 `bolt://localhost:7687`
  - `spring.neo4j.authentication.password`：默认 `neo4j123`（与 `docker/docker-compose.yml` 一致）
  - `dataset.path`：指向 `foodmate_dataset` 目录，用于参考数据（加工助剂、酶制剂、香精、附录D、使用原则）及**导入图库**时的 JSON 路径。默认：`../data-extraction/output/foodmate_dataset`

## 首次运行：导入数据到 Neo4j

1. 启动 Neo4j（例如在项目根目录执行 `docker compose -f docker/docker-compose.yml up -d`）。
2. 在 **gb-backend** 目录执行导入（仅需运行一次）：

```bash
mvn spring-boot:run -Dspring-boot.run.profiles=import
```

或设置环境变量后运行：

```bash
export DATASET_PATH=/absolute/path/to/gb/data-extraction/output/foodmate_dataset
mvn spring-boot:run -Dspring-boot.run.profiles=import
```

导入会将 `entities/additives.json`、`entities/categories.json`、`relations/additive_usage.json` 写入 Neo4j（Additive、Category 节点及 USED_IN 关系）。

## 正常启动 API

```bash
mvn spring-boot:run
```

确保 `dataset.path` 可访问（参考数据从 JSON 读取），且 Neo4j 已导入过数据。

## API 概览

| 接口 | 说明 |
|------|------|
| `GET /api/additives?q=` | 添加剂列表，可选搜索 |
| `GET /api/additives/{faid}` | 添加剂详情及使用范围 |
| `GET /api/categories?q=` | 食品分类列表，可选搜索 |
| `GET /api/categories/{code}` | 分类详情及可用添加剂 |
| `GET /api/reference/processing-aids` | 加工助剂 |
| `GET /api/reference/enzymes` | 酶制剂 |
| `GET /api/reference/spices/b1` | 表 B.1 禁止名单 |
| `GET /api/reference/spices/b2` | 表 B.2 天然香料 |
| `GET /api/reference/spices/b3` | 表 B.3 合成香料 |
| `GET /api/reference/appendix-d` | 附录D 功能定义 |
| `GET /api/reference/site-rules` | 首页使用原则 |
| `GET /api/reference/spices-rules` | 香精香料使用原则 |

前端默认通过 Vite 代理访问 `http://localhost:8080`。
