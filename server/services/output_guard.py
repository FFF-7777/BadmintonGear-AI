"""输出后处理：绝对化 / 夸大表述的确定性软改写兜底。

定位：作为 system prompt 软约束（layer 1）之外的 **layer 2 代码级兜底**。
当 LLM 仍吐出「最强 / 最贵 / 唯一选择」等绝对化用语时，由本模块在返回前
确定性地改写成中性表述，避免 REC009 类漏网。

设计原则（基于对 64 条真实答案的逐条审计）：
- 只拦「确实构成夸大宣称」的固定搭配；
- 避开物理量术语（绝对重量 / 绝对速度 / 绝对威力）、
  正确安全劝退（绝对避免 / 绝对不能 / 绝对不适合）、
  事实性陈述（唯一候选 / 唯一标注 / 唯一来源）等合规用法，避免误伤；
- 纯正则、O(n)、零外部调用、零额外延迟。
"""

from __future__ import annotations

import re
from typing import List, Tuple

# (正则, 替换) —— 顺序即优先级；更具体的先匹配。
_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # —— 强烈夸大宣称：在导购语境下均属过度承诺，统一中性化 ——
    (re.compile(r"最强进攻拍"), "综合进攻性能突出的球拍"),
    (re.compile(r"最强"), "综合表现突出的"),
    (re.compile(r"最强大"), "实力突出的"),
    (re.compile(r"无敌"), "优势明显的"),
    (re.compile(r"碾压"), "明显优于"),
    (re.compile(r"吊打"), "优于"),
    (re.compile(r"完爆"), "优于"),
    (re.compile(r"最贵"), "价格偏高的"),
    (re.compile(r"最便宜"), "价格偏低的"),
    (re.compile(r"必买"), "值得考虑"),
    (re.compile(r"闭眼入|闭眼买"), "可优先考虑"),
    (re.compile(r"100%\s*保证|百分百保证|百分之百保证"), "较有保障"),

    # —— 「绝对」+ 正面推荐（拦）；「绝对」+ 劝退 / 否定 / 物理量（放）——
    # 负向后接（不适合 / 不能 / 避免 / 不…）一律放过，仅拦正向承诺。
    (re.compile(r"(?<!不|无|没)绝对(适合|推荐|值得|选它|入手|买)"), r"通常\1"),

    # —— 「唯一」+ 推荐意味（拦）；「唯一」+ 事实陈述（放）——
    (re.compile(r"唯一(选择|之选|推荐)"), r"少有\1"),
]


def sanitize_superlative(text: str) -> str:
    """对答案文本做绝对化用语软改写，返回改写后文本。

    不改写合规表述；空输入原样返回。
    """
    if not text:
        return text
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out


def count_superlative(text: str) -> int:
    """统计命中次数（供可选的检测标记 / 日志使用）。"""
    if not text:
        return 0
    return sum(len(pat.findall(text)) for pat, _ in _PATTERNS)
