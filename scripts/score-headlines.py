#!/usr/bin/env python3
"""
热点刀锋 标题暴力预测评分器
============================
用途：发布前对3个备选标题做心理模型评分，选分最高的发
用法：
  python3 score-headlines.py "标题1" "标题2" "标题3"
  python3 score-headlines.py --topic "选题话题" "标题1" "标题2" "标题3"

评分维度（各25分，满分100）：
  - 损失厌恶: 标题是否暗示"不点开就亏了"
  - 锚定效应: 首句数字/概念的冲击力
  - 模仿欲望: 读者是否觉得"别人都在看"
  - 认知冲突: 是否挑战"大家都知道"的认知
"""

import sys, re, math

# === 损失厌恶信号 ===
LOSS_AVERSION_PATTERNS = [
    (r"再不|错过|最后|晚了|来不及", 5, "紧迫感(再不/错过/最后)"),
    (r"亏|赔|损失|白花|白费|浪费", 5, "直接损失(亏/赔/损失)"),
    (r"跌|降|缩水|贬值|蒸发", 5, "资产缩水(跌/降/缩水)"),
    (r"涨价|涨了|变贵|要涨", 5, "成本上升(涨价)"),
    (r"取消|停止|关闭|无法|不能", 4, "失去机会(取消/停止)"),
    (r"警惕|注意|当心|小心", 3, "警告(警惕/当心)"),
    (r"别[再]?[买做去信]", 4, "制止(别买/别做)"),
    (r"后悔|晚了|来不及", 4, "后悔预期"),
    (r"扣|收|交|付|掏", 3, "支出动作(扣/收/付)"),
]

# === 锚定效应信号 ===
ANCHORING_PATTERNS = [
    (r"\d{4,}[万亿亿千万]?", 5, "大数字锚(万级以上)"),
    (r"\d{1,3}[万亿亿]", 5, "万亿级锚"),
    (r"\d{1,3}[百千万]", 4, "千/百万级锚"),
    (r"\d+[%％倍成]", 4, "百分比/倍数锚"),
    (r"\d+[岁年日天月]", 3, "时间锚(岁/年/天)"),
    (r"\d+[块元]", 4, "价格锚(块/元)"),
    (r"\d+[个只家次]", 2, "普通计数锚"),
    (r"从.*到|涨了.*倍|翻了.*倍", 4, "对比锚(从A到B)"),
    (r"最高|最低|首个|唯一|第一|最[大多少]", 3, "极端锚(最高/最低/第一)"),
]

# === 模仿欲望信号 ===
MIMETIC_DESIRE_PATTERNS = [
    (r"都[在去]|都在|全民|全网|集体", 5, "社会认同(都在/全民)"),
    (r"为什么|怎么|原因|真相|背后", 4, "信息缺口(为什么/真相)"),
    (r"曝光|流出|泄露|内幕", 5, "独家信息(曝光/内幕)"),
    (r"疯抢|排队|抢购|断货", 5, "从众行为(疯抢/排队)"),
    (r"热议|争议|吵翻|炸锅|刷屏", 5, "社会热议(热议/刷屏)"),
    (r"关注|围观|紧盯|注意", 3, "关注信号(关注/紧盯)"),
    (r"突然|一夜|一觉醒来|瞬间", 4, "突发性(突然/一夜)"),
    (r"你[还]?[知不知道]?", 3, "直接对话(你)"),
    (r"99%|大多数人|很少有人", 4, "信息差(99%/大多数人)"),
]

# === 认知冲突信号 ===
COGNITIVE_CONFLICT_PATTERNS = [
    (r"其实是|并不是|你以为|想错了|真相是", 5, "认知反转(其实是/并不是)"),
    (r"骗局|陷阱|套路|猫腻|内幕", 5, "揭露(骗局/陷阱)"),
    (r"颠覆|打破|推翻|逆袭|反常识", 5, "颠覆(颠覆/打破)"),
    (r"别再|不要[再]?|错了|误区", 4, "纠正(别再/错了)"),
    (r"秘密|潜规则|潜台词|规则", 4, "隐藏规则(秘密/潜规则)"),
    (r"同样|一样|却|反而|竟然", 4, "反差(同样/却/反而)"),
    (r"对比|vs|VS|比一比|差在哪", 4, "对比结构(对比/vs)"),
    (r"你不知道|没人告诉你|没人说", 5, "不对称信息"),
    (r"假的|骗人|忽悠|割韭菜", 5, "揭穿(假的/骗人)"),
]


def score_headline(title, topic=""):
    title_lower = title.lower()
    scores = {"loss_aversion": 0, "anchoring": 0, "mimetic_desire": 0, "cognitive_conflict": 0}
    details = {k: [] for k in scores}

    # 损失厌恶
    for pat, pts, label in LOSS_AVERSION_PATTERNS:
        if re.search(pat, title):
            scores["loss_aversion"] += pts
            details["loss_aversion"].append(label)

    # 锚定效应
    for pat, pts, label in ANCHORING_PATTERNS:
        if re.search(pat, title):
            scores["anchoring"] += pts
            details["anchoring"].append(label)

    # 模仿欲望
    for pat, pts, label in MIMETIC_DESIRE_PATTERNS:
        if re.search(pat, title):
            scores["mimetic_desire"] += pts
            details["mimetic_desire"].append(label)

    # 认知冲突
    for pat, pts, label in COGNITIVE_CONFLICT_PATTERNS:
        if re.search(pat, title):
            scores["cognitive_conflict"] += pts
            details["cognitive_conflict"].append(label)

    # Seasoning: 长度惩罚
    length = len(title)
    if length < 10:
        scores["anchoring"] -= 3  # 太短，信息量不够
    if length > 40:
        for k in scores:
            scores[k] = max(0, scores[k] - 2)  # 太长，CTR下降

    # Seasoning: 话题匹配
    if topic:
        topic_words = set(topic.lower().split())
        title_words = set(title_lower.split())
        overlap = len(topic_words & title_words)
        if overlap == 0:
            pass  # 标题与话题无关是正常现象（悬念型标题）
        if overlap >= 2:
            scores["mimetic_desire"] += 2  # 话题词出现，热度借势

    # Cap each dimension at 25
    for k in scores:
        scores[k] = min(25, max(0, scores[k]))

    total = sum(scores.values())
    return total, scores, details


def get_grade(total):
    if total >= 85:
        return "S", "🔥 爆款潜力"
    elif total >= 70:
        return "A", "✅ 优质"
    elif total >= 55:
        return "B", "⚠️ 可发"
    elif total >= 40:
        return "C", "⚠️ 需优化"
    else:
        return "D", "❌ 重写"


def analyze_weakness(scores):
    """Find the weakest dimension for improvement suggestion."""
    dim_names = {
        "loss_aversion": "损失厌恶",
        "anchoring": "锚定效应",
        "mimetic_desire": "模仿欲望",
        "cognitive_conflict": "认知冲突",
    }
    weakest = min(scores, key=scores.get)
    weakest_val = scores[weakest]
    max_val = max(scores.values())
    if weakest_val < 10 and max_val > 20:
        return f"弱项: {dim_names[weakest]} ({weakest_val}/25)，可以加强"
    return None


def main():
    args = sys.argv[1:]

    topic = ""
    if "--topic" in args:
        tidx = args.index("--topic")
        if tidx + 1 < len(args):
            topic = args[tidx + 1]
            args = args[:tidx] + args[tidx + 2:]

    if len(args) < 1:
        print("用法: python3 score-headlines.py \"标题1\" \"标题2\" \"标题3\"")
        sys.exit(1)

    titles = args

    print(f"标题评分报告" + (f" (话题: {topic})" if topic else ""))
    print("=" * 70)
    print()

    ranked = []
    for title in titles:
        total, scores, details = score_headline(title, topic)
        grade, label = get_grade(total)
        ranked.append((total, grade, label, title, scores, details))
        weakness = analyze_weakness(scores)

        print(f"  [{grade}] {label}")
        print(f"  标题: {title}")
        print(f"  总分: {total}/100")
        dims = {
            "loss_aversion": "损失厌恶",
            "anchoring": "锚定效应",
            "mimetic_desire": "模仿欲望",
            "cognitive_conflict": "认知冲突",
        }
        for k, name in dims.items():
            bar = "█" * (scores[k] // 2) + "░" * (12 - scores[k] // 2)
            triggers = ", ".join(details[k][:3]) if details[k] else "无"
            print(f"    {name:8s} {scores[k]:2d}/25 {bar}  {triggers}")
        if weakness:
            print(f"    💡 {weakness}")
        print()

    # Rank
    ranked.sort(key=lambda x: x[0], reverse=True)
    print("=" * 70)
    print("  推荐排序:")
    for i, (total, grade, label, title, scores, details) in enumerate(ranked, 1):
        print(f"  {i}. [{grade}] {total}分 — {title[:50]}")

    print()
    print("  最佳标题: " + ranked[0][3])
    if ranked[0][0] >= 70:
        print("  评分达标，建议直接使用")
    elif ranked[0][0] >= 55:
        print("  评分中等，可发但建议优化弱项维度")
    else:
        print("  评分偏低，建议参考触发词列表重写")


if __name__ == "__main__":
    main()