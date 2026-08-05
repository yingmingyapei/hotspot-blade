#!/usr/bin/env python3
"""
热点刀锋 选题自动预评分 v6.2 (增强版)
========================
用途：对热榜话题自动做5维度预打分 + 类目同侪扩维 + 共振加成
用法：
  python3 auto-score.py "比亚迪降价到7万" "金价突破800元"
  python3 auto-score.py --category ai_bubble "AI泡沫进入倒计时"
  python3 auto-score.py --file /tmp/topics.json --category auto_industry
  python3 auto-score.py --verbose                    # 显示每个维度的匹配明细
  python3 auto-score.py --resonance /tmp/resonance.json  # 加载跨平台共振数据

新增功能 v6.2:
  - --category CLASS: 指定类目，自动追加同侪扩维加成
  - --resonance FILE: 加载跨平台共振检测结果，命中3+平台自动boost
  - 输出包含 category_boost / resonance_boost 字段
"""
import sys, re, json, math
from pathlib import Path

# === 钱包距离关键词 ===
WALLET_HIGH = [
    "裁员", "降薪", "涨薪", "工资", "收入", "房价", "房贷", "房租",
    "物价", "猪肉", "鸡蛋", "食用油", "米面", "蔬菜", "水果",
    "社保", "医保", "养老金", "公积金", "个税", "契税", "房产税",
    "利率", "LPR", "降息", "加息", "存款", "理财", "基金",
    "消费券", "补贴", "补助", "低保",
    "失业", "就业", "招聘", "求职",
    "退税", "摇号", "车牌", "油费", "停车费",
    "学费", "补习", "课外班", "托育", "幼儿园",
]
WALLET_MEDIUM = [
    "GDP", "CPI", "PPI", "通胀", "通缩", "汇率", "美元", "人民币",
    "贸易战", "关税", "制裁", "出口", "进口",
    "股票", "A股", "牛市", "熊市", "基金", "ETF",
    "黄金", "白银", "原油", "期货",
    "补贴", "减税", "降准", "降息",
    "罚单", "罚款", "退市", "ST",
    "行业", "产业", "产能", "供应链",
]
WALLET_LOW = [
    "明星", "八卦", "绯闻", "离婚", "出轨",
    "体育", "奥运", "世界杯", "NBA",
    "科技突破", "AI", "GPT", "大模型", "算法",
    "考古", "天文", "火星", "太空",
    "二次元", "动漫", "游戏", "电竞",
    "自然灾害", "地震", "台风", "洪水",
]

# === 反驳成本关键词 ===
REFUTE_HIGH = [
    "炒股", "炒房", "考公", "考研", "留学",
    "买房", "买车", "结婚", "生子",
    "努力", "奋斗", "选择", "躺平", "内卷",
    "报班", "补习", "鸡娃", "教育",
    "上岸", "裸辞", "副业", "创业",
    "借钱", "贷款", "信用", "花呗",
    "省钱", "花钱", "消费", "攒钱",
]
REFUTE_MEDIUM = [
    "政策", "监管", "调控", "改革",
    "利率", "税率", "关税",
    "技术", "转型", "升级",
    "管理", "效率", "创新",
    "风险", "泡沫", "危机",
]
REFUTE_LOW = [
    "法律", "法规", "条例", "宪法",
    "医学", "治疗", "手术", "药物",
    "论文", "研究", "统计", "模型",
    "精算", "工程", "物理", "化学",
    "国际法", "外交", "条约",
]

# === 物件锚点关键词 ===
OBJECT_HIGH = [
    "手机", "电脑", "汽车", "电动车", "外卖", "快递",
    "房租", "房贷", "水电", "物业", "停车",
    "超市", "菜市场", "药店", "医院",
    "口罩", "抗原", "药品", "疫苗",
    "奶茶", "咖啡", "外卖", "盒饭",
    "公众号", "抖音", "快手", "小红书",
    "账户", "银行卡", "支付宝", "微信",
]
OBJECT_MEDIUM = [
    "工厂", "车间", "仓库", "店铺",
    "写字楼", "园区", "开发区",
    "股票", "基金", "债券",
    "订单", "合同", "发票",
    "物流", "仓库", "货运",
]
OBJECT_LOW = [
    "数据", "算法", "模型", "平台",
    "体系", "制度", "机制", "架构",
    "概念", "理论", "框架",
    "战略", "布局", "生态",
    "指数", "系数", "率",
]

# === 头条适配关键词 ===
TOUTIAO_HIGH = [
    "退休", "延迟退休", "社保", "医保",
    "房价", "房贷", "租房",
    "工资", "收入", "加班",
    "裁员", "失业", "灵活就业",
    "教育", "学区", "高考", "中考",
    "养老", "老龄化", "独生子女",
    "农村", "农民", "农民工",
    "中美", "美国", "制裁", "关税",
    "涨价", "物价", "通胀",
    "食品安全", "添加剂", "预制菜",
]
TOUTIAO_MEDIUM = [
    "商业", "财经", "投资",
    "海外", "出海", "跨境",
    "科技", "互联网",
    "股市", "基金", "理财",
    "出口", "进口", "贸易",
]
TOUTIAO_LOW = [
    "AI", "大模型", "GPT", "开源",
    "二次元", "动漫", "游戏",
    "体育", "赛事",
    "小众", "圈层", "爱好者",
    "学术", "论文", "研究",
]

# === 天然分裂关键词 ===
SPLIT_HIGH = [
    "学区房", "该不该", "要不要", "对吗",
    "争议", "两派", "对立", "撕裂",
    "支持", "反对", "赞成",
    "结构性", "深层", "根源",
    "公平", "正义", "平等",
    "特权", "内定", "关系户",
    "争论", "吵翻", "互怼",
]
SPLIT_MEDIUM = [
    "风险", "机会", "泡沫",
    "取代", "淘汰", "消失",
    "传统", "新兴", "转型",
    "开放", "保守", "自由",
    "本地", "外来", "城乡",
]
SPLIT_LOW = [
    "感动", "泪目", "暖心", "正能量",
    "英雄", "致敬", "楷模",
    "惨案", "悲痛", "哀悼",
    "科普", "知识", "冷知识",
]


# =========================================================
# 类目同侪映射加载
# =========================================================
CATEGORIES_PATH = Path(__file__).parent.parent / "references" / "categories.json"

def load_categories():
    """加载类目同侪映射表"""
    if CATEGORIES_PATH.exists():
        return json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    return {}

CATEGORIES = load_categories()


def detect_category(topic):
    """自动检测话题所属类目（基于关键词匹配）"""
    topic_lower = topic.lower()
    matches = []
    for cat_name, cat_data in CATEGORIES.items():
        keywords = cat_data.get("keywords", [])
        if any(kw.lower() in topic_lower for kw in keywords):
            matches.append(cat_name)
    return matches


def get_category_boost(topic, category_names=None):
    """获取类目同侪扩维加成"""
    if category_names:
        cats = [c for c in category_names if c in CATEGORIES]
    else:
        cats = detect_category(topic)

    boost = {"wallet": 0, "refute": 0, "object": 0, "toutiao": 0, "split": 0}
    peer_info = []

    for cat_name in cats:
        cat_data = CATEGORIES[cat_name]
        cat_boost = cat_data.get("peer_boost", {})
        for dim in ["wallet", "refute", "object", "toutiao", "split"]:
            boost[dim] += cat_boost.get(dim, 0)
        peer_info.append({
            "category": cat_name,
            "zhihu_topics": cat_data.get("zhihu_topics", []),
            "weibo_super_topics": cat_data.get("weibo_super_topics", []),
            "36kr_columns": cat_data.get("36kr_columns", []),
        })

    return boost, peer_info


# =========================================================
# 共振加成
# =========================================================
def load_resonance(resonance_path):
    """加载跨平台共振检测结果"""
    try:
        return json.loads(Path(resonance_path).read_text(encoding="utf-8"))
    except Exception:
        return None


def get_resonance_boost(topic, resonance_data):
    """获取共振加成：3+平台=2.0, 2平台=1.0, 1平台=0"""
    if not resonance_data:
        return 0, "无共振数据"

    clusters = resonance_data.get("clusters", [])
    for cluster in clusters:
        # 标题关键词匹配
        cluster_title = cluster.get("title", "").lower()
        topic_lower = topic.lower()
        # 检查是否匹配核心关键词
        overlap = set(cluster_title.split()) & set(topic_lower.split())
        if len(overlap) >= 2 or topic_lower[:6] in cluster_title or cluster_title[:6] in topic_lower:
            platform_count = cluster.get("platform_count", 1)
            if platform_count >= 3:
                return 2.0, f"3+平台共振({platform_count}平台)"
            elif platform_count >= 2:
                return 1.0, f"2平台共振({platform_count}平台)"
            return 0, f"单平台({platform_count}平台)"
    return 0, "未发现共振"


def score_wallet(title):
    title_lower = title.lower()
    score = 5
    high = sum(1 for kw in WALLET_HIGH if kw in title_lower)
    med = sum(1 for kw in WALLET_MEDIUM if kw in title_lower)
    low = sum(1 for kw in WALLET_LOW if kw in title_lower)
    score += high * 2
    score += med * 1
    score -= low * 2
    triggers = []
    if high > 0: triggers.append(f"高({high})")
    if med > 0: triggers.append(f"中({med})")
    if low > 0: triggers.append(f"低({low})")
    return max(1, min(10, score)), triggers


def score_refute(title):
    title_lower = title.lower()
    score = 5
    high = sum(1 for kw in REFUTE_HIGH if kw in title_lower)
    med = sum(1 for kw in REFUTE_MEDIUM if kw in title_lower)
    low = sum(1 for kw in REFUTE_LOW if kw in title_lower)
    score += high * 2
    score += med * 1
    score -= low * 2
    triggers = []
    if high > 0: triggers.append(f"高({high})")
    if med > 0: triggers.append(f"中({med})")
    if low > 0: triggers.append(f"低({low})")
    return max(1, min(10, score)), triggers


def score_object(title):
    title_lower = title.lower()
    score = 5
    high = sum(1 for kw in OBJECT_HIGH if kw in title_lower)
    med = sum(1 for kw in OBJECT_MEDIUM if kw in title_lower)
    low = sum(1 for kw in OBJECT_LOW if kw in title_lower)
    score += high * 1.5
    score += med * 0.5
    score -= low * 2
    triggers = []
    if high > 0: triggers.append(f"高({high})")
    if med > 0: triggers.append(f"中({med})")
    if low > 0: triggers.append(f"低({low})")
    return max(1, min(10, score)), triggers


def score_toutiao(title):
    title_lower = title.lower()
    score = 5
    high = sum(1 for kw in TOUTIAO_HIGH if kw in title_lower)
    med = sum(1 for kw in TOUTIAO_MEDIUM if kw in title_lower)
    low = sum(1 for kw in TOUTIAO_LOW if kw in title_lower)
    score += high * 2
    score += med * 0.5
    score -= low * 2
    triggers = []
    if high > 0: triggers.append(f"高({high})")
    if med > 0: triggers.append(f"中({med})")
    if low > 0: triggers.append(f"低({low})")
    return max(1, min(10, score)), triggers


def score_split(title):
    title_lower = title.lower()
    score = 3
    high = sum(1 for kw in SPLIT_HIGH if kw in title_lower)
    med = sum(1 for kw in SPLIT_MEDIUM if kw in title_lower)
    low = sum(1 for kw in SPLIT_LOW if kw in title_lower)
    score += high * 2
    score += med * 1
    score -= low * 2
    triggers = []
    if high > 0: triggers.append(f"高({high})")
    if med > 0: triggers.append(f"中({med})")
    if low > 0: triggers.append(f"低({low})")
    return max(1, min(10, score)), triggers


def compute_total(scores, category_boost=None, resonance_boost=0.0):
    """计算总分，含类目加成和共振加成"""
    w = scores["wallet_distance"]
    r = scores["refutation_cost"]
    o = scores["object_anchor"]
    t = scores["toutiao_fit"]
    s = scores["natural_split"]

    # 应用类目加成
    if category_boost:
        w = min(10, w + category_boost.get("wallet", 0))
        r = min(10, r + category_boost.get("refute", 0))
        o = min(10, o + category_boost.get("object", 0))
        t = min(10, t + category_boost.get("toutiao", 0))
        s = min(10, s + category_boost.get("split", 0))

    # 共振加成加到总分上
    total = round(
        w * 0.35 + r * 0.25 + o * 0.15 + t * 0.15 + s * 0.10 + resonance_boost * 0.3,
        1,
    )
    return total


def get_grade(total):
    if total >= 8.0: return "S"
    elif total >= 6.0: return "A"
    elif total >= 4.0: return "B"
    else: return "C"


def score_topic(topic, verbose=False, category_names=None, resonance_data=None):
    topic_str = topic if isinstance(topic, str) else topic.get("title", str(topic))

    w, w_triggers = score_wallet(topic_str)
    r, r_triggers = score_refute(topic_str)
    o, o_triggers = score_object(topic_str)
    t, t_triggers = score_toutiao(topic_str)
    s, s_triggers = score_split(topic_str)

    # 类目同侪扩维
    cat_boost, peer_info = get_category_boost(topic_str, category_names)

    # 共振检测
    res_boost, res_note = get_resonance_boost(topic_str, resonance_data)

    # 应用加成后的维度分
    w_boosted = min(10, w + cat_boost.get("wallet", 0))
    r_boosted = min(10, r + cat_boost.get("refute", 0))
    o_boosted = min(10, o + cat_boost.get("object", 0))
    t_boosted = min(10, t + cat_boost.get("toutiao", 0))
    s_boosted = min(10, s + cat_boost.get("split", 0))

    scores = {
        "wallet_distance": w_boosted,
        "refutation_cost": r_boosted,
        "object_anchor": o_boosted,
        "toutiao_fit": t_boosted,
        "natural_split": s_boosted,
    }

    total = compute_total(
        {"wallet_distance": w, "refutation_cost": r, "object_anchor": o,
         "toutiao_fit": t, "natural_split": s},
        category_boost=cat_boost,
        resonance_boost=res_boost,
    )
    grade = get_grade(total)

    result = {
        "topic": topic_str,
        "scores": scores,
        "scores_raw": {
            "wallet_distance": w,
            "refutation_cost": r,
            "object_anchor": o,
            "toutiao_fit": t,
            "natural_split": s,
        },
        "category_boost": cat_boost,
        "peer_info": peer_info,
        "resonance_boost": res_boost,
        "resonance_note": res_note,
        "total": total,
        "grade": grade,
        "checklist": {
            "wallet_distance_ok": w_boosted >= 5,
            "refutation_cost_ok": r_boosted >= 6,
            "object_anchor_ok": o_boosted >= 4,
            "total_ok": total >= 6.0,
        },
    }

    if verbose:
        result["triggers"] = {
            "wallet_distance": w_triggers,
            "refutation_cost": r_triggers,
            "object_anchor": o_triggers,
            "toutiao_fit": t_triggers,
            "natural_split": s_triggers,
        }

    return result


def print_result(result, verbose=False):
    scores = result["scores"]
    raw = result.get("scores_raw", scores)
    cat_boost = result.get("category_boost", {})
    res_boost = result.get("resonance_boost", 0)
    res_note = result.get("resonance_note", "")

    print(f"话题: {result['topic']}")
    print(f"评级: [{result['grade']}] 总分: {result['total']}")

    has_boost = any(v > 0 for v in cat_boost.values()) or res_boost > 0
    if has_boost:
        boost_parts = []
        for dim, val in cat_boost.items():
            if val > 0:
                boost_parts.append(f"{dim}+{val}")
        if res_boost > 0:
            boost_parts.append(f"共振+{res_boost}")
        print(f"  加成: {', '.join(boost_parts)}")

    print(f"  钱包距离: {scores['wallet_distance']}/10 (基础{raw['wallet_distance']})", end="")
    if verbose and result.get("triggers"):
        print(f" 触发: {', '.join(result['triggers']['wallet_distance']) or '无'}", end="")
    print()
    print(f"  反驳成本: {scores['refutation_cost']}/10 (基础{raw['refutation_cost']})", end="")
    if verbose and result.get("triggers"):
        print(f" 触发: {', '.join(result['triggers']['refutation_cost']) or '无'}", end="")
    print()
    print(f"  物件锚点: {scores['object_anchor']}/10 (基础{raw['object_anchor']})", end="")
    if verbose and result.get("triggers"):
        print(f" 触发: {', '.join(result['triggers']['object_anchor']) or '无'}", end="")
    print()
    print(f"  头条适配: {scores['toutiao_fit']}/10 (基础{raw['toutiao_fit']})", end="")
    if verbose and result.get("triggers"):
        print(f" 触发: {', '.join(result['triggers']['toutiao_fit']) or '无'}", end="")
    print()
    print(f"  天然分裂: {scores['natural_split']}/10 (基础{raw['natural_split']})", end="")
    print()
    if result.get("resonance_note"):
        print(f"  共振: {result['resonance_note']}")
    if result.get("peer_info"):
        peers = []
        for p in result["peer_info"]:
            peers.append(p["category"])
        print(f"  类目: {', '.join(peers)}")

    cl = result["checklist"]
    checks = []
    checks.append(f"钱包{'✅' if cl['wallet_distance_ok'] else '❌'}")
    checks.append(f"反驳{'✅' if cl['refutation_cost_ok'] else '❌'}")
    checks.append(f"物件{'✅' if cl['object_anchor_ok'] else '❌'}")
    checks.append(f"总分{'✅' if cl['total_ok'] else '❌'}")
    print(f"  自检: {' | '.join(checks)}")
    print()


def main():
    topics = []
    verbose = "--verbose" in sys.argv
    category_names = None
    resonance_path = None

    # Parse flags
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    for i, a in enumerate(sys.argv[1:]):
        if a == "--category" and i + 2 < len(sys.argv):
            category_names = [sys.argv[i + 2]]
        elif a == "--resonance" and i + 2 < len(sys.argv):
            resonance_path = sys.argv[i + 2]

    if not args:
        print("请输入话题（每行一个，Ctrl+D结束）:")
        try:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    topics.append(line)
        except EOFError:
            pass
    elif args[0] == "--file" and len(args) >= 2:
        with open(args[1], "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                topics = data
            elif isinstance(data, dict):
                topics = data.get("topics", data.get("data", []))
    else:
        topics = args

    if not topics:
        print("未输入话题")
        return

    # 加载共振数据
    resonance_data = None
    if resonance_path:
        resonance_data = load_resonance(resonance_path)
        if resonance_data:
            print(f"✅ 加载共振数据: {len(resonance_data.get('clusters', []))} 个集群")
        else:
            print("⚠️ 无法加载共振数据")
    else:
        print("ℹ️ 未指定共振数据 (--resonance)，无共振加成")

    print(f"自动评分 {len(topics)} 个话题")
    if category_names:
        print(f"类目: {category_names[0]}")
    print("=" * 60)
    print()

    results = []
    for topic in topics:
        result = score_topic(topic, verbose=verbose, category_names=category_names, resonance_data=resonance_data)
        results.append(result)
        print_result(result, verbose=verbose)

    # Summary
    print("=" * 60)
    print("汇总:")
    s_count = sum(1 for r in results if r["grade"] == "S")
    a_count = sum(1 for r in results if r["grade"] == "A")
    b_count = sum(1 for r in results if r["grade"] == "B")
    c_count = sum(1 for r in results if r["grade"] == "C")
    print(f"  S级: {s_count}  A级: {a_count}  B级: {b_count}  C级: {c_count}")

    # Output JSON
    print()
    print("--- JSON ---")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()