"""RAG 检索管线中的纯逻辑：查询分析、知识切分、RRF 融合与轻量精排。"""
from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


CATEGORY_KEYWORDS = {
    "racket": ("球拍", "拍子", "中杆", "平衡点", "拍框", "甜区", "挥重", "握柄"),
    "string": ("球线", "拍线", "穿线", "线径", "磅数", "掉磅"),
    "shuttle": ("羽毛球", "鹅毛", "鸭毛", "球速"),
    "shoes": ("球鞋", "羽毛球鞋", "鞋子", "脚型", "宽脚"),
    "brand": ("品牌", "尤尼克斯", "李宁", "胜利", "川崎", "薰风", "凯胜"),
    "selection": ("推荐", "对比", "怎么选", "适合", "预算", "新手", "进阶"),
}

SYNONYM_GROUPS = (
    ("球拍", "拍子", "羽毛球拍"),
    ("球线", "拍线", "穿线"),
    ("羽毛球", "鹅毛", "鸭毛"),
    ("球鞋", "鞋子", "羽毛球鞋"),
    ("对比", "比较", "区别"),
    ("预算", "价格", "参考价"),
)

_SHUTTLE_EXCLUDE = ("拍", "鞋", "线", "球拍", "球鞋", "拍线", "球线")

FOLLOW_UP_MARKERS = ("这个", "那个", "它", "上面", "刚才", "怎么", "怎么办", "呢", "可以吗")
NUMBERED_TITLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(\d+)\\?[.、．]\s*(.+?)(?:\*\*)?\s*$"
)
MODEL_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?([A-Za-z]{1,12}\s*[- ]?\d{1,4}(?:\s*[A-Za-z0-9-]{1,6})?|(?:天斧|战戟|极速|神速|雷霆|弓箭|音速|疾光|65Z)\s*[- ]?\d{1,4}(?:\s*[A-Za-z0-9-]{1,6})?).*$"
)
# FAQ 常见问题类标题：### RACKET-Q001｜问题？ / Q140：问题 / YONEX-Q012｜问题
# 仅匹配「行首为 (可选##前缀)(可选英文标签-)Q<数字>(分隔符)」的结构，避免误切正文里的 "参见 Q002｜"。
FAQ_TITLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:[A-Za-z]+-)?Q\d+\s*[｜|:：]\s*(.+?)\s*$"
)
WORD_RE = re.compile(r"[a-zA-Z0-9]+")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
ASCII_MODEL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:astrox|arcsaber|nanoflare|auraspeed|jetspeed|halbertec|ax|arcs|nf|as|js|tk|hx|pc)\s*[- ]?\d{1,4}(?:\s*(?:pro|tour|game|play|bp|lcw)){0,2}[a-z0-9]{0,2}(?![A-Za-z0-9])"
)
TURBO_MODEL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])turbocharging\s*[- ]?n\s*[- ]?\d{1,3}(?![A-Za-z0-9])"
)
DIGIT_MODEL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])\d{2,4}\s*(?:pro|tour|game|play|bp|lcw|[a-z]{1,3}\d{0,2})(?![A-Za-z0-9])"
)
CHINESE_MODEL_RE = re.compile(
    r"(?:天斧|战戟|极速|神速|雷霆|弓箭|音速|疾光|锋影|驭|隼|65Z)\s*[- ]?\d{1,4}(?:\s*[A-Za-z]{1,4})?"
)
COMPARE_SPLIT_RE = re.compile(r"\s*(?:和|跟|与|vs\.?|VS\.?|还是)\s*")

BADMINTON_GENERAL_KEYWORDS = (
    "热身", "拉伸", "步法", "发力", "握拍", "启动", "启动步", "米字步", "交叉步", "并步",
    "手法", "训练", "练习", "发球", "接发", "站位", "轮转", "步伐", "体能",
    "如何打", "怎么打", "怎么练",
)
# 打法风格词：直接视为选品信号（杀球=进攻型→头重拍等），优先级高于 GENERAL/教学判定。
# 从 GENERAL / CONTEXT 中拆出，避免被误归为羽球周边知识而掐断推荐链路。
BADMINTON_PLAYSTYLE_KEYWORDS = (
    "杀球", "吊球", "高远球", "搓球", "勾对角", "上网",
    "进攻", "防守", "控球", "平抽", "拉吊", "网前",
)
BADMINTON_CONTEXT_WORDS = (
    "羽毛球", "单打", "双打", "混双", "后场", "前场", "中场", "连贯", "挥拍", "回球",
    "控制", "战术", "赢球",
)
BADMINTON_EQUIPMENT_TERMS = (
    "球拍", "拍子", "羽拍", "这支拍", "这把拍", "儿童拍", "成人拍", "入门拍", "进攻拍", "速度拍", "防守拍", "头重拍", "头轻拍",
    "3U", "4U", "5U", "6U", "头重", "头轻", "均衡", "平衡点", "挥重", "中杆", "硬杆", "软杆",
    "甜区", "拍框", "磅数", "拉线", "高磅", "低磅", "PRO", "TOUR", "GAME", "PLAY",
)
COMMERCE_BOUNDARY_TERMS = (
    "下单", "发货", "售后", "订单", "物流", "付款", "购物车", "保证明天", "全网最低价", "最低价",
    "实时价", "实时价格", "到手价", "包邮",
)
PROMPT_BOUNDARY_TERMS = (
    "系统提示词", "内部规则", "忽略你的", "忽略以上", "开发者消息", "原始提示词", "全部输出",
)
MEDICAL_BOUNDARY_TERMS = (
    "诊断", "治疗", "处方", "就医", "医生", "肩肘疼", "肩膀疼", "肘疼", "膝盖疼", "手腕疼", "伤病",
)

SERIES_CODE_VARIANTS = {
    "AX": ("ASTROX", "天斧"),
    "ARCS": ("ARCSABER", "弓箭"),
    "NF": ("NANOFLARE", "疾光"),
    "AS": ("AURASPEED", "神速"),
    "JS": ("JETSPEED", "极速"),
    "HAL": ("HALBERTEC", "战戟"),
    "TK": ("THRUSTER", "突击"),
    "HX": ("HYPERNANO", "铁锤"),
    "65Z": ("POWER CUSHION 65Z", "65Z"),
}
SERIES_CANONICAL_REPLACEMENTS = (
    ("ASTROX", "AX"),
    ("天斧", "AX"),
    ("ARCSABER", "ARCS"),
    ("弓箭", "ARCS"),
    ("NANOFLARE", "NF"),
    ("疾光", "NF"),
    ("AURASPEED", "AS"),
    ("神速", "AS"),
    ("JETSPEED", "JS"),
    ("极速", "JS"),
    ("HALBERTEC", "HAL"),
    ("战戟", "HAL"),
    ("THRUSTER", "TK"),
    ("突击", "TK"),
    ("POWERCUSHION", "PC"),
)
BRAND_ALIASES = {
    "YONEX": ("YONEX", "YY", "尤尼克斯", "尤尼"),
    "LI-NING": ("LI-NING", "LINING", "李宁"),
    "VICTOR": ("VICTOR", "胜利", "维克多"),
    "KAWASAKI": ("KAWASAKI", "川崎"),
    "KUMPOO": ("KUMPOO", "薰风"),
    "KASON": ("KASON", "凯胜"),
}
QUERY_REWRITE_ENABLED = os.getenv("QUERY_REWRITE_ENABLED", "true").lower() in {"true", "1", "yes", "on"}
QUERY_REWRITE_MAX_CHARS = int(os.getenv("QUERY_REWRITE_MAX_CHARS", "300"))


@dataclass(frozen=True)
class QueryAnalysis:
    original_query: str
    normalized_query: str
    expanded_query: str
    category: Optional[str]
    queries: List[str]
    keywords: List[str]
    scope: str
    model_tokens: List[str]
    compare_targets: List[str]


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
    title_score: float = 0.0
    metadata_score: float = 0.0
    model_score: float = 0.0
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
    for model_token in extract_model_tokens(text):
        tokens.add(model_token.lower())
    return {token for token in tokens if token}


def infer_category(text: str) -> Optional[str]:
    """根据明确业务词推断预过滤分类；证据不足时不强行过滤。"""
    scores = {
        category: sum(1 for keyword in keywords if keyword in text)
        for category, keywords in CATEGORY_KEYWORDS.items()
        if category in {"racket", "string", "shuttle", "shoes"}
    }
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return None
    return best_category


def normalize_model_token(token: str) -> str:
    """把型号、系列名统一为更稳定的检索键。"""
    cleaned = re.sub(r"[\s\-_/.]+", "", (token or "").upper())
    for source, target in SERIES_CANONICAL_REPLACEMENTS:
        cleaned = cleaned.replace(source, target)
    return cleaned


def model_alias_variants(token: str) -> List[str]:
    """为常见型号生成中英别名，提升型号级召回。"""
    normalized = normalize_model_token(token)
    variants = [normalized]
    for code, family_aliases in SERIES_CODE_VARIANTS.items():
        if normalized.startswith(code):
            suffix = normalized[len(code):]
            if suffix:
                variants.extend([f"{code}{suffix}"] + [f"{alias} {suffix}" for alias in family_aliases])
            else:
                variants.extend([code, *family_aliases])
    if normalized.startswith("65Z"):
        variants.extend(["65 Z", "POWER CUSHION 65Z"])
    return list(dict.fromkeys(normalize_text(item) for item in variants if item))


def extract_model_tokens(text: str) -> List[str]:
    """从用户问题或文档中抽取型号/系列关键 token。"""
    matches = extract_model_mentions(text)
    variants: List[str] = []
    for token in matches:
        variants.extend(model_alias_variants(token))
    return list(dict.fromkeys(variants))


def extract_model_mentions(text: str) -> List[str]:
    """抽取问题里真正出现过的型号提及，不展开别名。"""
    source = normalize_text(text)
    matches: List[Tuple[int, int, str]] = []
    for pattern in (ASCII_MODEL_RE, TURBO_MODEL_RE, DIGIT_MODEL_RE, CHINESE_MODEL_RE):
        matches.extend((match.start(), match.end(), match.group(0)) for match in pattern.finditer(source))

    mentions: List[str] = []
    selected_ranges: List[Tuple[int, int]] = []
    for start, end, token in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
        if any(start < used_end and end > used_start for used_start, used_end in selected_ranges):
            continue
        normalized = normalize_model_token(token)
        if any(char.isdigit() for char in normalized):
            mentions.append(normalized)
            selected_ranges.append((start, end))
    return list(dict.fromkeys(mentions))


def infer_brand(text: str) -> Optional[str]:
    haystack = normalize_text(text).upper()
    for canonical, aliases in BRAND_ALIASES.items():
        if any(alias.upper() in haystack for alias in aliases):
            return canonical
    return None


def infer_series(text: str) -> Optional[str]:
    haystack = normalize_text(text).upper()
    for code, aliases in SERIES_CODE_VARIANTS.items():
        if code in haystack or any(alias.upper() in haystack for alias in aliases):
            return code
    return None


def infer_doc_type(text: str) -> str:
    normalized = normalize_text(text)
    if any(keyword in normalized for keyword in ("对比", "区别", "比较", "哪个好")):
        return "compare"
    if any(keyword in normalized for keyword in ("参数", "规格", "平衡点", "线径", "中杆")):
        return "params"
    if any(keyword in normalized for keyword in ("入门", "选购", "推荐", "适合")):
        return "guide"
    return "knowledge"


def extract_compare_targets(question: str) -> List[str]:
    """抽取对比问题中的两个对象。"""
    model_mentions = extract_model_mentions(question)
    if len(model_mentions) >= 2:
        return model_mentions[:2]

    normalized = normalize_text(question)
    if not any(keyword in normalized for keyword in ("对比", "比较", "相比", "区别", "哪个好", "差别", "还是", "混着")):
        return []

    compared = re.search(r"(.+?)和(.+?)相比", normalized)
    if compared:
        targets = []
        for segment in compared.groups():
            mentions = extract_model_mentions(segment)
            quoted = re.search(r"[“\"]([^”\"]+)[”\"]", segment)
            targets.append(
                mentions[0]
                if mentions
                else quoted.group(1).strip()
                if quoted
                else segment.strip(" ，,？?、“”\"")
            )
        return list(dict.fromkeys(filter(None, targets)))[:2]

    split = COMPARE_SPLIT_RE.split(normalized)
    if len(split) < 2:
        return []

    targets: List[str] = []
    for segment in split[:2]:
        mentions = extract_model_mentions(segment)
        if mentions:
            targets.append(mentions[0])
            continue
        quoted = re.search(r"[“\"]([^”\"]+)[”\"]", segment)
        if quoted:
            targets.append(quoted.group(1).strip())
            continue
        cleaned = re.sub(r"(?:能)?混着买吗[？?]?$", "", segment).strip()
        cleaned = re.sub(r"(请|帮我|想问|我想|对比|比较|相比|区别|哪个好|差别|怎么样|适合谁|适合我)[？?]?$", "", cleaned).strip()
        cleaned = re.sub(r"^(请|帮我|想问|我想|对比|比较)", "", cleaned).strip()
        if cleaned:
            targets.append(cleaned)
    return list(dict.fromkeys(targets))[:2]


def _expand_query(query: str) -> str:
    additions = []
    for group in SYNONYM_GROUPS:
        if any(term in query for term in group):
            if group[0] == "羽毛球" and any(ex in query for ex in _SHUTTLE_EXCLUDE):
                continue
            additions.extend(term for term in group if term not in query)

    for model_token in extract_model_tokens(query):
        additions.extend(variant for variant in model_alias_variants(model_token) if variant not in query)

    if not additions:
        return query
    return normalize_text(f"{query} {' '.join(dict.fromkeys(additions))}")


def rewrite_query_for_retrieval(query: str, history: Optional[Sequence] = None) -> str:
    """把口语问题整理成稳定检索文本；纯规则实现，不访问 LLM。"""
    constraints = extract_constraints(query, history)
    normalized = normalize_text(query)
    model_tokens = extract_model_tokens(normalized)
    keywords = sorted(tokenize(_expand_query(normalized)), key=lambda value: (-len(value), value))

    level_map = {"beginner": "新手", "intermediate": "进阶", "advanced": "高手", "competitive": "竞技"}
    style_map = {"attack": "进攻", "defense": "防守", "control": "控制", "balanced": "均衡"}
    play_map = {"singles": "单打", "doubles": "双打", "mixed": "混双"}
    physical_map = {
        "knee_sensitive": "膝盖敏感",
        "ankle_sensitive": "脚踝敏感",
        "wrist_sensitive": "手腕力量弱/手腕敏感",
        "shoulder_sensitive": "肩部敏感",
    }

    profile = "、".join(filter(None, [
        level_map.get(constraints.level or ""),
        play_map.get(constraints.play_type or ""),
    ])) or "未明确"
    scene = "、".join(filter(None, [
        style_map.get(constraints.style or ""),
        "、".join(constraints.raw_categories),
    ])) or "未明确"
    budget = constraints.raw_budget or "未明确"
    risks = [physical_map.get(key, key) for key in constraints.physical]
    avoid = []
    if constraints.level == "beginner" or constraints.physical.get("wrist_sensitive"):
        avoid.extend(["3U极头重", "特硬中杆", "高磅"])
    if constraints.style == "defense":
        avoid.append("极端头重慢速拍")

    lines = [
        f"用户画像：{profile}",
        f"打法场景：{scene}",
        f"核心需求：预算{budget}；{normalized}",
        f"风险约束：{'、'.join(risks) if risks else '未明确'}",
        f"检索关键词：{' '.join(dict.fromkeys([*model_tokens, *keywords[:12]]))}",
        f"不应推荐：{'、'.join(dict.fromkeys(avoid)) if avoid else '未明确'}",
    ]
    rewritten = normalize_text("\n".join(lines))
    if len(rewritten) > QUERY_REWRITE_MAX_CHARS:
        rewritten = rewritten[:QUERY_REWRITE_MAX_CHARS].rstrip()
    return rewritten


def _last_user_message(history: Optional[Sequence]) -> str:
    for item in reversed(history or []):
        role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
        content = item.get("content") if isinstance(item, dict) else getattr(item, "content", "")
        if role == "user" and content:
            return normalize_text(content)
    return ""


def classify_question_scope(text: str) -> str:
    """把问题分成：问候/闲聊、装备问题、羽球周边问题、无关话题。"""
    normalized = normalize_text(text)
    lower = normalized.lower()
    if is_greeting_or_chitchat(normalized):
        return "greeting"

    has_product_fact_or_fit = any(keyword in normalized for keyword in (
        "适合", "参数", "规格", "型号", "价格能", "参考价", "实时价吗", "怎么样", "怎么回答",
    ))
    has_equipment_phrase = any(keyword in normalized for keyword in BADMINTON_EQUIPMENT_TERMS)
    has_model_mention = bool(extract_model_tokens(normalized))

    if any(keyword in normalized for keyword in PROMPT_BOUNDARY_TERMS):
        return "prompt_boundary"
    if any(keyword in normalized for keyword in COMMERCE_BOUNDARY_TERMS) and not (
        has_product_fact_or_fit or has_model_mention
    ):
        return "commerce_boundary"
    if any(keyword in normalized for keyword in MEDICAL_BOUNDARY_TERMS) and not has_equipment_phrase:
        return "medical_boundary"

    # 打法偏好属于选拍画像；询问“怎么发力/怎么赢球”则仍是训练或战术问题。
    has_playstyle = any(kw in normalized for kw in BADMINTON_PLAYSTYLE_KEYWORDS)
    has_playstyle_preference = has_playstyle and any(kw in normalized for kw in (
        "喜欢", "偏好", "偏向", "想要", "想打", "打法", "为主", "主打",
    ))
    has_budget_signal = any(kw in normalized for kw in (
        "预算", "元以内", "价位", "多少钱", "价格", "块钱", "块以内",
    ))
    guide_intent = classify_guide_intent(normalized)
    if guide_intent == "compare" and "比较好" in normalized:
        guide_intent = None
    has_equipment_signal = (
        guide_intent is not None
        or bool(extract_model_tokens(normalized))
        or has_equipment_phrase
        or has_budget_signal
        or has_playstyle_preference
    )
    if has_equipment_signal:
        return "equipment"

    has_badminton_general = any(keyword in normalized for keyword in BADMINTON_GENERAL_KEYWORDS)
    has_badminton_context = any(keyword in normalized for keyword in BADMINTON_CONTEXT_WORDS)
    if has_badminton_general or ("羽毛球" in normalized and "装备" not in normalized) or has_badminton_context or has_playstyle:
        return "badminton_general"

    if any(keyword in lower for keyword in ("weather", "python", "股票", "天气", "吃什么", "旅游", "新闻")):
        return "offtopic"
    return "offtopic"


def analyze_query(question: str, history: Optional[Sequence] = None) -> QueryAnalysis:
    """生成检索变体、关键词和前置过滤条件。"""
    normalized = normalize_text(question)
    previous_user_message = _last_user_message(history)
    contextual_query = normalized
    if previous_user_message and (
        len(normalized) <= 14 or any(marker in normalized for marker in FOLLOW_UP_MARKERS)
    ):
        contextual_query = normalize_text(f"{previous_user_message} {normalized}")

    expanded_query = rewrite_query_for_retrieval(contextual_query, history) if QUERY_REWRITE_ENABLED else _expand_query(contextual_query)
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
        scope=classify_question_scope(contextual_query),
        model_tokens=extract_model_tokens(contextual_query),
        compare_targets=extract_compare_targets(contextual_query),
    )


def _split_model_sections(text: str) -> List[KnowledgeSection]:
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    sections: List[KnowledgeSection] = []
    current_title = ""
    current_lines: List[str] = []

    for line in lines:
        model_match = MODEL_HEADING_RE.match(line)
        if model_match and len(line.strip()) <= 48:
            if current_title:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(KnowledgeSection(current_title, content))
            current_title = model_match.group(1).strip()
            current_lines = [line.strip()]
            continue

        if current_title:
            current_lines.append(line)

    if current_title:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(KnowledgeSection(current_title, content))
    return sections if len(sections) >= 2 else []


def split_knowledge_sections(text: str) -> List[KnowledgeSection]:
    """优先按编号 FAQ / 常见问题(Q编号)标题 / 型号或系列小节切分；否则交给外层递归切分。"""
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
        elif FAQ_TITLE_RE.match(line):
            faq_match = FAQ_TITLE_RE.match(line)
            if current_title:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(KnowledgeSection(current_title, content))
            # 段标题取问题正文（含可检索关键词），原始 Q 编号标题行保留在段首内容里
            current_title = faq_match.group(1).strip()
            current_lines = [line.strip()]
        elif current_title:
            current_lines.append(line)

    if current_title:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(KnowledgeSection(current_title, content))

    if len(sections) >= 2:
        return sections
    return _split_model_sections(text)


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


def _metadata_text(metadata: Dict) -> str:
    aliases = metadata.get("model_aliases") or metadata.get("model_tokens") or []
    if not isinstance(aliases, list):
        aliases = [str(aliases)]
    parts = [
        str(metadata.get("section_title", "")),
        str(metadata.get("file_name", "")),
        str(metadata.get("brand", "")),
        str(metadata.get("series", "")),
        " ".join(str(item) for item in aliases if item),
        str(metadata.get("doc_type", "")),
    ]
    return normalize_text(" ".join(part for part in parts if part))


def _model_match_score(model_tokens: Sequence[str], metadata: Dict, content: str) -> float:
    if not model_tokens:
        return 0.0
    metadata_tokens = metadata.get("model_tokens") or metadata.get("model_aliases") or []
    metadata_set = {normalize_model_token(token) for token in metadata_tokens}
    content_set = {normalize_model_token(token) for token in extract_model_tokens(content)}
    query_set = {normalize_model_token(token) for token in model_tokens}
    if query_set & metadata_set:
        return 1.0
    if query_set & content_set:
        return 0.8
    return 0.0


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
    query_tokens = tokenize(analysis.expanded_query)
    query_len = len(analysis.normalized_query)
    for candidate in candidates:
        candidate.lexical_score = _token_coverage(query_tokens, candidate.content)
        candidate.title_score = _token_coverage(
            query_tokens,
            str(candidate.metadata.get("section_title", "")),
        )
        candidate.metadata_score = _token_coverage(query_tokens, _metadata_text(candidate.metadata))
        candidate.model_score = _model_match_score(analysis.model_tokens, candidate.metadata, candidate.content)
        rrf_norm = candidate.rrf_score / max_rrf
        dense_norm = max(0.0, min(1.0, candidate.score))
        candidate.final_score = (
            0.40 * rrf_norm
            + 0.15 * dense_norm
            + 0.15 * candidate.lexical_score
            + 0.10 * candidate.title_score
            + 0.10 * candidate.metadata_score
            + 0.10 * candidate.model_score
        )
        candidate.confidence = max(
            candidate.lexical_score,
            candidate.title_score,
            candidate.metadata_score,
            candidate.model_score,
            0.65 * dense_norm + 0.35 * max(candidate.lexical_score, candidate.metadata_score),
        )

    ranked = sorted(candidates, key=lambda item: item.final_score, reverse=True)
    effective_threshold = threshold * (0.7 if query_len <= 6 else 1.0)
    filtered = [item for item in ranked if item.confidence >= effective_threshold]
    if filtered:
        return filtered[:top_k]

    if analysis.model_tokens or analysis.compare_targets:
        return []

    if any(max(item.lexical_score, item.title_score, item.metadata_score, item.model_score) > 0 for item in ranked):
        return ranked[:top_k]
    return []


# ============================================================================
# BM25 关键词召回打分（P1-1，纯函数）
# ============================================================================
# 标准参数：k1 控制词频饱和度，b 控制文档长度归一
_BM25_K1 = 1.5
_BM25_B = 0.75


def bm25_scores(
    query_tokens: Sequence[str],
    corpus: Sequence[Counter],
    doc_freq: Dict[str, int],
    doc_lens: Sequence[int],
    k1: float = _BM25_K1,
    b: float = _BM25_B,
) -> List[float]:
    """对语料逐文档计算 BM25 得分（纯函数，可在离线评测中直接验证）。

    query_tokens：查询词元；corpus：每篇文档的词频 Counter；
    doc_freq：词元在语料中的文档频率；doc_lens：每篇文档词元总数。
    IDF 在给定语料内计算，无需重索引 chroma，满足"知识库向量库不要动"约束。
    """
    n_docs = len(corpus)
    avgdl = (sum(doc_lens) / n_docs) if doc_lens else 0.0
    out: List[float] = []
    for i, toks in enumerate(corpus):
        score = 0.0
        dl = doc_lens[i]
        for term in query_tokens:
            if term not in doc_freq:
                continue
            tf = toks.get(term, 0)
            if tf == 0:
                continue
            idf = math.log(1.0 + (n_docs - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            score += idf * (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * dl / avgdl))
        out.append(score)
    return out


# ============================================================================
# 闲聊 / 问候拦截
# ============================================================================

_GREETING_WORDS = frozenset({
    "你好", "您好", "hi", "hello", "嗨", "嘿", "哈喽", "哈罗",
    "在吗", "在不在", "有人在", "打招呼",
    "谢谢", "感谢", "多谢", "thx", "thanks",
    "再见", "拜拜", "bye", "晚安", "早安", "午安",
    "好的", "ok", "okay", "嗯", "哦", "噢",
    "哈哈", "呵呵", "嘿嘿", "haha", "233",
})

_CHITCHAT_MARKERS = frozenset({
    "你是谁", "你叫什么", "你是ai", "你是机器人", "介绍一下你自己",
    "你会什么", "你能做什么", "帮我干", "陪我聊",
    "无聊", "干嘛", "真的么", "是吗", "对不对", "是不是",
    "我想聊", "聊天", "闲聊",
})


def is_greeting_or_chitchat(text: str) -> bool:
    """判断是否为闲聊/问候消息，若是则应跳过 RAG 与推荐引擎。"""
    t = normalize_text(text).lower()
    clean = re.sub(r"[，。！？、；：\"'（）【】\s]+", "", t)
    if clean in _GREETING_WORDS or t.strip() in _GREETING_WORDS:
        return True
    if len(clean) <= 4 and any(g in clean for g in _GREETING_WORDS):
        return True
    if any(marker in t for marker in _CHITCHAT_MARKERS):
        return True
    return False


# ============================================================================
# 导购意图识别 + 约束抽取
# ============================================================================

GUIDE_INTENT_KEYWORDS = {
    "single_recommend": ("推荐", "买什么", "选什么", "该买吗", "适合我", "推荐一下", "有什么好", "怎么选", "选个", "配吗"),
    "bundle_recommend": ("一套", "配齐", "组合", "怎么配", "搭配", "全配", "整套", "怎么买"),
    "compare": ("对比", "比较", "相比", "哪个好", "区别", "和什么比", "差别", "选哪个", "混着买吗"),
    "param_explain": ("什么意思", "是什么意思", "参数", "磅数", "平衡点", "中杆", "U数", "球速", "线径", "材质", "硬度"),
    "upgrade": ("升级", "提升", "想换", "进阶", "换拍", "怎么改"),
    "avoid": ("避坑", "不要买", "不建议", "新手不要", "别买", "坑", "雷"),
}

CATEGORY_NAME_BY_ID = {1: "球拍", 2: "球线", 3: "羽毛球", 4: "球鞋"}

CATEGORY_ALIASES = {
    1: ("球拍", "羽毛球拍", "拍子", "拍", "racket"),
    2: ("球线", "线", "拍线", "穿线", "string"),
    3: ("羽毛球", "鹅毛", "鸭毛", "shuttlecock"),
    4: ("球鞋", "鞋", "羽毛球鞋", "鞋子", "shoes"),
}

LEVEL_KEYWORDS = {
    "beginner": ("新手", "入门", "初学", "刚学", "菜鸟", "小白", "不会打"),
    "intermediate": ("进阶", "中级", "有点基础", "打了一段时间", "业余"),
    "advanced": ("高手", "高级", "熟练", "老手", "常年打"),
    "competitive": ("比赛", "专业", "职业", "赛事", "国家队", "运动员"),
}

STYLE_KEYWORDS = {
    "attack": ("进攻", "杀球", "后场", "重杀", "下压"),
    "defense": ("防守", "双打", "平抽", "网前", "防守反击"),
    "control": ("控制", "控球", "拉吊", "落点"),
    "balanced": ("均衡", "全面", "平衡", "攻守"),
}

PLAY_TYPE_KEYWORDS = {
    "singles": ("单打",),
    "doubles": ("双打",),
    "mixed": ("混双", "混合"),
}

PHYSICAL_KEYWORDS = {
    "knee_sensitive": ("膝盖", "膝关节"),
    "ankle_sensitive": ("脚踝", "踝关节"),
    "wrist_sensitive": ("手腕",),
    "shoulder_sensitive": ("肩膀", "肩关节"),
}

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


def _extract_budget(text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """返回 (budget_min, budget_max, raw)。"""
    budget_min = budget_max = None
    raw = None
    match = re.search(r"(\d+)\s*[-~到至]\s*(\d+)", text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        budget_min, budget_max = min(a, b), max(a, b)
        raw = f"{budget_min}-{budget_max}"
        return budget_min, budget_max, raw
    match = re.search(r"(\d+)\s*(?:元|块)?\s*(?:以内|以下|之内|不超过|不超|封顶)", text)
    if match:
        budget_max = int(match.group(1))
        raw = f"<={budget_max}"
        return budget_min, budget_max, raw
    match = re.search(r"(\d+)\s*(?:元|块)?\s*(?:以上|起|往上)", text)
    if match:
        budget_min = int(match.group(1))
        raw = f">={budget_min}"
        return budget_min, budget_max, raw
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
        if cid == 3:
            matched = any(alias in merged for alias in aliases if alias != "羽毛球")
            matched = matched or ("羽毛球" in merged and "羽毛球拍" not in merged)
        else:
            matched = any(alias in merged for alias in aliases)
        if matched:
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
