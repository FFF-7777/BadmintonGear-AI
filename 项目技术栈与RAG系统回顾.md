# 羽智选 BadmintonGear AI — 技术栈、选型与 RAG 系统深度回顾

> 本文档系统回顾项目的**技术栈、技术选型理由、技术亮点**，并用 **STAR 法则** 深度拆解最重要的 RAG 系统（架构、设计细节、关键参数与权衡）。
> 适用场景：项目复盘、技术分享、简历/面试项目陈述。

---

## 一、技术栈总览

| 层 | 技术 | 版本/说明 |
|---|---|---|
| **前端（用户端）** | Vue 3 + Vite + 原生 WebSocket | 聊天导购前端，端口 5184 |
| **前端（管理后台）** | Vue 3 + Vite + Element Plus | 知识库/商品管理，端口 5183 |
| **后端** | FastAPI + Uvicorn（reload） | 异步框架，天然适配流式 SSE/WS |
| **ORM / 数据库** | SQLAlchemy + **SQLite** | `server/dev.db`；单机轻量，零运维 |
| **向量库** | ChromaDB | 1.5.9；子进程隔离访问，防 Windows segfault |
| **Embedding** | 阿里云百炼 `text-embedding-v4` | 维度 2048 |
| **生成模型** | 阿里云百炼 `qwen3.7-plus` | 对话/选品生成，`temperature=0.2` |
| **重排模型** | 阿里云百炼 `qwen3-rerank` | Cross-Encoder 语义重排 |
| **评测** | 自研黄金集 + DeepEval | 确定性打分主指标 + 独立 LLM 裁判佐证 |
| **工程化** | Docker / docker-compose / GitHub Actions CI | 容器化 + 自动构建测试 |
| **质量门禁** | pytest / mypy / ruff / ESLint / Prettier / Vitest | 后端 37 + 前端 9 测试 |
| **可观测** | Prometheus `/metrics` + 结构化 JSON 日志 | 深度健康检查 `/api/health` |
| **运行环境** | Python 3.13（托管 venv）/ Node 22 | 纯本地，Clash 代理旁路 `127.0.0.1` |

---

## 二、技术选型与理由

### 2.1 为什么是 FastAPI + 原生 WebSocket
RAG 导购的核心体验是**流式回答 + 实时推荐卡片**。FastAPI 基于 ASGI，对 `async/await`、SSE、WebSocket 是一等公民；`WebSocket /api/chat/ws` 让前端逐字渲染 token，无需长轮询。前端用原生 `WebSocket` + `vite proxy`（含 `ws:true`）连后端，WS 失败再降级本地兜底——零额外依赖。

### 2.2 为什么是 SQLite 而不是 MySQL
项目是**单机部署的装备导购原型**，没有高并发写入、没有跨服务事务需求。SQLite 文件即数据库，备份=复制文件（覆盖 DB 前 `cp dev.db dev.db.bak_时间戳` 即可秒级回滚），零运维。`db_ai_shop.sql` 虽是 MySQL 语法，但仅作历史参考；真实建表走 SQLAlchemy 模型 + `bootstrap.py`，保证 schema 与代码同源。

### 2.3 为什么是 ChromaDB（且必须子进程隔离）
Chroma 轻量、可嵌入、API 简单，适合中小知识库。但它 1.5.9 的 Rust 绑定在 **Windows 上偶发原生崩溃（segfault）**，且 segfault 无法被 Python `try/except` 捕获——会直接拖死主进程。解决方案：**所有 Chroma 操作经 `chroma_runner.py` 子进程隔离**，子进程崩溃只影响自身，主进程拿到结构化错误 JSON 后优雅降级（返回空检索 + 友好提示，不崩服务）。

### 2.4 为什么统一走阿里云百炼 OpenAI 兼容端点
- **中文羽毛球域能力强**：qwen 系列对中文商品参数、型号别名的语义理解优于同规格开源模型。
- **一个端点三种能力**：chat / embedding / rerank 全走百炼，凭证统一、调用简单。
- **成本可控**：检索侧（向量召回 + BM25 + 启发式精排）**零 LLM 调用**；只在 rerank 与最终生成时才调用模型。

### 2.5 为什么自研黄金集而不是只接 Ragas/DeepEval
Ragas 0.4.3 与百炼端点**结构性不兼容**（其 `generate_with_schema` 走 litellm/instructor，触发百炼不支持的 `n=3` 多采样 → 400）。因此以**自研确定性黄金集**为主指标（可复现、可审计、权重透明），DeepEval 仅作独立裁判佐证（且须同步串行跑，否则并发撞限流丢条）。

---

## 三、技术亮点

1. **双前端 + 匿名登录**：用户聊天端无需注册，前端自动注册 guest 用户拿 JWT 并 localStorage 缓存；WS 认证改首条消息（`{"type":"auth","token":...}`），避免 token 进 URL 日志。
2. **Chroma 子进程隔离 + HNSW 自愈**：segfault 不拖死主进程；`add` 模式检测到 HNSW 损坏自动清库重试，`search/delete` 损坏只降级绝不丢向量。
3. **推荐引擎防幻觉**：选品候选**参数只来自 `t_product.specs`**，SQL 硬过滤 + 加权评分 + 硬规则，LLM 只负责"解释"，不负责"编造型号/参数"。
4. **意图四分类分流**：`greeting / offtopic / badminton_general / equipment` 四类，闲聊与离题不触发检索与推荐，省 token 且避免乱答。
5. **跨会话用户画像**：独立 `t_user_profile` 表，跨多轮/多会话记住用户水平、打法、预算、身体状况，下次对话自动复用。
6. **流式渲染独立 ref（Vue3 最佳实践）**：用独立 `streamingText = ref('')` 直绑模板，绕开数组嵌套 Proxy 响应式链，流式最平滑。
7. **安全加固**：密码 MD5→bcrypt（带旧密码自动迁移）、`SECRET_KEY` 强制环境变量、CORS 限定域名、登录/注册限流、上传文件魔术字节校验。
8. **输出护栏 `output_guard`**：正则软改写"最强/吊打/闭眼入"等绝对化夸大表述，拦截模型自发夸大，零误伤合规用法。
9. **评测诚信闭环**：三角验证（确定性黄金集 + 独立 LLM 裁判 + 框架如实排除），所有分数标注前提与边界。

---

## 四、RAG 系统（核心 · STAR 法则）

### S — Situation（背景）

羽智选是一个**羽毛球装备智能导购**系统，业务仅覆盖 4 品类（球拍 / 球线 / 羽毛球 / 球鞋），不含交易。它面临几个真实挑战：

- **知识分散**：选拍知识、参数术语、型号对比、训练安全分散在多份文档里；
- **参数复杂**：重量等级（3U/4U/5U）、平衡点（头重/均衡/头轻）、中杆硬度、拉线磅数等，**错一个参数就误导用户**；
- **易幻觉**：直接让 LLM 推荐球拍，会编造不存在的型号或错误参数；
- **冷启动**：知识库需从零向量化，且 Windows 上 Chroma 易损坏；
- **中文域 + 低成本**：需在中文场景准确，且控制 API 费用。

### T — Task（任务）

构建一套**可靠**的 RAG 导购系统，同时满足：

1. 知识问答准确、有出处；
2. 选品推荐结构化、参数真实（防幻觉）；
3. 闲聊/离题被正确分流，不浪费检索与生成；
4. 流式体验顺滑；
5. 可评测、可量化、诚信可审计；
6. 工程韧性强（不崩、可恢复）。

### A — Action（架构与设计细节）

#### A1 总体架构：双路检索融合

系统不是"单一向量库问答"，而是**两条并行的检索/生成路径在 AI 层汇合**：

```
用户 Query
   │
   ├─ 路 A：知识库向量检索（Chroma，子进程隔离）→ 知识片段 context_docs
   │
   └─ 路 B：结构化商品推荐引擎（SQL 硬过滤 + 加权评分 + 硬规则）→ recommended_products
                                              （参数只来自 t_product.specs，零幻觉）
   │
   ▼
AI 组装层：知识资料 + 候选装备卡 + 用户画像 → LLM 生成
```

**为什么双路**：知识问答（"羽毛球线径怎么选"）与选品推荐（"预算800双打后场进攻拍"）是本质不同的任务。路 B 不依赖向量库，纯 SQL——即使知识库为空，只要 DB 有商品，推荐仍能工作（"推荐引擎活着，知识补给线断了"的韧性设计）。

#### A2 查询分析（analyze_query）

入口先做结构化分析，产出 `QueryAnalysis`：

- **同义词扩展**：如"进攻拍"→"攻击型/后场"，但带守卫 `_SHUTTLE_EXCLUDE` 避免裸"球"歧义展开；
- **上下文补全**：结合历史轮次补全省略（多轮"那预算加到1000呢"）；
- **品类推断** `category`：羽拍/球线/球/鞋，用于后续 where 预过滤；
- **型号 token 提取** `extract_model_tokens`（rag_pipeline.py:209）：用正则抽出 ASTROX / 天斧 / JS-12 等，供路 B 精准匹配 DB；
- **意图分流** `classify_question_scope`（rag_pipeline.py:363）：输出四类之一。

#### A3 双路召回

- **Dense×2**：两个稠密向量表示提升语义覆盖；
- **Keyword 召回改 BM25**（bm25_scores，rag_pipeline.py:624）：

```python
def bm25_scores(query_tokens, corpus, doc_freq, doc_lens, k1=1.5, b=0.75):
    # 标准库实现，无新依赖；IDF 在"类别语料"内计算，结果归一化到 [0,1]
    # k1 控制词频饱和度（1.5=适度），b 控制文档长度归一化（0.75=标准）
```

**为什么 BM25 替代纯 token 覆盖率**：BM25 用 IDF 区分"羽毛球"这种高频词与"ASTROX"这种判别词，比"覆盖率"更准，且可解释、零依赖。

#### A4 融合：RRF（Reciprocal Rank Fusion, k=60）

```text
RRF(d) = Σ_over_runs  1 / (k + rank_i(d))      k = 60
```

**为什么 k=60**：经验值。k 太小→高排名文档权重被过度放大、单一路主导；k 太大→所有文档趋于平权、融合失效。60 是 IR 界常用平衡点，让 dense 与 lexical 两路贡献可加、互不碾压。

#### A5 六维启发式精排

融合后做加权精排（rag_pipeline.py 内）：

```text
final_score = 0.40·rrf_norm      # 融合排名（主导）
            + 0.15·dense         # 语义相似度
            + 0.15·lexical       # 词面命中
            + 0.10·title         # 标题命中
            + 0.10·metadata      # 元数据（品牌/品类/型号）
            + 0.10·model         # 型号 token 命中
```

权重归一化后求和为 1.0。**设计要点**：
- **rrf 占 0.40 主导**：因为它已综合两路排名，最稳健；
- **短查询（≤6 字）阈值自适应 ×0.7**：短词（"进攻拍"）天然歧义高，降低置信阈值避免误召回；
- **型号/对比类低置信度不兜底**：宁可返回空，也不硬推一个可能错的型号（防幻觉红线）。

#### A6 语义重排（Cross-Encoder, 主进程隔离）

`services/rerank.py` 调用 `qwen3-rerank` 原生端点，对**已召回候选**做二次语义排序：

```python
# 仅在主进程 safe_search 内对已召回候选重排；隔离于 chroma 子进程
# 任意异常/非200/超时 → 返回 None → 优雅降级回启发式排序
```

**为什么隔离 + 降级**：rerank 是"锦上添花"，绝不能因为 rerank 服务抖动而让整个检索失败。故障只退回六维启发式，检索链路不受影响。

#### A7 意图分流与分支处理

`ai_service.py` 按 `classify_question_scope` 结果走不同分支：

| 意图 | 处理函数 | 行为 |
|---|---|---|
| `greeting` | `_handle_chitchat`（:392） | 轻量问候，不检索不推荐 |
| `offtopic` | `_handle_offtopic`（:417） | 边界声明，引导回装备话题 |
| `badminton_general` | `_handle_badminton_general`（:447） | 羽球周边知识，不强拉装备 |
| `equipment` | 完整 RAG + 推荐 | 走路 A + 路 B 全链路 |

**为什么分流**：闲聊若误入重路径会触发"推荐整列商品"的乱答；离题问题若进检索会返回无意义兜底。分流省 token、提准率、保体验。

#### A8 防幻觉设计（最关键）

- 路 B 候选参数**只来自 `t_product.specs`**，LLM 看不到"自己编的参数"的入口；
- 知识资料与候选装备卡**结构化注入** system prompt，而非让 LLM 自由发挥；
- **硬规则**（`_spec_fit` 覆盖全 4 品类，recommendation.py:392）：
  - 新手不推超硬中杆；
  - 膝盖敏感不推低缓震鞋；
  - 双打防守不推极端头重 3U 拍；
  - 球线按线径/打法适配、羽毛球按毛片/水平适配。

#### A9 跨会话用户画像

独立表 `t_user_profile`（与 `t_user` 一对一，不改任何现有表/列）：

```python
_load_profile_constraints(db, user_id)   # 读 → GuideConstraints
_merge_profile_into(...)                  # 本次优先·画像补缺·身体情况并集
_format_profile_text(...)                 # 画像 → 中文提示注入 system prompt
_persist_profile(db, user_id, fresh)      # 仅合并本轮新约束，空不写
```

实现"这次说'我是新手'→ 下次对话自动记得"，个性化跨会话生效。

#### A10 输出护栏 output_guard

`server/services/output_guard.py` 的 `sanitize_superlative(text)` 正则软改写绝对化表述（最强/最便宜/必买/闭眼入…），**只拦模型自发的夸大宣称，不拦回声用户原句**。接入点覆盖所有答案返回（非流式 7 处 + 流式主路径 1 处），线上 + 离线验证零误伤合规用法。

#### A11 工程韧性

- **HNSW 自愈**：`add` 模式检测到 `Error loading hnsw index` → 自动 `rmtree(chroma_db)` + 重建 + 重试一次；`search/delete` 损坏只返回结构化错误由上层降级（不清库=不丢向量）；
- **子进程隔离**：chroma 的 segfault 不拖死 FastAPI；
- **管道 UTF-8**：主进程 `json.dumps(payload).encode('utf-8')` 纯字节 → 子进程 `sys.stdin.buffer.read().decode('utf-8')`，杜绝 Windows GBK 乱码。

### R — Result（结果）

以**修正后（评测有效的）黄金集**为尺度，qwen3.7-plus 端到端跑 64 条球拍子集：

| 指标 | 数值 |
|---|---|
| **确定性综合 overall** | **0.882** |
| routing（路由准确） | 1.00 |
| general_training_safety | 0.909 |
| recommendation（推荐） | 0.899 |
| grounding_policy（边界声明） | 0.891 |
| parameter（参数解读） | 0.856 |
| comparison（对比） | 0.813 |
| product_fact（商品事实） | 0.778 |

**DeepEval 独立裁判**（三角验证佐证）：Faithfulness **0.996** / Hallucination **0.011** / AnswerRelevancy 0.82——印证"高忠实、低幻觉、相关好"。

**唯一真弱点**（三角验证共同定位）：source_hit / ContextualRecall 偏低 = **来源标注与检索召回完整性不足**，而非答案内容问题。这是后续合法提分方向（强化来源标注、补检索覆盖），不是刷分。

**成本**：检索侧（向量召回 + BM25 + 六维精排 + RRF）零 LLM 调用；仅 rerank + 生成为百炼 API 费用。

---

## 五、STAR 法则 · 简历/面试精炼版

> **Situation**：从零搭建羽毛球装备（4 品类）智能导购 RAG 系统，知识分散、参数复杂、LLM 易幻觉、中文域且需控成本。
>
> **Task**：构建可靠导购 RAG——知识问答准确有出处、选品结构化防幻觉、闲聊离题正确分流、流式体验顺滑、可评测诚信。
>
> **Action**：
> - 设计**双路检索融合**——路 A 知识库向量检索（Chroma 子进程隔离防 segfault），路 B 结构化商品推荐引擎（SQL 硬过滤+加权评分+硬规则，参数只来自 DB，杜绝幻觉）；
> - 召回用 **Dense×2 + BM25**，融合用 **RRF(k=60)**，精排用**六维启发式权重**（rrf 主导 0.40），短查询阈值自适应、低置信度不兜底；
> - 接入 **qwen3-rerank Cross-Encoder 重排**（主进程隔离，失败优雅降级）；
> - **意图四分类分流**（闲聊/离题/周边/装备）省 token 防乱答；
> - **跨会话用户画像**（独立 `t_user_profile` 表）实现个性化；
> - **output_guard** 拦截绝对化夸大表述；
> - 工程韧性：HNSW 自愈 + 子进程隔离 + UTF-8 管道。
>
> **Result**：确定性黄金集综合 **0.882**（64 条领域子集）；DeepEval 独立裁判 Faithfulness **0.996** / Hallucination **0.011**，三角验证印证高忠实低幻觉；检索侧零 LLM 调用控成本。评测以"修正评测有效的黄金集"为尺度（原始版由初始化模型混入不存在来源的源关键词，已修正使评测有效），诚信可审计。

---

## 六、可改进方向（诚实列出）

1. **source_hit 提升**：让 `_build_sources` 把 `page_content` 也写入 sources（合法溯源改进），system prompt 强化显式来源标注；
2. **温度对照实验**：补跑 0.4 / 0.6 对照 64 条，确认 0.2 是否最优（当前未做，不能断言"不用调"）；
3. **扩全品类黄金集**：当前仅球拍子集，补球线/羽毛球/球鞋子集增强覆盖面；
4. **Ragas 兼容性**：为百炼端点补齐 `BaseRagasLLM` 子类，纳入第三角验证；
5. **检索覆盖**：部分对比类问题（如 CMP002）未召回商品库，可加定向召回路由。

---

*文档基于 `server/`（rag_pipeline.py / vector_store.py / ai_service.py / recommendation.py / config.py / output_guard.py）逐文件核实，参数与函数名均对应实际代码。*
