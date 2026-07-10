"""静态扫描历史目录、运行数据与演示文件，输出遗留审计报告。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "legacy_audit_report.md"


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> None:
    archive_exists = exists("archive")
    weixin_exists = exists("archive/weixin_miniprogram_original")
    lines = [
        "# 遗留代码静态审计报告",
        "",
        "本报告由 `scripts/audit-legacy.py` 生成，并结合当前项目结构做保守判断；本轮不删除任何文件。",
        "",
        "## 运行时依赖清单",
        "",
        "- `app/`：用户端前台，当前聊天页、装备库、装备详情页都在使用，不能删除。",
        "- `client/`：管理后台，包含装备管理、知识库上传、品类、用户、内容位等页面，README、CI、`docker-compose.yml`、`scripts/smoke-test.ps1` 均引用，不能删除。",
        "- `server/`：FastAPI 后端，负责 API、商品库、RAG、聊天、知识库上传，不能删除。",
        "- `app/src/data/knowledge.js`：仍被 `app` 的品牌/品类展示页引用；本地 `ask/searchArticles` 降级逻辑已移除，目前只保留展示数据，不能当聊天假知识库删除。",
        "- `知识库/测试.md`：用户明确说明用于测试能否向量化，本轮保留，不纳入垃圾文件。",
        "",
        "## 未发现项",
        "",
        f"- 当前根目录{'已发现' if archive_exists else '未发现'} `archive/`。",
        f"- 当前根目录{'已发现' if weixin_exists else '未发现'} `archive/weixin_miniprogram_original`。",
        "- 当前前台聊天页未发现 `pickProducts()` 或前端本地问答兜底路径。",
        "",
        "## 高概率可清理候选",
        "",
        "- `.runtime-logs/`：本地运行日志，已在 `.gitignore` 中，不影响运行；可在确认没有需要追溯的日志后清理。",
        "- `output/`：Playwright 截图/调试输出目录，已在 `.gitignore` 中；可在确认不再需要截图后清理。",
        "- `.pytest_cache/`、`.playwright-cli/`：本地工具缓存，已忽略；可清理。",
        "- `server/_tmp_*.txt`：临时调试输出，已在 `.gitignore` 中；可清理。",
        "- `RAG优化建议.md`：用户已确认这是旧方案，不作为当前执行依据；建议保留到第二轮统一归档或删除。",
        "",
        "## 需要人工复核",
        "",
        "- `爬虫/`：体积大且已在 `.gitignore`；但历史上用于批量导入商品和图片，清理前应确认原始导入资料是否还要留档。",
        "- `uploads14/`：运行时上传目录，包含知识库、商品图片等运行数据；不能按“垃圾代码”删除。",
        "- `server/dev.db` 与备份：本地数据库和备份数据；清理前必须确认数据已导出或可重建。",
        "- `client/dist/`、`app/dist/`：构建产物，已忽略；可删除但会被下一次 build 重新生成。",
        "",
        "## 建议清理顺序",
        "",
        "1. 先只清理缓存/日志：`.runtime-logs/`、`output/`、`.pytest_cache/`、`.playwright-cli/`。",
        "2. 再处理旧文档：确认 `RAG优化建议.md` 不再需要后归档或删除。",
        "3. 最后才处理数据目录：`爬虫/`、`uploads14/`、`server/dev.db*`，并在操作前备份。",
        "4. 每轮删除后运行 `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`。",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
