#!/usr/bin/env python3
"""
YouMind X/Twitter 爆款文章抓取脚本
数据源：https://youmind.com/zh-CN/landing/x-viral-articles
特点：每日追踪 X/Twitter 爆款文章，含互动数据（views/likes/reposts/comments/bookmarks）
需要通过代理访问（WSL 环境下站点被 Cloudflare CDN 屏蔽）

用法：
  python3 youmind_viral_scraper.py [--proxy http://127.0.0.1:1080] [--limit 20] [--format json|text]
"""

import json
import re
import sys
import argparse

PROXY_DEFAULT = "http://127.0.0.1:1080"
URL = "https://youmind.com/zh-CN/landing/x-viral-articles"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_html(proxy=None):
    """通过 curl 获取页面 HTML（支持 SOCKS5 代理）"""
    import subprocess
    cmd = ["curl", "-s", "-L", "--max-time", "30"]
    if proxy:
        cmd += ["--proxy", proxy]
    cmd += [
        "-H", f"User-Agent: {UA}",
        "-H", "Accept: text/html,application/xhtml+xml",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    if result.returncode != 0 or len(result.stdout) < 1000:
        return None
    return result.stdout


def parse_articles(html):
    """
    从 HTML 中解析文章数据。
    数据嵌在 self.__next_f.push([1,"..."]) 调用中，JSON 值用 \\\" 转义。
    需要先提取 push 块 → 拼接 → 反转义 → 正则匹配。
    """
    # Step 1: 提取所有 push 块内容
    pushes = re.findall(
        r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html
    )
    if not pushes:
        return []

    # Step 2: 拼接 + 反转义
    full = "".join(pushes).replace('\\"', '"')

    # Step 3: 正则匹配完整文章对象
    pattern = (
        r'"id":(\d+),"slug":"([^"]+)","title":"((?:[^"\\]|\\.)*)",'
        r'"description":"[^"]*","summary":"[^"]*",'
        r'"coverImageUrl":"[^"]*".*?'
        r'"sourceLink":"([^"]+)",'
        r'"sourcePlatform":"([^"]+)",'
        r'"sourcePublishedAt":"([^"]+)",'
        r'"originalLanguage":"([^"]+)",'
        r'"engagement":\{"views":(\d+),"likes":(\d+),"reposts":(\d+),"comments":(\d+),"bookmarks":(\d+)'
    )

    articles = []
    for m in re.finditer(pattern, full, re.DOTALL):
        article = {
            "id": int(m.group(1)),
            "slug": m.group(2),
            "title": m.group(3),
            "source_link": m.group(4),
            "platform": m.group(5),
            "published_at": m.group(6),
            "language": m.group(7),
            "engagement": {
                "views": int(m.group(8)),
                "likes": int(m.group(9)),
                "reposts": int(m.group(10)),
                "comments": int(m.group(11)),
                "bookmarks": int(m.group(12)),
            },
        }
        if not any(a["id"] == article["id"] for a in articles):
            articles.append(article)

    # Fallback: 简化匹配（仅 id/slug/title）
    if not articles:
        simple = r'"id":(\d+),"slug":"([^"]+)","title":"((?:[^"\\]|\\.)*)"'
        for m in re.finditer(simple, full):
            articles.append({
                "id": int(m.group(1)),
                "slug": m.group(2),
                "title": m.group(3),
            })

    return articles


def format_text(articles, limit=20):
    """格式化为文本输出"""
    lines = [f"YouMind X/Twitter 爆款文章（Top {min(limit, len(articles))}）\n"]
    for i, a in enumerate(articles[:limit]):
        eng = a.get("engagement", {})
        views = eng.get("views", 0)
        likes = eng.get("likes", 0)
        reposts = eng.get("reposts", 0)
        bookmarks = eng.get("bookmarks", 0)
        lang = a.get("language", "")
        pub = a.get("published_at", "")[:10]

        lines.append(
            f"#{i+1} [{lang}] {a['title']}\n"
            f"   👁 {views:,} | ❤ {likes:,} | 🔁 {reposts:,} | 🔖 {bookmarks:,} | 📅 {pub}\n"
            f"   🔗 {a.get('source_link', a.get('slug', ''))}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="YouMind X/Twitter 爆款文章抓取")
    parser.add_argument("--proxy", default=PROXY_DEFAULT, help="SOCKS5 代理地址")
    parser.add_argument("--limit", type=int, default=20, help="返回文章数量")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    parser.add_argument("--no-proxy", action="store_true", help="不使用代理（直连，通常超时）")
    args = parser.parse_args()

    proxy = None if args.no_proxy else args.proxy

    html = fetch_html(proxy)
    if not html:
        print("❌ 无法获取 YouMind 页面，请检查代理设置", file=sys.stderr)
        sys.exit(1)

    articles = parse_articles(html)
    if not articles:
        print("❌ 未解析到文章数据", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(articles[:args.limit], ensure_ascii=False, indent=2))
    else:
        print(format_text(articles, args.limit))


if __name__ == "__main__":
    main()
