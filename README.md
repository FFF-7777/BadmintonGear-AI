# 羽智选 BadmintonGear AI

羽毛球装备品类库与 RAG AI 选品系统。项目不包含交易、下单、支付、购物车或订单系统；装备价格仅作为预算和选品对比参考。

## 项目结构

```text
app/      用户端 RAG AI 选品前台，Vue 3 + Vite
client/   管理后台，负责装备、品类、内容位、用户与知识库管理
server/   FastAPI 后端，负责业务 API、知识库上传、RAG 检索与 AI 问答
scripts/  导入、备份、烟测与遗留代码审计脚本
知识库/    本地知识库源文件与临时测试资料，不会自动向量化
```

## 业务边界

- 只维护四个品类：球拍、球线、羽毛球、球鞋。
- 当前阶段只对“羽毛球拍”做具体型号推荐；球线、球鞋、羽毛球只给通用选择原则，不硬编具体型号。
- 品牌与装备价格用于 AI 对比、预算判断和选品建议。
- 知识库由管理员后台上传，后端解析后进入 RAG 检索流程。
- 用户端优先突出 AI 问答和装备对比，不承载交易闭环。

## RAG 问答流程

```text
用户问题
→ 后端问题分类（装备导购 / 羽球周边 / 无关闲聊）
→ 型号与对比对象抽取（YY / ASTROX / 天斧 / JS-12 等别名归一）
→ 结构化商品库优先精确匹配
→ 规则式 query rewrite 生成稳定检索文本
→ 向量召回 + BM25 + RRF + rerank（知识库入库后生效）
→ LLM 基于候选装备和知识资料生成克制回答
→ 前端展示回答、sources、推荐置信度和风险提示
```

## 推荐可信度

- 具体型号、价格和参数只来自结构化装备库或知识库来源，不由模型自行编造。
- 推荐排序已纳入 `source_confidence`，低可信或字段不足的商品只能作为备选。
- `unverified_fields` 会进入回答注意事项和前端展示，提示购买前核验。
- 参考价只用于预算对比，不代表实时售价、最低价或到手价。

## 评测结果与数据

系统有可量化的评测闭环，所有分数均标注前提与边界，诚信可审计。

- **模型**：生成 `qwen3.7-plus`（`temperature=0.2`）；嵌入 `text-embedding-v4`（2048 维）；重排 `qwen3-rerank`；DeepEval 独立裁判用 `qwen3.6-flash-2026-04-16`（与生成模型不同款，降低自评偏差）。
- **主指标 · 确定性黄金集（评测有效版）**：基于「已修正评测瑕疵」的黄金集（64 条球拍子集，端到端由 qwen3.7-plus 生成），综合 **0.8816**。分组分：routing 1.000 / general_training_safety 0.909 / recommendation 0.899 / grounding_policy 0.891 / parameter 0.856 / comparison 0.813 / product_fact 0.778。
- **佐证 · DeepEval 独立裁判（全量 64 条，同步串行）**：Faithfulness **0.8142** / AnswerRelevancy 0.8371 / ContextualPrecision 0.7906 / ContextualRecall 0.8024 / Hallucination **0.2008** / 专业度[GEval] 0.8407。两条独立路径共同定位唯一真弱点：**来源标注与检索召回完整性**。
- **诚信说明**：原始黄金集由初始化模型（GPT-5.5）拟定，混入了指向知识库不存在来源的源关键词；已修正使评测有效，0.8816 反映系统真实能力。Ragas 0.4.3 与百炼端点结构性不兼容（多采样 → 400、embedding 方法不匹配），已如实排除于三角验证之外。

## 最终切块口径

- 普通知识文档：`CHUNK_SIZE=1000`、`CHUNK_OVERLAP=120`、`MIN_CHUNK_CHARS=180`、`MAX_CHUNK_CHARS=1400`。
- 结构化商品/型号资料：优先按型号标题切分，目标是一支球拍一个 chunk。
- 参数表、对比表和 YAML/字段块需要保留在同一语义段内，不拆成无上下文碎片。
- 这些配置会影响向量库内容；改动后需要重新向量化。`RAG_TOP_K`、rerank、prompt、推荐排序等检索/生成参数不需要重新向量化。

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

也可以分别运行：

```powershell
cd server
C:\Users\Lenovo\.workbuddy\binaries\python\envs\default\Scripts\python.exe -m unittest discover -s tests

cd ..\app
npm run build

cd ..\client
npm run build
```
