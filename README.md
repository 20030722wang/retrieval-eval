# 检索评测系统

对一份公开产品说明书做离线检索评测：解析 → 文本质量门禁 → 切分 →
token 化 / 语义向量对照 → 召回 → 证据支持校验 → 固定集报告。

## 快速开始

uv sync
uv run python experiments/ch03_loader_ab.py
uv run python experiments/ch04_tokenizer_ab.py

## 语料与边界

`data/raw/` 为公开产品说明书（24 页），仅用于检索评测练习，非客户项目。
答案合同与拒答策略见 `PROBLEM_BOUNDARY.md`，链路与断点见 `DESIGN.md`。

## 结构

experiments/  可复现的对照实验
logs/         实验输出（由脚本生成，非手写）
data/raw/     原始语料

## 评测口径

`ch03` / `ch04` 为桩级行为对照与 token 化对照，非系统级指标；
固定评测集、Recall@K 与拒答率在 evaluation 阶段补齐。
评测按 chunk 判定，不按页判定。

## 已知边界

图示页不做图像理解；单版本知识库，无灰度与回滚；
拒答阈值来自本机评测集，不是生产阈值；低文本页标记为不可答。

## 出处

章节划分参考 rag-from-zero（MIT, https://github.com/MisterBooo/rag-from-zero）。
本仓库差异：自有语料评测集、解析层文本质量门禁、
印刷 / 物理页码归一化、换解析器与换 tokenizer 的证伪对照。
其余为独立实现与评测。
