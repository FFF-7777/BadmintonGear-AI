# 遗留代码静态审计报告

本报告由 `scripts/audit-legacy.py` 自动生成，基于源码文本引用扫描，不等同于运行时完全证明。

## 高概率可清理候选
- `archive/weixin_miniprogram_original`：源码中未发现对该历史微信小程序目录的引用，当前作为高概率可清理候选。
- `client/src/components/HelloWorld.vue`：未发现外部引用，属于演示/脚手架残留候选。

## 需要人工复核
- 目前未发现必须人工复核的模糊项；如后续接入运行时动态加载资源，仍建议删除前手工回归。

## 当前仍在使用或存在文本引用的文件
- `app/src/data/knowledge.js`：仍存在文本引用，暂不建议删除。
- `client/src/assets/vite.svg`：仍存在文本引用，暂不建议删除。
- `client/src/assets/vue.svg`：仍存在文本引用，暂不建议删除。

## 建议
- 第二轮清理前，先跑一次前台 `app` 构建、后台 `client` 构建和后端 smoke test。
- 对 `archive/` 这类目录建议整目录打包备份后再删除。