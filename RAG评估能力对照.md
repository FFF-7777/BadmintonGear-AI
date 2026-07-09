# 羽智选 RAG 评估能力对照

> 评估对象：`server/services/{rag_pipeline,ai_service,recommendation,vector_store}.py`、`server/routers/chat.py`、现有 `server/tests/*`。
> 评估依据：用户提供的《开放域/主观性强 RAG 评估框架》。
> 结论口径：`✅ 已具备` / `⚠️ 部分具备（有雏形但缺关键链路）` / `❌ 缺失（需新建）`。

---

## 一、总览对照表

| 框架维度 | 当前状态 | 说明 |
|---|---|---|
| 第一层·检索 Recall@K / MRR / NDCG | ❌ | 检索链路支持，但无标注集+评测脚本 |
| 第一层·Context Relevance（LLM 打分） | ❌ | 无 |
| 第二层·事实准确性（Factuality） | ⚠️ | 靠 prompt 硬约束+结构化注入防幻觉，无自动 faithfulness 校验 |
| 第二层·回答相关性（Answer Relevancy） | ⚠️ | 有 scope 分流避免答非所问，无打分 |
| 第二层·个性化匹配度（核心） | ⚠️→❌ | **关键缺口**：画像不持久化，跨会话为零 |
| 第二层·多样性与覆盖度 | ⚠️ | bundle 限每类 2 个，single 无品牌/价位分散强制 |
| 第三层·意图识别 | ✅ | 四类 scope + 六类 guide intent，型号识别稳健 |
| 第三层·追问能力（slot-filling） | ⚠️ | 信息不足只给"请补充"软提示，非主动追问 |
| 第三层·多轮一致性 | ❌ | 无显式检测，靠 LLM+history |
| 特化·专家答案基准 Golden Set | ❌ | 无 |
| 特化·参数一致性硬检查 | ⚠️ | 参数来自真实 DB（按构造不错），无自动比对脚本 |
| 特化·反事实/对抗测试 | ⚠️ | 部分硬规则覆盖，无专门路由 |
| 工具·RAGAS / TruLens / Phoenix | ❌ | 全部未集成 |
| 线上闭环·埋点/反馈 | ❌ | 前端无"推荐有用吗"、无点击/追问追踪 |

**关键洞察**：框架反复强调的"不编造、不匹配就过滤、答非所问要避免"——这三条**已经被你做成架构硬约束了**，只是没有"评测它们"的手段。这是优势，不是劣势，但意味着下一步的重点是**评测与闭环**，而不是继续堆功能。

---

## 二、分层逐项分析

### 第一层：检索质量（Retriever）

**已具备（底座）**
- 多路召回 + RRF(k=60) 融合：`reciprocal_rank_fusion()`（`rag_pipeline.py:413`）。
- 6 维精排：`rerank_candidates()` 权重 `0.40·rrf + 0.15·dense + 0.15·lexical + 0.10·title + 0.10·metadata + 0.10·model`（`rag_pipeline.py:498`）。
- 短查询自适应阈值 `×0.7`（`rag_pipeline.py:515`），型号/对比低置信度**不兜底**（`rag_pipeline.py:520`）——这本身就是"答非所问防护"的检索侧实现。
- `safe_search()` 返回带 `score` 的 `documents`，**数据上是可评测的**。

**缺失**
- 没有任何人工标注的"问题→相关文档"测试集，所以 Recall@K / MRR / NDCG **算不出来**。
- 现有 `test_rag_pipeline.py` 只验证"rerank 排序逻辑是否正确"（如相关片段应排前面），是**单元测试**，不是对知识库全量的**检索质量评测**。
- 无 Context Relevance 的 LLM 打分。

**要做的事**：建 50–100 题标注集（按打法/预算/品牌分层），写 `scripts/eval_retrieval.py` 跑批，对每题算 Recall@5 / MRR / NDCG。底座函数（`analyze_query` / `safe_search` / `rerank_candidates`）可直接复用，几乎不用改检索逻辑。

---

### 第二层：生成质量（Generator）

#### 1. 事实准确性（Factuality）—— ⚠️
**架构已防住幻觉**：
- system prompt 第 1 条强制："不编造装备参数；装备参数只能引用下方'候选装备'中的真实字段"（`ai_service.py:157`）。
- 候选装备卡来自 `recommend_products()` → 真实 `t_product.specs`，参数按构造不会错。
- 具体型号未收录时走 `_missing_model_answer()` 诚实拒答（`ai_service.py:235`），不硬编。

**缺口**：没有自动化 faithfulness 校验。完全依赖 prompt 自律 + 人工肉眼检查。

#### 2. 回答相关性（Answer Relevancy）—— ⚠️
- `classify_question_scope()` 把问候/离题/周边/装备分四类（`rag_pipeline.py:294`），离题直接走 `_handle_offtopic`，**不会触发选品幻觉**——这天然降低了"答非所问"率。
- 但没有任何"回答是否紧扣用户需求"的打分机制。

#### 3. 个性化匹配度（核心！）—— ⚠️→❌ **最关键的缺口**
**单次问题内已能匹配**：
- `extract_constraints()` 能从问题抽取 `level / style / play_type / budget / physical`（`rag_pipeline.py:667`）。
- `recommendation.py` 用这些做 4 维加权评分 + 硬规则（新手不推硬杆、膝盖敏感不推低缓震鞋等，`recommendation.py:246`）。

**但画像不持久化，是架构级缺口**：
- `models/user.py` 的用户表只有 `username/password/phone/nickname/avatar`——**完全没有羽毛球维度**。
- `routers/user_profile.py` 的 `UserProfileUpdate` 只能改昵称/头像/手机号（`:26`），**无打法/力量/预算/品牌偏好字段**。
- `ai_service.py` 全文 grep `user_profile` **零命中**——推荐引擎**根本不读用户画像**，只看当前 message + 上一句用户消息（`_last_user_message` 拼一句上文，`rag_pipeline.py:285`）。
- 因此框架里的"用户画像维度（打法/力量/预算/品牌/手感/场景）"目前**只在单次提问里生效，跨会话为零**。用户第二次来，系统不记得他上次说自己是新手、打双打。

**要做的事**：在 `t_user` 增加羽毛球画像字段（或独立 `t_user_profile` 表），`user_profile.py` 开放编辑，`ai_service._build_recommendations` 把持久画像与当次 `extract_constraints` 合并后再推荐。这是让"个性化匹配度"从"单次"升级为"用户级"的必要改造。

#### 4. 多样性与覆盖度 —— ⚠️
- `bundle_recommend` 每品类最多 2 个（`recommendation.py:363`），避免单类霸榜。
- 但 `single_recommend`（默认）返回 `top_n=5` 纯按分数排，**无品牌分散度/价位覆盖度强制**。Top-3 可能全是同一品牌同价位。

---

### 第三层：对话质量（Conversational）

| 维度 | 状态 | 证据 |
|---|---|---|
| 意图识别 | ✅ | `classify_question_scope`（4 类）+ `classify_guide_intent`（6 类：单推/套装/对比/参数解释/升级/避坑，`rag_pipeline.py:628`）；型号正则+别名识别稳健（`extract_model_tokens`） |
| 追问能力 | ⚠️ | 信息不足时 `_fallback_answer` 提示"建议补充预算/水平/打法"（`ai_service.py:296`），但**非主动 slot-filling 追问**，不会像客服一样问"你打单打还是双打？" |
| 一致性 | ❌ | 无显式跨轮矛盾检测；靠 LLM + `history`（最近 `RAG_HISTORY_TURNS*2` 条，`ai_service.py:313`）。第 1 轮推荐软杆、第 3 轮又说硬杆适合新手，系统不会发现 |

**要做的事**：追问可做成"约束槽位填充"——当 `extract_constraints` 抽到的关键维度缺失时，由 LLM 生成一句针对性追问（已有 history 机制可复用）。一致性检测可加一层"本轮推荐理由 vs 历史推荐理由"的轻量比对。

---

### 特化策略

**① 专家答案基准（Golden Set）—— ❌**
无。需找 3–5 位资深球友/穿线师对标注集写"理想回答"，存为 `data/golden_set.jsonl`。代码侧零基础，是纯数据+流程工作。

**② 参数一致性硬检查 —— ⚠️**
- 好消息：候选参数来自真实 DB，按构造不会错；未收录型号走诚实拒答。
- 缺口：没有脚本自动比对"生成文本中的参数" vs "知识库/商品库真实参数"。可后续用规则引擎 + LLM 做，但当前无。

**③ 反事实/对抗测试 —— ⚠️**
- "新手推荐硬杆拍"→ `_apply_hard_rules` 直接排除（`recommendation.py:251`）。✅ 已覆盖。
- "预算不足买高端拍"→ `budget_max` 过滤高价（`recommendation.py:49`）。✅ 已覆盖。
- "新手要 AX99"的**劝阻+解释**→ 无专门逻辑，靠 prompt 软约束"对新手优先考虑容错率"（`ai_service.py:160`）。⚠️ 可加显式"高端进攻拍 vs 新手"冲突检测。
- "完美球拍"类不可能需求→ 无专门路由，会退回最佳匹配。⚠️ 可加"需求冲突/不可能满足"识别。

---

### 工具与线上闭环

- **RAGAS / TruLens / Phoenix**：❌ 全部未集成。最易落地的是 RAGAS 的 `faithfulness` + `answer_relevancy`，直接消费现有 `context_docs` + `answer` 即可。
- **线上反馈闭环**：❌ 前端 `app/` 无"这个推荐有帮助吗？"按钮，无"用户是否点击推荐/是否追问'还有别的吗'"的埋点（`error-report.js` 只报错误，不报满意度）。

---

## 三、落地路线图（对齐框架四阶段，具体到本项目）

### 阶段 1（冷启动）—— 低成本，建底座
1. 建 `data/eval_set.jsonl`：50–100 题，字段 `{question, expected_doc_ids[], expected_category, expected_constraints, golden_answer?}`。
2. 写 `scripts/eval_retrieval.py`：复用 `analyze_query`+`safe_search`+`rerank_candidates`，算 Recall@5 / MRR / NDCG，输出 CSV。
3. 人工跑 30 题，对每题给 factuality / relevance / match 1–5 分，建基线。重点验证：参数是否错、是否答非所问。
4. **顺手补一个对抗测试集**：新手要 AX99、100 块买高端拍、完美球拍——验证现有硬规则是否兜住。

### 阶段 2（自动化）—— 接框架
5. 接 RAGAS：`faithfulness`（防幻觉回归）、`answer_relevancy`（相关性回归），每次改知识库/prompt 后跑。
6. 把阶段 1 的脚本接进 `pytest` / CI（已有 `.github/workflows/ci.yml`），做成回归门禁。
7. **个性化升级（关键）**：`t_user` 加羽毛球画像字段 → `user_profile.py` 开放编辑 → `ai_service` 合并持久画像与当次约束。这一步让"个性化匹配度"从单次变用户级。

### 阶段 3（线上闭环）—— 反馈驱动
8. 前端加"推荐有用吗？👍👎" + "还有别的吗"追踪，埋点上报（复用现有上报通道）。
9. 收集显式反馈进 `t_feedback` 表，定期回看低分案例，反哺 Golden Set 与 prompt。
10. （可选）用反馈数据做轻量 RLHF / 规则微调推荐权重。

---

## 四、可以立刻复用的现有资产（别重复造轮子）

| 你想做的评估 | 直接复用 |
|---|---|
| 检索评测脚本 | `analyze_query` / `safe_search` / `rerank_candidates` / `reciprocal_rank_fusion` |
| 约束抽取单测 | `extract_constraints` / `classify_guide_intent`（已是纯函数，易测） |
| 推荐质量回归 | `recommend_products` / `_apply_hard_rules` / `_user_fit` / `_spec_fit`（已有 `test_recommendation.py` 13 例） |
| faithfulness 校验 | `_build_sources()` 产出的 `sources` + `recommended_products` 真实字段，天然是"事实锚点" |
| 多轮上下文 | `_recent_history` / `_last_user_message` |
