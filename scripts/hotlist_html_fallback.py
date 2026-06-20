#!/usr/bin/env python3
"""
热榜 HTML Fallback 抓取模板 v1.0
当某平台 JSON API 不可用时，用 curl_cffi + 正则 从 HTML 页面提取热榜数据。

使用条件：
- 某平台 API 返回空数据或 403/429
- curl_cffi JSON 模式失败
- 需要从 HTML 页面解析热榜

用法（作为模块导入）：
  from hotlist_html_fallback import fetch_zhihu_html, fetch_weibo_html, ...

用法（独立运行）：
  python3 hotlist_html_fallback.py --platform zhihu --limit 10
  python3 hotlist_html_fallback.py --platform weibo --limit 10 --json
"""

import json
import re
import sys
import argparse

try:
    from curl_cffi.requests import Session
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False


def get_session():
    if not HAS_CURL_CFFI:
        print("❌ curl_cffi 未安装", file=sys.stderr)
        return None
    return Session(impersonate="chrome")


# ─────────────────────────────────────────
# 平台 HTML 解析函数
# ─────────────────────────────────────────

def fetch_zhihu_html(limit=50):
    """知乎热榜 — 从HTML页面解析（API不可用时的fallback）"""
    session = get_session()
    if not session:
        return {"platform": "zhihu", "error": "curl_cffi不可用", "items": []}

    try:
        resp = session.get("https://www.zhihu.com/hot", timeout=15)
        if resp.status_code != 200:
            return {"platform": "zhihu", "error": f"HTTP {resp.status_code}", "items": []}

        # 知乎热榜页面有 SSR 的 JSON 数据
        match = re.search(r'<script id="js-initialData"[^>]*>(.*?)</script>', resp.text)
        if match:
            data = json.loads(match.group(1))
            # 知乎 initialData 结构复杂，尝试多种路径
            hot_list = (
                data.get("initialState", {}).get("topstory", {}).get("hotList", [])
                or data.get("initialState", {}).get("entities", {}).get("feeds", {})
            )
            if isinstance(hot_list, list):
                items = []
                for i, item in enumerate(hot_list[:limit]):
                    target = item.get("target", {})
                    items.append({
                        "rank": i + 1,
                        "title": target.get("titleArea", {}).get("text", ""),
                        "heat": target.get("metricsArea", {}).get("text", ""),
                        "excerpt": target.get("excerptArea", {}).get("text", "")[:100],
                        "url": target.get("link", {}).get("url", ""),
                    })
                if items:
                    return {"platform": "zhihu", "count": len(items), "items": items, "source": "html_fallback"}

        return {"platform": "zhihu", "error": "HTML解析失败", "items": []}
    except Exception as e:
        return {"platform": "zhihu", "error": str(e), "items": []}


def fetch_weibo_html(limit=50):
    """微博热搜 — 从HTML页面解析"""
    session = get_session()
    if not session:
        return {"platform": "weibo", "error": "curl_cffi不可用", "items": []}

    try:
        resp = session.get("https://s.weibo.com/top/summary", timeout=15)
        if resp.status_code != 200:
            return {"platform": "weibo", "error": f"HTTP {resp.status_code}", "items": []}

        # 微博热搜榜 HTML: <a href="/weibo?q=...">标题</a>
        pattern = r'<td class="td-02">\s*<a[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, resp.text)

        items = []
        for i, title in enumerate(matches[:limit]):
            title = title.strip()
            if title and title != "热搜排序":
                items.append({
                    "rank": i + 1,
                    "title": title,
                    "heat": "",
                    "url": f"https://s.weibo.com/weibo?q=%23{title}%23",
                })

        if items:
            return {"platform": "weibo", "count": len(items), "items": items, "source": "html_fallback"}
        return {"platform": "weibo", "error": "HTML解析失败", "items": []}
    except Exception as e:
        return {"platform": "weibo", "error": str(e), "items": []}


def fetch_bilibili_html(limit=50):
    """B站热门 — 从HTML页面解析"""
    session = get_session()
    if not session:
        return {"platform": "bilibili", "error": "curl_cffi不可用", "items": []}

    try:
        resp = session.get("https://www.bilibili.com/v/popular/all", timeout=15)
        if resp.status_code != 200:
            return {"platform": "bilibili", "error": f"HTTP {resp.status_code}", "items": []}

        # B站热门页面有 SSR 数据
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*\(function', resp.text)
        if match:
            data = json.loads(match.group(1))
            video_list = data.get("popularList", {}).get("list", [])
            items = []
            for i, item in enumerate(video_list[:limit]):
                stat = item.get("stat", {})
                items.append({
                    "rank": i + 1,
                    "title": item.get("title", ""),
                    "author": item.get("owner", {}).get("name", ""),
                    "view": stat.get("view", 0),
                    "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                })
            if items:
                return {"platform": "bilibili", "count": len(items), "items": items, "source": "html_fallback"}

        return {"platform": "bilibili", "error": "HTML解析失败", "items": []}
    except Exception as e:
        return {"platform": "bilibili", "error": str(e), "items": []}


def fetch_baidu_html(limit=50):
    """百度热搜 — 从HTML页面解析"""
    session = get_session()
    if not session:
        return {"platform": "baidu", "error": "curl_cffi不可用", "items": []}

    try:
        resp = session.get("https://top.baidu.com/board?tab=realtime", timeout=15)
        if resp.status_code != 200:
            return {"platform": "baidu", "error": f"HTTP {resp.status_code}", "items": []}

        # 百度热搜页面有 SSR JSON
        match = re.search(r'<!--s-data:(.*?)-->', resp.text)
        if match:
            data = json.loads(match.group(1))
            cards = data.get("data", {}).get("cards", [])
            if cards:
                content = cards[0].get("content", [])
                items = []
                for i, item in enumerate(content[:limit]):
                    items.append({
                        "rank": i + 1,
                        "title": item.get("word", ""),
                        "heat": item.get("hotScore", ""),
                        "desc": item.get("desc", "")[:100],
                        "url": item.get("url", ""),
                    })
                if items:
                    return {"platform": "baidu", "count": len(items), "items": items, "source": "html_fallback"}

        return {"platform": "baidu", "error": "HTML解析失败", "items": []}
    except Exception as e:
        return {"platform": "baidu", "error": str(e), "items": []}


# ─────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────

HTML_FETCH_MAP = {
    "zhihu": fetch_zhihu_html,
    "weibo": fetch_weibo_html,
    "bilibili": fetch_bilibili_html,
    "baidu": fetch_baidu_html,
}


def fetch_html_fallback(platform, limit=50):
    """统一入口：尝试从HTML解析热榜数据"""
    fn = HTML_FETCH_MAP.get(platform)
    if not fn:
        return {"platform": platform, "error": "不支持的平台", "items": []}
    return fn(limit=limit)


def main():
    parser = argparse.ArgumentParser(description="热榜HTML Fallback抓取")
    parser.add_argument("--platform", "-p", required=True, help="平台名")
    parser.add_argument("--limit", "-l", type=int, default=50, help="条数限制")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    result = fetch_html_fallback(args.platform, args.limit)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("error"):
            print(f"❌ {result['platform']}: {result['error']}")
        else:
            print(f"✅ {result['platform']}: {result['count']} 条 (HTML fallback)")
            for item in result["items"][:5]:
                print(f"  {item['rank']}. {item['title']}")


if __name__ == "__main__":
    main()
