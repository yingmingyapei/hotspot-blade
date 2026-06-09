#!/usr/bin/env python3
"""
hotlist_to_excel.py — 将热榜数据保存为Excel文件
用法：python3.10 hotlist_to_excel.py [--input /tmp/hotlist_data.json] [--output /path/to/file.xlsx]
"""

import json
import sys
import os
from datetime import datetime

try:
    import openpyxl
except ImportError:
    print("错误: openpyxl 未安装，请先 pip install openpyxl", file=sys.stderr)
    sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="/tmp/hotlist_data.json", help="热榜JSON数据文件")
    parser.add_argument("--output", "-o", default="", help="输出Excel路径（默认保存到Windows桌面）")
    args = parser.parse_args()

    # 读取数据
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = f"/mnt/c/Users/yingm/OneDrive/Desktop/热榜数据_{today}.xlsx"

    # 创建Excel
    wb = openpyxl.Workbook()
    # 删除默认sheet
    wb.remove(wb.active)

    platform_config = {
        "zhihu": {
            "name": "知乎热榜",
            "columns": ["排名", "标题", "热度", "回答数", "关注数", "摘要", "链接"],
            "extract": lambda item: [item.get("rank"), item.get("title"), item.get("heat"), item.get("answer_count"), item.get("follower_count"), item.get("excerpt"), item.get("url")]
        },
        "weibo": {
            "name": "微博热搜",
            "columns": ["排名", "标题", "热度", "标签", "链接"],
            "extract": lambda item: [item.get("rank"), item.get("title"), item.get("heat"), item.get("label"), item.get("url")]
        },
        "bilibili": {
            "name": "B站热门",
            "columns": ["排名", "标题", "UP主", "分区", "播放量", "点赞", "评论", "链接"],
            "extract": lambda item: [item.get("rank"), item.get("title"), item.get("author"), item.get("tname"), item.get("view"), item.get("like"), item.get("reply"), item.get("url")]
        },
        "36kr": {
            "name": "36氪热榜",
            "columns": ["排名", "标题", "作者", "阅读量", "点赞", "收藏", "评论", "链接"],
            "extract": lambda item: [item.get("rank"), item.get("title"), item.get("author"), item.get("read"), item.get("like"), item.get("collect"), item.get("comment"), item.get("url")]
        },
        "baidu": {
            "name": "百度热搜",
            "columns": ["排名", "标题", "热度", "描述", "链接"],
            "extract": lambda item: [item.get("rank"), item.get("title"), item.get("heat"), item.get("desc"), item.get("url")]
        },
    }

    for platform, config in platform_config.items():
        if platform not in data:
            continue
        result = data[platform]
        if result.get("error"):
            print(f"⚠️ {config['name']}有错误: {result['error']}", file=sys.stderr)
            continue

        ws = wb.create_sheet(config["name"])
        ws.append(config["columns"])

        for item in result.get("items", []):
            ws.append(config["extract"](item))

        # 设置列宽
        for i, col in enumerate(config["columns"]):
            ws.column_dimensions[chr(65 + i)].width = max(8, min(50, len(col) * 4 + 4))

    # 保存
    wb.save(output_path)
    total = sum(data.get(p, {}).get("count", 0) for p in platform_config if p in data)
    print(f"✅ 已保存: {output_path}")
    print(f"   {len(wb.sheetnames)}个平台, 共{total}条数据")
    return output_path

if __name__ == "__main__":
    main()
