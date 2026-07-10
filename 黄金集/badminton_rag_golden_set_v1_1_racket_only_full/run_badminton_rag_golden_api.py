#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run BadmintonGear-AI golden set against the FastAPI chat endpoint.

Example:
  python run_badminton_rag_golden_api.py \
    --base-url http://127.0.0.1:8000 \
    --golden badminton_rag_golden_set_v1.jsonl \
    --out badminton_rag_golden_results.jsonl \
    --token "$TOKEN"
"""
import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def call_chat(
    base_url: str,
    message: str,
    session_id: Optional[str],
    token: Optional[str],
    timeout: int,
) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/api/chat/send"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload: Dict[str, Any] = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    try:
        body = response.json()
    except Exception:
        body = {"raw_text": response.text}

    return {"status_code": response.status_code, "ok": response.ok, "response": body}


def unwrap_api_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Support both raw chat payloads and success({data: ...}) API envelopes."""
    data = body.get("data") if isinstance(body, dict) else None
    return data if isinstance(data, dict) else body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--golden", default="badminton_rag_golden_set_v1.jsonl")
    parser.add_argument("--out", default="badminton_rag_golden_results.jsonl")
    parser.add_argument("--token", default=None, help="Bearer token if the API requires auth")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    cases = load_jsonl(Path(args.golden))
    output_path = Path(args.out)

    with output_path.open("w", encoding="utf-8") as f:
        for index, case in enumerate(cases, start=1):
            session_id: Optional[str] = None

            # Recreate minimal history for follow-up cases.
            for message in case.get("history", []):
                if message.get("role") == "user":
                    history_result = call_chat(
                        args.base_url,
                        message.get("content", ""),
                        session_id,
                        args.token,
                        args.timeout,
                    )
                    session_id = (
                        unwrap_api_data(history_result.get("response") or {}).get("session_id")
                        or session_id
                    )
                    time.sleep(args.sleep)

            result = call_chat(
                args.base_url,
                case["user_query"],
                session_id,
                args.token,
                args.timeout,
            )
            raw_body = result.get("response") or {}
            body = unwrap_api_data(raw_body)
            answer = body.get("answer") or body.get("content") or body.get("message") or ""

            row = {
                "id": case["id"],
                "group": case["group"],
                "user_query": case["user_query"],
                "status_code": result["status_code"],
                "ok": result["ok"],
                "answer": answer,
                "sources": body.get("sources", []),
                "recommended_products": body.get("recommended_products", []),
                "response": raw_body,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{index}/{len(cases)}] {case['id']} status={result['status_code']} chars={len(answer)}")
            time.sleep(args.sleep)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
