# GB 2760 三服务一键启动（Docker）

本目录通过 Docker Compose 一次性启动 **Neo4j**、**Java 后端**、**Vue 前端** 三个服务。

## 前置条件

1. 已安装 [Docker](https://docs.docker.com/get-docker/) 与 [Docker Compose](https://docs.docker.com/compose/install/)（或 `docker compose` 插件）。
2. 本地已生成数据集目录 `data-extraction/output/foodmate_dataset`（若尚未生成，在项目根目录执行：
   ```bash
   cd data-extraction && python3 scripts/build_foodmate_dataset.py
   ```
   ）。

## 一键启动

**在项目根目录**执行：

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

或使用本目录下的脚本（在项目根目录执行）：

```bash
./deploy/up.sh
```

- **前端**：http://localhost （端口 80）
- **后端 API**：http://localhost:8080
- **Neo4j Browser**：http://localhost:7474（可选，账号 neo4j / neo4j123）

## 首次运行：导入图数据

首次启动后 Neo4j 为空，需执行一次数据导入后再使用查询功能：

```bash
docker compose -f deploy/docker-compose.yml run --rm backend \
  java -jar /app/app.jar --spring.profiles.active=import
```

导入完成后，刷新前端即可正常查询添加剂与分类。

## 常用命令

| 命令 | 说明 |
|------|------|
| `docker compose -f deploy/docker-compose.yml up -d --build` | 构建并后台启动三服务 |
| `docker compose -f deploy/docker-compose.yml down` | 停止并删除容器 |
| `docker compose -f deploy/docker-compose.yml logs -f` | 查看所有服务日志 |
| `docker compose -f deploy/docker-compose.yml ps` | 查看服务状态 |

## 目录与镜像说明

- `docker-compose.yml`：定义 neo4j、backend、frontend 三个服务及依赖关系。
- `Dockerfile.backend`：基于 `gb-backend` 与 JDK 17 构建 Spring Boot 镜像；数据集通过卷挂载 `foodmate_dataset`。
- `Dockerfile.frontend`：基于 `gb-web` 构建 Vue 产物，由 nginx 提供静态资源并将 `/api` 代理到后端。
- `nginx.conf`：前端容器内 nginx 配置，根路径走静态，`/api/` 反向代理到 `backend:8080`。

构建上下文为**项目根目录**，因此以上命令均需在仓库根目录执行。
