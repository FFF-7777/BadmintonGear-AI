# 羽智选 RAG 系统精研报告

> 对象：`server/` 下的 RAG 检索链路、知识库入库链路、结构化商品推荐引擎、Prompt 组装与生成。
> 方法：逐文件通读 + 真实运行态核验（登录后台、调用线上接口、冷启动子进程）。
> 时间：2026-07-08

---

## 0. 结论速览（TL;DR）

你的 RAG 系统**架构设计是生产级的，但当前运行态是"停摆"的**：

1. **致命根因：缺失 `.env` → `OPENAI_API_KEY` 为空**。这导致三件事同时失效：
   - 知识库文件永远无法向量化（上传即 `status=2` 失败）→ **知识库为空**；
   - 向量检索（dense + keyword）被代码主动禁用 → 检索降级为空；
   - LLM 问答在 key 非空路径下发起对不可达端点的 HTTP 请求，**无超时挂死**（实测 >5 分钟）。
2. **知识库为空是证实事实**：`chroma_db/` 目录 0 字节，`t_knowledge_file` 表 `count=0`。RAG 的"知识增强"部分当前名存实亡——线上 AI 问答退化成"商品库 + LLM 通用知识"。
3. **设计亮点真实存在**：子进程隔离 Chroma 防 segfault、双路召回 + RRF 融合、查询分析（同义词扩展 + 上下文补全 + 品类推断）、商品推荐用 SQL 硬过滤 + 规则杜绝 LLM 编造参数——这些都是对的。
4. **若干可落地缺陷**：LLM 调用无超时、删除接口未走子进程隔离、`keyword_recall` 全库内存扫描无索引、精排分数尺度不一致、置信度阈值对短 query 失效等。

下面逐段精研，并给出带文件行号的问题清单与改进建议。

---

## 1. 系统架构总览

数据流向（一次 `/api/chat/send` 为例）：

```
用户消息
  │
  ├─[主进程] _build_recommendations()  ──►  classify_guide_intent() + extract_constraints()
  │        │                                （纯文本规则，不依赖外部服务）
  │        └─► recommend_products(db, ...)  ──► SQL 硬过滤(t_product) + 加权评分 + 硬规则
  │                                          （走 SQLite，不需要 API key）
  │
  ├─[子进程] safe_search(message)  ──► 启动 services.chroma_runner 子进程
  │        │                                │
  │        │                                ├─ analyze_query()      查询分析（纯逻辑）
  │        │                                ├─ _dense_recall ×2     双塔向量召回（需 embedding key）
  │        │                                ├─ _keyword_recall       词元覆盖召回（需 chroma 实例）
  │        │                                ├─ reciprocal_rank_fusion  RRF 融合 k=60
  │        │                                └─ rerank_candidates     轻量精排 + 置信度阈值
  │        └─ 返回 documents（降级时为空）
  │
  └─[主进程] llm.invoke(_build_rag_messages(...))  ──► 组装 Prompt
             │  知识资料块（来自检索结果）
             │  候选装备块（来自推荐引擎，真实 specs）
             └─ 返回 answer + sources + recommended_products
```

**两条相互独立的检索路线**：
- **路线 A：知识库向量检索**（RAG 经典形态，依赖 Chroma + Embedding）。
- **路线 B：结构化商品推荐引擎**（把用户约束翻译成 SQL，依赖 SQLite + 规则）。

这是本系统的核心设计哲学——**商品参数只来自结构化数据库（`t_product.specs`），绝不靠 LLM 生成**，从架构上消灭"幻觉装备"。

---

## 2. 检索链路逐段精研

### 2.1 Query Analysis（查询分析）— `rag_pipeline.py:114`

`analyze_query(question, history)` 产出 `QueryAnalysis`，包含：

```python
@dataclass(frozen=True)
class QueryAnalysis:
    original_query: str          # 原始问题
    normalized_query: str        # 去空白
    expanded_query: str          # 同义词扩展后
    category: Optional[str]      # 推断的品类（用于前置过滤）
    queries: List[str]           # 实际送检索的查询变体（最多 2 条）
    keywords: List[str]          # token 列表
```

三个子能力：

**(a) 上下文补全（`analyze_query:117-122`）**
若当前问题短（≤14 字）或含指代词（"这个/那个/它/怎么…"），把**上一条 user 消息**拼到前面。例如：
- 历史 user："预算 800 想选一支速度快的球拍"
- 当前 user："球拍中杆硬度呢？"
- → `contextual_query = "预算 800 想选一支速度快的球拍 球拍中杆硬度呢？"`

> **为什么这么做**：羽毛球选品对话天然多轮、大量代词指代。短 query 直接检索会严重失准，补上下文是低成本高收益的做法。

**(b) 同义词扩展（`_expand_query:95`）**
基于 `SYNONYM_GROUPS`（如 `("球拍","拍子","羽毛球拍")`），把 query 里没出现的同义词补进去。扩展后作为第二路 dense 召回的 query。

**(c) 品类推断（`infer_category:83`）**
用 `CATEGORY_KEYWORDS` 统计每个品类关键词命中数，`max` 取最高；得 0 分则返回 `None`（不强行过滤）。这个 `category` 后续用于 Chroma 的 `where={"category": ...}` 前置过滤。

> **概念：前置过滤（pre-filtering） vs 后过滤**。这里是在向量召回**之前**用元数据过滤，缩小候选集、降低噪声。代价是：若推断错品类，会直接漏掉正确文档（代码对此有兜底：dense 召回若过滤后为空，会再无条件重查一次，见 `vector_store.py:209`）。

### 2.2 多路召回 — `vector_store.py:256`

`search()` 同时跑 3 路召回，每路取 `RAG_CANDIDATE_K=12` 个候选：

| 路线 | 方法 | 依赖 | 说明 |
|---|---|---|---|
| `dense_original` | `_dense_recall(queries[0])` | Embedding + Chroma | 原始问题向量召回 |
| `dense_enhanced` | `_dense_recall(queries[1])` | Embedding + Chroma | 扩展问题向量召回（仅当扩展≠原始） |
| `keyword` | `_keyword_recall(analysis)` | Chroma 全量 `get()` | 词元覆盖召回（lexical） |

**dense 召回（`_dense_recall:196`）**：
```python
kwargs = {"k": candidate_k}
if category:
    kwargs["filter"] = {"category": category}   # Chroma 元数据精确过滤
results = self.vectorstore.similarity_search_with_relevance_scores(query, **kwargs)
```
`similarity_search_with_relevance_scores` 返回 `(document, relevance_score)`，score 是 Chroma 把 HNSW 距离归一化到 `[0,1]` 的分数（越接近 1 越相关）。

**keyword 召回（`_keyword_recall:219`）**：
```python
data = self.vectorstore.get(include=["documents", "metadatas"])  # 拉全库
query_tokens = tokenize(analysis.expanded_query)
for content, metadata in zip(data["documents"], data["metadatas"]):
    document_tokens = tokenize(content)
    coverage = len(query_tokens & document_tokens) / len(query_tokens)   # Jaccard 思想
    title_coverage = ...
    score = min(1.0, coverage * 0.8 + title_coverage * 0.2)
```

> **重要概念澄清：这里的 keyword 召回 ≠ BM25。**
> 它用的是 `|Q∩D| / |Q|` 的覆盖度（类似 Jaccard 的简化），**没有 TF、没有 IDF、没有文档长度归一化**。
> - BM25 公式：`score(D,Q) = Σ IDF(qi) · (f(qi,D)·(k1+1)) / (f(qi,D)+k1·(1−b+b·|D|/avgdl))`
> - 区别：BM25 用 **IDF** 压低高频词（如"球拍"）权重、用 **词频饱和** 防止重复词刷分、用 **文档长度** 归一化。本项目的覆盖度全部没做，所以"球拍"和"鹅毛"同权，长文档天然吃亏。
> - 优点：零依赖、可解释、快。缺点：召回精度明显弱于 BM25，尤其语料变大后。

**tokenize（`rag_pipeline.py:70`）**：中英文混合的轻量词元化——英文按 `\w+`，中文按"整段 + 二元组（bigram）"。例如"羽毛球拍" → `{"羽","毛","球","拍","羽毛","毛球","球拍"}`。这是规避专业分词依赖的实用方案，但 bigram 会引入噪声（"毛球"不是词）。

### 2.3 RRF 融合（Reciprocal Rank Fusion）— `rag_pipeline.py:175`

```python
def reciprocal_rank_fusion(routes, rrf_k=60):
    fused = {}
    for route_candidates in routes:
        for rank, candidate in enumerate(route_candidates, start=1):
            key = candidate_key(candidate)
            item = fused.setdefault(key, RetrievalCandidate(...))
            item.rrf_score += 1.0 / (rrf_k + rank)   # 核心公式
    return sorted(fused.values(), key=lambda i: i.rrf_score, reverse=True)
```

**概念讲透 RRF**：
- 公式：`RRF_score(d) = Σ_{r∈routes} 1 / (k + rank_r(d))`
- 直觉：一个文档在某路召回里排第 1，贡献 `1/(60+1)=0.0164`；排第 60，贡献 `1/120=0.0083`。多路都靠前 → 累加 → 靠前。
- **为什么 k=60？** Cormack et al. (2009) 的实证经验值。k 越大，**高排名的权重优势越被放大**，低排名贡献迅速衰减。k=60 对"前几名"足够敏感，又不会让第 1 名垄断。本项目 `RAG_RRF_K=60`（config:51）沿用该标准值。
- **RRF 的关键优势——对分数尺度不敏感**：dense 的 relevance_score（归一化距离）和 keyword 的 coverage（0~1）量纲不同、不可直接相加，但 **RRF 只看"排名"不看"分数"**，所以异质召回天然可融合。这正是混合检索（hybrid search）的标准做法。
- **去重**：用 `chunk_id`（或内容 hash）做 key，同一 chunk 在多路出现时合并，并把 `routes` 累积记录（用于可解释："该片段同时被向量和关键词命中"）。

### 2.4 轻量精排（rerank_candidates）— `rag_pipeline.py:208`

```python
candidate.lexical_score = _token_coverage(query_tokens, candidate.content)
title_score = _token_coverage(query_tokens, section_title)
rrf_score = candidate.rrf_score / max_rrf
candidate.confidence = max(lexical_score, 0.65*score + 0.35*lexical_score)
candidate.final_score = (
    0.35*rrf_score + 0.35*candidate.score + 0.25*lexical_score + 0.05*title_score
)
ranked = sorted(candidates, key=lambda i: i.final_score, reverse=True)
return [i for i in ranked if i.confidence >= threshold][:top_k]   # threshold=0.15
```

**问题点（精研重点）**：
1. **分数尺度不一致直接加权**：`final_score = 0.35*rrf_score + 0.35*score + 0.25*lexical + 0.05*title`。
   - `rrf_score` 是融合后的相对名次（范围约 `0~0.05`）；
   - `score` 是 dense 的 relevance（0~1）；
   - `lexical` 是覆盖度（0~1）。
   三者量纲不同却线性相加，权重比例实际被 rrf_score 的量级（很小）稀释——**0.35 的 rrf 权重几乎不起作用**。这是常见误区：RRF 已给出最终排序，再把它当一个弱特征加回去意义不大。
2. **confidence 阈值对短 query 失效**：短 query（如"球鞋"）tokenize 后可能只有 1~2 个 token，长文档极易 100% 覆盖 → `lexical_score=1.0` → `confidence=1.0` → 阈值 0.15 形同虚设。反之，长知识段落因 token 多、难全覆盖，lexical 偏低被压。
3. **代码注释说"后续可替换为 Cross-Encoder"**——这是正确方向，见 §9 改进建议。

> **概念：Cross-Encoder（交叉编码器）**。当前是"双塔/bi-encoder"思路的延伸：dense 用 query、doc 各自编码后算相似度；精排用 heuristic（lexical 加权）。Cross-Encoder 把 `query ⊕ doc` 拼接输入一个模型**联合打分**，能捕捉细粒度交互（如"进攻拍"和"防守拍"的语义对立），精度远高于 bi-encoder + heuristic，代价是慢（不能预计算 doc 向量），所以**只用于 rerank top-N（如 RRF 后的 top-20）**。标准 RAG 优化路径就是「bi-encoder 召回 → Cross-Encoder 重排」。

---

## 3. 知识库入库链路

### 3.1 入库流程（`knowledge.py:45` → `vector_store.py:139` → `chroma_runner.py`）

```
上传文件 → file_parser.parse_file() 解析文本
        → safe_add_documents(text, file_id, ...)   # 子进程隔离
            → chroma_runner._do_add()
                → vector_store_service.add_documents()
                    → _build_documents(): split_knowledge_sections() 优先按"编号问答"切分
                                         否则 RecursiveCharacterTextSplitter(chunk=500, overlap=50)
                    → vectorstore.add_documents(documents, ids=chunk_id)   # upsert
                    → 删除旧 chunk（幂等）
```

**亮点**：
- **FAQ 优先切分（`split_knowledge_sections:141`）**：识别 `1. 关于平衡点` 这类编号问答，按问题切块，块粒度贴合"一问一答"，比机械按字符切更利于检索。
- **幂等 upsert（`add_documents:161-172`）**：先 `add_documents`（成功），再删 `stale_ids`（旧版 chunk）。注释明确：失败保留旧索引，避免脏数据。
- **chunk_id 稳定**：`f"{file_id}:{index}:{hash16}"`，重传同文件可精确覆盖。

### 3.2 子进程隔离设计（核心亮点）— `vector_store.py:345-429` + `chroma_runner.py`

**背景**：chroma 1.5.9 的 Rust 绑定在部分 Windows 上对 HNSW 索引读写会**原生 segfault**，Python 的 `try/except` 捕获不到，会直接拖死 uvicorn。

**设计**：所有 Chroma 操作（检索/入库）放进独立子进程 `services.chroma_runner` 执行。`_run_chroma_subprocess` 用 `subprocess.run(..., timeout=40)` 跑子进程，子进程崩溃 → `returncode != 0` → 主进程拿到 `None` → 优雅降级（检索返回空、入库返回失败）。

```python
def _run_chroma_subprocess(payload, timeout=40):
    proc = subprocess.run([sys.executable, "-m", "services.chroma_runner"],
                          input=json.dumps(payload), capture_output=True,
                          text=True, timeout=timeout, cwd=str(BASE_DIR))
    if proc.returncode != 0:
        return None          # 子进程崩了，主进程只当"无结果"
    return json.loads(proc.stdout)
```

> **这是生产级稳健设计**：把"可能原生崩溃的外部依赖"关进沙箱，主进程永不被连累。值得肯定。

**但有一个隔离缺口（见 §8 P1-2）**：`knowledge.py:205` 的 `delete_knowledge` 直接在主进程调用 `vector_store_service.delete_by_file_id(...)`，绕过了子进程隔离——删除走主进程，若该环境真有 segfault，删除操作会拖垮主进程。

### 3.3 真实核验：知识库为空

```
$ ls -la server/chroma_db/        →  total 0   （0 字节，空目录）
$ sqlite t_knowledge_file count   →  0
$ sqlite t_product count          →  13
```

根因链：缺 `OPENAI_API_KEY` → `embeddings` property（`vector_store.py:73`）直接 `raise RuntimeError` → 子进程 `chroma_runner` 退出码非 0 → `safe_add_documents` 返回 `(0, "vector store subprocess crashed")` → 上传接口把 `kf.status=2`（失败）。**任何知识库上传都会失败**，知识库永远空。

---

## 4. 商品推荐引擎精研（`recommendation.py`）

这是系统最有价值的部分——**把自然语言选品意图翻译成可解释的结构化检索**，且参数 100% 来自 `t_product.specs`，杜绝 LLM 编造。

### 4.1 约束抽取（`rag_pipeline.py:359`）

`extract_constraints(text, history)` 从问题+上文抽：
- `category_ids`：球拍/球线/羽毛球/球鞋（1/2/3/4）
- `level`：新手/进阶/高手/专业
- `style`：进攻/防守/控制/均衡
- `play_type`：单打/双打/混双
- `budget_min/max`：正则解析「500-800」「800以内」「预算500」等
- `physical`：膝盖/脚踝/手腕/肩膀敏感

> 正则预算解析（`_extract_budget:326`）覆盖区间/上限/下限/单一数字四种，实用但对「性价比高」「便宜点」等模糊表述无能为力（合理取舍）。

### 4.2 SQL 硬过滤（`retrieve_candidates:37`）

```python
query = db.query(Product).filter(Product.status == 1)
if constraints.category_ids:
    query = query.filter(Product.category_id.in_(constraints.category_ids))
if constraints.budget_max is not None:
    query = query.filter(Product.price <= constraints.budget_max)
if constraints.budget_min is not None:
    query = query.filter(Product.price >= constraints.budget_min)
```

纯 SQL，确定性、可审计、零幻觉。

### 4.3 加权评分（`score_and_rank:206`）

四个维度（权重和归一化到 1）：
```python
_WEIGHTS = {"user_fit":0.25, "style_fit":0.20, "budget_fit":0.15, "spec_fit":0.15}
```
- `user_fit`：用户水平 vs 商品 `suitable_level`（缺字段给中立 0.7）
- `style_fit`：打法匹配（缺约束给 0.8）
- `budget_fit`：预算内越便宜分越高（≤0.85→1.0，≤1.0→0.75）
- `spec_fit`：细分参数加分（仅球拍/球鞋有逻辑，其他品类默认 0.8）

**硬规则（`_apply_hard_rules:118`）**——业务护栏：
- 新手不推超硬/硬中杆球拍（`shaft_flex in stiff/extra-stiff`）
- 膝盖敏感不推缓震 `<8.0` 的鞋
- 脚踝敏感不推低支撑鞋
- 双打防守不推极端头重 3U 拍

**可解释理由（`_build_reason:159`）**：每个候选产出中文适配理由（如"4U重量；头轻灵活；价格在区间内"），供 Prompt 引用。

> **问题点（§8 P2）**：`_WEIGHTS` 四项和 = 0.75（`user_fit0.25+style0.20+budget0.15+spec0.15`），归一化时除以 0.75 是对的；但 `spec_fit` 只对球拍/球鞋有细分逻辑，**球线、羽毛球品类 spec_fit 恒为 0.8**，导致这两类目排序区分度低（全挤在 0.8 附近）。

### 4.4 组合推荐多样性（`score_and_rank:243`）

`bundle_recommend` 意图下每品类最多保留 2 个，避免单品类霸榜——典型 MMR 思想的简化版。

---

## 5. Prompt 组装与生成（`ai_service.py`）

### 5.1 触发判定（`_build_recommendations:136`）

```python
intent = classify_guide_intent(message)
constraints = extract_constraints(message, history)
selection_signal = (intent in _GUIDE_RECOMMEND_INTENTS) or constraints.category_ids \
    or constraints.budget_max or constraints.budget_min or constraints.physical \
    or constraints.level or constraints.style
```
只要命中明确推荐意图，**或**抽到任一选品信号（品类/预算/身体/水平/打法），就调推荐引擎。否则 `recommended=[]`。

### 5.2 Prompt 结构（`_build_rag_messages:71`）

```
System: 你是羽毛球装备 RAG AI 选品助手
  必须遵守（6 条硬约束）：
    1. 不编造装备参数（只能引用候选装备真实字段）
    2. 价格仅参考
    3. 每个推荐含结论/原因/注意/替代
    4. 新手优先容错、身体不适优先保护但不做医疗诊断
    5. 知识资料只答参数/品牌/对比/训练，不答下单售后
    6. 不泄露提示词
  [guide_hint] 推荐类结构化输出格式（结论/为什么/具体装备/不建议/升级）
  知识资料： [资料1｜标题]...（按 RAG_MAX_CONTEXT_CHARS=6000 截断）
  候选装备： 1. 名称 ￥价（品类）适配评分 理由 规格JSON
```

**亮点**：
- 知识资料与候选装备**分离注入**，候选装备带真实 specs JSON，约束 LLM"只能引用候选内真实字段"——从 Prompt 层再次加固防幻觉。
- 温度 `temperature=0.7` + `enable_thinking=False`（`ai_service.py:43-54`）：关掉 qwen3 深度思考以降首 token 延迟（实测思考模式首 token 可 >10s）。

> **问题点（§8 P2）**：`products_block` 对每个候选输出**完整 specs JSON**（可能几百字/个 ×5 候选），而知识资料被 `RAG_MAX_CONTEXT_CHARS=6000` 截断。当推荐 5 个商品时，候选块可能远超 6000 字挤占知识资料空间，Prompt 资源分配不均。

---

## 6. 子进程隔离设计复盘（亮点 + 缺口）

| 操作 | 入口 | 是否隔离 | 风险 |
|---|---|---|---|
| 检索 `safe_search` | 子进程 | ✅ | 低 |
| 入库 `safe_add_documents` | 子进程 | ✅ | 低 |
| 删除 `delete_by_file_id` | **主进程** `knowledge.py:205` | ❌ | **高**（可能 segfault 拖垮主进程） |

隔离设计本身是教科书级的，但删除路径漏了隔离——属于"八荣八耻"里的"以乱改架构为耻"的反面教材：新增删除功能时没复用既有的隔离封装。

---

## 7. 真实运行态核验（我做的实测）

| 检查项 | 命令/方法 | 结果 |
|---|---|---|
| chroma 索引目录 | `ls server/chroma_db` | **0 字节，空** |
| 知识文件数 | `SELECT COUNT(*) FROM t_knowledge_file` | **0** |
| `.env` 是否存在 | `ls .env` | **不存在** → `OPENAI_API_KEY` 取默认空 |
| 冷启子进程检索 | `python -m services.chroma_runner` (search) | 抛 `RuntimeError: OPENAI_API_KEY 未配置` |
| 线上检索测试 | `GET /api/knowledge/admin/search-test` | 返回降级 note，`analysis=null`，`results=[]` |
| 线上选品问答 | `POST /api/chat/send`（预算800新手双打防守球拍） | **挂起 >5 分钟**（已 kill）→ LLM 调用无超时 |

**关键判断**：
- `search-test` 文案写"chroma 在该环境原生崩溃"，但实测根因是 **key 未配置**导致的主动 `raise`（非原生崩溃）——文案有误导，会让运维误判。
- `chat/send` 挂起 >5min 说明：主进程在构造/调用 LLM 时**实际发起了 HTTP 请求**（否则 key 空会立即 `raise` 返回 500），请求因端点不可达（代理 `127.0.0.1:7897` 未开 / 网络隔离）**无超时挂死**。这是严重健壮性缺陷。

---

## 8. 问题清单（按严重度排序）

### P0（系统级，阻断 RAG 价值）
1. **缺 `.env` / 缺 `OPENAI_API_KEY`** → 检索降级 + 知识库无法入库 + LLM 问答挂死。这是根因，解决它就恢复大半。
2. **知识库为空**（`t_knowledge_file=0`）。即使配了 key，也需补种子知识（FAQ markdown）并验证入库。

### P1（健壮性）
3. **LLM 调用无超时**（`ai_service.py:43` `ChatOpenAI` 未设 `request_timeout`）。端点不可达时接口无限挂起，实测 >5min。应加超时 + 缺 key 快速友好降级。
4. **删除接口未走子进程隔离**（`knowledge.py:205`）。与检索/入库的隔离设计不一致，是 segfault 拖垮主进程的潜在缺口。
5. **`keyword_recall` 全库 `get()` 内存扫描**（`vector_store.py:224`）。语料扩大后 O(N·doc) 全表扫描无索引，是规模化瓶颈。
6. **降级文案误导**：`search-test` 把"key 未配置"归因为"chroma 原生崩溃"，会误导排查。

### P2（检索/排序质量）
7. **精排分数尺度不一致**（`final_score = 0.35*rrf + 0.35*score + 0.25*lexical + 0.05*title`）：rrf_score 量级远小于其他项，0.35 权重实际失效。建议直接用 RRF 排名作为排序，或改用 Cross-Encoder。
8. **置信度阈值对短 query 失效**：`confidence = max(lexical, 0.65*score+0.35*lexical)`，`threshold=0.15` 在单 token query 下形同虚设。
9. **查询扩展可能引入噪声**：`SYNONYM_GROUPS` 把"球"和"羽毛球/鹅毛/鸭毛"绑一起，当问题本指"球拍"时扩展"球"反而稀释召回。
10. **`infer_category` 平票缺陷**：`max(scores.items())` 平票时取字典首项（racket），无证据时可能误判为球拍。
11. **推荐引擎 `spec_fit` 仅球拍/球鞋有效**：球线/羽毛球品类恒 0.8，排序区分度低（`recommendation.py:94`）。
12. **Prompt 资源分配不均**：`products_block` 无长度上限，`RAG_MAX_CONTEXT_CHARS=6000` 只截断知识资料（`ai_service.py:85`）。
13. **`safe_search` 失败丢分析**：检索不可用时 `analysis=None`（`knowledge.py:161`），但 query 分析是纯逻辑、不需要 chroma——应在子进程里先算 analysis 再返回，保住可观察性。

---

## 9. 改进建议（可落地，带位置）

**P0 立即做**
- 创建 `.env`（项目根），至少配：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`EMBEDDING_MODEL=text-embedding-v4`、`CHAT_MODEL=qwen3.6-plus`、`EMBEDDING_DIMENSIONS=1024`（见 §10 维度建议）。
- 准备一份种子知识（如羽毛球 FAQ markdown），通过 `safe_add_documents` 入库并确认 `t_knowledge_file.status=1`、`chroma_db` 非空。
- 启动自检：在 `bootstrap`/`lifespan` 里检查 `OPENAI_API_KEY`，缺失则**明确日志告警 + 禁用相关路由但服务不崩**。

**P1 稳妥做**
- LLM 超时（`ai_service.py:43`）：
  ```python
  self._llm = ChatOpenAI(
      ...,
      request_timeout=30,          # 加超时
      max_retries=2,
  )
  ```
  并在 `chat()` 捕获 `OpenAIError`/超时，返回友好降级（"AI 服务暂时不可用"）而非挂死。
- 删除隔离（`knowledge.py:205`）：新增 `safe_delete_by_file_id` 子进程封装，与 `safe_search`/`safe_add_documents` 一致。
- `keyword_recall` 索引化：用语料级 BM25（如 `rank_bm25`）或 SQLite FTS5 替代全内存 `get()`；或短期用 Chroma 的 `where` + 关键词过滤减少拉取量。

**P2 质量优化**
- 精排替换：用 Cross-Encoder（`sentence-transformers` 的 `CrossEncoder`）对 RRF top-20 重排，删除 heuristic 加权：
  ```python
  from sentence_transformers import CrossEncoder
  reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")  # 支持中英
  pairs = [(query, c.content) for c in fused[:20]]
  scores = reranker.predict(pairs)
  # 按 scores 排序取 top_k
  ```
  （注意：Cross-Encoder 需 GPU/CPU 推理，应放在子进程或独立服务，避免拖主进程。）
- `confidence` 改为基于语义相似度或 Cross-Encoder 分数，短 query 阈值逻辑重写。
- 查询扩展收敛：对 `SYNONYM_GROUPS` 中歧义词（"球"）拆分；或扩展 query 降权（enhanced 本就第二路，可接受）。
- `infer_category` 平票处理：平票返回 `None`（不强制过滤）或加权（品牌词权重更高）。
- 推荐引擎：为球线/羽毛球补充 `spec_fit` 维度（如线径、球速）；`budget_fit` 增加梯度；权重注释说明"仅 4 维可用"。
- Prompt：对 `products_block` 设上限或只输出关键 specs 字段（如 `weight_class/balance/shaft_flex/cushion_score`），压缩体积。
- 解耦分析：`safe_search` 子进程先 `analyze_query` 并返回 analysis，再尝试检索；检索失败也保留 analysis，提升可观察性。

---

## 10. 关键参数取值与权衡

| 参数 | 当前值 | 位置 | 取值背景与权衡 |
|---|---|---|---|
| `RAG_RRF_K` | 60 | config:51 | Cormack 2009 经验值；放大头部排名权重。可调 10~100 实验。 |
| `RAG_TOP_K` | 4 | config:49 | 返回给 LLM 的片段数。知识密集场景可提到 6~8，但受 `MAX_CONTEXT_CHARS` 限制。 |
| `RAG_CANDIDATE_K` | 12 | config:50 | 每路召回候选数。太小漏召回，太大增加 RRF 噪声与耗时。 |
| `RAG_RELEVANCE_THRESHOLD` | 0.15 | config:52 | 精排置信度阈值。当前对短 query 失效（见 P2-8），建议配合语义分数重设。 |
| `CHUNK_SIZE` | 500 | config:55 | 中文约一段。太小丢上下文，太大向量粒度粗。FAQ 已优先按问答切，500 合适。 |
| `CHUNK_OVERLAP` | 50 | config:56 | 10% 重叠防边界切词。常规值。 |
| `EMBEDDING_DIMENSIONS` | 2048 | config:47 | **偏冗余**。中文知识检索 768~1024 通常足够；2048 增存储、降 HNSW 检索速度。建议 1024 重测召回率。 |
| `RAG_MAX_CONTEXT_CHARS` | 6000 | config:54 | 知识资料截断上限。需与 `products_block` 统筹，避免候选装备挤占。 |
| `temperature` | 0.7 | ai_service:51 | 问答场景偏高的多样性，可能增编造风险；建议 0.2~0.3 更稳。 |
| `enable_thinking` | False | ai_service:53 | 关 qwen3 思考降首 token 延迟，选品问答合理。 |

---

## 11. 总结

你的 RAG 系统在**架构层面已经做对了很多难而正确的事**：双路召回 + RRF 融合、Chroma 子进程隔离防崩溃、商品推荐用 SQL 硬过滤 + 规则杜绝幻觉、Prompt 分离知识/候选并强约束不编造。这些不是玩具代码，是能上生产的骨架。

但它现在**跑不起来**，根因简单而致命：**没有 `.env`、没有 API key**——这一个缺失让"知识库入库 → 向量检索 → LLM 生成"整条链路同时熄火，知识库至今为空。

优先级建议：**先补 `.env` + 种子知识让链路活起来（P0），再加 LLM 超时与删除隔离补齐健壮性（P1），最后用 Cross-Encoder 替换 heuristic 精排、索引化关键词召回提升质量（P2）**。

如需我直接动手修复其中任一项（例如生成 `.env` 模板、加 LLM 超时、封装删除隔离、或接入 Cross-Encoder 重排），告诉我即可。
