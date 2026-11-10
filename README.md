# 检索评测系统

对一份公开产品说明书做离线检索评测：解析 → 文本质量门禁 → 切分 →
token 化/向量化对照 → 召回 → 证据支持校验 → 固定集报告。

## 快速开始
uv sync
uv run python experiments/ch03_loader_ab.py
uv run python experiments/ch04_tokenizer_ab.py

## 语料
data/raw/ 下为公开产品说明书，仅用于检索评测练习，非客户项目。

## 结构
experiments/  可复现的对照实验
logs/         实验输出（由脚本生成）
data/raw/     原始语料
DESIGN.md     链路与已知边界

## 评测口径
见各实验日志。ch03/ch04 为桩级行为对照，非系统级指标；
固定评测集与 Recall@K / 拒答率在 evaluation 阶段补齐。

## 已知边界
图示页不做图像理解；单版本知识库；拒答阈值来自本机评测集。

部分章节划分参考开源项目 rag-from-zero（MIT）。本仓库为独立实现与评测。