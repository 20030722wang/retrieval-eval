# -*- coding: utf-8 -*-
"""基线：检索命中但未做证据支持校验。"""
from pathlib import Path

DOCS = {
    "gap": "空调器与可燃表面间的最小间隙为1.5米。",
    "warranty": "本公司产品实行三包,详情见《包修卡》。",
    "remote": "无线遥控型窗式空调器、控制器根据室温变化微电脑自动选择运行状态。",
}
QUERIES = [
    ("空调器与可燃表面间的最小间隙是多少?", "gap"),
    ("保修期是几年?", "warranty"),
    ("能用手机App或WiFi控制吗?", None),
    ("我家15平米该选哪个型号?", None),
]
lines = []
for q, key in QUERIES:
    if key is None:
        lines.append(q + " -> 【没检索到资料】模型只能凭记忆瞎猜")
    else:
        lines.append(q + " -> 【检索到资料,照着答】依据:" + DOCS[key])
lines.append(">> 样本：检索命中但证据不支持")
out = Path("logs/ch01_no_guard.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")