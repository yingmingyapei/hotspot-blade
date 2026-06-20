#!/usr/bin/env python3
"""
退役句式扫描器 v2.0 — 从统一禁用语清单读取规则
单一信源：references/banned-phrases-data.json

用法:
  echo "文章内容" | python3 retired-phrase-scanner.py
  python3 retired-phrase-scanner.py <file>
  python3 retired-phrase-scanner.py --strict <file>    # 严格模式（含频率检查）
"""
import sys
import os
import re
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "..", "references", "banned-phrases-data.json")

def load_rules():
    """从统一JSON数据文件加载禁用规则"""
    if not os.path.exists(DATA_FILE):
        print(f"⚠️ 数据文件不存在: {DATA_FILE}")
        print("请确保 banned-phrases-data.json 在 hotspot-blade/references/ 下")
        sys.exit(2)
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def scan_text(text, rules, strict=False):
    """扫描文本中的禁用语"""
    findings = []
    
    # 1. 禁止词精确匹配
    for phrase in rules.get("banned_words", []):
        if phrase in text:
            idx = text.find(phrase)
            start = max(0, idx - 15)
            end = min(len(text), idx + len(phrase) + 15)
            context = text[start:end]
            findings.append({
                "type": "禁止词",
                "phrase": phrase,
                "context": f"...{context}...",
                "severity": "error"
            })
    
    # 2. 禁止句式正则匹配
    for pattern in rules.get("banned_sentence_patterns", []):
        matches = re.findall(pattern, text)
        for match in matches:
            findings.append({
                "type": "禁止句式",
                "phrase": match if isinstance(match, str) else pattern,
                "context": match if isinstance(match, str) else "",
                "severity": "error"
            })
    
    # 3. 退役组合句式
    for pattern in rules.get("retired_combos", []):
        matches = re.findall(pattern, text)
        for match in matches:
            findings.append({
                "type": "退役组合",
                "phrase": match,
                "context": match,
                "severity": "warning"
            })
    
    # 4. 频率检查（strict模式）
    if strict:
        for pattern, limit in rules.get("frequency_limits", {}).items():
            count = len(re.findall(pattern, text))
            if count > limit:
                findings.append({
                    "type": "频率超限",
                    "phrase": f"{pattern}（{count}次，限制{limit}次）",
                    "context": "",
                    "severity": "warning"
                })
    
    return findings

def main():
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    
    if args:
        with open(args[0], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    
    rules = load_rules()
    findings = scan_text(text, rules, strict=strict)
    
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    
    if findings:
        if errors:
            print(f"❌ 发现 {len(errors)} 处禁用语（必须修改）：")
            for f in errors:
                print(f"  [{f['type']}] 「{f['phrase']}」")
                if f['context']:
                    print(f"    上下文: {f['context']}")
            print()
        
        if warnings:
            print(f"⚠️ 发现 {len(warnings)} 处警告（建议修改）：")
            for f in warnings:
                print(f"  [{f['type']}] 「{f['phrase']}」")
            print()
        
        print(f"共发现 {len(findings)} 处问题（{len(errors)} 错误 + {len(warnings)} 警告）")
        sys.exit(1 if errors else 0)
    else:
        print("✅ 禁用语检查通过")
        sys.exit(0)

if __name__ == "__main__":
    main()
