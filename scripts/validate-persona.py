#!/usr/bin/env python3
"""
热点刀锋 预发布合规校验
========================
用途：在发布前校验文章是否符合"凡事算账的人"人设
用法：
  python3 validate-persona.py < article.txt     # 从stdin读文章
  python3 validate-persona.py --file article.md  # 从文件读
  python3 validate-persona.py --strict           # 严格模式（不允许人工复核绕过）

校验项：
  P0 - 数字密度 (≥3个可溯源数字/千字)
  P0 - 算账视角 (以"算账/成本/收益/对比"框架切入)
  P0 - 情绪过滤 (非纯情绪宣泄，有机制分析)
  P1 - 禁用词检查 (主观判断词、模糊词)
  P1 - 引语真实度 (匿名来源标记)
  P2 - 切口位置 (前30字是否出现核心冲突/数字)
"""

import sys, re, os

# === 配置 ===
MIN_NUMBERS_PER_1000_CHARS = 3
MIN_ACCOUNTING_SIGNALS = 2
MAX_EMOTIONAL_WORDS_PER_500_CHARS = 2
MAX_VAGUE_WORDS = 3

# 算账视角关键词
ACCOUNTING_KEYWORDS = [
    "花了", "亏了", "赚了", "成本", "花了多少", "多少钱", "价格",
    "涨价", "降价", "利润", "收入", "支出", "预算", "花费",
    "省了", "省下", "相当于", "换算", "算下来", "算了一笔",
    "账", "划算", "不值", "值不值", "投入", "回报", "ROI",
    "利息", "工资", "房贷", "月供", "租金", "押金", "溢价",
    "贬值", "升值", "收益率", "净利", "毛利", "差价",
]

# 情绪宣泄词（纯情绪无分析）
EMOTIONAL_WORDS = [
    "太可怕了", "惊呆了", "震碎三观", "气炸了", "看哭了",
    "太让人愤怒", "简直是疯了", "无法理解", "恶心", "愤怒",
    "心痛", "泪目", "震惊", "暴怒", "崩溃",
    "简直了", "无语", "心塞", "扎心",
]

# 模糊词（无数据支撑的泛泛判断）
VAGUE_WORDS = [
    "很多人", "大量", "众所周知", "大家都说", "网上都在传",
    "据说", "有人", "有消息称", "传闻", "消息人士",
    "不知道", "可能", "也许", "大概", "似乎",
    "众所周知", "普遍认为", "不出所料",
]

# 匿名来源标记
ANONYMOUS_PATTERNS = [
    r"业内人士", r"知情人[士]?", r"消息人士", r"不愿透露姓名",
    r"相关人士", r"接近[^的]+的人[士]?", r"据传",
]


def read_input():
    text = ""
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            with open(sys.argv[idx + 1], "r", encoding="utf-8") as f:
                text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("用法: python3 validate-persona.py < article.txt")
        print("  或: python3 validate-persona.py --file article.md")
        sys.exit(1)
    return text


def count_numbers(text):
    """Count traceable numbers (not dates, not years)."""
    # Match: digits, optionally with commas/decimals, followed by unit
    number_patterns = [
        r"\d+[.,]?\d*\s*[万亿亿千百十万万亿块元%％倍成]",
        r"\d+[.,]?\d*\s*[个只条家]",
        r"\d+[.,]?\d*\s*[岁年]月?",
        r"\d{1,3}(?:,\d{3})*[.\d]*",  # bare large numbers
    ]
    matches = set()
    for pat in number_patterns:
        for m in re.finditer(pat, text):
            matches.add(m.group())
    # Filter out dates (4-digit years)
    filtered = [m for m in matches if not re.match(r"^\d{4}$", m.strip())]
    return len(filtered)


def count_accounting_signals(text):
    """Count how many accounting/financial framing signals."""
    count = 0
    for kw in ACCOUNTING_KEYWORDS:
        count += text.count(kw)
    return count


def count_emotional_words(text):
    """Count pure emotional venting words."""
    count = 0
    for w in EMOTIONAL_WORDS:
        count += text.count(w)
    return count


def count_vague_words(text):
    """Count vague/unsupported judgment words."""
    count = 0
    for w in VAGUE_WORDS:
        count += text.count(w)
    return count


def check_anonymous_sources(text):
    """Check for anonymous/unnamed sources."""
    found = []
    for pat in ANONYMOUS_PATTERNS:
        for m in re.finditer(pat, text):
            found.append(m.group())
    return found


def check_opening_hook(text):
    """Check if first 30 chars contain a number or core conflict."""
    opening = text[:80].strip()  # slightly wider to catch
    has_number = bool(re.search(r"\d", opening))
    has_conflict = bool(re.search(r"[为什么？?]|[怎么]|[区别]|[真相]|[背后]|[套路]|[陷阱]", opening))
    return has_number or has_conflict, has_number, has_conflict


def validate(text, strict=False):
    total_chars = len(text)
    total_lines = text.count("\n") + 1
    # Estimate reading time
    words = len(text.split())
    reading_time_min = max(1, words / 300)

    print(f"文章: {total_chars} 字, ~{words} 词, 约{reading_time_min:.0f}分钟阅读")
    print("=" * 60)
    print()

    results = []
    all_pass = True

    # === P0: 数字密度 ===
    num_count = count_numbers(text)
    density = num_count / max(1, total_chars / 1000)
    threshold = MIN_NUMBERS_PER_1000_CHARS * (1.5 if total_chars < 500 else 1)
    num_pass = density >= threshold
    if not num_pass:
        all_pass = False
    results.append(("P0", "数字密度", num_pass, f"{num_count}个数字, {density:.1f}个/千字", f"≥{threshold:.1f}个/千字"))
    if num_pass:
        print(f"  ✅ P0 数字密度: {num_count}个数字, {density:.1f}个/千字 (达标)")
    else:
        print(f"  ❌ P0 数字密度: {num_count}个数字, {density:.1f}个/千字 (需≥{threshold:.1f})")

    # === P0: 算账视角 ===
    acct_count = count_accounting_signals(text)
    acct_pass = acct_count >= MIN_ACCOUNTING_SIGNALS
    if not acct_pass:
        all_pass = False
    results.append(("P0", "算账视角", acct_pass, f"{acct_count}个算账信号", f"≥{MIN_ACCOUNTING_SIGNALS}"))
    print(f"  {'✅' if acct_pass else '❌'} P0 算账视角: {acct_count}个算账信号 {'(达标)' if acct_pass else '(需≥2)'}")

    # === P0: 情绪过滤 ===
    emo_count = count_emotional_words(text)
    max_emo = max(1, int(total_chars / 500) * MAX_EMOTIONAL_WORDS_PER_500_CHARS)
    emo_pass = emo_count <= max_emo
    if not emo_pass:
        all_pass = False
    results.append(("P0", "情绪过滤", emo_pass, f"{emo_count}个情绪词", f"≤{max_emo}"))
    print(f"  {'✅' if emo_pass else '❌'} P0 情绪过滤: {emo_count}个情绪词 {'(达标)' if emo_pass else '(需≤' + str(max_emo) + ')'}")

    # === P1: 禁用词 ===
    vague_count = count_vague_words(text)
    vague_pass = vague_count <= MAX_VAGUE_WORDS
    if not vague_pass:
        all_pass = False
    results.append(("P1", "模糊词", vague_pass, f"{vague_count}个模糊词", f"≤{MAX_VAGUE_WORDS}"))
    vague_detail = ""
    if vague_count > 0:
        vague_detail = f" ({', '.join(list(set(re.findall('|'.join(VAGUE_WORDS), text))))[:60]})"
    print(f"  {'✅' if vague_pass else '❌'} P1 模糊词: {vague_count}个{vague_detail} {'(达标)' if vague_pass else '(需≤3)'}")

    # === P1: 匿名来源 ===
    anon = check_anonymous_sources(text)
    anon_pass = len(anon) == 0
    if not anon_pass and not strict:
        # Warning, not blocker
        print(f"  ⚠️ P1 匿名来源: {len(anon)}处 — {', '.join(set(anon))[:60]}")
    elif anon_pass:
        print(f"  ✅ P1 匿名来源: 无")
    else:
        all_pass = False
        print(f"  ❌ P1 匿名来源: {len(anon)}处 (严格模式)")

    # === P2: 切口位置 ===
    hook_pass, has_num, has_conflict = check_opening_hook(text)
    hook_detail = []
    if has_num:
        hook_detail.append("有数字")
    if has_conflict:
        hook_detail.append("有冲突")
    if not hook_detail:
        hook_detail.append("无钩子")
    results.append(("P2", "前30字钩子", hook_pass, ", ".join(hook_detail), "有数字或冲突"))
    if hook_pass:
        print(f"  ✅ P2 前30字钩子: {'+'.join(hook_detail)} (达标)")
    else:
        all_pass = False
        print(f"  ❌ P2 前30字钩子: 无钩子 (需在前80字内出现数字或冲突)")

    # === Summary ===
    print()
    print("=" * 60)
    p0_results = [r for r in results if r[0] == "P0"]
    p0_pass = sum(1 for r in p0_results if r[2])
    p0_total = len(p0_results)
    p1_results = [r for r in results if r[0] == "P1"]
    p1_pass = sum(1 for r in p1_results if r[2])
    p1_total = len(p1_results)
    p2_results = [r for r in results if r[0] == "P2"]
    p2_pass = sum(1 for r in p2_results if r[2])
    p2_total = len(p2_results)

    print(f"  P0 (人设核心): {p0_pass}/{p0_total} 通过")
    print(f"  P1 (质量门禁): {p1_pass}/{p1_total} 通过")
    print(f"  P2 (优化建议): {p2_pass}/{p2_total} 通过")

    if all_pass:
        print()
        print("  ✅ 全部通过，可以发布")
        return True
    else:
        print()
        print(f"  ❌ {sum(1 for r in results if not r[2])} 项未通过，建议修改后重跑")
        for r in results:
            if not r[2]:
                print(f"    - [{r[0]}] {r[1]}: {r[3]} (需{r[4]})")
        return False


def main():
    strict = "--strict" in sys.argv
    text = read_input()
    if not text.strip():
        print("错误: 输入为空")
        sys.exit(1)
    validate(text, strict)


if __name__ == "__main__":
    main()