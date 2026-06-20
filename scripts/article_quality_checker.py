#!/usr/bin/env python3
"""
文章质量自动验证器 v1.0
热点刀锋 Step 5 质量后验——写作完成后自动检查，不通过则拒绝推送。

检查项：
1. 标题字数（20-30字）
2. 禁用语扫描（调用 retired-phrase-scanner）
3. 句式频率（同一句式不能超限）
4. 数字密度（统计可疑编造数字）
5. 段落长度（不能均匀平铺）
6. AI味标志词

用法:
  python3 article_quality_checker.py <article_file> [--title "标题文字"]
  python3 article_quality_checker.py --stdin [--title "标题文字"] < article.txt
  echo "文章内容" | python3 article_quality_checker.py --stdin

输出 JSON:
  {"passed": true/false, "score": 85, "checks": [...], "errors": [...], "warnings": [...]}
"""
import sys
import os
import re
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "..", "references", "banned-phrases-data.json")

# ── 配置 ──────────────────────────────────────────
TITLE_MIN = 15
TITLE_MAX = 35
PARAGRAPH_MIN_AVG = 30   # 段落平均字数下限
PARAGRAPH_MAX_AVG = 150  # 段落平均字数上限
NUMBER_PATTERN = re.compile(r'\d+[\.\d]*[%％亿万]')
SENTENCE_SPLIT = re.compile(r'[。！？\n]')

# 句式频率限制（从 banned-phrases-data.json 读取，这里设默认值）
DEFAULT_FREQ_LIMITS = {
    "说白了": 1,
    "本质剥离": 1,
    "定性重锤": 1,
    "递进王": 1,
    "你猜": 2,
}

def load_rules():
    """加载禁用规则"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def check_title(title, checks, errors, warnings):
    """检查标题"""
    if not title:
        warnings.append("未提供标题，跳过标题检查")
        return
    
    length = len(title)
    if length < TITLE_MIN:
        errors.append(f"标题过短（{length}字，最少{TITLE_MIN}字）")
    elif length > TITLE_MAX:
        errors.append(f"标题过长（{length}字，最多{TITLE_MAX}字）")
    else:
        checks.append(f"✅ 标题字数: {length}字")
    
    # 标题必须有数字或反差词
    has_number = bool(re.search(r'\d', title))
    contrast_words = ['不是', '而是', '竟然', '居然', '真相', '背后', '最', '比']
    has_contrast = any(w in title for w in contrast_words)
    if not has_number and not has_contrast:
        warnings.append("标题缺少数字或反差词，CTR可能偏低")

def check_banned_phrases(text, rules, checks, errors):
    """检查禁用语"""
    banned_words = rules.get("banned_words", [])
    found = []
    for phrase in banned_words:
        if phrase in text:
            count = text.count(phrase)
            found.append(f"{phrase}({count}次)")
    
    if found:
        errors.append(f"发现禁用语: {', '.join(found)}")
    else:
        checks.append("✅ 禁用语检查: 通过")

def check_sentence_frequency(text, rules, checks, warnings):
    """检查句式频率"""
    limits = rules.get("frequency_limits", DEFAULT_FREQ_LIMITS)
    violations = []
    for pattern, limit in limits.items():
        count = len(re.findall(pattern, text))
        if count > limit:
            violations.append(f"「{pattern}」{count}次(限制{limit})")
    
    if violations:
        warnings.append(f"句式频率超限: {', '.join(violations)}")
    else:
        checks.append("✅ 句式频率: 正常")

def check_numbers(text, checks, warnings):
    """检查数字密度和可疑编造"""
    numbers = NUMBER_PATTERN.findall(text)
    char_count = len(text)
    
    if not numbers:
        checks.append("✅ 数字密度: 无具体数字（安全）")
        return
    
    density = len(numbers) / max(char_count / 100, 1)
    if density > 5:
        warnings.append(f"数字密度过高: {len(numbers)}个数字/{char_count}字，可能有编造风险")
    else:
        checks.append(f"✅ 数字密度: {len(numbers)}个数字（正常）")

def check_paragraphs(text, checks, warnings):
    """检查段落长度分布"""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 5]
    
    if len(paragraphs) < 3:
        warnings.append(f"段落数过少（{len(paragraphs)}段），节奏可能单调")
        return
    
    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    
    # 检查是否均匀平铺（标准差太小 = 匀速平铺 = AI味）
    if len(lengths) > 3:
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        std = variance ** 0.5
        cv = std / avg if avg > 0 else 0  # 变异系数
        
        if cv < 0.2:
            warnings.append(f"段落长度过于均匀（变异系数{cv:.2f}），缺乏节奏感")
        else:
            checks.append(f"✅ 段落节奏: 变异系数{cv:.2f}（有变化）")
    
    if avg < PARAGRAPH_MIN_AVG:
        warnings.append(f"段落平均过短（{avg:.0f}字），可能碎片化")
    elif avg > PARAGRAPH_MAX_AVG:
        warnings.append(f"段落平均过长（{avg:.0f}字），手机阅读体验差")
    else:
        checks.append(f"✅ 段落长度: 平均{avg:.0f}字")

def check_ai_smell(text, checks, warnings):
    """快速AI味检测"""
    # 排比三连检测
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    if len(sentences) >= 3:
        # 检查连续三句是否结构相似（排比）
        for i in range(len(sentences) - 2):
            s1, s2, s3 = sentences[i], sentences[i+1], sentences[i+2]
            # 简单启发式：三句长度相近且都有相同关键词
            lengths = [len(s) for s in [s1, s2, s3]]
            if max(lengths) - min(lengths) < 5 and all(len(s) > 10 for s in [s1, s2, s3]):
                warnings.append(f"疑似排比三连（第{i+1}-{i+3}句），建议砍掉两个留一个")
                break
    
    # "首先/其次/最后"排序依赖
    ordering_words = ['首先', '其次', '最后', '第一，', '第二，', '第三，']
    ordering_count = sum(1 for w in ordering_words if w in text)
    if ordering_count >= 3:
        warnings.append(f"排序依赖过重（{ordering_count}处），建议用自然过渡替代")
    
    checks.append("✅ AI味快速检测: 完成")

def main():
    parser = argparse.ArgumentParser(description="文章质量自动验证器")
    parser.add_argument("file", nargs="?", help="文章文件路径")
    parser.add_argument("--stdin", action="store_true", help="从stdin读取")
    parser.add_argument("--title", default="", help="标题文字")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()
    
    # 读取文章
    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        parser.print_help()
        sys.exit(2)
    
    rules = load_rules()
    checks = []
    errors = []
    warnings = []
    
    # 执行所有检查
    check_title(args.title, checks, errors, warnings)
    check_banned_phrases(text, rules, checks, errors)
    check_sentence_frequency(text, rules, checks, warnings)
    check_numbers(text, checks, warnings)
    check_paragraphs(text, checks, warnings)
    check_ai_smell(text, checks, warnings)
    
    # 计算分数
    score = 100
    score -= len(errors) * 15
    score -= len(warnings) * 5
    score = max(0, min(100, score))
    
    passed = len(errors) == 0 and score >= 60
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if passed:
            print(f"✅ 质量检查通过（{score}分）")
        else:
            print(f"❌ 质量检查不通过（{score}分）")
        
        for c in checks:
            print(f"  {c}")
        for e in errors:
            print(f"  ❌ {e}")
        for w in warnings:
            print(f"  ⚠️ {w}")
    
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
