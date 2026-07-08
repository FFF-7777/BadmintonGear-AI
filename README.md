# 羽智选 BadmintonGear AI

羽毛球装备品类库与 RAG AI 选品系统。项目不包含交易、下单、支付、购物车或订单系统；装备价格仅作为预算和选品对比参考。

## 项目结构

```text
app/      用户端 RAG AI 选品前台，Vue 3 + Vite
client/   管理后台，负责装备、品类、内容位、用户与知识库管理
server/   FastAPI 后端，负责业务 API、知识库上传、RAG 检索与 AI 问答
archive/  历史小程序源码归档，不参与当前运行
```

## 业务边界

- 只维护四个品类：球拍、球线、羽毛球、球鞋。
- 品牌与装备价格用于 AI 对比、预算判断和选品建议。
- 知识库由管理员后台上传，后端解析后进入 RAG 检索流程。
- 用户端优先突出 AI 问答和装备对比，不承载交易闭环。

## 本地运行

后端：

```powershell
cd server
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

管理后台：

```powershell
cd client
npm install
npm run dev
```

用户端：

```powershell
cd app
npm install
npm run dev
```

## 工程化验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
```

该脚本会依次执行后端编译、后端单测、管理后台构建和用户端构建。
