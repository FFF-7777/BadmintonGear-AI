"""RAG 检索管线中的纯逻辑：查询分析、知识切分、RRF 融合与轻量精排。"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set


CATEGORY_KEYWORDS = {
    "after_sale": ("售后", "退货", "退款", "换货", "维修", "保修", "运费", "拒收"),
    "logistics": ("物流", "快递", "包裹", "发货", "签收", "配送", "运输", "快递柜"),
    "product": ("装备", "质量", "颜色", "尺寸", "款式", "配件", "赠品", "保质期", "正品"),
    "account": ("账号", "账户", "登录", "密码", "注销", "异常", "被盗"),
    "payment": ("支付", "扣款", "付款", "价格", "降价", "优惠", "积分", "会员"),
    "invoice": ("发票", "开票", "税务"),
}

SYNONYM_GROUPS = (
    ("物流", "快递", "包裹", "配送"),
    ("退货退款", "退货", "退款", "售后"),
    ("质量问题", "故障", "损坏", "瑕疵"),
    ("支付", "付款", "扣款"),
    ("发票", "开票"),
    ("账号", "账户"),
)

FOLLOW_UP_MARKERS = ("这个", "那个", "它", "上面", "刚才", "怎么", "怎么办", "呢", "谁承担", "可以吗")
NUMBERED_TITLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(\d+)[.、．]\s*(.+?)(?:\*\*)?\s*$"
)
WORD_RE = re.compile(r"[a-zA-Z0-9]+")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")


@dataclass(frozen=True)
class QueryAnalysis:
    original_query: str
    normalized_query: str
    expanded_query: str
    category: Optional[str]
    queries: List[str]
    keywords: List[str]


@dataclass(frozen=True)
class KnowledgeSection:
    title: str
    content: str


@dataclass
class RetrievalCandidate:
    content: str
    metadata: Dict
    route: str
    score: float = 0.0
    routes: List[str] = field(default_factory=list)
    rrf_score: float = 0.0
    lexical_score: float = 0.0
    final_score: float = 0.0
    confidence: float = 0.0


def normalize_text(text: str) -> str:
    """压缩空白并统一为适合检索的文本。"""
    return re.sub(r"\s+", " ", (text or "").strip())


def tokenize(text: str) -> Set[str]:
    """无需分词依赖的中英文检索词元：英文单词、中文短语及二元组。"""
    normalized = normalize_text(text).lower()
    tokens = set(WORD_RE.findall(normalized))
    for segment in CHINESE_RE.findall(normalized):
        tokens.add(segment)
        if len(segment) == 1:
            tokens.add(segment)
        else:
            tokens.update(segment[i:i + 2] for i in range(len(segment) - 1))
    return {token for token in tokens if token}


def infer_category(text: str) -> Optional[str]:
    """根据明确业务词推断预过滤分类；证据不足时不强行过滤。"""
    scores = {
        category: sum(1 for keyword in keywords if keyword in text)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return None
    return best_category


def _expand_query(query: str) -> str:
    additions = []
    for group in SYNONYM_GROUPS:
        if any(term in query for term in group):
            additions.extend(term for term in group if term not in query)
    if not additions:
        return query
    return normalize_text(f"{query} {' '.join(dict.fromkeys(additions))}")


def _last_user_message(history: Optional[Sequence]) -> str:
    for item in reversed(history or []):
        role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
        content = item.get("content") if isinstance(item, dict) else getattr(item, "content", "")
        if role == "user" and content:
            return normalize_text(content)
    return ""


def analyze_query(question: str, history: Optional[Sequence] = None) -> QueryAnalysis:
    """生成检索变体、关键词和前置过滤条件。"""
    normalized = normalize_text(question)
    previous_user_message = _last_user_message(history)
    contextual_query = normalized
    if previous_user_message and (
        len(normalized) <= 14 or any(marker in normalized for marker in FOLLOW_UP_MARKERS)
    ):
        contextual_query = normalize_text(f"{previous_user_message} {normalized}")

    expanded_query = _expand_query(contextual_query)
    queries = [normalized]
    if expanded_query and expanded_query != normalized:
        queries.append(expanded_query)

    category = infer_category(contextual_query)
    keywords = sorted(tokenize(expanded_query), key=lambda value: (-len(value), value))
    return QueryAnalysis(
        original_query=question,
        normalized_query=normalized,
        expanded_query=expanded_query,
        category=category,
        queries=queries[:2],
        keywords=keywords,
    )


def split_knowledge_sections(text: str) -> List[KnowledgeSection]:
    """优先按编号问答切分；无法识别时由调用方使用通用递归切分。"""
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    sections: List[KnowledgeSection] = []
    current_title = ""
    current_lines: List[str] = []

    for line in lines:
        match = NUMBERED_TITLE_RE.match(line)
        if match:
            if current_title:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(KnowledgeSection(current_title, content))
            current_title = match.group(2).strip()
            current_lines = [line.strip()]
        elif current_title:
            current_lines.append(line)

    if current_title:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(KnowledgeSection(current_title, content))

    return sections if len(sections) >= 2 else []


def candidate_key(candidate: RetrievalCandidate) -> str:
    chunk_id = candidate.metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    return hashlib.sha256(candidate.content.encode("utf-8")).hexdigest()


def reciprocal_rank_fusion(
    routes: Iterable[Sequence[RetrievalCandidate]],
    rrf_k: int = 60,
) -> List[RetrievalCandidate]:
    """跨召回路线去重，并使用 RRF 合并名次。"""
    fused: Dict[str, RetrievalCandidate] = {}
    for route_candidates in routes:
        for rank, candidate in enumerate(route_candidates, start=1):
            key = candidate_key(candidate)
            if key not in fused:
                fused[key] = RetrievalCandidate(
                    content=candidate.content,
                    metadata=dict(candidate.metadata),
                    route=candidate.route,
                    score=max(0.0, min(1.0, candidate.score)),
                    routes=[],
                )
            item = fused[key]
            item.rrf_score += 1.0 / (rrf_k + rank)
            item.score = max(item.score, max(0.0, min(1.0, candidate.score)))
            if candidate.route not in item.routes:
                item.routes.append(candidate.route)

    return sorted(fused.values(), key=lambda item: item.rrf_score, reverse=True)


def _token_coverage(query_tokens: Set[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    document_tokens = tokenize(text)
    return len(query_tokens & document_tokens) / len(query_tokens)


def rerank_candidates(
    analysis: QueryAnalysis,
    candidates: Sequence[RetrievalCandidate],
    top_k: int,
    threshold: float,
) -> List[RetrievalCandidate]:
    """轻量精排；保留统一接口，后续可替换为 Cross-Encoder。"""
    if not candidates:
        return []

    max_rrf = max(candidate.rrf_score for candidate in candidates) or 1.0
    query_tokens = tokenize(analysis.normalized_query)
    for candidate in candidates:
        candidate.lexical_score = _token_coverage(query_tokens, candidate.content)
        title_score = _token_coverage(
            query_tokens,
            str(candidate.metadata.get("section_title", "")),
        )
        rrf_score = candidate.rrf_score / max_rrf
        candidate.confidence = max(
            candidate.lexical_score,
            0.65 * candidate.score + 0.35 * candidate.lexical_score,
        )
        candidate.final_score = (
            0.35 * rrf_score
            + 0.35 * candidate.score
            + 0.25 * candidate.lexical_score
            + 0.05 * title_score
        )

    ranked = sorted(candidates, key=lambda item: item.final_score, reverse=True)
    return [item for item in ranked if item.confidence >= threshold][:top_k]


# ============================================================================
# 导购意图识别 + 约束抽取（P0 新增，纯逻辑，不依赖数据库）
# ============================================================================

# 导购意图关键词
GUIDE_INTENT_KEYWORDS = {
    "single_recommend": ("推荐", "买什么", "选什么", "适合我", "推荐一下", "有什么好", "怎么选", "选个", "配吗"),
    "bundle_recommend": ("一套", "配齐", "组合", "怎么配", "搭配", "全配", "整套", "怎么买"),
    "compare": ("对比", "比较", "哪个好", "区别", "和什么比", "差别", "选哪个"),
    "param_explain": ("什么意思", "是什么意思", "参数", "磅数", "平衡点", "中杆", "U数", "球速", "线径", "材质", "硬度"),
    "upgrade": ("升级", "提升", "想换", "进阶", "换拍", "怎么改"),
    "avoid": ("避坑", "不要买", "不建议", "新手不要", "别买", "坑", "雷"),
}

# category_id → 中文名
CATEGORY_NAME_BY_ID = {1: "球拍", 2: "球线", 3: "羽毛球", 4: "球鞋"}

# 品类别名 → category_id
CATEGORY_ALIASES = {
    1: ("球拍", "羽毛球拍", "拍子", "拍", "racket"),
    2: ("球线", "线", "拍线", "穿线", "string"),
    3: ("羽毛球", "球", "鹅毛", "鸭毛", "shuttlecock"),
    4: ("球鞋", "鞋", "羽毛球鞋", "鞋子", "shoes"),
}

# 用户水平关键词
LEVEL_KEYWORDS = {
    "beginner": ("新手", "入门", "初学", "刚学", "菜鸟", "小白", "不会打"),
    "intermediate": ("进阶", "中级", "有点基础", "打了一段时间", "业余"),
    "advanced": ("高手", "高级", "熟练", "老手", "常年打"),
    "competitive": ("比赛", "专业", "职业", "赛事", "国家队", "运动员"),
}

# 打法关键词
STYLE_KEYWORDS = {
    "attack": ("进攻", "杀球", "后场", "重杀", "下压"),
    "defense": ("防守", "双打", "平抽", "网前", "防守反击"),
    "control": ("控制", "控球", "拉吊", "落点"),
    "balanced": ("均衡", "全面", "平衡", "攻守"),
}

# 单双打
PLAY_TYPE_KEYWORDS = {
    "singles": ("单打",),
    "doubles": ("双打",),
    "mixed": ("混双", "混合"),
}

# 身体情况
PHYSICAL_KEYWORDS = {
    "knee_sensitive": ("膝盖", "膝关节"),
    "ankle_sensitive": ("脚踝", "踝关节"),
    "wrist_sensitive": ("手腕",),
    "shoulder_sensitive": ("肩膀", "肩关节"),
}

# 导购意图集合（命中即触发结构化商品检索）
GUIDE_INTENTS = frozenset(GUIDE_INTENT_KEYWORDS.keys())


@dataclass
class GuideConstraints:
    """从用户问题中抽取的选购约束。"""
    category_ids: List[int] = field(default_factory=list)
    level: Optional[str] = None
    style: Optional[str] = None
    play_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    physical: Dict[str, bool] = field(default_factory=dict)
    raw_categories: List[str] = field(default_factory=list)
    raw_budget: Optional[str] = None


def classify_guide_intent(text: str) -> Optional[str]:
    """识别导购意图；无命中返回 None。"""
    scores = {
        intent: sum(1 for kw in kws if kw in text)
        for intent, kws in GUIDE_INTENT_KEYWORDS.items()
    }
    best, best_score = max(scores.items(), key=lambda item: item[1])
    return best if best_score > 0 else None


def _extract_budget(text: str):
    """返回 (budget_min, budget_max, raw)。"""
    budget_min = budget_max = None
    raw = None
    # 区间：500-800 / 500~800 / 500到800
    match = re.search(r"(\d+)\s*[-~到至]\s*(\d+)", text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        budget_min, budget_max = min(a, b), max(a, b)
        raw = f"{budget_min}-{budget_max}"
        return budget_min, budget_max, raw
    # 上限：500以内 / 不超过800 / 800以下
    match = re.search(r"(\d+)\s*(?:元|块)?\s*(?:以内|以下|之内|不超过|不超|封顶)", text)
    if match:
        budget_max = int(match.group(1))
        raw = f"<={budget_max}"
        return budget_min, budget_max, raw
    # 下限：800以上 / 1000起
    match = re.search(r"(\d+)\s*(?:元|块)?\s*(?:以上|起|往上)", text)
    if match:
        budget_min = int(match.group(1))
        raw = f">={budget_min}"
        return budget_min, budget_max, raw
    # 单一数字：预算500 / 500元 / 价位500
    match = re.search(r"(?:预算|价位|价格)\s*[:：]?\s*(\d+)|(\d+)\s*元", text)
    if match:
        value = int(match.group(1) or match.group(2))
        budget_max = value
        raw = str(value)
        return budget_min, budget_max, raw
    return budget_min, budget_max, raw


def extract_constraints(text: str, history: Optional[Sequence] = None) -> GuideConstraints:
    """从用户问题与上文抽取选购约束。"""
    merged = normalize_text(text)
    last = _last_user_message(history)
    if last:
        merged = normalize_text(f"{last} {text}")

    constraints = GuideConstraints()
    for cid, aliases in CATEGORY_ALIASES.items():
        if any(alias in merged for alias in aliases):
            constraints.category_ids.append(cid)
            constraints.raw_categories.append(CATEGORY_NAME_BY_ID[cid])

    for level, kws in LEVEL_KEYWORDS.items():
        if any(kw in merged for kw in kws):
            constraints.level = level
            break

    for style, kws in STYLE_KEYWORDS.items():
        if any(kw in merged for kw in kws):
            constraints.style = style
            break

    for play_type, kws in PLAY_TYPE_KEYWORDS.items():
        if any(kw in merged for kw in kws):
            constraints.play_type = play_type
            break

    for physical, kws in PHYSICAL_KEYWORDS.items():
        if any(kw in merged for kw in kws):
            constraints.physical[physical] = True

    constraints.budget_min, constraints.budget_max, constraints.raw_budget = _extract_budget(merged)
    return constraints

