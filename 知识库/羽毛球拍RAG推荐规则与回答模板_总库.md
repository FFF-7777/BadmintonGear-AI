# 羽毛球拍 RAG 推荐规则与回答模板_总库

> 版本：v1.0  
> 整合日期：2026-07-09  
> 文档类型：RAG 检索规则 / 商品字段模板 / 推荐决策树 / 回答模板 / 数据清洗规范  
> 适用场景：羽毛球装备推荐 Agent、商品检索、参数解释、型号对比、问答安全规范。  
> 来源基础：整合两份原始选拍指导文档，去重、修正冲突表达，并补充公开可核验资料。  

---

## 0. 本文档与总库的分工

《羽毛球拍选拍知识库_总库.md》回答“参数和用户画像是什么”。  
本文档回答“RAG 系统如何检索、判断、推荐、拒绝不可靠内容、生成回答”。

推荐系统应至少拆成四类知识：

```text
1. 稳定知识：重量、平衡点、中杆、拍框、球线、磅数、握柄。
2. 用户画像：新手、初级、中级、进阶、单打、双打、护臂等。
3. 商品知识：品牌、系列、型号、规格、来源、可信度。
4. 生成策略：如何问答、如何推荐、如何处理不确定性。
```

---

## 1. RAG 文档切块规范

### 1.1 推荐切块参数

```yaml
chunk_strategy:
  split_by: heading
  heading_level: "H2/H3/H4"
  max_chunk_chars: 800-1200
  overlap_chars: 80-150
  keep_tables: true
  keep_yaml_blocks: true
  keep_answer_templates: true
  keep_source_fields: true
  do_not_mix:
    - official_specs
    - subjective_feedback
    - recommendation_logic
    - price_inventory
```

### 1.2 Chunk 元数据字段

```yaml
chunk_metadata:
  chunk_id: ""
  doc_type: "parameter_knowledge/user_profile/scenario_rule/product_spec/faq/template"
  sport: "badminton"
  category: "racket"
  topic: "weight/balance/flex/frame/string/tension/grip/user_profile/scenario"
  user_level: "beginner/low_intermediate/intermediate/advanced/unknown"
  scenario: "singles/doubles/mixed/front_court/back_court/recreational/unknown"
  source_level: "L1/L2/L3/L4/L5"
  confidence: "high/medium/low"
  last_verified: "YYYY-MM-DD"
  keywords: []
```

### 1.3 商品条目必须一拍一块

错误切块：把 200 支球拍放进一个大 chunk。  
正确切块：一支球拍一个主 chunk；一个系列一个系列级 chunk；常见对比单独一个对比 chunk。

```yaml
product_chunk:
  granularity: "1 racket = 1 chunk"
  fields:
    - product_name
    - brand
    - series
    - model
    - weight_options
    - grip_options
    - balance_type
    - shaft_stiffness
    - frame_type
    - stringing_advice
    - product_tier
    - official_positioning
    - suitable_for
    - not_suitable_for
    - model_difference
    - comparison_notes
    - source
    - confidence
```

---

## 2. 商品知识库标准字段模板

### 2.1 推荐字段

```yaml
product_name: ""
brand: "YONEX/LI-NING/VICTOR/其他"
brand_cn: "尤尼克斯/李宁/胜利/其他"
series: ""
model: ""
model_aliases: []
equipment_type: "羽毛球拍"
status: "在售/停产/未知"
release_or_catalog_year: ""
region_version: "CN/JP/TW/US/EU/CA/unknown"

specs:
  weight_grip_original: "官方原文，例如 3UG5, 4UG5/G6, W2/S1"
  weight_options_normalized: []
  grip_options_original: []
  balance_original: ""
  balance_type_normalized: "head_heavy/slightly_head_heavy/even/slightly_head_light/head_light/unknown"
  shaft_flex_original: ""
  shaft_flex_normalized: "hi_flex/medium/stiff/extra_stiff/unknown"
  frame_material: ""
  shaft_material: ""
  frame_type_original: ""
  frame_type_normalized: "aero/box/hybrid/isometric/compact/unknown"
  length: ""
  string_pattern: ""
  stringing_advice_original: ""
  max_tension_lbs: ""

positioning:
  product_tier_original: "PRO/TOUR/GAME/PLAY/FEEL/其他/未知"
  performance_original: "Power/Speed/Accuracy/Control/All-round/官方原文"
  player_type_original: "Beginner/Intermediate/Advanced/官方原文"
  internal_style_tags:
    - "进攻"
    - "速度"
    - "控制"
    - "均衡"
    - "防守"

recommendation:
  suitable_for: []
  not_suitable_for: []
  user_level_fit: []
  scenario_fit: []
  main_advantages: []
  main_tradeoffs: []
  caution_notes: []

model_difference:
  same_series_difference: ""
  compared_with_common_models: []
  uncertainty_notes: ""

source:
  source_level: "L1/L2/L3/L4/L5"
  source_name: ""
  source_url: ""
  access_date: "YYYY-MM-DD"
  verified_fields: []
  unverified_fields: []
confidence:
  specs: "high/medium/low"
  positioning: "high/medium/low"
  recommendation: "medium/low"
  user_feedback: "high/medium/low/none"
  price: "high/medium/low/none"

rag_keywords: []
```

### 2.2 字段填写规则

| 字段 | 填写规则 | 错误写法 |
|---|---|---|
| weight_grip_original | 保留官方原文 | 自动改成统一格式但丢失原始标识 |
| balance_type_normalized | 只做内部检索归一化 | 把未核验平衡点写成事实 |
| shaft_flex_normalized | 根据官方原文映射 | 没来源就写“硬杆旗舰” |
| suitable_for | 基于参数和画像推导，标注为推荐逻辑 | 写成官方定位 |
| user_feedback | 必须有真实来源 | 用“很多人说”但无来源 |
| price | 必须有地区、币种、日期 | 写成长期固定价格 |

---

## 3. 参数归一化映射规则

### 3.1 重量归一化

```yaml
weight_normalization:
  2U: "约90-94g，重拍，现代业余少见"
  3U: "约85-89g，扎实，偏单打和后场进攻"
  4U: "约80-84g，主流均衡，多数业余适用"
  5U: "约75-79g，轻快省力，适合新手/双打/防守"
  6U_or_lighter: "约70-74g或更轻，特定轻量需求"
  warning: "不同品牌可能有差异，必须保留官方原文。"
```

### 3.2 平衡归一化

```yaml
balance_normalization:
  head_heavy:
    cn: "头重"
    fit: ["单打后场", "进攻", "男双后场", "力量较好"]
    risk: ["接杀慢", "打久累", "新手手腕负担"]
  even:
    cn: "平衡"
    fit: ["单打双打兼顾", "打法未定", "中性推荐"]
    risk: ["不极端"]
  head_light:
    cn: "头轻"
    fit: ["双打", "防守", "平抽挡", "前场"]
    risk: ["重杀厚度可能不足"]
```

### 3.3 中杆归一化

```yaml
shaft_flex_normalization:
  hi_flex:
    cn: "软/高弹"
    fit: ["新手", "省力", "力量一般", "后场打不远"]
    risk: ["高速发力时反馈不够直接"]
  medium:
    cn: "适中"
    fit: ["多数业余", "均衡", "初级到中级"]
    risk: ["极端风格不够鲜明"]
  stiff:
    cn: "偏硬/硬"
    fit: ["中级以上", "控制", "发力稳定"]
    risk: ["门槛更高"]
  extra_stiff:
    cn: "特硬"
    fit: ["进阶/高阶", "挥速快", "击球点稳定"]
    risk: ["新手打不动，震手，后场不到位"]
```

### 3.4 磅数归一化

```yaml
tension_recommendation:
  beginner: "20-23 lbs"
  low_intermediate: "22-24 lbs"
  intermediate: "24-26 lbs"
  advanced: "26-28+ lbs"
  warnings:
    - "不要超过球拍官方建议范围。"
    - "官方建议范围不等于用户推荐值。"
    - "硬杆+高磅会显著提高门槛。"
```

---

## 4. 推荐决策树

### 4.1 顶层决策树

```text
Step 1：识别用户水平
  ├─ 完全新手/娱乐：优先容错、省力、低门槛
  ├─ 初级/初中级：均衡为主，按问题轻微偏向
  ├─ 中级：按主场景和问题定参数
  └─ 进阶/高阶：做 trade-off 分析

Step 2：识别主场景
  ├─ 单打：后场稳定、控制、体能
  ├─ 双打前场：挥速、转拍、封网
  ├─ 双打后场：下压、连贯、稳定
  ├─ 混双男后场：进攻和下压
  ├─ 混双女前场：速度和网前
  └─ 娱乐健身：省力、耐用、低风险

Step 3：识别当前问题
  ├─ 打不远：先查线磅、硬度、发力门槛
  ├─ 杀球没力：检查动作、磅数、头重和中杆
  ├─ 接杀慢：降低挥重，选速度配置
  ├─ 打久累：控制头重和总重量，降磅
  └─ 震手/疼痛：降低风险，提示休息/专业建议

Step 4：输出参数组合
  ├─ 重量
  ├─ 平衡
  ├─ 中杆
  ├─ 拍框
  ├─ 线磅
  └─ 不推荐项

Step 5：若商品库可信，给具体型号；若不可信，只给参数方向。
```

### 4.2 新手推荐决策

```yaml
beginner_rule:
  if:
    - 用户说刚开始打/第一支拍/不懂参数/娱乐为主/打不远/手腕酸
  recommend:
    weight: "4U或5U"
    balance: "平衡或微头重，避免极端头重"
    shaft: "软或适中"
    frame: "大甜区/容错高"
    tension: "20-23 lbs"
    string: "耐打或弹性友好"
  avoid:
    - "3U极端头重"
    - "特硬中杆"
    - "26磅以上"
    - "小甜区紧凑框"
    - "盲买职业同款"
```

### 4.3 双打速度推荐决策

```yaml
doubles_speed_rule:
  if:
    - 用户主打双打
    - 或接杀慢/平抽挡慢/前场多
  recommend:
    weight: "4U/5U"
    balance: "头轻/平衡/微头轻"
    shaft: "适中或适中偏硬"
    frame: "破风或低风阻"
    grip: "偏细便于转拍"
    tension: "22-25 lbs，根据水平"
  avoid:
    - "3U极端头重硬杆"
    - "过粗握柄"
    - "过高磅导致防守弹性下降"
```

### 4.4 单打进攻推荐决策

```yaml
singles_attack_rule:
  if:
    - 用户主打单打
    - 喜欢后场进攻/杀球/下压
    - 力量和发力较好
  recommend:
    weight: "4U或3U"
    balance: "微头重或头重"
    shaft: "适中偏硬/硬"
    frame: "稳定框或混合框"
    tension: "24-27 lbs，根据水平"
  caution:
    - "若是新手或高远球不到位，不建议直接上3U头重硬杆。"
    - "进攻提升要同时看动作、击球点和线磅。"
```

### 4.5 护臂省力推荐决策

```yaml
arm_friendly_rule:
  if:
    - 用户手腕酸/肩肘不适/打久累/力量一般
  recommend:
    weight: "4U/5U"
    balance: "平衡/微头轻，避免极端头重"
    shaft: "软/适中"
    tension: "20-23或中低磅"
    string: "弹性或舒适型"
  avoid:
    - "硬杆"
    - "高磅"
    - "3U极端头重"
    - "小甜区高门槛拍"
  safety_note: "疼痛持续或明显影响发力时，应休息并咨询专业人士。"
```

---

## 5. 检索与重排规则

### 5.1 检索 Query 扩展

当用户说“新手拍”，扩展检索：

```yaml
query_expansion_beginner:
  original: "新手拍"
  expanded:
    - "新手 第一支拍 4U 5U 软中杆 大甜区 20-23磅"
    - "入门 好上手 省力 容错 羽毛球拍"
    - "beginner racket 4U 5U hi-flex forgiving"
```

当用户说“杀球更重”，扩展检索：

```yaml
query_expansion_smash:
  original: "杀球更重"
  expanded:
    - "进攻 头重 微头重 稳定框 适中偏硬"
    - "后场 下压 重杀 3U 4U"
    - "smash power head heavy stiff racket"
```

当用户说“接杀慢”，扩展检索：

```yaml
query_expansion_defense:
  original: "接杀慢"
  expanded:
    - "双打 防守 接杀 平抽挡 4U 5U 头轻 破风"
    - "挥速 快 连贯 转拍"
    - "doubles defense head light aero frame"
```

### 5.2 重排优先级

```yaml
rerank_priority:
  P0:
    - 用户水平匹配
    - 伤病风险匹配
    - 主场景匹配
  P1:
    - 参数匹配
    - 商品规格可信度
    - 是否有官方来源
  P2:
    - 预算匹配
    - 品牌偏好
    - 外观偏好
  demote:
    - specs_confidence_low
    - source_level_L4_or_L5
    - model_has_duplicate_generic_description
    - price_stale
    - no_verified_weight_or_flex
```

### 5.3 商品召回规则

| 用户意图 | 首选召回 | 次选召回 | 降权 |
|---|---|---|---|
| 参数解释 | 稳定知识卡 | FAQ | 商品页 |
| 新手推荐 | 用户画像 + 参数规则 | 商品库中低门槛型号 | 硬杆头重高磅 |
| 型号规格 | 商品官方规格 chunk | 正规零售商 chunk | 无来源汇总 |
| A/B 对比 | 对比 chunk + 两个商品 chunk | 系列 chunk | 只有通用描述的 chunk |
| 预算推荐 | 商品价格 chunk + 参数规则 | 预算知识卡 | 无采集日期价格 |
| 口碑问题 | L3/L4 口碑 chunk | 商品规格 | 无来源口碑 |

---

## 6. 回答生成规范

### 6.1 标准回答结构

```text
1. 先判断用户画像/问题。
2. 给参数方向。
3. 解释为什么。
4. 说明不推荐项。
5. 如果商品库可信，再给具体型号；否则不强推型号。
6. 如涉及疼痛、伤病、真假、价格、库存，给风险提示。
```

### 6.2 不确定性表达

当来源不足时：

```text
我目前不能把这个规格当作已核验事实，因为知识库里缺少品牌官方或正规零售商来源。可以先按参数方向判断：……；具体型号建议以官方商品页或授权店页面为准。
```

当用户给的信息不足但不需要追问时：

```text
在你还没说明单打/双打和水平的情况下，比较稳的默认方向是 4U、平衡或微头重、适中中杆、22–24 磅。如果你是完全新手或手腕容易累，再保守一点选 4U/5U、软/适中中杆、20–23 磅。
```

### 6.3 禁止回答样式

| 错误回答 | 问题 |
|---|---|
| “新手直接买最贵旗舰。” | 忽略门槛、预算和发力能力。 |
| “硬杆杀球一定更重。” | 错，把用户能力排除在外。 |
| “5U 没法进攻。” | 绝对化。 |
| “这支拍所有人都适合。” | 不符合个性化推荐。 |
| “某型号口碑很好。”但无来源 | 不可追溯。 |
| “官方建议 29 磅，所以你拉 29 磅。” | 混淆官方承受范围与用户推荐。 |

---

## 7. 可直接使用的回答模板

### 7.1 新手第一支拍

```text
新手第一支拍建议优先好上手、省力和容错，不要先追职业同款或极端进攻。参数上优先 4U/5U、平衡或微头重、软到适中中杆、大甜区，拉线 20–23 磅。这样更容易借力，击球点不稳定时也不容易震手。暂时不建议 3U 极端头重、特硬中杆和高磅组合。
```

### 7.2 3U、4U、5U 怎么选

```text
3U 更扎实，适合力量好、单打或后场进攻，但挥起来更累；4U 是多数业余玩家最稳妥的均衡选择；5U 更轻快，适合新手、双打、防守和力量一般的人。不要只看 U 数，因为同样 4U 的拍，头重和平衡、软杆和硬杆的手感会差很多。
```

### 7.3 头重和头轻怎么选

```text
头重更利于后场进攻和杀球，但会牺牲一些防守和连续速度；头轻更适合双打、防守、平抽挡和前场转拍，但重杀厚度通常不如头重。打法不明确时，平衡或微头重比极端头重更安全。
```

### 7.4 中杆软硬怎么选

```text
中杆软更容易借力，适合新手、力量一般和后场打不远的人；中杆硬反馈更直接、控制更清晰，但需要更好的发力和稳定击球点。硬杆不会自动让杀球更重，如果打不弯反而可能更没力。
```

### 7.5 拉线多少磅

```text
新手通常建议 20–23 磅，初级 22–24 磅，中级 24–26 磅，进阶再考虑 26–28 磅或更高。高磅控制更直接，但甜区更小、借力更少、震手风险更高。不要把球拍官方建议上限当成自己应该拉的磅数。
```

### 7.6 杀球没力

```text
杀球没力不一定是拍子不够硬，常见原因还包括击球点、发力链、磅数过高、球线弹性不足或球拍太难打。新手想提升进攻，可以先选 4U 微头重、适中中杆、22–24 磅；如果高远球还不到位，不建议直接上 3U 头重硬杆。
```

### 7.7 接杀慢

```text
接杀慢优先考虑挥速和回拍速度。装备上建议 4U/5U、平衡或头轻、破风框、适中中杆，握柄不要太粗。如果你现在用的是 3U 头重硬杆，可能是挥重拖慢了防守。
```

### 7.8 手腕酸/肩肘不适

```text
手腕酸或肩肘不适时，装备上应降低负担：4U/5U、平衡或微头轻、软/适中中杆、中低磅、弹性友好球线。避免极端头重、硬杆和高磅。如果疼痛持续、加重或影响正常发力，应先休息并咨询医生或运动康复专业人士。
```

---

## 8. FAQ 知识库

### FAQ 01：买高端拍一定更好吗？

不一定。高端拍通常在材料、稳定性、反馈和上限方面更好，但也可能更硬、更挑发力、更贵。新手和初级用户更需要好上手、容错和合适线磅。参数不合适的高端拍，可能比参数合适的中端拍更难打。

### FAQ 02：新手能买进攻拍吗？

可以买轻进攻或低门槛进攻方向，但不建议盲买极端头重、硬杆、高磅组合。更稳的是 4U、微头重、适中中杆、大甜区、22–24 磅。

### FAQ 03：后场打不远是不是要买头重拍？

不一定。头重可以提供拍头惯性，但如果中杆太硬、磅数太高或用户挥不动，仍然打不远。应先检查线磅和发力门槛，再考虑微头重、软/适中中杆。

### FAQ 04：双打一定要头轻吗？

不一定。双打更重视速度和连贯，头轻或平衡通常更安全。后场进攻型双打也可以用微头重或头重，但要避免拖慢接杀和平抽挡。

### FAQ 05：女生一定要用 5U 吗？

不一定。性别不是唯一标准，力量、水平、打法更重要。力量一般、主要双打或娱乐，可以优先 5U 或轻 4U；力量好或单打后场多，也可以用 4U 甚至更扎实的配置。

### FAQ 06：磅数越高越好吗？

不是。高磅控制更直接，但甜区更小、借力更少、震手风险更高。新手盲目高磅常常导致后场打不远、杀球没速度。

### FAQ 07：5U 是不是一定没力量？

不是。5U 更轻快，适合速度和省力；它也可以进攻，但重杀厚度和被动稳定性通常不如更扎实的 3U/4U。具体还要看平衡点、中杆和拍框。

### FAQ 08：同一型号 3U 和 4U 怎么选？

3U 更扎实、后场惯性更强，但更累；4U 更灵活、适合多数业余和双打。力量好、单打多、后场进攻多可考虑 3U；不确定或双打多优先 4U。

### FAQ 09：一支拍可以单打双打都用吗？

可以。多数业余玩家适合 4U、平衡或微头重、适中中杆的全能配置。极端单打进攻或极端双打速度需求才需要明显分化。

### FAQ 10：选拍前最该问用户什么？

优先问水平、单打/双打、当前问题、力量/手腕情况、预算和当前线磅。若不追问，也应以安全默认参数回答。

---

## 9. 数据清洗与纠错规则

### 9.1 原始资料常见问题

| 问题 | 影响 | 修正方式 |
|---|---|---|
| 多个型号描述完全一样 | 向量相似，召回混淆 | 增加型号差异字段和来源 |
| 缺少官方来源 | 规格不可信 | 添加 source_level 与 verified_fields |
| 价格无日期 | 价格过期 | 添加地区、币种、采集日期 |
| 口碑无来源 | 容易编造 | 标注 L3/L4，不能写成事实 |
| 系列定位替代型号参数 | 误导推荐 | 每个型号逐条核验 |
| U/W/G/S 混用 | 品牌标法混乱 | 保留原文 + 内部归一化 |
| 重复附录/短句堆砌 | 降低检索质量 | 去重，改成知识卡 |

### 9.2 商品描述去同质化模板

错误：

```text
该型号适合进攻型选手，杀球强，控制好，适合中高级。
```

正确：

```yaml
model_difference:
  compared_to_same_series: "相对 XXX，该型号的已核验差异是……；若无官方来源，写未知。"
verified_specs:
  weight_grip: "官方原文"
  balance: "官方原文"
  shaft_flex: "官方原文"
recommendation_logic:
  reason: "根据重量/平衡/硬度推导，非官方定位"
uncertainty:
  - "暂无可核验口碑来源"
```

### 9.3 冲突处理规则

当两个来源冲突时：

```yaml
conflict_resolution:
  priority:
    - L1_brand_official
    - L1_official_catalog
    - L2_authorized_retailer
    - L3_professional_review
    - L4_community
    - L5_unverified_summary
  answer_rule: "说明存在冲突，以更高等级来源为准；保留冲突备注。"
```

### 9.4 过期处理规则

| 字段 | 过期风险 | 建议刷新频率 |
|---|---|---|
| 价格 | 高 | 7–30 天 |
| 库存 | 高 | 1–7 天 |
| 在售/停产 | 中 | 30–90 天 |
| 官方规格 | 低到中 | 新配色/新版本发布时 |
| 用户口碑 | 中 | 30–180 天 |
| 参数解释 | 低 | 每年检查一次 |

---

## 10. 事实核验清单

### 10.1 型号规格核验

```yaml
spec_verification_checklist:
  - 是否找到品牌官方页面或官方目录？
  - 是否保留 Weight & Grip 原文？
  - 是否核验 Stringing Advice 或 String tension？
  - 是否核验 Balance 与 Shaft Flex 原文？
  - 是否区分 3U/4U 不同建议磅数？
  - 是否记录地区版本？
  - 是否记录访问日期？
  - 是否把未核验字段列入 unverified_fields？
```

### 10.2 推荐逻辑核验

```yaml
recommendation_checklist:
  - 是否先判断用户水平？
  - 是否识别单打/双打/混双/娱乐？
  - 是否识别当前问题？
  - 是否考虑手腕、肩肘、体能风险？
  - 是否把官方规格与推导建议分开？
  - 是否说明不推荐项？
  - 是否避免绝对化？
```

### 10.3 回答安全核验

```yaml
answer_safety_checklist:
  - 不编造型号参数
  - 不编造价格和库存
  - 不编造用户口碑
  - 不把高端等于适合所有人
  - 不把官方建议上限当用户推荐磅数
  - 不做医疗诊断
  - 疼痛持续时提示就医或咨询专业人士
```

---

## 11. 商品对比模板

### 11.1 两支球拍对比

```text
这两支拍不要只看谁更贵，先看参数取向：

1. 重量/挥重：A 更……，B 更……
2. 平衡点：A 偏……，B 偏……
3. 中杆：A ……，B ……
4. 场景：A 更适合……，B 更适合……
5. 门槛：A 对发力要求……，B 对发力要求……
6. 不推荐：如果你……，不建议选……

如果你的主要问题是……，优先选……；如果你更在意……，优先选……。
```

### 11.2 同系列 Pro/Tour/Game/Play 对比

```yaml
series_ladder_template:
  series: ""
  brand: ""
  source: ""
  model_ladder:
    Pro:
      common_meaning: "通常是高端/旗舰调校，以上限和反馈为主"
      caution: "不同品牌和系列含义不完全相同，必须以官方为准"
    Tour:
      common_meaning: "通常比 Pro 稍低门槛或价格更低"
      caution: "不能无来源假定参数"
    Game:
      common_meaning: "通常面向更广业余用户"
      caution: "仍需核验具体规格"
    Play:
      common_meaning: "通常更入门，价格更低"
      caution: "材料和手感不能凭名称推断"
```

回答模板：

```text
同系列不同后缀不能只按“贵=更适合”判断。一般来说 Pro 更强调上限和反馈，门槛可能更高；Game/Play 往往更面向普通业余或入门预算。但具体差异必须看官方规格，包括重量、平衡、中杆、材质和建议磅数。若知识库没有逐条核验，不应编造差异。
```

---

## 12. 典型推荐输出格式

### 12.1 只给参数方向

```text
按你的描述，更适合的方向是：

- 重量：4U 或 5U
- 平衡：平衡或微头轻
- 中杆：软或适中
- 拍框：大甜区/低风阻
- 线磅：20–23 磅
- 不建议：3U 极端头重、特硬中杆、26 磅以上

原因是你现在的核心需求是省力和容错，而不是极致进攻。具体型号要看商品库是否有官方规格来源。
```

### 12.2 给具体型号但带可信度

```text
可以优先看以下型号方向：

1. 型号 A：适合……；已核验字段：重量、握柄、平衡、中杆；来源：品牌官方；可信度高。
2. 型号 B：适合……；已核验字段：重量、建议磅数；来源：授权零售商；可信度中。
3. 型号 C：只作为备选，因为口碑和型号差异字段暂无可靠来源。

注意：如果某型号只有社区口碑或无来源参数，我不会把它当成确定推荐。
```

### 12.3 用户预算有限

```text
预算有限时，不建议为了“高端”牺牲参数匹配。你更应该优先找 4U/5U、适中或偏软中杆、平衡或微头重、正规渠道、能按合适磅数穿线的中低价或中端拍。对新手来说，线磅和上手难度比旗舰名气更重要。
```

---

## 13. Agent 系统提示词建议

### 13.1 推荐 Agent 核心提示词

```text
你是羽毛球装备选拍助手。回答时必须先判断用户水平、打法场景、当前问题和身体风险，再给参数方向。只有当商品条目包含可核验来源和可信度字段时，才推荐具体型号。禁止编造型号参数、价格、销量和口碑。对不确定信息必须说明不确定。涉及疼痛或伤病时，不做医疗诊断，只给装备降负担建议，并提醒必要时咨询专业人士。
```

### 13.2 商品入库 Agent 提示词

```text
你负责清洗羽毛球拍商品数据。每支球拍必须一条记录，保留品牌、系列、型号、Weight & Grip 原文、Balance 原文、Shaft Flex 原文、Stringing Advice 原文、材质、来源 URL、访问日期和可信度。没有来源的字段必须进入 unverified_fields，不能根据系列名编造参数。若多个型号描述相同，必须添加 model_difference 或标注 unknown。
```

### 13.3 对比 Agent 提示词

```text
你负责比较羽毛球拍型号。必须分别读取两个商品条目的已核验规格，再比较重量、平衡、中杆、拍框、建议磅数、适用场景和门槛。若缺少官方或可靠来源，必须说明“不足以得出确定差异”。禁止用同系列通用描述替代具体型号差异。
```

---

## 14. 维护流程

### 14.1 新增商品流程

```text
1. 查品牌官方页面或官方目录。
2. 查正规授权零售商补充地区版本和价格。
3. 记录原始规格，不先归一化覆盖。
4. 填写 verified_fields 和 unverified_fields。
5. 生成推荐逻辑，但标注为“根据参数推导”。
6. 加入 rag_keywords。
7. 如果是系列内相似型号，补充 model_difference。
8. 入库前检查是否有重复型号、重复描述、无来源参数。
```

### 14.2 更新商品流程

```text
1. 检查官方页面是否变更。
2. 检查在售/停产状态。
3. 更新价格、库存、地区版本。
4. 保留历史变更记录。
5. 若来源冲突，以更高等级来源为准。
6. 重新计算检索关键词和推荐标签。
```

### 14.3 口碑字段维护

```yaml
feedback_maintenance:
  acceptable_sources:
    - "长期评测文章/视频"
    - "教练/穿线师经验"
    - "较大样本社区讨论"
  must_record:
    - source_url
    - access_date
    - sample_type
    - subjective_or_common
  prohibited:
    - "无来源写很多人说"
    - "把个体体验写成确定事实"
    - "把短视频评论当官方定位"
```

---

## 15. 可核验来源索引

| 编号 | 来源级别 | 来源名称 | 用途 | URL | 访问日期 |
|---|---|---|---|---|---|
| S01 | L1 | YONEX USA - ASTROX 100ZZ | 官方规格示例：重量/握柄、平衡、硬度、建议磅数、定位 | https://us.yonex.com/products/astrox-100zz | 2026-07-09 |
| S02 | L1 | YONEX USA - ARCSABER 11 PRO | 官方规格示例：平衡拍、硬中杆、建议磅数、控制定位 | https://us.yonex.com/products/arcsaber-11-pro | 2026-07-09 |
| S03 | L1 | YONEX USA - NANOFLARE 001 FEEL | 官方规格示例：5U、Head Light、Hi-Flex、Beginner | https://us.yonex.com/products/nanoflare-001-feel | 2026-07-09 |
| S04 | L1 | YONEX USA - BG65 SET | 球线示例：0.70mm、Durability | https://us.yonex.com/products/bg65-set | 2026-07-09 |
| S05 | L1 | YONEX USA - EXBOLT 63 SET | 球线示例：0.63mm、Quick Repulsion | https://us.yonex.com/products/exbolt-63-set | 2026-07-09 |
| S06 | L1 | YONEX Global - EXBOLT 68 | 球线示例：0.68mm、Powerful Smash、Durability | https://www.yonex.com/bgxb68 | 2026-07-09 |
| S07 | L1 | VICTOR - Beginner Racket Guide | 新手选拍与 3U/4U 重量解释 | https://www.victorsport.com/blog/article/how-to-pick-the-right-badminton-rackets-for-beginners | 2026-07-09 |
| S08 | L1/L2 | VICTOR Product Pages | VICTOR 商品页规格字段示例 | https://www.victorsport.com/ | 2026-07-09 |
| S09 | L2 | Official Li-Ning Distributor Canada | 李宁商品规格和地区销售信息补充 | https://shopbadmintononline.com/ | 2026-07-09 |
| S10 | L1 | BWF Laws of Badminton | 球拍尺寸规则上限 | https://system.bwfbadminton.com/documents/folder_1_81/Statutes/CHAPTER-4---RULES-OF-THE-GAME/SECTION%204.1-%20Laws%20of%20Badminton.pdf | 2026-07-09 |

---

## 16. 最终落地建议

1. 把《羽毛球拍选拍知识库_总库.md》作为稳定知识库主源，适合回答“怎么选、参数是什么意思、什么人适合什么配置”。
2. 把本文档作为 Agent 规则库，适合控制“如何检索、如何推荐、如何回答、如何避免胡编”。
3. 商品数据库不要和指导知识混在一起；每支球拍单独建 chunk，并且必须有来源和可信度字段。
4. 型号对比必须基于逐条核验的商品规格，不要使用同系列通用描述。
5. 当商品信息缺来源时，宁可只给参数方向，也不要强推具体型号。
