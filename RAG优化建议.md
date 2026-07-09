# 羽智选 RAG 系统优化建议（2026-07-09 代码复核版）

> 本文基于对整个 RAG 管线的逐文件通读（已实际定位代码行号核对），给出可执行的优化路线图。
> 覆盖：`rag_pipeline.py` / `ai_service.py` / `vector_store.py` / `recommendation.py` / `file_parser.py` / `chroma_runner.py` / `routers/chat.py` / `routers/knowledge.py`。
>
> **重要前提**：你的系统**已经具备不少业界标准能力**（多路召回 + RRF 融合、六维启发式精排、意图四分类分流、防幻觉约束、子进程隔离防 segfault、硬规则推荐）。下面的建议是"从 80 分到 95 分"，不是推倒重来。请按优先级推进，**不要一次性大改核心架构**（参见协作约束：后端核心加载方式改动需先对齐）。

---

## 〇、总体评估

| 维度 | 当前状态 | 评级 | 一句话 |
|---|---|---|---|
| 召回（Recall） | dense×2 + keyword 三路 + RRF(k=60) | ✅ 良好 | 已是标准 hybrid 做法，主要短板在精排 |
| 精排（Rerank） | 六维启发式加权，**无语义重排** | ⚠️ 中等 | 最大质量提升点，Cross-Encoder 缺席 |
| 生成（Generation） | 知识优先 + 候选封顶 + 防幻觉 | ✅ 良好 | 约束到位，缺可观测/引用跳转 |
| 分块（Chunking） | 型号/FAQ 优先 + 递归字符切分 | 🟡 基础 | 长文缺语义边界感知 |
| 推荐（Recommend） | SQL 硬过滤 + 四维加权 + 硬规则 | ⚠️ 性能隐忧 | 逻辑对，但每次全表扫描 |
| 工程健壮性 | 子进程隔离 + HNSW 自愈(add) + 鉴权 | ⚠️ 有缺口 | HNSW 自愈只覆盖 add 模式 |
| 评估闭环 | 无标注集 / 无指标 / 无 RAGAS | ❌ 空白 | 无法量化"改了有没有更好" |

**结论**：系统**还能明显优化**，且性价比最高的是 **P0-1（语义重排）** 和 **P1-4（推荐引擎 DB 层过滤）** 这两件事。下面分层展开。

---

## 一、P0 —— 质量/正确性关键项（建议优先做）

### P0-1：引入语义重排（Cross-Encoder / Reranker），替换"纯启发式精排"

**当前代码（已核实）**：
`rag_pipeline.py:475-525` 的 `rerank_candidates` 完全是加权求和：

```python
candidate.final_score = (
    0.40 * rrf_norm          # RRF 融合名次
    + 0.15 * dense_norm       # 向量相似度
    + 0.15 * candidate.lexical_score
    + 0.10 * candidate.title_score
    + 0.10 * candidate.metadata_score
    + 0.10 * candidate.model_score
)
```

函数 docstring 自己写着 *"后续可替换为 Cross-Encoder"*——但至今没替换。

**为什么这是最大提升点**：
- 启发式加权是"相关性代理"，它**永远分不清**"提到同一批型号词但语义相反/无关"的 chunk。比如用户问"进攻拍推荐"，一个 chunk 写"**不适合**进攻的防守拍 List"，因为型号词覆盖高，启发式会给它高分，排序可能压过真正的进攻拍评测。
- Cross-Encoder（或重排模型）把 `(query, doc)` **拼在一起**过一遍 transformer，直接输出相关性分数——这是目前公认能带来最大检索质量跃升的单点改动（多项 RAG 基准显示 MRR@10 提升 5~15 个点）。

**怎么做（低成本、可回退）**：
1. 你的 embedding 走的是 DashScope `text-embedding-v4`。DashScope / 通义也提供 **reranker 模型**（如 `gte-rerank` / `bce-reranker` 类）。优先评估用同一服务商的 reranker，省去自建推理。
2. **不要替换、要叠加**：保留现有六维启发式作为"粗排/召回过滤"（它便宜、能先砍掉明显无关项），在其输出的 top-N（如 30 条）之上跑 Cross-Encoder，取重排后的 top-8 进 LLM。这就是标准 "bi-encoder recall + cross-encoder rerank" 两段式。
3. 在 `rerank_candidates` 内加一个开关 `USE_RERANKER`，默认 False；接好模型后切 True，并保留启发式作为降级路径（reranker 不可达时回退，防止端点 500）。

**权衡（trade-off）**：
- 延迟：Cross-Encoder 比向量检索慢，但只对 top-30 跑，端到端增加通常 200~600ms，可接受。
- 成本：每次问答多一次 reranker 调用。可对"短查询/高置信命中"跳过（启发式已足够时不再重排）。

---

### P0-2：修复 HNSW 自愈"只覆盖 add 模式"的真实缺口

**当前代码（已核实）**：`chroma_runner.py:144-148`

```python
# 注释写："add/search/delete 操作都可能碰到 HNSW 索引损坏，统一走自动恢复"
if mode == "add":
    data = _wipe_chroma_and_retry(handler, payload)   # 只有 add 自愈
else:
    data = handler(payload)                             # search/delete 直接跑，损坏即报错
```

**问题**：
- 注释声称 search/delete 也自动恢复，但实现只给 `add` 套了 `_wipe_chroma_and_retry`。search 或 delete 碰到 HNSW 损坏时，**不会自愈**，直接抛错。
- 更关键：**不能无脑把 `_wipe_chroma_and_retry` 也套到 search/delete**。`_wipe_chroma_and_retry` 的行为是**清空整个 chroma_db**——如果 search 时损坏就清空，等于把全部向量知识库删光，这是灾难性数据丢失。

**正确修复方向**：
1. `add` 模式：维持现有"损坏→清空→重试一次"（写操作清空后还能靠重新向量化恢复，可接受）。
2. `search` / `delete` 模式：检测到 HNSW 损坏时，**不要清空**，而是返回结构化错误 `{"_error": "HNSW_CORRUPTED", "mode": "search"}`，由上层（`vector_store` / `routers/knowledge`）决定降级策略——例如 search 降级为"仅用推荐引擎 + 诚实告知用户知识检索暂不可用"，并打告警日志，提醒运维人工重建向量库。
3. 顺手把那行**误导性注释改对**，明确"add 自愈、search/delete 报错不自愈"。

---

## 二、P1 —— 质量/性能改进项（性价比高）

### P1-1：关键词召回不要"全量拉类别到内存"

**当前代码（已核实）**：`vector_store.py:249-289` 的 `_keyword_recall`

```python
if analysis.category:
    get_kwargs["where"] = {"category": analysis.category}
data = self.vectorstore.get(**get_kwargs)   # ← 把该类别全部 chunk 拉进内存
# 然后循环 data["documents"] 逐条算 _token_coverage(...)
```

**问题**：`collection.get(where=category)` 会**把整个类别的所有文档+元数据搬到 Python 内存**，再本地算 token 覆盖。知识库现在是 153 chunk（1 个文件），无所谓；但当你按规划上传 yonex/victor/li_ning 三大球拍库 + 术语词典（预计数千 chunk）后，每次查询都搬全量，内存与延迟都会恶化。

**优化方案（二选一，推荐 A）**：
- **A（最小改动）**：keyword 召回也走 Chroma 的 `query`（带 `where={"category": ...}` 预过滤 + `query_texts`），让 Chroma 在索引层做近似/关键词匹配，返回 top-K。这样天然只在索引层工作，不搬全量。
- **B（更强但更重）**：在进程内建一个**一次性 BM25 索引**（`rank_bm25`），索引全部 chunk 的 token；keyword 召回直接 BM25 打分取 top-K。BM25 比当前自写的 `_token_coverage` 更严谨（考虑词频+逆文档频率），且索引常驻、查询 O(log) 级。代价是多维护一个索引结构与增量更新逻辑。

### P1-2：推荐引擎改在数据库层做硬过滤（去掉全表扫描）

**当前代码（已核实）**：`recommendation.py`
- `retrieve_candidates` 第 45 行：`query = db.query(Product).filter(Product.status == 1)` … 第 52 行 `return query.all()`（**拉全表**后在 Python 里按约束过滤）
- `match_products_for_query` 第 124 行：`for product in db.query(Product).filter(Product.status == 1).all():`（**又拉一次全表**）

商品表已 1184+ 条，每次问答两条查询各拉全表，纯属浪费。

**优化方案**：
1. 把 `weight_class / shaft_flex / balance_type / cushion_score / gauge / material` 等约束**翻译成 SQLAlchemy 的 `filter()` 条件**，让 SQLite 在 SQL 层过滤，只取候选子集回 Python。
2. 给常用过滤列加索引（`CREATE INDEX` on `status`, `category`, `brand`）。
3. 对于"预算区间""重量等级"这类范围条件用 `between_`；对于"新手不推硬中杆"这类硬规则，先 SQL 过滤再用 Python 算评分——**先窄后宽**。
4. 两个函数可共享同一个"SQL 预过滤"helper，避免重复全表扫描。

### P1-3：合并 `chat()` 与 `chat_stream()` 的重复逻辑

**当前代码（已核实）**：`ai_service.py`
- `chat()` 第 318 行起，`chat_stream()` 第 461 行起。
- 两者**几乎逐行重复**：`analyze_query` → 四类 scope 分支 → 写 `ChatMessage`（user/assistant）→ `db.commit()` → 组装返回。差异仅在：chat 返回 dict，chat_stream 用 `yield json.dumps(...)` 推 SSE。

**问题**：双路维护，改一处易漏另一处（例如你之前加的"LLM 失败降级兜底"在 chat 里有，需确认 chat_stream 也同步了）。

**优化方案**：
1. 抽一个内部协程/方法 `_resolve_and_persist(user_id, session_id, message, analysis) -> (user_msg, answer, sources, recommended)`，负责"分析→检索→生成→落库"的全部共享逻辑。
2. `chat()` 调它一次，把结果包成 dict 返回。
3. `chat_stream()` 调它一次，再把 `answer/sources/recommended` 用 SSE 流式推出。
4. 这样降级兜底、闲聊分支、型号未收录诚实回答等逻辑**只写一遍**。

### P1-4：用户画像跨会话持久化（个性化只活在单次问答内）

**当前状态（已核实）**：`ai_service.py` 每次只调 `_recent_history(db, user_id, session_id)` 拿近几轮历史；`t_user` 表无羽毛球维度字段；约束完全来自"本次提问 + 当前 session 历史"。

**问题**：用户第一次说"我是新手、预算 300、膝盖不好"，第二次进来系统就忘了，又得重说。个性化无法沉淀。

**优化方案（渐进）**：
1. 新增 `t_user_profile(user_id, skill_level, budget_range, knee_sensitive, pref_brands, play_style, updated_at)`。
2. 在 `analyze_query` 之后、检索之前，把"本次抽取到的约束"与"历史画像"做**合并**（本次优先，缺失填画像默认值）。
3. 每次对话结束抽取稳定约束写回画像（可用 LLM 轻量抽取，或正则匹配预算/水平关键词）。
4. 前端可在"我的"页展示/编辑画像，形成闭环。

### P1-5：建立最小评估闭环（否则"优化"无法证明有效）

**当前状态**：无标注集、无 Recall@K / MRR / NDCG、无 faithfulness 校验、无 RAGAS。你现在的每次改动都只能"凭感觉看回答好不好"。

**优化方案（低成本起步）**：
1. 建一个 `eval/golden_set.jsonl`，每条含 `{query, expected_model_or_topic, must_mention[], must_not_mention[]}`，先攒 30~50 条高频真实问题。
2. 写一个简单的 eval 脚本：跑 `safe_search` + `ai_service`，对比返回是否命中 `must_mention`、是否误触 `must_not_mention`，统计 Recall@5 / MRR。
3. 后续接 RAGAS（`context_precision` / `faithfulness` / `answer_relevancy`）做自动打分。
4. **价值**：P0-1 的 Cross-Encoder 上线前后，用同一 golden_set 跑分，就能用数字证明"改了更好"。

---

## 三、P2 —— 增强项（锦上添花，按需做）

### P2-1：分块加语义边界感知
当前 `file_parser` + `vector_store._build_documents` 用 `RecursiveCharacterTextSplitter`，对型号/FAQ 已有优先切分。对长文（战术/训练/规则）建议：
- 结构化文档（Markdown）按 **heading 层级**切分，chunk 自带"父标题"上下文；
- 加小重叠（overlap=100~200）避免跨边界信息断裂；
- 表格/参数表整体保留不切断。

### P2-2：查询侧增强（HyDE / 查询改写）
- `dense_enhanced` 目前是 query 改写。可加 **HyDE**（先让 LLM 生成一段"假设性答案"，再用其 embedding 去检索），对"抽象诉求"（如"手感扎实的拍"）召回更准。
- 多语言/同义词：品牌别名映射已有，建议抽成**可配置同义词表**（管理后台可编辑），而非硬编码在 `rag_pipeline.py`。

### P2-3：生成层增强
- **引用可追溯**：答案中必须标注 `chunk_id`，前端点击可跳转知识源（目前 `sources` 已有但前端未必渲染跳转）。
- **超参治理**：`temperature` / `top_p` 集中配置，装备推荐类问题用更低 temperature 防自由发挥。
- **长上下文摘要**：超长历史用 LLM 压缩为"用户画像摘要"再带入，节省 token。

### P2-4：可观测与反馈闭环
- 每次查询落一条检索日志：query / 召回候选数 / 命中源 chunk_id / 是否触发 reranker / 用户最终是否点击推荐商品。
- 点击/收藏推荐商品 = 正反馈信号，可反过来微调推荐权重（在线学习雏形）。

---

## 四、建议的推进顺序（不要一次全做）

| 阶段 | 做哪些 | 预期收益 | 风险 |
|---|---|---|---|
| **第一步** | P0-1 语义重排（叠加式，带开关+降级） | 检索质量最大跃升 | 低（不破坏原有逻辑） |
| **第一步** | P0-2 修 HNSW 自愈缺口（注释+search/delete 不自愈只报错） | 消除潜在数据丢失风险 | 极低（纯防御） |
| **第二步** | P1-2 推荐引擎 DB 层过滤 | 延迟下降、可扩展性 | 低 |
| **第二步** | P1-3 合并 chat/chat_stream | 维护性 | 低（需补测试） |
| **第三步** | P1-5 评估闭环（golden_set + 脚本） | 让后续所有改动可量化 | 低 |
| **第三步** | P1-1 keyword 召回改 Chroma query/BM25 | 内存/延迟 | 中（需验证召回质量不降） |
| **第四步** | P1-4 用户画像持久化 | 个性化体验 | 中（涉及表结构+前端） |
| **第五步** | P2 各项 | 体验打磨 | 视具体项 |

---

## 五、已具备、请勿动的核心能力（避免好心改坏）

- ✅ **多路召回 + RRF 融合**（dense_original / dense_enhanced / keyword，k=60）——已是标准 hybrid。
- ✅ **六维启发式精排**——作为 Cross-Encoder 的粗排层继续保留，别删。
- ✅ **意图四分类分流**（greeting / offtopic / badminton_general / equipment）——避免无效 RAG，效果好。
- ✅ **防幻觉约束**（参数只引用候选真实字段、型号未收录诚实说明、对比类低置信不兜底）。
- ✅ **子进程隔离 chroma_runner**——防 segfault 拖死主进程，是 Windows 下的关键设计。
- ✅ **推荐硬规则**（新手不推超硬杆、膝盖敏感不推低缓震鞋、双打防守不推极端头重 3U 拍）。

---

*复核说明：本报告所有"当前代码"结论均来自 2026-07-09 对仓库实际文件的行号核对，非凭印象。如需针对某一项直接落地实现，告诉我具体编号（如"做 P0-1"），我再给出可执行的代码改动方案并与你对齐后动手。*
