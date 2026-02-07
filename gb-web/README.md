# GB 2760 综合查询前端（Vue 3）

复刻 2760.foodmate.net 的查询功能，提供食品添加剂查询、按食品名称查询、加工助剂、酶制剂、香精香料、附录D 等页面。

## 技术栈

- Vue 3 + TypeScript + Vite
- Vue Router、Pinia
- Axios（请求后端 API）

## 开发

```bash
npm install
npm run dev
```

默认打开 http://localhost:5173，API 请求通过 Vite 代理到 `http://localhost:8080`。请先启动并导入数据后的 [gb-backend](../gb-backend/README.md)。

## 构建

```bash
npm run build
```

产物在 `dist/`，可部署到任意静态服务器；需配置反向代理将 `/api` 转发到后端。

## 页面说明

- **首页**：使用原则摘要、快速入口
- **食品添加剂查询**：表 A.1 列表、搜索、进入详情看使用范围
- **按食品名称查询**：表 A.2 分类列表、进入某分类看可用添加剂
- **加工助剂 / 酶制剂 / 香精香料 / 附录D**：对应参考数据表格与说明
