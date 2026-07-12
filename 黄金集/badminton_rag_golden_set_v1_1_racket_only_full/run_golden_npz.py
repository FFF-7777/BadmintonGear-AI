# -*- coding: utf-8 -*-
"""一键跑黄金集(npz 模式)并打分。
前置：
  - 后端在 http://127.0.0.1:8000 运行（VECTOR_STORE_LOCAL=1，已 reload 含 _keyword_recall 修复）
产物：
  - badminton_rag_golden_results_v1_1_npz.jsonl  （系统真实输出）
  - badminton_rag_eval_report_v1_1_npz.json / .csv （评分报告）
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

PY = r"C:\Users\Lenovo\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
GOLDEN = "badminton_rag_golden_set_v1_1_racket_only.jsonl"
RESULTS = "badminton_rag_golden_results_v1_1_npz.jsonl"

ROOT = Path(HERE).parents[1]
SERVER = ROOT / "server"
sys.path.insert(0, str(SERVER))
from database import SessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from utils.security import create_access_token  # noqa: E402

db = SessionLocal()
try:
    user = db.query(User).order_by(User.id.asc()).first()
    if user is None:
        raise RuntimeError("数据库中没有可用于评测的普通用户")
    tok = create_access_token({"sub": str(user.id), "type": "user"})
finally:
    db.close()
print("temporary evaluation token created in memory", flush=True)

env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

print("=== STEP1: 跑黄金集（live 后端 / npz 模式）===", flush=True)
t0 = time.time()
r = subprocess.run(
    [PY, "run_badminton_rag_golden_api.py",
     "--base-url", "http://127.0.0.1:8000",
     "--golden", GOLDEN,
     "--out", RESULTS,
     "--token", tok,
     "--timeout", "120",
     "--sleep", "0.3"],
    env=env,
)
print("run exit=%s 耗时=%.1f 分" % (r.returncode, (time.time() - t0) / 60), flush=True)
if r.returncode != 0:
    print("RUN FAILED，中止打分", flush=True)
    sys.exit(1)

print("=== STEP2: 打分 ===", flush=True)
r2 = subprocess.run(
    [PY, "eval_badminton_rag_golden.py",
     "--golden", GOLDEN,
     "--results", RESULTS,
     "--out", "badminton_rag_eval_report_v1_1_npz.json",
     "--csv-out", "badminton_rag_eval_report_v1_1_npz.csv"],
    env=env,
)
print("eval exit=%s" % r2.returncode, flush=True)
print("ALL DONE", flush=True)
