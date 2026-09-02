#!/usr/bin/env python3
"""
热点刀锋批量合规校验脚本（═══分隔的多篇文章）
cron 环境执行方式：
  terminal(python3 <<'PYEOF'
  (this script content)
  PYEOF)

用法：python3 validate-hotspot-batch.py output.md
输出：逐篇字数/禁用词/标题合规检查，全部通过才交付
"""

import re
import sys

# 「不是A是B」反差句式检测（同批5篇标题过度集中会显得模板化）
_FLIP_PATTERNS = [
    r"不是.+是",   # 不是智商税是入场券
    r"买的?不是.+是",  # 买的不是房子是退路
    r"亏的是.+不是",  # 亏的是学费不是工资
]


def _count_flip_titles(titles):
    """统计标题里用了「不是X是Y」反差句式的数量。"""
    n = 0
    for t in titles:
        if any(re.search(p, t) for p in _FLIP_PATTERNS):
            n += 1
    return n

def validate_batch(filepath: str) -> bool:
    t = open(filepath, encoding='utf-8').read()
    arts = re.split(r'═══+', t)
    splits = len(arts)
    has_titles = sum('标题：' in a for a in arts)
    print(f'splits: {splits} | has标题: {has_titles}')
    print(f'期望篇数对齐: splits == 期望篇数+1')
    print()

    ok = True
    all_titles = []
    for i, a in enumerate(arts):
        if '标题：' not in a:
            continue
        # ⚠️ 行首+行末+re.M，行内引号不会打断贪心匹配
        title_m = re.search(r'^标题：(.+)$', a, re.M)
        # 正文 capture：贪婪到 ═══，不用 \n\n评论（会被正文内"评论区"提前截断）
        body_m = re.search(r'^正文：\n?(.*)', a, re.S | re.M)
        if not title_m or not body_m:
            print(f'  第{i+1}篇 ⚠️ 解析失败，跳过')
            continue
        title = title_m.group(1).strip()
        all_titles.append(title)
        body = body_m.group(1)
        # 向后截断到 ═══（确定性的分隔符）
        body = re.split(r'\n═══', body)[0]
        cn = len(re.findall(r'[\u4e00-\u9fff]', body))
        en = len(re.findall(r'[a-zA-Z]', body))
        total = cn + en

        issues = []
        if re.search(r'[【\u3010][^】\u3011]*[】\u3011]', title):
            issues.append('标题含【】标注')
        title_len = len(title)
        if title_len < 20 or title_len > 30:
            issues.append(f'标题长度{title_len}字（应20-30）')
        if total < 450 or total > 600:
            issues.append(f'正文{total}字（应450-600）')
        for w in ['底层逻辑', '赋能', '抓手', '综上所述', '值得注意的是', '并没有']:
            if w in body:
                issues.append(f'禁用词: {w}')
        slc = body.count('说白了')
        if slc > 1:
            issues.append(f'说白了次数: {slc}（应≤1）')

        status = '✅' if not issues else '❌'
        print(f'  {status} 第{i+1}篇: {total}字 | 标题: {title[:40]}')
        if issues:
            for iss in issues:
                print(f'       → {iss}')
            ok = False

    # === 标题句式轮换检查（同批"不是A是B"不超过60%）===
    if all_titles:
        flip_n = _count_flip_titles(all_titles)
        flip_ratio = flip_n / len(all_titles)
        if flip_ratio > 0.6:
            ok = False
            print(f'  ❌ 标题句式: {flip_n}/{len(all_titles)} 篇用了「不是X是Y」反差句式（占{flip_ratio:.0%}），模板化，需轮换至少3种句式')
        else:
            print(f'  ✅ 标题句式: 反差句式 {flip_n}/{len(all_titles)} 篇，未过度集中')

    # === 反 slop: 全批算账起手式计数（Hallmark 移植 · v6.10.0）===
    # 同批5篇 "我帮你算算" 等起手式合计≤2次，避免模板化
    _ACCOUNTING_OPENERS = [
        "我帮你算算", "咱们算算", "说句实在的", "先算笔账",
        "算一笔账", "算笔账", "来算算", "咱们来算",
    ]
    batch_opener_count = sum(a.count(p) for a in arts for p in _ACCOUNTING_OPENERS)
    batch_opener_pass = batch_opener_count <= 2
    if not batch_opener_pass:
        ok = False
        print(f'  ❌ 算账句式: 全批 {batch_opener_count} 处算账起手式（应≤2处/批），需轮换句式')
    else:
        print(f'  ✅ 算账句式: 全批 {batch_opener_count} 处起手式，未过度集中')

    # === 反 slop: 结构类型多样性（Hallmark 移植 · v6.10.0）===
    # 检测每篇的开头类型，统计分布；标准四段式（开场冲突→算账→反转→收尾追问）占比≤60%
    STRUCTURE_MARKERS = {
        "数据冲击型": [r"^\d+[万亿亿千百十万块元%]", r"^\d+\.?\d*%"],
        "场景代入型": [r"^\d{4}年?\d{1,2}月?\d{1,2}日?", r"^\d{1,2}月?\d{1,2}日?", r"^(上午|下午|晚上|早上|昨晚|今早|深夜)"],
        "对话辩论型": [r"^(很多人|大家|网上|普遍认为|都说|常识)", r"^你以为"],
        "机制剥离型": [r"^(这不是|表面看|本质上|底层|机制|逻辑是)", r"^所谓"],
        "标准四段式": [
            r"我帮你算算.*听着没毛病",
            r"听着没毛病.*我帮你算算",
            r"咱们算算.*听着没毛病",
            r"听着没毛病.*咱们算算",
            r"说句实在的.*但",
            r"先算笔账.*但",
            r"算笔账.*听着没毛病",
        ],
    }

    structure_counts = {name: 0 for name in STRUCTURE_MARKERS}
    for a in arts:
        if '正文：' not in a:
            continue
        body_m = re.search(r'^正文：\n?(.*)', a, re.S | re.M)
        if not body_m:
            continue
        body = body_m.group(1)
        opening = body[:60]
        matched = False
        for struct_name, patterns in STRUCTURE_MARKERS.items():
            if any(re.search(p, opening) for p in patterns):
                structure_counts[struct_name] += 1
                matched = True
                break
        if not matched:
            structure_counts["标准四段式"] += 1  # 未知归入默认类

    total_structured = sum(structure_counts.values())
    if total_structured > 0:
        std_ratio = structure_counts["标准四段式"] / total_structured
        struct_diversity_pass = std_ratio <= 0.6
        if not struct_diversity_pass:
            ok = False
            print(f'  ❌ 结构多样性: 标准四段式 {structure_counts["标准四段式"]}/{total_structured} 篇（占{std_ratio:.0%}），需至少2篇换结构模板')
        else:
            print(f'  ✅ 结构多样性: 标准四段式 {structure_counts["标准四段式"]}/{total_structured} 篇，未过度集中')
        # 打印分布（提示用，不拦）
        dist_str = ", ".join(f"{k}:{v}" for k, v in structure_counts.items() if v > 0)
        print(f'     结构分布: {dist_str}')

    print()
    print('=' * 50)
    if ok:
        print('批量校验: ✅ 通过，可以交付')
    else:
        print('批量校验: ❌ 需修复，不能交付不合格成品')
    return ok

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 validate-hotspot-batch.py <output-file>')
        sys.exit(1)
    success = validate_batch(sys.argv[1])
    sys.exit(0 if success else 1)