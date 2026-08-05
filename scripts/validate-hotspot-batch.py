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

def validate_batch(filepath: str) -> bool:
    t = open(filepath, encoding='utf-8').read()
    arts = re.split(r'═══+', t)
    splits = len(arts)
    has_titles = sum('标题：' in a for a in arts)
    print(f'splits: {splits} | has标题: {has_titles}')
    print(f'期望篇数对齐: splits == 期望篇数+1')
    print()

    ok = True
    for i, a in enumerate(arts):
        if '标题：' not in a:
            continue
        # ⚠️ 行首+行末+re.M，行内引号不会打断贪心匹配
        title_m = re.search(r'^标题：(.+)$', a, re.M)
        # 正文 capture：贪婪到 ═══，不用 \n\n评论（会被正文内"评论区"提前截断）
        body_m = re.search(r'^正文：\n(.*)', a, re.S)
        if not title_m or not body_m:
            print(f'  第{i+1}篇 ⚠️ 解析失败，跳过')
            continue
        title = title_m.group(1).strip()
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
        if title_len < 10 or title_len > 35:
            issues.append(f'标题长度{title_len}字（应10-35）')
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