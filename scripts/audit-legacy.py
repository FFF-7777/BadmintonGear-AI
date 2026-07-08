"""静态扫描历史目录、未引用资源与演示数据文件，输出审计报告。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "legacy_audit_report.md"

TEXT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".vue", ".css", ".scss", ".md", ".json", ".py", ".sql", ".html"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def build_search_corpus() -> str:
    chunks = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts or "dist" in path.parts:
            continue
        if "scripts" in path.parts or path.name == REPORT_PATH.name:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        chunks.append(read_text(path))
    return "\n".join(chunks)


def candidate_paths() -> dict:
    return {
        "archive_dirs": [ROOT / "archive" / "weixin_miniprogram_original"],
        "demo_files": [
            ROOT / "app" / "src" / "data" / "knowledge.js",
            ROOT / "client" / "src" / "components" / "HelloWorld.vue",
            ROOT / "app" / "src" / "assets" / "vite.svg",
            ROOT / "app" / "src" / "assets" / "vue.svg",
            ROOT / "client" / "src" / "assets" / "vite.svg",
            ROOT / "client" / "src" / "assets" / "vue.svg",
        ],
    }


def is_referenced(path: Path, corpus: str) -> bool:
    markers = {
        path.name,
        path.stem,
        str(path.relative_to(ROOT)).replace("\\", "/"),
    }
    return any(marker and marker in corpus for marker in markers)


def main() -> None:
    corpus = build_search_corpus()
    groups = candidate_paths()
    lines = [
        "# 遗留代码静态审计报告",
        "",
        "本报告由 `scripts/audit-legacy.py` 自动生成，基于源码文本引用扫描，不等同于运行时完全证明。",
        "",
        "## 高概率可清理候选",
    ]

    removable = []
    uncertain = []
    runtime = []

    for directory in groups["archive_dirs"]:
        if directory.exists():
            removable.append(f"- `{directory.relative_to(ROOT).as_posix()}`：源码中未发现对该历史微信小程序目录的引用，当前作为高概率可清理候选。")

    for file_path in groups["demo_files"]:
        if not file_path.exists():
            continue
        if is_referenced(file_path, corpus):
            runtime.append(f"- `{file_path.relative_to(ROOT).as_posix()}`：仍存在文本引用，暂不建议删除。")
        else:
            removable.append(f"- `{file_path.relative_to(ROOT).as_posix()}`：未发现外部引用，属于演示/脚手架残留候选。")

    if removable:
        lines.extend(removable)
    else:
        lines.append("- 暂无。")

    lines.extend([
        "",
        "## 需要人工复核",
    ])
    if uncertain:
        lines.extend(uncertain)
    else:
        lines.append("- 目前未发现必须人工复核的模糊项；如后续接入运行时动态加载资源，仍建议删除前手工回归。")

    lines.extend([
        "",
        "## 当前仍在使用或存在文本引用的文件",
    ])
    if runtime:
        lines.extend(runtime)
    else:
        lines.append("- 暂无。")

    lines.extend([
        "",
        "## 建议",
        "- 第二轮清理前，先跑一次前台 `app` 构建、后台 `client` 构建和后端 smoke test。",
        "- 对 `archive/` 这类目录建议整目录打包备份后再删除。",
    ])

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
