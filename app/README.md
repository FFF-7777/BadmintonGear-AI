# 羽智选用户端

面向普通用户的羽毛球装备品类库与 RAG AI 选品前台，基于 Vue 3 + Vite 实现。价格字段仅用于预算和选品对比，不承载交易、下单或支付流程。

## 技术栈

- Vue 3
- Vite
- Pinia
- Vue Router
- Axios

## 目录结构

```text
app/
  package.json
  vite.config.js
  index.html
  .env
  src/
    api/
    components/
    data/
    layout/
    router/
    store/
    styles/
    utils/
    views/
```

## 本地运行

1. 启动后端：在 `../server` 中运行 FastAPI 服务，默认监听 `http://127.0.0.1:8000`。
2. 安装依赖：`npm install`
3. 启动用户端：`npm run dev`
4. 构建检查：`npm run build`

开发期 `/api` 与 `/uploads` 会通过 Vite proxy 转发到后端。
