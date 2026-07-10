#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Score BadmintonGear-AI golden-set outputs with transparent keyword/rule checks.

Example:
  python eval_badminton_rag_golden.py \
    --golden badminton_rag_golden_set_v1.jsonl \
    --results badminton_rag_golden_results.jsonl \
    --out badminton_rag_eval_report.json \
    --csv-out badminton_rag_eval_report.csv
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def contains_any(text: str, terms: List[str]) -> bool:
    low = text.lower()
    return any(term and term.lower() in low for term in terms)


FORMAT_MARKER_ALIASES = {
    "推荐装备清单": ["推荐结论", "为什么适合你", "注意事项", "替代方案"],
    "适合原因": ["为什么适合你", "适合原因"],
}


def marker_hit(answer: str, marker: str) -> bool:
    return contains_any(answer, FORMAT_MARKER_ALIASES.get(marker, [marker]))


def score_case(case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    answer = to_text(result.get("answer"))
    sources_text = to_text(result.get("sources"))
    products_text = to_text(result.get("recommended_products"))
    response_text = to_text(result.get("response"))

    rubric = case["rubric"]
    weights = rubric["weights"]

    must_groups = rubric.get("must_include_any_groups") or []
    group_hits = [contains_any(answer, group) for group in must_groups]
    answer_keypoints = sum(group_hits) / len(must_groups) if must_groups else 1.0

    forbidden = rubric.get("must_not_include") or []
    forbidden_hits = [term for term in forbidden if term and term.lower() in answer.lower()]
    forbidden_score = 0.0 if forbidden_hits else 1.0

    source_keywords = case["expected"].get("expected_source_keywords") or []
    source_corpus = sources_text + "\n" + answer + "\n" + response_text
    source_hit = (
        sum(contains_any(source_corpus, [keyword]) for keyword in source_keywords)
        / len(source_keywords)
        if source_keywords else 1.0
    )

    expected_products = case["expected"].get("expected_products") or []
    product_corpus = products_text + "\n" + answer + "\n" + response_text
    product_hit = (
        sum(contains_any(product_corpus, [product]) for product in expected_products)
        / len(expected_products)
        if expected_products else 1.0
    )

    format_markers = rubric.get("expected_format_markers") or []
    format_score = (
        sum(marker_hit(answer, marker) for marker in format_markers)
        / len(format_markers)
        if format_markers else 1.0
    )

    score = (
        weights.get("answer_keypoints", 0) * answer_keypoints
        + weights.get("forbidden_content", 0) * forbidden_score
        + weights.get("source_hit", 0) * source_hit
        + weights.get("product_hit", 0) * product_hit
        + weights.get("format", 0) * format_score
    )

    return {
        "id": case["id"],
        "group": case["group"],
        "score": round(score, 4),
        "answer_keypoints": round(answer_keypoints, 4),
        "forbidden_content": round(forbidden_score, 4),
        "source_hit": round(source_hit, 4),
        "product_hit": round(product_hit, 4),
        "format": round(format_score, 4),
        "forbidden_hits": forbidden_hits,
        "missing_keypoint_groups": [
            must_groups[i] for i, hit in enumerate(group_hits) if not hit
        ],
        "answer_chars": len(answer),
        "ok": bool(result.get("ok", True)),
        "status_code": result.get("status_code"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="badminton_rag_golden_set_v1.jsonl")
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", default="badminton_rag_eval_report.json")
    parser.add_argument("--csv-out", default="badminton_rag_eval_report.csv")
    args = parser.parse_args()

    cases = {case["id"]: case for case in load_jsonl(Path(args.golden))}
    results = {row["id"]: row for row in load_jsonl(Path(args.results))}

    rows = []
    for case_id, case in cases.items():
        result = results.get(case_id, {"id": case_id, "answer": "", "ok": False})
        rows.append(score_case(case, result))

    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(row["score"])

    summary = {
        "case_count": len(rows),
        "overall_score": round(sum(row["score"] for row in rows) / len(rows), 4) if rows else 0,
        "pass_rate_0_80": round(sum(row["score"] >= 0.80 for row in rows) / len(rows), 4) if rows else 0,
        "group_scores": {
            group: round(sum(scores) / len(scores), 4)
            for group, scores in sorted(by_group.items())
        },
        "weak_cases": [row for row in rows if row["score"] < 0.80],
    }

    report = {"summary": summary, "cases": rows}
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    with Path(args.csv_out).open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "id", "group", "score", "answer_keypoints", "forbidden_content",
            "source_hit", "product_hit", "format", "forbidden_hits",
            "answer_chars", "ok", "status_code",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(row[key], ensure_ascii=False)
                if isinstance(row.get(key), (list, dict)) else row.get(key)
                for key in fieldnames
            })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved: {args.out}")
    print(f"Saved: {args.csv_out}")


if __name__ == "__main__":
    main()
