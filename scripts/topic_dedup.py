#!/usr/bin/env python3
"""
话题去重脚本 v1.0 — simhash + SHA256 硬去重
热点刀锋 P0 核心脚本：不走LLM，0 token，0误判。

原理：
1. SHA256 哈希精确匹配（完全相同标题）
2. simhash 近似匹配（相似标题，如"金价暴跌" vs "金价大跌"）
3. history.json 记录已写话题的哈希

用法:
  python3 topic_dedup.py --check "新话题标题"
  python3 topic_dedup.py --check-file /tmp/topics.json
  python3 topic_dedup.py --add "已写话题标题"
  python3 topic_dedup.py --list
  python3 topic_dedup.py --stats
"""
import sys
import os
import json
import hashlib
import re
import argparse
from datetime import datetime, timedelta

HISTORY_FILE = os.path.expanduser(
    "~/.hermes/skills/productivity/hotspot-blade/hotspot-blade-history.json"
)

# simhash 配置
SIMHASH_BITS = 64
SIMHASH_THRESHOLD = 3  # 汉明距离 <= 3 视为相似


def load_history():
    """加载历史话题库"""
    if not os.path.exists(HISTORY_FILE):
        return {"last_updated": "", "topics": []}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_history(data):
    """保存历史话题库"""
    data["last_updated"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sha256_hash(text):
    """SHA256 精确哈希"""
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()


def tokenize_chinese(text):
    """简易中文分词：按字+数字+英文切分"""
    tokens = []
    current = []
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            if current:
                tokens.append(''.join(current))
                current = []
            tokens.append(ch)
        elif ch.isalnum():
            current.append(ch)
        else:
            if current:
                tokens.append(''.join(current))
                current = []
    if current:
        tokens.append(''.join(current))
    return tokens


def simhash(text, bits=SIMHASH_BITS):
    """计算 simhash 值"""
    tokens = tokenize_chinese(text)
    if not tokens:
        return 0

    v = [0] * bits
    for token in tokens:
        h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
        for i in range(bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint


def hamming_distance(h1, h2):
    """计算两个 simhash 的汉明距离"""
    x = h1 ^ h2
    count = 0
    while x:
        count += 1
        x &= x - 1
    return count


def normalize_title(title):
    """标题归一化：去标点、去空格、小写"""
    title = re.sub(r'[，。！？、；：""''（）\s]+', '', title)
    title = title.lower()
    return title


def check_duplicate(title, history, threshold=SIMHASH_THRESHOLD):
    """
    检查标题是否与历史重复
    返回: (is_dup, method, detail)
    """
    norm = normalize_title(title)
    sha = sha256_hash(norm)
    sh = simhash(norm)

    for entry in history.get("topics", []):
        hist_sha = entry.get("sha256", "")
        hist_sh = entry.get("simhash", 0)

        # 精确匹配
        if sha == hist_sha:
            return True, "exact", f"与「{entry.get('title', '?')}」完全相同"

        # simhash 近似匹配
        if hist_sh and sh:
            dist = hamming_distance(sh, hist_sh)
            if dist <= threshold:
                return True, "similar", f"与「{entry.get('title', '?')}」相似（汉明距离{dist}）"

    return False, None, None


def add_topic(title, history):
    """添加话题到历史库"""
    norm = normalize_title(title)
    entry = {
        "title": title.strip(),
        "sha256": sha256_hash(norm),
        "simhash": simhash(norm),
        "added_at": datetime.now().isoformat(),
    }
    history.setdefault("topics", []).append(entry)
    return entry


def prune_old(history, days=7):
    """清理超过 N 天的旧记录"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    before = len(history.get("topics", []))
    history["topics"] = [
        t for t in history.get("topics", [])
        if t.get("added_at", "") > cutoff
    ]
    after = len(history["topics"])
    return before - after


def main():
    parser = argparse.ArgumentParser(description="话题去重脚本（simhash + SHA256）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="TITLE", help="检查单个标题是否重复")
    group.add_argument("--check-file", metavar="FILE", help="检查JSON文件中的话题列表")
    group.add_argument("--add", metavar="TITLE", help="添加标题到历史库")
    group.add_argument("--list", action="store_true", help="列出历史话题")
    group.add_argument("--stats", action="store_true", help="显示统计信息")
    group.add_argument("--prune", type=int, metavar="DAYS", help="清理超过N天的旧记录")
    parser.add_argument("--threshold", type=int, default=SIMHASH_THRESHOLD, help="simhash汉明距离阈值")
    args = parser.parse_args()

    history = load_history()

    if args.check:
        is_dup, method, detail = check_duplicate(args.check, history, args.threshold)
        if is_dup:
            print(f"❌ 重复（{method}）: {detail}")
            sys.exit(1)
        else:
            print(f"✅ 不重复: 「{args.check}」")
            sys.exit(0)

    elif args.check_file:
        with open(args.check_file, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        if isinstance(topics, dict):
            topics = topics.get("topics", [])
        dupes = []
        for t in topics:
            title = t if isinstance(t, str) else t.get("title", "")
            is_dup, method, detail = check_duplicate(title, history, args.threshold)
            if is_dup:
                dupes.append({"title": title, "method": method, "detail": detail})
        if dupes:
            print(f"❌ 发现 {len(dupes)} 个重复话题：")
            for d in dupes:
                print(f"  「{d['title']}」 — {d['detail']}")
            sys.exit(1)
        else:
            print(f"✅ {len(topics)} 个话题全部不重复")
            sys.exit(0)

    elif args.add:
        entry = add_topic(args.add, history)
        save_history(history)
        print(f"✅ 已添加: 「{args.add}」")
        print(f"   SHA256: {entry['sha256'][:16]}...")
        print(f"   SimHash: {entry['simhash']}")
        sys.exit(0)

    elif args.list:
        topics = history.get("topics", [])
        if not topics:
            print("📭 历史库为空")
        else:
            print(f"📋 历史话题（{len(topics)} 条）：")
            for i, t in enumerate(topics[-20:], 1):  # 最近20条
                added = t.get("added_at", "?")[:10]
                print(f"  {i}. [{added}] {t.get('title', '?')}")
        sys.exit(0)

    elif args.stats:
        topics = history.get("topics", [])
        print(f"📊 去重库统计：")
        print(f"  总话题数: {len(topics)}")
        if topics:
            dates = [t.get("added_at", "")[:10] for t in topics]
            print(f"  最早: {min(dates)}")
            print(f"  最新: {max(dates)}")
            print(f"  更新时间: {history.get('last_updated', '?')}")
        sys.exit(0)

    elif args.prune is not None:
        removed = prune_old(history, args.prune)
        save_history(history)
        print(f"🧹 已清理 {removed} 条超过 {args.prune} 天的旧记录")
        sys.exit(0)


if __name__ == "__main__":
    main()
