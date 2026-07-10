# BadmintonGear-AI RAG 黄金集 v1.1（球拍-only）使用说明

生成日期：2026-07-10  
适用项目：BadmintonGear-AI / 羽智选  
版本说明：本版已按你的要求移除“球线、球鞋、羽毛球耗材/多品类推荐”测试项，只评估当前知识库已经覆盖的球拍与羽毛球规则/训练安全相关能力。

## 1. 文件说明

| 文件 | 用途 |
|---|---|
| `badminton_rag_golden_set_v1_1_racket_only.jsonl` | 主黄金集，程序评测使用。一行一个测试样例。 |
| `badminton_rag_golden_set_v1_1_racket_only.csv` | 人工审阅版，方便查看问题、断言、禁用词和预期来源。 |
| `run_badminton_rag_golden_api.py` | 批量调用本地 FastAPI `/api/chat/send`，脚本无需修改，只需要换 golden 文件名。 |
| `eval_badminton_rag_golden.py` | 自动评分，输出总体分、分组分和弱项样例，脚本无需修改。 |

本黄金集共 **64 条**。分组数量：

| 分组 | 数量 | 说明 |
|---|---:|---|
| routing | 6 | 闲聊、无关问题、交易边界、提示词攻击、信息不足追问 |
| parameter | 8 | 球拍重量、平衡点、中杆、拍框/甜区、磅数上限等参数解释 |
| recommendation | 17 | 新手、双打、单打、混双、预算、身体不适、训练/比赛兼顾等球拍推荐 |
| comparison | 12 | 型号对比、同系列后缀、儿童拍 vs 成人拍、低可信字段处理 |
| general_training_safety | 10 | 羽毛球规则、术语、步法、战术和安全边界 |
| grounding_policy | 8 | 反编造、价格非实时、source_confidence、待核验字段 |
| product_fact | 3 | 具体球拍型号事实与来源边界 |

## 2. 相比 v1 的改动

1. 删除/替换了球线线径、球鞋、羽毛球耗材、多品类预算分配相关样例。
2. `R005` 从“买东西推荐”改成“买一支羽毛球拍”，只测试球拍需求澄清。
3. `P005` 改为“拍框形状和甜区大小对新手容错的影响”。
4. `REC011` 改为“新手预算 600 只买球拍怎么选”。
5. `F004-F006` 由多品类题替换为球拍预算、伤痛边界下的球拍选择、训练/比赛兼顾球拍取舍。
6. 保留少量“磅数上限”边界题，因为它属于球拍使用参数；不再测试球线型号、线径、耐打、弹性等球线知识。

## 3. 黄金集评估什么

1. 能否把闲聊、无关问题、交易诉求、提示词攻击和羽毛球球拍问题分开。
2. 能否基于用户水平、单双打/混双、打法、身体状态、预算、当前用拍给球拍推荐。
3. 能否在型号对比中读取两个具体型号，而不是只套系列介绍。
4. 能否处理 `source_confidence`、`待核验字段` 和“价格非实时”的边界。
5. 能否避免医疗诊断、价格承诺、下单承诺、系统提示词泄露和编造型号参数。

## 4. 运行前准备

在项目根目录启动后端：

```bash
cd server
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

如果 `/api/chat/send` 需要登录鉴权，先拿到 token：

```bash
export TOKEN="你的访问令牌"
```

Windows PowerShell：

```powershell
$env:TOKEN="你的访问令牌"
```

## 5. 批量跑黄金集

```bash
python run_badminton_rag_golden_api.py \
  --base-url http://127.0.0.1:8000 \
  --golden badminton_rag_golden_set_v1_1_racket_only.jsonl \
  --out badminton_rag_golden_results_v1_1.jsonl \
  --token "$TOKEN"
```

本地暂时不需要鉴权时，去掉 `--token`。

## 6. 自动评分

```bash
python eval_badminton_rag_golden.py \
  --golden badminton_rag_golden_set_v1_1_racket_only.jsonl \
  --results badminton_rag_golden_results_v1_1.jsonl \
  --out badminton_rag_eval_report_v1_1.json \
  --csv-out badminton_rag_eval_report_v1_1.csv
```

输出字段：

- `overall_score`：总体平均分；
- `pass_rate_0_80`：分数 >= 0.80 的通过率；
- `group_scores`：各能力分组得分；
- `weak_cases`：低于 0.80 的样例，优先修复这些。

## 7. 分数建议

| 分数 | 建议 |
|---|---|
| >= 0.90 | 稳定，可作为回归基线。 |
| 0.80–0.90 | 可用，但要看弱项是否集中。 |
| 0.70–0.80 | 有明显缺陷，优先查召回、rerank、系统提示词。 |
| < 0.70 | 不建议上线，需要重点修复。 |

## 8. 常见失败原因

### `source_hit` 低

优先检查知识库切块和 metadata：商品是否一拍一块，对比问题是否能召回两个具体型号，是否保留 `source_confidence` 和 `待核验字段`。

### `forbidden_content` 低

说明回答出现禁用内容，如“全网最低价”“适合所有人”“能治疗膝盖/手腕疼”“已下单”。优先检查系统提示词和生成后处理。

### `product_hit` 低

说明商品召回或结构化推荐不稳定。检查商品导入、型号别名、标准型号、关键词、预算过滤和 `match_products_for_query`。

### `answer_keypoints` 低

说明关键选拍逻辑缺失。检查回答是否包含：推荐结论、适合原因、注意事项、替代方案，以及官方规格和推导建议是否分开。

## 9. CI 接入示例

```bash
python run_badminton_rag_golden_api.py --base-url http://127.0.0.1:8000 --golden badminton_rag_golden_set_v1_1_racket_only.jsonl --out results_v1_1.jsonl
python eval_badminton_rag_golden.py --golden badminton_rag_golden_set_v1_1_racket_only.jsonl --results results_v1_1.jsonl --out report_v1_1.json
python -c "import json,sys; r=json.load(open('report_v1_1.json',encoding='utf-8')); s=r['summary']['overall_score']; print('score=',s); sys.exit(0 if s>=0.80 else 1)"
```

## 10. 后续升级

等你补齐球线、球鞋、羽毛球耗材知识库后，再单独新增：

- `string_recommendation`：球线线径、手感、耐打、磅数组合；
- `shoes_recommendation`：缓震、支撑、防滑、脚型、膝踝保护；
- `shuttle_recommendation`：训练球、比赛球、耐打、飞行稳定和预算消耗。
