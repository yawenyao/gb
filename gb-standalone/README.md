# GB 2760 食品添加剂使用标准 · 本地查询

本目录为**独立运行包**：只需安装 Docker，无需 Java、Node、Python 或其它环境。

## 使用步骤

1. 确保已安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)（或 `docker compose` 插件）。

2. 在本目录下执行：
   ```bash
   docker compose up -d --build
   ```

3. **首次运行**会自动把数据导入图数据库，约 2～5 分钟。完成后在浏览器打开：
   - **查询页面**：http://localhost  
   - （可选）Neo4j 管理界面：http://localhost:7474（账号 neo4j / 密码 neo4j123）

4. 之后每次使用只需执行：
   ```bash
   docker compose up -d
   ```

## 停止

```bash
docker compose down
```

## 说明

- 数据与后端、前端均包含在本包内，无需联网获取数据。
- 首次启动会执行一次数据导入，之后启动不再导入。
- 查询结果仅供参考，具体以 GB 2760 标准文本为准。

---

**发给别人时（维护者）**：若从本仓库新克隆，需先在项目根目录执行一次 `./gb-standalone/prepare.sh` 生成 backend、frontend、dataset，再将整个 `gb-standalone` 目录打成 zip 或 tar 发出即可。
