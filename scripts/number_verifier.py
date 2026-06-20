#!/usr/bin/env python3
"""
数字校验脚本 v1.0 — 防止LLM编造数据
扫描文章中的具体数字，标记可疑编造项。

用法:
  python3 number_verifier.py <article_file>
  python3 number_verifier.py --stdin < article.txt
  echo "文章内容" | python3 number_verifier.py --stdin
  python3 number_verifier.py --source /tmp/hotlist_data.json <article_file>

原理：
- 提取文章中所有具体数字（百分比、金额、数量等）
- 与原始热榜数据对比（如有）
- 标记"可疑"数字——不在原始数据中且过于精确的数字
"""
import sys
import os
import re
import json
import argparse

# 数字模式
PATTERNS = {
    "百分比": re.compile(r'(\d+\.?\d*)\s*[%％]'),
    "金额_亿": re.compile(r'(\d+\.?\d*)\s*亿'),
    "金额_万": re.compile(r'(\d+\.?\d*)\s*万'),
    "金额_元": re.compile(r'(\d+\.?\d*)\s*元'),
    "大数字": re.compile(r'(\d{4,})'),
    "倍数": re.compile(r'(\d+\.?\d*)\s*倍'),
}


def extract_numbers(text):
    """提取文章中所有具体数字"""
    numbers = []
    for ntype, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(1)
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 10)
            context = text[start:end]
            numbers.append({
                "type": ntype,
                "value": value,
                "full_match": match.group(0),
                "context": f"...{context}...",
                "position": match.start(),
                "verified": False,
                "suspicious": False,
            })
    return numbers


def load_source_data(source_file):
    """加载原始热榜数据用于对比"""
    if not source_file or not os.path.exists(source_file):
        return None
    with open(source_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_against_source(numbers, source_data):
    """与原始数据对比"""
    if not source_data:
        return
    
    # 将原始数据中的所有文本拼接为一个大字符串
    source_text = json.dumps(source_data, ensure_ascii=False)
    
    for num in numbers:
        # 如果数字出现在原始数据中，标记为已验证
        if num["value"] in source_text:
            num["verified"] = True


def mark_suspicious(numbers):
    """标记可疑数字"""
    for num in numbers:
        if num["verified"]:
            continue
        
        # 高精确度数字（如 37.8%、1.23亿）更可能是编造的
        value = num["value"]
        if '.' in value:
            num["suspicious"] = True
            num["reason"] = "高精确度数字，不在原始数据中"
        
        # 百分比超过95%或低于5%的极端值
        if num["type"] == "百分比":
            pct = float(value)
            if pct > 95 or pct < 1:
                num["suspicious"] = True
                num["reason"] = f"极端百分比({value}%)"


def main():
    parser = argparse.ArgumentParser(description="数字校验脚本")
    parser.add_argument("file", nargs="?", help="文章文件路径")
    parser.add_argument("--stdin", action="store_true", help="从stdin读取")
    parser.add_argument("--source", help="原始热榜数据文件（用于对比）")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()
    
    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        parser.print_help()
        sys.exit(2)
    
    # 提取数字
    numbers = extract_numbers(text)
    
    if not numbers:
        if args.json:
            print(json.dumps({"total": 0, "verified": 0, "suspicious": 0, "numbers": []}, ensure_ascii=False))
        else:
            print("✅ 文章中无具体数字（安全）")
        sys.exit(0)
    
    # 加载原始数据对比
    source_data = load_source_data(args.source)
    verify_against_source(numbers, source_data)
    mark_suspicious(numbers)
    
    verified = [n for n in numbers if n["verified"]]
    suspicious = [n for n in numbers if n["suspicious"]]
    unverified = [n for n in numbers if not n["verified"] and not n["suspicious"]]
    
    if args.json:
        result = {
            "total": len(numbers),
            "verified": len(verified),
            "suspicious": len(suspicious),
            "unverified": len(unverified),
            "numbers": numbers,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"📊 数字扫描结果：共 {len(numbers)} 个数字")
        print()
        
        if verified:
            print(f"  ✅ 已验证: {len(verified)} 个")
            for n in verified:
                print(f"    {n['full_match']} — {n['context']}")
        
        if suspicious:
            print(f"  ❌ 可疑编造: {len(suspicious)} 个")
            for n in suspicious:
                print(f"    {n['full_match']} — {n.get('reason', '不在原始数据中')}")
                print(f"      上下文: {n['context']}")
        
        if unverified:
            print(f"  ⚠️ 未验证: {len(unverified)} 个")
            for n in unverified:
                print(f"    {n['full_match']} — {n['context']}")
        
        if suspicious:
            print()
            print("💡 建议：将可疑数字改为「据报道」「有数据显示」或删除")
            sys.exit(1)
    
    sys.exit(0 if not suspicious else 1)


if __name__ == "__main__":
    main()
