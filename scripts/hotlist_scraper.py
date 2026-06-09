#!/usr/bin/env python3
"""
hotlist_scraper.py — 热点刀锋热榜抓取脚本
替代 opencli，使用 curl + Cookie + Python 直接调用各平台 API。

用法：
  python3 hotlist_scraper.py              # 抓取所有平台
  python3 hotlist_scraper.py --platform zhihu  # 只抓知乎
  python3 hotlist_scraper.py --platform bilibili  # 只抓B站
  python3 hotlist_scraper.py --limit 20   # 每平台最多20条
  python3 hotlist_scraper.py --json       # 输出JSON格式
"""

import json
import subprocess
import sys
import os
import argparse
from datetime import datetime

COOKIE_FILE = os.path.expanduser("~/.hermes/cookies/hotlist-cookies.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def load_cookies():
    """从配置文件加载各平台Cookie"""
    with open(COOKIE_FILE, 'r') as f:
        return json.load(f)

def curl_get(url, cookie="", referer="", extra_headers=None, timeout=15):
    """通用curl GET请求"""
    cmd = [
        "curl", "-s", "--max-time", str(timeout),
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", f"Cookie: {cookie}",
        "-H", f"Referer: {referer}",
    ]
    if extra_headers:
        for k, v in extra_headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

# ─────────────────────────────────────────
# 平台抓取函数
# ─────────────────────────────────────────

def fetch_zhihu(cookies, limit=50):
    """知乎热榜"""
    cookie = cookies.get("zhihu", "")
    data = curl_get(
        "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
        cookie=cookie,
        referer="https://www.zhihu.com/hot"
    )
    if not data or "data" not in data:
        return {"platform": "zhihu", "error": "请求失败", "items": []}
    
    items = []
    for i, item in enumerate(data["data"][:limit]):
        target = item.get("target", {})
        items.append({
            "rank": i + 1,
            "title": target.get("title", ""),
            "heat": item.get("detail_text", ""),
            "answer_count": target.get("answer_count", 0),
            "follower_count": target.get("follower_count", 0),
            "excerpt": target.get("excerpt", "")[:100],
            "url": f"https://www.zhihu.com/question/{target.get('id', '')}"
        })
    return {"platform": "zhihu", "count": len(items), "items": items}

def fetch_weibo(cookies, limit=50):
    """微博热搜"""
    cookie = cookies.get("weibo", "")
    data = curl_get(
        "https://weibo.com/ajax/side/hotSearch",
        cookie=cookie,
        referer="https://weibo.com",
        extra_headers={"X-XSRF-TOKEN": "ZkZp4a3bU7varFmwZhUpAxZa"}
    )
    if not data or data.get("ok") != 1:
        return {"platform": "weibo", "error": "请求失败", "items": []}
    
    items = []
    for i, item in enumerate(data["data"].get("realtime", [])[:limit]):
        label = item.get("label_name", "")
        items.append({
            "rank": item.get("realpos", i + 1),
            "title": item.get("word", ""),
            "heat": f'{item.get("num", 0)//10000}万' if item.get("num", 0) >= 10000 else str(item.get("num", 0)),
            "label": label,
            "is_ad": item.get("is_ad", 0),
            "url": "https://s.weibo.com/weibo?q=%23" + item.get("word", "") + "%23"
        })
    return {"platform": "weibo", "count": len(items), "items": items}

def fetch_bilibili(cookies, limit=50):
    """B站热门"""
    cookie = cookies.get("bilibili", "")
    data = curl_get(
        "https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1",
        cookie=cookie,
        referer="https://www.bilibili.com"
    )
    if not data or data.get("code") != 0:
        return {"platform": "bilibili", "error": "请求失败", "items": []}
    
    items = []
    for i, item in enumerate(data["data"]["list"][:limit]):
        stat = item.get("stat", {})
        items.append({
            "rank": i + 1,
            "title": item.get("title", ""),
            "author": item.get("owner", {}).get("name", ""),
            "tname": item.get("tname", ""),
            "view": stat.get("view", 0),
            "danmaku": stat.get("danmaku", 0),
            "like": stat.get("like", 0),
            "reply": stat.get("reply", 0),
            "duration": item.get("duration", 0),
            "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}"
        })
    return {"platform": "bilibili", "count": len(items), "items": items}

def fetch_toutiao(cookies=None, limit=50):
    """今日头条热榜（无需Cookie）"""
    data = curl_get(
        "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
        referer="https://www.toutiao.com"
    )
    if not data or "data" not in data:
        return {"platform": "toutiao", "error": "请求失败", "items": []}
    
    items = []
    for i, item in enumerate(data["data"][:limit]):
        items.append({
            "rank": i + 1,
            "title": item.get("Title", ""),
            "heat": item.get("HotValue", ""),
            "url": item.get("Url", "")
        })
    return {"platform": "toutiao", "count": len(items), "items": items}

def fetch_36kr(cookies, limit=50):
    """36氪热榜"""
    cookie = cookies.get("36kr", "")
    # 36氪热榜用 POST 请求
    cmd = [
        "curl", "-s", "--max-time", "15",
        "-X", "POST",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", f"Cookie: {cookie}",
        "-H", "Referer: https://36kr.com/",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}}),
        "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"platform": "36kr", "error": "请求失败", "items": []}

    if data.get("code") != 0:
        return {"platform": "36kr", "error": f"API错误: {data.get('code')}", "items": []}

    hot_list = data.get("data", {}).get("hotRankList", [])
    items = []
    for i, item in enumerate(hot_list[:limit]):
        mat = item.get("templateMaterial", {})
        items.append({
            "rank": i + 1,
            "title": mat.get("widgetTitle", ""),
            "author": mat.get("authorName", ""),
            "read": mat.get("statRead", 0),
            "like": mat.get("statPraise", 0),
            "collect": mat.get("statCollect", 0),
            "comment": mat.get("statComment", 0),
            "url": f"https://36kr.com/p/{mat.get('itemId', '')}"
        })
    return {"platform": "36kr", "count": len(items), "items": items}

def fetch_baidu(cookies=None, limit=50):
    """百度热搜（无需Cookie）"""
    data = curl_get(
        "https://top.baidu.com/board?tab=realtime",
        referer="https://top.baidu.com"
    )
    # 百度热搜返回HTML，需要用不同方式解析
    # 这里用API接口
    data = curl_get(
        "https://top.baidu.com/api/board?platform=wise&tab=realtime",
        referer="https://top.baidu.com"
    )
    if not data or "data" not in data:
        return {"platform": "baidu", "error": "请求失败", "items": []}
    
    items = []
    items_raw = data["data"].get("cards", [{}])[0].get("content", [])
    # 百度API嵌套：cards[0].content[0].content才是实际条目
    if items_raw and isinstance(items_raw[0], dict) and "content" in items_raw[0]:
        items_raw = items_raw[0]["content"]
    
    for i, item in enumerate(items_raw[:limit]):
        items.append({
            "rank": i + 1,
            "title": item.get("word", ""),
            "heat": item.get("hotScore", ""),
            "desc": item.get("desc", "")[:100],
            "url": item.get("url", "")
        })
    return {"platform": "baidu", "count": len(items), "items": items}

# ─────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────

PLATFORMS = {
    "zhihu": {"name": "知乎热榜", "fetch": "zhihu", "needs_cookie": True},
    "weibo": {"name": "微博热搜", "fetch": "weibo", "needs_cookie": True},
    "bilibili": {"name": "B站热门", "fetch": "bilibili", "needs_cookie": True},
    "36kr": {"name": "36氪热榜", "fetch": "36kr", "needs_cookie": False},
    "toutiao": {"name": "头条热榜", "fetch": "toutiao", "needs_cookie": False},
    "baidu": {"name": "百度热搜", "fetch": "baidu", "needs_cookie": False},
}

FETCH_MAP = {
    "zhihu": fetch_zhihu,
    "weibo": fetch_weibo,
    "bilibili": fetch_bilibili,
    "36kr": fetch_36kr,
    "toutiao": fetch_toutiao,
    "baidu": fetch_baidu,
}

def main():
    parser = argparse.ArgumentParser(description="热点刀锋热榜抓取")
    parser.add_argument("--platform", "-p", help="指定平台 (zhihu/weibo/bilibili/36kr/toutiao/baidu)")
    parser.add_argument("--limit", "-l", type=int, default=50, help="每平台最多条数")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--all", action="store_true", help="抓取所有平台")
    args = parser.parse_args()
    
    # 加载Cookie
    cookies = {}
    if os.path.exists(COOKIE_FILE):
        cookies = load_cookies()
    else:
        print(f"⚠️ Cookie文件不存在: {COOKIE_FILE}", file=sys.stderr)
    
    # 确定要抓取的平台
    if args.platform:
        platforms_to_fetch = [args.platform]
    else:
        platforms_to_fetch = ["zhihu", "weibo", "bilibili", "36kr", "toutiao", "baidu"]
    
    results = {}
    for platform in platforms_to_fetch:
        if platform not in FETCH_MAP:
            print(f"❌ 未知平台: {platform}", file=sys.stderr)
            continue
        
        info = PLATFORMS[platform]
        print(f"📡 抓取 {info['name']}...", file=sys.stderr)
        
        fetch_fn = FETCH_MAP[platform]
        result = fetch_fn(cookies, limit=args.limit)
        
        results[platform] = result
        
        if result.get("error"):
            print(f"  ❌ {result['error']}", file=sys.stderr)
        else:
            print(f"  ✅ 获取 {result['count']} 条", file=sys.stderr)
    
    # 输出结果
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for platform, result in results.items():
            info = PLATFORMS[platform]
            print(f"\n{'='*60}")
            print(f"  {info['name']} ({result.get('count', 0)} 条)")
            print(f"{'='*60}")
            
            if result.get("error"):
                print(f"  ❌ 错误: {result['error']}")
                continue
            
            for item in result["items"]:
                rank = item.get("rank", "?")
                title = item.get("title", "")
                
                if platform == "bilibili":
                    view = item.get("view", 0)
                    view_str = f"{view/10000:.1f}万" if view >= 10000 else str(view)
                    author = item.get("author", "")
                    tname = item.get("tname", "")
                    print(f"  {rank:2d}. [{tname}] {title}")
                    print(f"      UP主:{author} | 播放:{view_str} | 评论:{item.get('reply', 0)}")
                elif platform == "zhihu":
                    print(f"  {rank:2d}. {title} [{item.get('heat', '')}]")
                    print(f"      回答:{item.get('answer_count', 0)} | 关注:{item.get('follower_count', 0)}")
                elif platform == "weibo":
                    label = item.get("label", "")
                    label_str = f"[{label}]" if label else ""
                    print(f"  {rank:2d}. {label_str} {title} ({item.get('heat', '')})")
                elif platform == "36kr":
                    read = item.get("read", 0)
                    read_str = f"{read/10000:.1f}万" if read >= 10000 else str(read)
                    author = item.get("author", "")
                    print(f"  {rank:2d}. {title}")
                    print(f"      作者:{author} | 阅读:{read_str} | 点赞:{item.get('like', 0)}")
                else:
                    print(f"  {rank:2d}. {title}")
                print()

if __name__ == "__main__":
    main()
