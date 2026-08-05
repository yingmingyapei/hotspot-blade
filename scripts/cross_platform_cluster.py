#!/usr/bin/env python3
"""
跨平台共振检测器
=================
用途：检测同一话题在多个平台的出现情况，输出共振评分
用法：
  python3 cross_platform_cluster.py --input /tmp/hotlist_data.json
  python3 cross_platform_cluster.py --input /tmp/hotlist_data.json --output /tmp/resonance.json

输出：
  - clusters: 按话题聚合的集群数组
    - title: 集群标题
    - platform_count: 命中平台数
    - items: 各平台具体条目
    - total_engagement: 总互动量（归一化）
  - resonance_map: 每条话题的共振评分字典

共振加成规则：
  - 3+ 平台同时出现同一话题 → wallet +2.0, refute +1.0
  - 2 平台同时出现 → wallet +1.0
  - 1 平台 → 不加成
"""
import json, sys, re
from pathlib import Path
from collections import defaultdict


def load_hotlist(path):
    """加载热榜JSON数据"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_keywords(title, max_len=4):
    """提取标题关键词片段（排除停用词后的短词）"""
    stop_words = {"的", "了", "是", "在", "有", "和", "与", "及", "或",
                  "吗", "啊", "呢", "吧", "哦", "嗯", "哈",
                  "我", "你", "他", "她", "它", "我们", "你们", "他们",
                  "这", "那", "哪", "什么", "怎么", "为什么",
                  "不", "没", "别", "也", "都", "还", "就", "又", "再",
                  "个", "只", "条", "块", "张", "家", "种", "次",
                  "了", "着", "过", "被", "让", "把", "将", "从", "对",
                  "到", "去", "来", "上", "下", "年", "月", "日",
                  "https", "http", "com", "www", "amp", "gt", "lt"}
    # 分句 + 去停用词 + 取2-4字词
    words = re.findall(r'[\u4e00-\u9fff]{2,8}', title)
    keywords = [w for w in words if w not in stop_words and len(w) >= 2]
    return keywords[:max_len]


def normalize_engagement(item, platform):
    """归一化互动量到0-100分"""
    raw = 0
    if platform == "zhihu":
        raw = max(
            int(item.get("heat", 0) or 0),
            int(item.get("answer_count", 0) or 0) * 10,
            int(item.get("follower_count", 0) or 0) * 5,
        )
    elif platform == "weibo":
        raw = int(item.get("heat", 0) or 0)
    elif platform == "bilibili":
        raw = max(
            int(item.get("view", 0) or 0),
            int(item.get("like", 0) or 0) * 10,
            int(item.get("reply", 0) or 0) * 50,
        )
    elif platform == "36kr":
        raw = max(
            int(item.get("read", 0) or 0),
            int(item.get("like", 0) or 0) * 50,
        )
    elif platform == "baidu":
        raw = int(item.get("heat", 0) or 0)
    else:
        raw = 0

    # 对数归一化: log(1+x) / log(1+max) * 100
    # 参考值：微博热搜通常几十万到几百万
    ref_max = 10000000  # 1千万参考
    if raw <= 0:
        return 0
    score = min(100, round(math.log(1 + raw) / math.log(1 + ref_max) * 100, 1))
    return score


import math


def build_clusters(data):
    """构建跨平台话题集群"""
    # 1. 提取所有平台的条目
    all_items = []  # (title, keywords, platform, item, engagement)
    for platform, result in data.items():
        if not isinstance(result, dict) or result.get("error"):
            continue
        items = result.get("items", [])
        name_map = {
            "zhihu": "知乎", "weibo": "微博", "bilibili": "B站",
            "36kr": "36氪", "baidu": "百度"
        }
        platform_name = name_map.get(platform, platform)
        for item in items:
            title = item.get("title", "")
            if not title:
                continue
            keywords = extract_keywords(title)
            eng = normalize_engagement(item, platform)
            all_items.append({
                "title": title,
                "keywords": set(keywords),
                "platform": platform_name,
                "platform_key": platform,
                "raw_item": item,
                "engagement": eng,
            })

    # 2. 基于关键词交集构建集群
    clusters = []
    used = set()

    # 按互动量降序排列，优先处理高互动话题
    all_items.sort(key=lambda x: x["engagement"], reverse=True)

    for i, item_a in enumerate(all_items):
        if i in used:
            continue
        cluster_items = [item_a]
        used.add(i)

        for j, item_b in enumerate(all_items):
            if j in used:
                continue
            # 检查关键词重叠度
            overlap = item_a["keywords"] & item_b["keywords"]
            # 至少2个关键词重叠，或标题包含对方的核心词
            a_title = item_a["title"]
            b_title = item_b["title"]
            title_overlap = (
                any(kw in a_title for kw in list(item_b["keywords"])[:2])
                or any(kw in b_title for kw in list(item_a["keywords"])[:2])
            )
            if len(overlap) >= 2 or title_overlap:
                cluster_items.append(item_b)
                used.add(j)

        if len(cluster_items) > 1:
            # 只有跨平台才形成集群
            platforms = set(it["platform"] for it in cluster_items)
            if len(platforms) >= 2:
                # 找最佳标题（取最短的那条，通常是核心话题）
                best_item = min(cluster_items, key=lambda x: len(x["title"]))
                total_eng = sum(it["engagement"] for it in cluster_items)

                clusters.append({
                    "title": best_item["title"],
                    "platform_count": len(platforms),
                    "platforms": sorted(platforms),
                    "item_count": len(cluster_items),
                    "total_engagement": round(total_eng, 1),
                    "items": [
                        {
                            "title": it["title"],
                            "platform": it["platform"],
                            "engagement": it["engagement"],
                        }
                        for it in sorted(cluster_items, key=lambda x: x["engagement"], reverse=True)
                    ],
                })

    # 按平台数 + 总互动量排序
    clusters.sort(key=lambda x: (x["platform_count"], x["total_engagement"]), reverse=True)

    return clusters


def build_resonance_map(clusters, all_items):
    """为每条话题构建共振评分表"""
    # 为每个独立条目打上共振分
    resonance_map = {}

    for item in all_items:
        title = item["title"]
        resonance_map[title] = {
            "platform": item["platform"],
            "engagement": item["engagement"],
            "resonance_boost": 0,
            "resonance_note": "单平台，无共振",
        }

    # 从集群更新共振分
    for cluster in clusters:
        boost = 2.0 if cluster["platform_count"] >= 3 else 1.0
        note = f"{cluster['platform_count']}平台共振({cluster['platform_count']}平台)"
        for citem in cluster["items"]:
            if citem["title"] in resonance_map:
                resonance_map[citem["title"]]["resonance_boost"] = boost
                resonance_map[citem["title"]]["resonance_note"] = note
                resonance_map[citem["title"]]["cluster_title"] = cluster["title"]

    return resonance_map


def main():
    import argparse
    parser = argparse.ArgumentParser(description="跨平台共振检测器")
    parser.add_argument("--input", "-i", default="/tmp/hotlist_data.json",
                        help="热榜JSON数据文件")
    parser.add_argument("--output", "-o", default="",
                        help="输出JSON路径（默认stdout）")
    args = parser.parse_args()

    data = load_hotlist(args.input)
    clusters = build_clusters(data)

    # 收集所有条目用于共振映射
    all_items = []
    for platform, result in data.items():
        if not isinstance(result, dict) or result.get("error"):
            continue
        for item in result.get("items", []):
            title = item.get("title", "")
            if not title:
                continue
            all_items.append({
                "title": title,
                "platform": platform,
                "engagement": normalize_engagement(item, platform),
                "raw_item": item,
            })

    resonance_map = build_resonance_map(clusters, all_items)

    output = {
        "total_items": len(all_items),
        "total_clusters": len(clusters),
        "clusters": clusters,
        "resonance_map": resonance_map,
    }

    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"✅ 共振检测完成: {len(clusters)} 个集群, {len(all_items)} 条话题")
        print(f"   {len([c for c in clusters if c['platform_count'] >= 3])} 个3+平台共振集群")
        print(f"   已保存: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()