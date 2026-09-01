#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 results/ 下的 JSON 汇总为 report.md"""
import json, os, re, glob

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "results")
OUT = os.path.join(BASE, "report.md")

# outline.yaml 中的章节顺序（文件名 -> 章节名）
ORDER = [
    ("contract_template", "契约式派单模板"),
    ("acceptance_gate", "派单验收门禁"),
    ("agents_md", "AGENTS.md 写法与长度控制"),
    ("goal_mode", "Goal Mode 长任务自治"),
    ("config_toml", "config.toml 核心配置"),
    ("permissions", "权限新体系"),
    ("hooks", "Hooks 强制验证"),
    ("verification_loop", "验证循环设计"),
    ("context_management", "上下文与会话治理"),
    ("cost_control", "成本与额度可视化"),
    ("parallel_agents", "并行与自定义 agent 分档"),
    ("model_deprecation", "模型弃用与迁移时点"),
    ("china_adaptation", "国内环境适配"),
    ("task_templates", "任务模板库与 Skills 打包"),
    ("troubleshooting", "故障排查"),
]

# fields.yaml 中定义的字段顺序
FIELD_ORDER = [
    "核心做法",
    "可直接复制的模板命令配置",
    "关键参数",
    "常见坑",
    "降级与回退路径",
    "版本与生效时间",
    "可自动化程度",
    "优先级",
    "对一人公司的适用性",
    "信息来源",
]

SUMMARY_FIELD = "对一人公司的适用性"
INTERNAL = {"条目", "uncertain", "_source_file", "_file"}


def load_fields():
    """尝试从 fields.yaml 读取字段顺序，失败则用内置列表"""
    path = os.path.join(BASE, "fields.yaml")
    if not os.path.exists(path):
        return FIELD_ORDER
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        names = [fd["name"] for fd in data.get("fields", [])]
        return names or FIELD_ORDER
    except Exception:
        return FIELD_ORDER


def anchor(name):
    """生成锚点：保留中英文数字，空格转连字符"""
    s = name.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s)
    return s.strip("-")


def is_uncertain(value):
    if value is None:
        return True
    if isinstance(value, str):
        return "[不确定]" in value or value.strip() == ""
    return False


def fmt(value, indent=0):
    """把任意 JSON 值格式化为 markdown 文本"""
    pad = "  " * indent
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(x, (str, int, float)) for x in value):
            items = [str(x).strip() for x in value]
            joined = "；".join(items)
            if len(joined) <= 120:
                return joined
            return "\n".join(f"{pad}- {x}" for x in items)
        parts = []
        for x in value:
            if isinstance(x, dict):
                line = " | ".join(f"{k}: {fmt(v)}" for k, v in x.items())
                parts.append(f"{pad}- {line}")
            else:
                parts.append(f"{pad}- {fmt(x, indent)}")
        return "\n".join(parts)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            sub = fmt(v, indent + 1)
            if "\n" in sub:
                parts.append(f"{pad}- **{k}**\n{sub}")
            else:
                parts.append(f"{pad}- **{k}**：{sub}")
        return "\n".join(parts)
    return str(value)


def main():
    fields = load_fields()
    sections = []
    toc = []

    for idx, (slug, title) in enumerate(ORDER, 1):
        path = os.path.join(RESULTS, slug + ".json")
        if not os.path.exists(path):
            print(f"[跳过] 缺少文件: {slug}.json")
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        uncertain_fields = set(data.get("uncertain") or [])
        item_name = data.get("条目") or title

        # 目录摘要
        summary = data.get(SUMMARY_FIELD, "")
        if isinstance(summary, (list, dict)):
            summary = fmt(summary)
        if isinstance(summary, str):
            summary = summary.replace("\n", " ").strip()
            if len(summary) > 60:
                summary = summary[:60] + "…"
        toc.append(f"{idx}. [{item_name}](#{anchor(item_name)}) — {summary}")

        # 正文
        blocks = [f"## {idx}. {item_name}", ""]
        ordered = [f for f in fields if f in data] + \
                  [k for k in data if k not in fields and k not in INTERNAL]

        for field in ordered:
            if field in INTERNAL:
                continue
            if field in uncertain_fields:
                continue
            raw = data.get(field)
            if is_uncertain(raw):
                continue
            text = fmt(raw)
            if not text.strip():
                continue
            blocks.append(f"### {field}")
            blocks.append("")
            blocks.append(text)
            blocks.append("")

        # 不确定项清单
        if uncertain_fields:
            blocks.append("### 待核实")
            blocks.append("")
            for u in sorted(uncertain_fields):
                blocks.append(f"- {u}")
            blocks.append("")

        sections.append("\n".join(blocks))

    header = [
        "# Codex 工作流落地手册",
        "",
        "> 面向一人公司的可操作手册：契约式派单、AGENTS.md 写法、验证循环、省钱配置",
        ">",
        "> 调研时间：2026-08-31 ｜ 检索范围：2026-03 至今 ｜ 并行 5 组 agent，覆盖 15 个章节",
        ">",
        "> 说明：字段值若标注 `[不确定]` 或列入「待核实」，表示多个来源冲突或未找到官方依据，已跳过正文展示。",
        "",
        "## 目录",
        "",
    ]
    doc = header + toc + ["", "---", ""] + sections
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(doc))

    print(f"已生成: {OUT}")
    print(f"章节数: {len(sections)} / {len(ORDER)}")


if __name__ == "__main__":
    main()
