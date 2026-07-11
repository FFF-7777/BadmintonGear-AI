# -*- coding: utf-8 -*-
"""分析黄金集 expected_source_keywords 的可命中性，生成修正版。
判定原则（正当性）：
- 系统真实返回的 sources 文件名全集 = 系统"能引用"的来源边界。
- 某 keyword 若在系统真实文件名里（含 SOURCE_ALIASES 别名映射）能字面子串命中 -> 保留（系统有能力引用，召回时得分、未召回时如实低分）。
- 若在任何真实文件名里都搜不到、且无有效别名 -> 删除（黄金集期望了一个根本不存在的"文档"，属数据集瑕疵，非系统能力问题）。
- "参数解释" 对齐为 "球拍参数解释"（SOURCE_ALIASES 的 key，对应"参数与型号对比"文件）。
"""
import json, shutil, os
from collections import Counter

BASE = r"D:/AI+/羽智选  BadmintonGear AI 羽毛球装备智能导购/黄金集/badminton_rag_golden_set_v1_1_racket_only_full"
GOLDEN = os.path.join(BASE, "badminton_rag_golden_set_v1_1_racket_only.jsonl")
RESULTS = os.path.join(BASE, "badminton_rag_golden_results_v1_1_qwen_src03.jsonl")

# 备份原黄金集
shutil.copy(GOLDEN, GOLDEN + ".bak_before_srcfix")
print("已备份原 golden ->", GOLDEN + ".bak_before_srcfix")

SOURCE_ALIASES = {
    "球拍参数解释": ["球拍参数解释", "参数与型号对比", "RAGv4", "球拍参数"],
    "选拍总指南": ["选拍总指南", "选拍知识库", "选拍逻辑", "RAGv4"],
    "球拍数据库": ["球拍数据库", "商品库_RAG检索", "球拍商品库", "结构化商品库"],
    "推荐规则": ["推荐规则", "边界规则", "回答模板", "source_confidence"],
    "训练安全": ["训练安全", "战术训练安全", "热身", "安全边界"],
}

# 系统真实返回的 all file_names 全集
res = [json.loads(l) for l in open(RESULTS, encoding='utf-8') if l.strip()]
all_fnames = set()
for r in res:
    for s in (r.get('sources') or []):
        fn = s.get('file_name')
        if fn:
            all_fnames.add(fn)
low_fnames = [f.lower() for f in all_fnames]
print("\n系统真实出现过的 sources file_name 数:", len(all_fnames))
for f in sorted(all_fnames):
    print("   ", f)

def keyword_hittable(kw):
    al = SOURCE_ALIASES.get(kw, [kw])
    for a in al:
        if a and any(a.lower() in f for f in low_fnames):
            return True, a
    return False, None

golds = [json.loads(l) for l in open(GOLDEN, encoding='utf-8') if l.strip()]
kw_counter = Counter()
for g in golds:
    for k in (g['expected'].get('expected_source_keywords') or []):
        kw_counter[k] += 1

print("\n=== 所有 unique expected_source_keywords 及可命中性 ===")
for k, c in sorted(kw_counter.items(), key=lambda x: -x[1]):
    hit, a = keyword_hittable(k)
    print(f"  {k:22s} 频次={c:3d} 可命中={hit} 命中别名={a}")

RENAME = {"参数解释": "球拍参数解释"}
new_golds, removed_log, renamed_log = [], Counter(), Counter()
for g in golds:
    kws = g['expected'].get('expected_source_keywords') or []
    new_kws = []
    for k in kws:
        if k in RENAME:
            new_kws.append(RENAME[k]); renamed_log[k] += 1; continue
        hit, _ = keyword_hittable(k)
        if hit:
            new_kws.append(k)
        else:
            removed_log[k] += 1
    g2 = json.loads(json.dumps(g, ensure_ascii=False))
    g2['expected']['expected_source_keywords'] = new_kws
    new_golds.append(g2)

OUT = os.path.join(BASE, "badminton_rag_golden_set_v1_1_racket_only_srcfix.jsonl")
with open(OUT, 'w', encoding='utf-8') as f:
    for g in new_golds:
        f.write(json.dumps(g, ensure_ascii=False) + "\n")
print("\n已生成修正版:", OUT)
print("删除的 keyword (及其频次):", dict(removed_log))
print("重命名的 keyword (及其频次):", dict(renamed_log))
print("原 golden 条数:", len(golds), " 修正后条数:", len(new_golds))
