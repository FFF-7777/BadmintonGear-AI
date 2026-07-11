import json, glob, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DIMS = ["routing", "parameter", "recommendation", "comparision",
        "grounding_policy", "product_fact", "general_training_safety",
        "source_hit", "format", "product_hit", "forbidden_content",
        "answer_keypoints"]

def analyze(f):
    d = json.load(open(f, encoding="utf-8"))
    if isinstance(d, dict):
        print("  top-keys:", list(d.keys()))
        s = d.get("summary")
        if s:
            print("  SUMMARY:", json.dumps(s, ensure_ascii=False)[:1500])
        results = d.get("results", [] if isinstance(d, list) else d)
    else:
        results = d
    if not isinstance(results, list):
        return None
    n = len(results)
    sc = [r["score"] for r in results if isinstance(r, dict) and "score" in r]
    mean = round(sum(sc) / len(sc), 4) if sc else None
    # 过线率：score>=0.7
    passrate = round(sum(1 for x in sc if x >= 0.7) / len(sc), 4) if sc else None
    print(f"  条数={n}  总分(mean score)={mean}  过线率(>=0.7)={passrate}")
    # 各维度均值
    print("  各维度均值:")
    for dim in DIMS:
        vals = [r.get(dim) for r in results if isinstance(r, dict) and isinstance(r.get(dim), (int, float))]
        if vals:
            print(f"    {dim:28s} {round(sum(vals)/len(vals),4)}")
    return mean

files = sorted(glob.glob("*eval_report*.json"))
print("发现报告文件:", files)
for f in files:
    print("\n=====", f)
    analyze(f)
