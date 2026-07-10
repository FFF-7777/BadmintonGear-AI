# BadmintonGear-AI RAG 第一阶段整改完成清单

> 当前状态：代码侧不依赖向量库的整改已完成；向量数据库仍由用户后续自行向量化/重新入库。

## 已完成

- RAG 生成参数接线：`temperature=0.2`、`top_p=0.85`、`max_tokens=1200`、低重复惩罚与关闭默认 thinking。
- 检索参数接线：`RAG_TOP_K=6`、`RAG_CANDIDATE_K=30`、`RAG_MAX_CONTEXT_CHARS=9000`、`CHUNK_SIZE=1000`、`CHUNK_OVERLAP=120`。
- Query rewrite：规则式生成“用户画像 / 打法场景 / 核心需求 / 风险约束 / 检索关键词 / 不应推荐”。
- 型号别名归一：支持 `YY`、`YONEX`、`ASTROX/AX/天斧`、`JS-12/JS12` 等结构化商品匹配。
- 对比题增强：同一问题内两个型号会优先各自匹配商品库对象。
- 品类边界：当前只对球拍做具体型号推荐；球线、球鞋、羽毛球降级为通用原则，不硬编型号。
- 推荐排序：加入 `source_confidence`，低可信或字段不足商品只作为备选。
- 推荐返回字段：补齐 `confidence`、`source_confidence`、`recommendation_role`、`risk`。
- 回答模板：推荐题固定四段式，资料不足固定“初步判断 / 还需要确认的信息 / 保守选择方向 / 暂不建议”。
- Sources 展示：后端返回 `source_confidence`、`unverified_fields`、`doc_type`、`matched_model`；前端聊天页展示参考资料面板。
- 推荐卡：前端展示首推/备选、推荐置信度、来源可信度和风险提示。
- 流式体验：移除大量调试日志；推荐卡只在 `done` 后挂载；`done` 后不强制滚到推荐卡。
- 装备详情：相关对比卡点击后会更新当前详情页内容。
- 批量导入模板：补 `source_confidence` 和 `unverified_fields` 字段。
- 遗留审计：生成 `legacy_audit_report.md`，明确 `client/` 是后台不能删，`知识库/测试.md` 是用户向量化测试文件。
- 文档：README 更新当前结构、RAG 流程、品类边界、验证方式。
- 烟测：`scripts/smoke-test.ps1` 优先使用 WorkBuddy Python 环境。

## 已验证

## 已定最终 chunk 配置

- `CHUNK_SIZE=1000`
- `CHUNK_OVERLAP=120`
- `MIN_CHUNK_CHARS=180`
- `MAX_CHUNK_CHARS=1400`
- `SPLIT_BY_HEADING=true`
- `KEEP_TABLES=true`
- `KEEP_YAML_BLOCKS=true`
- `PRODUCT_CHUNK_MODE=one_product_one_chunk`
- 以上配置会影响向量库内容；本次定稿后再向量化，后续优先只调召回、rerank、prompt 和推荐排序。

- 后端单测：18 个通过。
- 用户端 `app` 构建通过。
- 管理后台 `client` 构建通过。
- 总烟测脚本通过。

## 留待向量化后验证

- 新切块参数是否让型号 chunk 更稳定，需要用户重新入库/向量化后验证。
- 空向量库状态下，知识库 sources 不会出现；向量化后再测具体型号召回、对比题来源命中和低置信度过滤。
- 黄金集评估需要等知识库向量化完成后再跑。

## 不做自动处理

- 不自动向量化。
- 不删除 `知识库/测试.md`。
- 不删除 `uploads14/`、`server/dev.db`、`爬虫/` 等数据目录。
