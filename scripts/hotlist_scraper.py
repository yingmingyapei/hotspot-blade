#!/usr/bin/env python3
"""
hotlist_scraper.py v2.0 — 热点刀锋热榜抓取脚本
使用 curl_cffi（浏览器指纹模拟）替代 curl+Cookie，解决 Cookie 过期问题。

核心改进（v2.0）：
- curl_cffi impersonate="chrome" 模拟浏览器 TLS 指纹，无需 Cookie
- Cookie 文件作为 fallback（需要登录态的平台）
- 自动重试（2次）
- 更好的错误处理

用法：
  python3 hotlist_scraper.py              # 抓取所有平台
  python3 hotlist_scraper.py --platform zhihu  # 只抓知乎
  python3 hotlist_scraper.py --platform bilibili  # 只抓B站
  python3 hotlist_scraper.py --limit 20   # 每平台最多20条
  python3 hotlist_scraper.py --json       # 输出JSON格式
  python3 hotlist_scraper.py --legacy     # 用旧版curl+Cookie（fallback）
"""

import json
import subprocess
import sys
import os
import argparse
import time
from datetime import datetime

COOKIE_FILE = os.path.expanduser("~/.hermes/cookies/hotlist-cookies.json")
IMPERSONATE = "chrome"  # curl_cffi 浏览器指纹
MAX_RETRIES = 2
RETRY_DELAY = 1  # 秒

# ─────────────────────────────────────────
# curl_cffi HTTP 客户端
# ─────────────────────────────────────────

_session = None

def get_session():
    """获取 curl_cffi session（延迟初始化）"""
    global _session
    if _session is None:
        try:
            from curl_cffi.requests import Session
            _session = Session(impersonate=IMPERSONATE)
        except ImportError:
            print("❌ curl_cffi 未安装，使用 --legacy 模式", file=sys.stderr)
            return None
    return _session


def http_get(url, cookie="", referer="", extra_headers=None, timeout=15):
    """curl_cffi GET 请求（带重试）"""
    session = get_session()
    if session is None:
        return None

    headers = {
        "Referer": referer or url,
    }
    if cookie:
        headers["Cookie"] = cookie
    if extra_headers:
        headers.update(extra_headers)

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return None
            elif resp.status_code == 403:
                # Cloudflare 挑战，等待后重试
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
            else:
                return None
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


def http_post(url, data=None, cookie="", referer="", extra_headers=None, timeout=15):
    """curl_cffi POST 请求（带重试）"""
    session = get_session()
    if session is None:
        return None

    headers = {
        "Referer": referer or url,
        "Content-Type": "application/json",
    }
    if cookie:
        headers["Cookie"] = cookie
    if extra_headers:
        headers.update(extra_headers)

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.post(url, headers=headers, json=data, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return None
            elif attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            else:
                return None
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


# ─────────────────────────────────────────
# 旧版 curl+Cookie（--legacy 模式）
# ─────────────────────────────────────────

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def load_cookies():
    """从配置文件加载各平台Cookie"""
    if not os.path.exists(COOKIE_FILE):
        return {}
    with open(COOKIE_FILE, 'r') as f:
        return json.load(f)

def legacy_curl_get(url, cookie="", referer="", extra_headers=None, timeout=15):
    """旧版curl GET请求"""
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

def fetch_zhihu(cookies, limit=50, legacy=False):
    """知乎热榜"""
    cookie = cookies.get("zhihu", "")
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
    if legacy:
        data = legacy_curl_get(url, cookie=cookie, referer="https://www.zhihu.com/hot")
    else:
        data = http_get(url, cookie=cookie, referer="https://www.zhihu.com/hot")

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


def fetch_weibo(cookies, limit=50, legacy=False):
    """微博热搜"""
    cookie = cookies.get("weibo", "")
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {"X-XSRF-TOKEN": "ZkZp4a3bU7varFmwZhUpAxZa"}
    if legacy:
        data = legacy_curl_get(url, cookie=cookie, referer="https://weibo.com", extra_headers=headers)
    else:
        data = http_get(url, cookie=cookie, referer="https://weibo.com", extra_headers=headers)

    if not data or data.get("ok") != 1:
        return {"platform": "weibo", "error": "请求失败", "items": []}

    items = []
    for i, item in enumerate(data["data"].get("realtime", [])[:limit]):
        label = item.get("label_name", "")
        num = item.get("num", 0)
        items.append({
            "rank": item.get("realpos", i + 1),
            "title": item.get("word", ""),
            "heat": f'{num // 10000}万' if num >= 10000 else str(num),
            "label": label,
            "is_ad": item.get("is_ad", 0),
            "url": "https://s.weibo.com/weibo?q=%23" + item.get("word", "") + "%23"
        })
    return {"platform": "weibo", "count": len(items), "items": items}


def fetch_bilibili(cookies, limit=50, legacy=False):
    """B站热门"""
    cookie = cookies.get("bilibili", "")
    url = "https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1"
    if legacy:
        data = legacy_curl_get(url, cookie=cookie, referer="https://www.bilibili.com")
    else:
        data = http_get(url, cookie=cookie, referer="https://www.bilibili.com")

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


def fetch_36kr(cookies, limit=50, legacy=False):
    """36氪热榜（POST请求）
    注意：36氪gateway对curl_cffi的impersonate有兼容问题，默认用legacy模式。
    """
    cookie = cookies.get("36kr", "")
    url = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
    payload = {"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}}

    # 36氪优先用legacy（curl_cffi连接该API不稳定）
    cmd = [
        "curl", "-s", "--max-time", "15", "-X", "POST",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", f"Cookie: {cookie}",
        "-H", "Referer: https://36kr.com/",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        url
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


def fetch_baidu(cookies=None, limit=50, legacy=False):
    """百度热搜（无需Cookie）"""
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    if legacy:
        data = legacy_curl_get(url, referer="https://top.baidu.com")
    else:
        data = http_get(url, referer="https://top.baidu.com")

    if not data or "data" not in data:
        return {"platform": "baidu", "error": "请求失败", "items": []}

    items = []
    items_raw = data["data"].get("cards", [{}])[0].get("content", [])
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
    "baidu": {"name": "百度热搜", "fetch": "baidu", "needs_cookie": False},
}

FETCH_MAP = {
    "zhihu": fetch_zhihu,
    "weibo": fetch_weibo,
    "bilibili": fetch_bilibili,
    "36kr": fetch_36kr,
    "baidu": fetch_baidu,
}


def main():
    parser = argparse.ArgumentParser(description="热点刀锋热榜抓取 v2.0 (curl_cffi)")
    parser.add_argument("--platform", "-p", help="指定平台 (zhihu/weibo/bilibili/36kr/baidu)")
    parser.add_argument("--limit", "-l", type=int, default=50, help="每平台最多条数")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--all", action="store_true", help="抓取所有平台")
    parser.add_argument("--legacy", action="store_true", help="使用旧版curl+Cookie模式")
    args = parser.parse_args()

    # 加载Cookie（curl_cffi模式下作为可选fallback）
    cookies = load_cookies()

    # 确定要抓取的平台
    if args.platform:
        platforms_to_fetch = [args.platform]
    else:
        platforms_to_fetch = ["zhihu", "weibo", "bilibili", "36kr", "baidu"]

    # 检查 curl_cffi 可用性
    if not args.legacy:
        try:
            from curl_cffi.requests import Session
            print("📡 使用 curl_cffi（浏览器指纹模拟）", file=sys.stderr)
        except ImportError:
            print("⚠️ curl_cffi 不可用，自动切换到 --legacy 模式", file=sys.stderr)
            args.legacy = True
    else:
        print("📡 使用旧版 curl+Cookie 模式", file=sys.stderr)

    results = {}
    success_count = 0

    for platform in platforms_to_fetch:
        if platform not in FETCH_MAP:
            print(f"❌ 未知平台: {platform}", file=sys.stderr)
            continue

        info = PLATFORMS[platform]
        print(f"📡 抓取 {info['name']}...", file=sys.stderr)

        fetch_fn = FETCH_MAP[platform]
        result = fetch_fn(cookies, limit=args.limit, legacy=args.legacy)

        # curl_cffi 失败时自动 fallback 到 legacy 模式
        if not args.legacy and result.get("error"):
            print(f"  ⚠️ curl_cffi 失败，自动用 legacy 模式重试...", file=sys.stderr)
            result = fetch_fn(cookies, limit=args.limit, legacy=True)

        results[platform] = result

        if result.get("error"):
            print(f"  ❌ {result['error']}", file=sys.stderr)
        else:
            print(f"  ✅ 获取 {result['count']} 条", file=sys.stderr)
            success_count += 1

    # 输出摘要
    total_platforms = len(platforms_to_fetch)
    print(f"\n📊 采集完成: {success_count}/{total_platforms} 个平台成功", file=sys.stderr)

    # 输出结果
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for platform, result in results.items():
            info = PLATFORMS[platform]
            print(f"\n{'=' * 60}")
            print(f"  {info['name']} ({result.get('count', 0)} 条)")
            print(f"{'=' * 60}")

            if result.get("error"):
                print(f"  ❌ 错误: {result['error']}")
                continue

            for item in result["items"]:
                rank = item.get("rank", "?")
                title = item.get("title", "")

                if platform == "bilibili":
                    view = item.get("view", 0)
                    view_str = f"{view / 10000:.1f}万" if view >= 10000 else str(view)
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
                    read_str = f"{read / 10000:.1f}万" if read >= 10000 else str(read)
                    author = item.get("author", "")
                    print(f"  {rank:2d}. {title}")
                    print(f"      作者:{author} | 阅读:{read_str} | 点赞:{item.get('like', 0)}")
                else:
                    print(f"  {rank:2d}. {title}")
                print()


if __name__ == "__main__":
    main()
