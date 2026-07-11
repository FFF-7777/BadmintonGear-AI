# 黄金集目录分析报告（v1，基于已跑评测结果）

生成日期：2026-07-10  
分析对象：`黄金集/badminton_rag_golden_set_v1_1_racket_only_full/`  
数据依据：已实际运行 `run_badminton_rag_golden_api.py` + `eval_badminton_rag_golden.py`，结果文件齐全（64 条全部有回包）。

---

## 1. 目录结构与文件职责

| 文件 | 大小 | 职责 |
|---|---|---|
| `badminton_rag_golden_set_v1_1_racket_only.jsonl` | 71 KB | 主黄金集，一行一例，程序评测用 |
| `badminton_rag_golden_set_v1_1_racket_only.csv` | 40 KB | 人工审阅版（问题/断言/禁用词/预期来源） |
| `run_badminton_rag_golden_api.py` | — | 批量调本地 `/api/chat/send`，产出 results |
| `eval_badminton_rag_golden.py` | — | 透明的关键词/规则评分，产出 report |
| `badminton_rag_golden_results_v1_1.jsonl` | 818 KB | 实际跑出的模型回答 |
| `badminton_rag_eval_report_v1_1.json` / `.csv` | — | 评分结果（总体/分组/弱项） |
| `badminton_rag_golden_set_v1_1_racket_only_usage.md` | — | 使用说明与分数建议 |

**结论**：目录结构是完整、自洽、可复现的评测闭环（数据集 → 跑批 → 评分 → 报告 → 文档），设计质量高，可直接接 CI。

---

## 2. 黄金集本身的设计质量

- **覆盖合理**：64 例，7 个能力分组。routing(6)/parameter(8)/recommendation(17)/comparison(12)/general_training_safety(10)/grounding_policy(8)/product_fact(3)。其中 recommendation + comparison 占 45%，符合"选品助手"主职责。
- **评分可解释**：`eval_badminton_rag_golden.py` 用 5 维加权（answer_keypoints / forbidden_content / source_hit / product_hit / format），纯规则、无黑盒模型，弱项可逐条定位。这是优点。
- **rubric 设计到位**：每个用例带 `must_include_any_groups`（命中任一即算）、`must_not_include`（禁语）、`expected_source_keywords`、`expected_products`、`expected_format_markers`——维度齐全。
- **已按知识库边界裁剪**：v1.1 移除了球线/球鞋/耗材多品类题，只评当前已覆盖的球拍能力，避免"知识库没覆盖却要求答对"的无效用例。这是严谨的做法。

**小建议**：`expected_format_markers` 目前依赖"推荐结论/为什么适合你/注意事项/替代方案"等**固定措辞**。如果模型用同义表达（如"选它的理由""避坑"），会被判 format=0。建议把格式校验从"字面 marker"放宽到"结构存在性"（只要出现结论+原因+注意+替代四类语义区块即给分），否则格式分偏低是评测本身的假阴性，不是模型真问题。

---

## 3. 已跑评测结果总览

| 指标 | 数值 | 项目自身标准（usage.md） |
|---|---|---|
| 总体分 `overall_score` | **0.7107** | ≥0.90 稳定；0.80–0.90 可用；**0.70–0.80 有明显缺陷**；<0.70 不建议上线 |
| 通过率 `pass_rate_0_80` | **0.4531**（29/64 通过） | — |

**结论**：当前总分 0.71，落在"有明显缺陷，优先查召回、rerank、系统提示词"区间。距 0.80 上线线还差约 0.09。

### 各分组得分（弱→强）
| 分组 | 得分 | 评价 |
|---|---|---|
| comparison | 0.598 | 🔴 最弱，型号对比全面失利 |
| grounding_policy | 0.594 | 🔴 接地/反编造边界多处缺失 |
| routing | 0.620 | 🟠 路由与拒答边界不稳 |
| parameter | 0.681 | 🟠 参数解释缺官方来源/边界 |
| recommendation | 0.773 | 🟡 基本可用，格式/来源扣分 |
| general_training_safety | 0.855 | 🟢 较好 |
| product_fact | 0.899 | 🟢 最好 |

---

## 4. 核心发现：路由误判 bug（最值得修）

### 现象
14/64 条返回了 ≤200 字符的短答案，其中 **9 条命中了同一条闲聊兜底话术**：

> "我目前主要擅长两类内容：羽毛球装备选购，以及羽毛球基础训练/热身建议。\n\n如果你愿意，我们可以继续聊这些方向，比如：\n- 预算 600 元的新手球拍怎么选\n- 两支球拍怎么对比\n- 打球前怎么热身更稳妥"

另有 5 条命中"知识库没有足够可靠信息/暂不建议硬推荐"兜底（如 CMP001）。

### 受影响用例（本该完整回答，却被判离题/缺料）
| 用例 | 分组 | 真实问题 | 误判去向 |
|---|---|---|---|
| CMP007 | comparison | 同样是 4U，头重进攻拍和头轻速度拍有什么取舍？ | 闲聊兜底 |
| CMP009 | comparison | 单打进攻拍和双打速度拍的选择逻辑有什么不同？ | 闲聊兜底 |
| G008 | general_training_safety | 单打拉吊控制型主要靠什么赢球？ | 闲聊兜底 |
| U006 | grounding_policy | 用户说肩肘疼时，回答边界是什么？ | 闲聊兜底 |
| R003 | routing | 这把拍你能帮我下单并保证明天发货吗？ | 闲聊兜底（此例拒答本合理，但 rubric 期望更具体） |
| CMP001/002/004 | comparison | ASTROX 99/77 PRO、NF700/弓剑7、天斧100/99 LCW 对比 | 缺料兜底 |

### 根因（已在 `server/services/rag_pipeline.py` 定位）
`classify_question_scope()` 判定装备信号的依据是：

```python
CATEGORY_KEYWORDS["racket"] = ("球拍", "拍子", "中杆", "平衡点", "拍框", "甜区", "挥重")
```

关键词只有 **"球拍"/"拍子"**，**没有裸"拍"**。而用户真实表达是"进攻拍""速度拍""双打拍""4U""头重/头轻/进攻/防守/速度"——这些都不含"球拍"二字，也不含型号名 → `has_equipment_signal` 全 False → 一路 `return "offtopic"` → 触发闲聊兜底。

此外 `classify_question_scope` **默认 fall-through 到 `"offtopic"`**（第 367–369 行），只要没命中任何装备/周边信号就判离题，过于激进：只要用户没写"球拍"、没写型号、没写"羽毛球"，哪怕问的是纯装备战术/边界，都会被当成闲聊。

### 影响量化
仅修复这一路由 bug（让装备类口语正确进入 RAG 路径），预计可直接救回 comparison 中 5 条、general_training_safety 1 条、grounding_policy 2 条、parameter 1 条等——约 9–14 条从 0.25–0.55 提升到 0.7+，对 overall_score 的拉动在 +0.1 以上，**有望把总分从 0.71 拉到 0.80 附近**。

---

## 5. 次要问题

### 5.1 `source_hit` 普遍偏低
大量用例 `source_hit = 0.0`，包括本应走 RAG 的 recommendation/comparison。两种可能：
- 模型回答未回带知识库来源关键词（回答与引用脱节）；
- 或黄金集 `expected_source_keywords` 与系统实际返回的来源文本词面不一致（如系统返回"尤尼克斯天斧99"，而预期写"ASTROX 99"）。
**建议**：先抽样对比 `recommended_products`/sources 与 `expected_source_keywords` 的词面，确认是召回问题还是评测词面 mismatch。

### 5.2 `format` 分大量为 0
recommendation 组多个用例 `format=0.0`，但 `answer_keypoints` 满分（说明内容逻辑都在）。即模型答得对，只是没用"推荐结论/为什么适合你/注意事项/替代方案"这套**固定措辞**。这是第 2 节提到的评测假阴性，建议放宽格式校验。

### 5.3 仍有禁用词漏出
- P007 含"适合所有人"（绝对化）→ forbidden=0；
- REC009 含"最强"（最高级承诺）→ forbidden=0。
说明系统提示词对"绝对化/最高级"的约束仍偶发失效，需在后处理或提示词补强。

---

## 6. 修复优先级建议

| 优先级 | 动作 | 预期收益 |
|---|---|---|
| **P0** | 修 `classify_question_scope`：racket 关键词加裸"拍"，并补重量级(3U/4U/5U)、头重/头轻/进攻/防守/速度/均衡等装备信号；把默认 `offtopic` 改为"存在羽毛球上下文词则归 badminton_general/equipment" | 救回 9–14 条，总分有望 +0.1 |
| **P1** | 放宽 `expected_format_markers` 为"结构语义存在性"校验 | recommendation 格式分回升，减少假阴性 |
| **P1** | 排查 `source_hit=0` 是召回问题还是词面 mismatch | 确认是否真有召回缺陷 |
| **P2** | 系统提示词补强"禁止绝对化/最高级"（适合所有人/最强） | 消除 forbidden 漏出 |

---

## 7. 下一步
1. 先改 `rag_pipeline.py` 的 `CATEGORY_KEYWORDS["racket"]` 与 `classify_question_scope` 默认分支（P0）。
2. 重新跑 `run_..._api.py` + `eval_..._py`，对比 `overall_score` 是否过 0.80。
3. 若仍 <0.80，按 P1 排查 source_hit 与 format 假阴性。
4. 评测通过后，把"跑批+评分+分数门禁"接进 CI（usage.md 第 9 节已有示例）。

> 注：本分析未改动任何代码，仅基于现有黄金集与已跑结果给出结论。
