#!/usr/bin/env python3
"""
热点刀锋 反馈闭环工具
========================
用途：记录每篇文章的选题评分 vs 实际表现 → 校准评分模型

用法：
  python3 feedback-tracker.py init          # 创建空白追踪表
  python3 feedback-tracker.py add           # 交互式添加一条记录
  python3 feedback-tracker.py list          # 查看所有记录
  python3 feedback-tracker.py analyze       # 偏差分析 + 校准建议
  python3 feedback-tracker.py export        # 导出分析报告

数据文件：~/.hermes/hotspot-feedback.json
"""

import json, os, sys, datetime
from pathlib import Path

DATA_PATH = Path.home() / ".hermes" / "hotspot-feedback.json"

SCHEMA = {
    "date": "发布日期 (YYYY-MM-DD)",
    "title": "标题",
    "topic": "话题",
    "level": "选题级别 (热点/痛点/认知/微头条)",
    "predicted": {
        "wallet_distance": "钱包距离 1-10",
        "refutation_cost": "反驳成本 1-10",
        "object_anchor": "物件锚点 1-10",
        "toutiao_fit": "头条适配 1-10",
        "natural_split": "天然分裂 1-10",
        "total_score": "总分 (自动计算)",
    },
    "headline_version": "标题版本 (A/B/C)",
    "actual": {
        "ctr": "CTR (%)，留空=未知",
        "completion_rate": "完读率 (%)，留空=未知",
        "comments": "评论数",
        "likes": "点赞数",
        "shares": "转发数",
        "views": "阅读量，留空=未知",
    },
    "is_hit": "是否爆款 True/False (阅读>1万或评论>100)",
    "notes": "备注",
}


def compute_total(p):
    return round(
        p["wallet_distance"] * 0.35
        + p["refutation_cost"] * 0.25
        + p["object_anchor"] * 0.15
        + p["toutiao_fit"] * 0.15
        + p["natural_split"] * 0.10,
        1,
    )


def load():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def save(records):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init():
    if DATA_PATH.exists():
        print(f"追踪表已存在：{DATA_PATH}")
        return
    save([])
    print(f"已创建空白追踪表：{DATA_PATH}")


def cmd_add():
    records = load()
    r = {}
    print("=== 添加新记录 ===")
    r["date"] = input("日期 (YYYY-MM-DD, 留空=今天): ").strip() or datetime.date.today().isoformat()
    r["title"] = input("标题: ").strip()
    r["topic"] = input("话题: ").strip()
    r["level"] = input("选题级别 (热点/痛点/认知/微头条): ").strip()
    r["headline_version"] = input("标题版本 (A/B/C): ").strip().upper() or "A"

    print("\n--- 评分 (1-10) ---")
    p = {}
    p["wallet_distance"] = int(input("钱包距离: "))
    p["refutation_cost"] = int(input("反驳成本: "))
    p["object_anchor"] = int(input("物件锚点: "))
    p["toutiao_fit"] = int(input("头条适配: "))
    p["natural_split"] = int(input("天然分裂: "))
    p["total_score"] = compute_total(p)
    r["predicted"] = p
    print(f"总分: {p['total_score']}")

    print("\n--- 实际数据 (留空=未知) ---")
    a = {}
    ctr = input("CTR (%): ").strip()
    a["ctr"] = float(ctr) if ctr else None
    cr = input("完读率 (%): ").strip()
    a["completion_rate"] = float(cr) if cr else None
    comm = input("评论数: ").strip()
    a["comments"] = int(comm) if comm else None
    likes = input("点赞数: ").strip()
    a["likes"] = int(likes) if likes else None
    shares = input("转发数: ").strip()
    a["shares"] = int(shares) if shares else None
    views = input("阅读量: ").strip()
    a["views"] = int(views) if views else None
    r["actual"] = a

    # Auto-detect hit
    views_val = a.get("views") or 0
    comments_val = a.get("comments") or 0
    r["is_hit"] = views_val > 10000 or comments_val > 100
    r["notes"] = input("备注: ").strip()

    records.append(r)
    save(records)
    print(f"\n已保存。总记录数: {len(records)}")


def cmd_list():
    records = load()
    if not records:
        print("暂无记录。")
        return
    print(f"共 {len(records)} 条记录\n")
    for i, r in enumerate(records, 1):
        hit = "🔥" if r.get("is_hit") else " "
        p = r["predicted"]
        a = r["actual"]
        views = a.get("views", "?")
        comm = a.get("comments", "?")
        print(f"  {i:2d}. {hit} [{r['level']}] {r['title'][:50]}")
        print(f"      评分: {p['total_score']} | 阅读: {views} | 评论: {comm} | {r['date']}")


def bootstrap_ci(data, n_bootstrap=10000):
    """Simple bootstrap to estimate confidence interval for mean."""
    import random
    if not data or len(data) < 2:
        return None, None
    means = []
    for _ in range(n_bootstrap):
        sample = [random.choice(data) for _ in range(len(data))]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[250], means[9750]  # 95% CI


def cmd_analyze():
    records = load()
    if len(records) < 3:
        print(f"数据不足 (需要≥3条，当前{len(records)}条)。先用 add 添加数据。")
        return

    print("=" * 60)
    print("  偏差分析报告")
    print(f"  数据量: {len(records)} 条")
    print("=" * 60)

    # 1. 整体评分 vs 实际表现
    hits = [r for r in records if r.get("is_hit")]
    non_hits = [r for r in records if not r.get("is_hit")]
    hit_rate = len(hits) / len(records) * 100 if records else 0
    print(f"\n爆款率: {hit_rate:.0f}% ({len(hits)}/{len(records)})")

    # 2. 分维度偏差
    print("\n--- 分维度偏差分析 ---")
    dims = ["wallet_distance", "refutation_cost", "object_anchor", "toutiao_fit", "natural_split"]
    dim_labels = {
        "wallet_distance": "钱包距离",
        "refutation_cost": "反驳成本",
        "object_anchor": "物件锚点",
        "toutiao_fit": "头条适配",
        "natural_split": "天然分裂",
    }

    # Proxy for "actual performance": if we have CTR, use it; else use comments as proxy
    for dim in dims:
        # For hits vs non-hits, compare average scores
        hit_scores = [r["predicted"][dim] for r in hits]
        non_hit_scores = [r["predicted"][dim] for r in non_hits]
        if hit_scores and non_hit_scores:
            avg_hit = sum(hit_scores) / len(hit_scores)
            avg_non = sum(non_hit_scores) / len(non_hit_scores)
            diff = avg_hit - avg_non
            arrow = "↑" if diff > 0.5 else ("↓" if diff < -0.5 else "→")
            print(f"  {dim_labels[dim]:10s}: 爆款均分 {avg_hit:.1f} | 非爆款 {avg_non:.1f} | 差 {diff:+.1f} {arrow}")

    # 3. Weight calibration suggestion
    print("\n--- 权重校准建议 ---")
    # Calculate which dimension has the biggest gap between hit and non-hit
    weight_suggestions = {}
    for dim in dims:
        hit_scores = [r["predicted"][dim] for r in hits]
        non_hit_scores = [r["predicted"][dim] for r in non_hits]
        if hit_scores and non_hit_scores:
            avg_hit = sum(hit_scores) / len(hit_scores)
            avg_non = sum(non_hit_scores) / len(non_hit_scores)
            weight_suggestions[dim] = avg_hit - avg_non

    # Sort by predictive power
    sorted_dims = sorted(weight_suggestions.items(), key=lambda x: abs(x[1]), reverse=True)
    for dim, diff in sorted_dims:
        if abs(diff) > 1.0:
            direction = "提高" if diff > 0 else "降低"
            print(f"  建议{direction}「{dim_labels[dim]}」权重 (差{diff:+.1f})")
        else:
            print(f"  「{dim_labels[dim]}」权重合理 (差{diff:+.1f})")

    # 4. 标题版本分析
    if any(r.get("headline_version") for r in records):
        versions = {}
        for r in records:
            v = r.get("headline_version", "A")
            if v not in versions:
                versions[v] = {"count": 0, "hits": 0, "total_ctr": 0, "ctr_count": 0}
            versions[v]["count"] += 1
            if r.get("is_hit"):
                versions[v]["hits"] += 1
            ctr = r["actual"].get("ctr")
            if ctr is not None:
                versions[v]["total_ctr"] += ctr
                versions[v]["ctr_count"] += 1
        print("\n--- 标题版本分析 ---")
        for v in sorted(versions.keys()):
            d = versions[v]
            hr = d["hits"] / d["count"] * 100 if d["count"] else 0
            avg_ctr = d["total_ctr"] / d["ctr_count"] if d["ctr_count"] else None
            ctr_str = f" | 均CTR {avg_ctr:.1f}%" if avg_ctr else ""
            print(f"  版本 {v}: {d['count']}篇 | 爆款率 {hr:.0f}%{ctr_str}")

    # 5. 选题级别分析
    levels = {}
    for r in records:
        lv = r.get("level", "?")
        if lv not in levels:
            levels[lv] = {"count": 0, "hits": 0}
        levels[lv]["count"] += 1
        if r.get("is_hit"):
            levels[lv]["hits"] += 1
    print("\n--- 选题级别表现 ---")
    for lv in sorted(levels.keys()):
        d = levels[lv]
        hr = d["hits"] / d["count"] * 100 if d["count"] else 0
        print(f"  {lv}: {d['count']}篇 | 爆款率 {hr:.0f}%")

    # 6. 结论
    print("\n--- 结论 ---")
    if len(records) >= 10:
        print("  数据量充足，建议根据偏差分析调整权重。")
        for dim, diff in sorted_dims[:2]:
            if abs(diff) > 1.0:
                direction = "提高" if diff > 0 else "降低"
                print(f"  优先{direction}「{dim_labels[dim]}」权重")
    else:
        print(f"  数据量不足 (<10条)，继续积累。当前 {len(records)} 条，再记 {10 - len(records)} 条后分析更可靠。")

    print("\n" + "=" * 60)


def cmd_export():
    records = load()
    if not records:
        print("暂无数据。")
        return
    lines = []
    lines.append("日期,标题,话题,级别,总分,钱包距离,反驳成本,物件锚点,头条适配,天然分裂,标题版本,CTR,完读率,评论,点赞,阅读,爆款")
    for r in records:
        p = r["predicted"]
        a = r["actual"]
        lines.append(
            ",".join(
                str(v)
                for v in [
                    r["date"],
                    r["title"],
                    r["topic"],
                    r["level"],
                    p["total_score"],
                    p["wallet_distance"],
                    p["refutation_cost"],
                    p["object_anchor"],
                    p["toutiao_fit"],
                    p["natural_split"],
                    r.get("headline_version", "?"),
                    a.get("ctr") or "",
                    a.get("completion_rate") or "",
                    a.get("comments") or "",
                    a.get("likes") or "",
                    a.get("views") or "",
                    "是" if r.get("is_hit") else "否",
                ]
            )
        )
    out = Path.home() / ".hermes" / "hotspot-feedback-export.csv"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"已导出 CSV: {out}")
    print(f"共 {len(records)} 条记录，可用 Excel/Google Sheets 打开分析。")


def main():
    if len(sys.argv) < 2:
        print("用法: python3 feedback-tracker.py <init|add|list|analyze|export>")
        sys.exit(1)

    cmd = sys.argv[1]
    dispatcher = {
        "init": cmd_init,
        "add": cmd_add,
        "list": cmd_list,
        "analyze": cmd_analyze,
        "export": cmd_export,
    }
    fn = dispatcher.get(cmd)
    if not fn:
        print(f"未知命令: {cmd}")
        sys.exit(1)
    fn()


if __name__ == "__main__":
    main()