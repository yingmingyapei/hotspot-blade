#!/usr/bin/env python3
"""
generate_chart.py — 热点刀锋算账对比图生成器

从微头条正文中提取数字对比 → 生成 3:2 高清社交媒体图
解决 SKILL 规范 HB-04（每张图必带具体数字）+ HB-05（不得编造数据）

使用场景：
1. agent 写完微头条后 -> 提取正文数字对 -> 调用此脚本
2. 发布前检查 -> 算哪张图最能点击 -> 输出为发布封面
3. 多平台适配 -> 头条封面 (3:2) / 小红书封面 (3:4) 一键切换

CLI 调用：
    python3 generate_chart.py --json '{"title":"自研vs蒸馏成本对比","labels":["自研GPU","蒸馏GPT-4"],"values":[10000,100]}'

Python API:
    from generate_chart import build_chart
    build_chart({"title": "...", "labels": [...], "values": [...]})
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# CJK 字体配置（WSL 已验证有文泉驿）
import matplotlib
matplotlib.use("Agg")  # 无显示环境
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False  # 负号正常显示


def build_chart(
    data: dict,
    output_path: str = "/tmp/hotspot_chart.png",
    aspect: str = "3:2",  # "3:2" 头条 / "3:4" 小红书
) -> str:
    """
    data = {
        "title": "标题（会渲染在图上）",
        "labels": ["类别A", "类别B", ...],
        "values": [数字A, 数字B, ...],
        # optional:
        "unit": "元",       # 数值单位后缀，默认无
        "currency": False,  # 是货币就显示千分位
    }
    """
    labels = data["labels"]
    values = data["values"]
    title = data.get("title", "算账对比")
    unit = data.get("unit", "")
    currency = data.get("currency", False)

    # 画幅
    if aspect == "3:2":
        figsize = (6, 4)
    elif aspect == "3:4":
        figsize = (4.5, 6)
    else:
        figsize = (6, 4)

    # 暗色高对比度（社交极简）
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#121212")

    # 配色：青/红/黄循环（头条爆款配色）
    palette = ["#00E5FF", "#FF1744", "#FFEA00", "#76FF03", "#FF9100"]
    colors = palette[: len(values)]

    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="none")

    # 去除多余边框
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")

    # 标题
    ax.set_title(title, fontsize=14, pad=18, fontweight="bold", color="#FFFFFF")

    # Y 轴格式化
    if currency:
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f"{x:,.0f}")
        )
    max_v = max(values)

    # 数值标注（柱子顶部）
    for bar, v in zip(bars, values):
        height = bar.get_height()
        if currency:
            label = f"{v:,.0f}{unit}"
        else:
            label = f"{v}{unit}"
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + max_v * 0.02,
            label,
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#FFFFFF",
        )

    # Y 轴留顶部空间
    ax.set_ylim(0, max_v * 1.15)
    ax.tick_params(colors="#AAAAAA", labelsize=10)

    plt.tight_layout()
    plt.savefig(output_path, facecolor="#121212", dpi=200)
    plt.close(fig)
    return output_path


def extract_numbers_from_text(text: str) -> dict:
    """
    从微头条正文提取数字对（用于自动生成图表）。
    返回 {"title": ..., "labels": [...], "values": [...]}，不成功返回 None。
    """
    import re

    # 匹配 "X 元/万/亿/美金/美元" 或 "约 X 元"
    pattern = r"([\u4e00-\u9fa5\w]{2,20}?)[^\d]{0,12}?(\d+(?:\.\d+)?)\s*(万|亿|元|美金|美元|元/斤|度/小时|度电|%|‰|颗|台|人)"
    matches = re.findall(pattern, text)
    if len(matches) < 2:
        return None

    # 统一换算成数字
    def parse(val_str: str, unit_str: str) -> float:
        v = float(val_str)
        if "万" in unit_str:
            v *= 10000
        elif "亿" in unit_str:
            v *= 100000000
        return v

    labels = [m[0].strip("约大约一共") for m in matches[:5]]
    values = [parse(m[1], m[2]) for m in matches[:5]]

    return {
        "title": "正文数字对比",
        "labels": labels,
        "values": values,
        "currency": True,
    }


def main():
    parser = argparse.ArgumentParser(description="热点刀锋封面图生成器")
    parser.add_argument("--json", help='JSON 数据: {"title":...,"labels":[...],"values":[...]}')
    parser.add_argument("--text", help="微头条正文文本，自动提取数字")
    parser.add_argument("--output", default="/tmp/hotspot_chart.png", help="输出路径")
    parser.add_argument("--aspect", choices=["3:2", "3:4"], default="3:2", help="画幅比例")
    args = parser.parse_args()

    if args.json:
        data = json.loads(args.json)
    elif args.text:
        data = extract_numbers_from_text(args.text)
        if not data:
            print("[!] 未能从正文提取足够数字，请用 --json 手动传入")
            sys.exit(1)
    else:
        # 演示模式
        data = {
            "title": "DeepSeek vs OpenAI 调用成本",
            "labels": ["DeepSeek", "OpenAI"],
            "values": [14, 270],
            "currency": True,
        }

    out = build_chart(data, args.output, args.aspect)
    print(f"[+] 图已生成：{out}")


if __name__ == "__main__":
    main()
