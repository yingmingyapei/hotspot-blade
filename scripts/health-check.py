#!/usr/bin/env python3
"""
热点刀锋 数据源健康检查 + 自动降级
====================================
用途：每天检查所有数据源是否可用，不可用则自动降级
用法：
  python3 health-check.py               # 完整检查所有源
  python3 health-check.py --quick        # 快速检查（只测P0源）
  python3 health-check.py --status       # 只看上次结果
  python3 health-check.py --cron         # cron模式：检查+降级，输出报告

数据源分级：
  P0 - 核心源（必须通）
  P1 - 备用源
  P2 - 补充源
"""

import json, os, sys, subprocess, time, datetime, urllib.request, urllib.error
from pathlib import Path

DATA_FILE = Path.home() / ".hermes" / "hotspot-health.json"

SOURCES = [
    # P0: 核心源
    {
        "id": "hn_api",
        "name": "Hacker News API",
        "level": "P0",
        "type": "http",
        "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "timeout": 10,
        "check": "http_200",
        "fallback": "无",
    },
    {
        "id": "hn_item",
        "name": "HN 文章详情",
        "level": "P0",
        "type": "http",
        "url": "https://hacker-news.firebaseio.com/v0/item/1.json",
        "timeout": 10,
        "check": "http_200",
        "fallback": "web_search Hacker News",
    },
    {
        "id": "jina_reader",
        "name": "Jina AI Reader",
        "level": "P0",
        "type": "http",
        "url": "https://r.jina.ai/http://example.com",
        "timeout": 15,
        "check": "http_200",
        "fallback": "直接 curl 原站",
    },
    {
        "id": "weibo_tophub",
        "name": "微博热搜 (tophub)",
        "level": "P0",
        "type": "http",
        "url": "https://tophub.today/n/KqndgxeLl9",
        "timeout": 15,
        "check": "http_200",
        "fallback": "web_search 微博热搜",
    },
    # P1: 备用源
    {
        "id": "baidu_tophub",
        "name": "百度热搜 (tophub)",
        "level": "P1",
        "type": "http",
        "url": "https://tophub.today/n/4aHmB2l9s0",
        "timeout": 10,
        "check": "http_200",
        "fallback": "web_search 百度热搜",
    },
    {
        "id": "zhihu_tophub",
        "name": "知乎热搜 (tophub)",
        "level": "P1",
        "type": "http",
        "url": "https://tophub.today/n/34738a41a1",
        "timeout": 10,
        "check": "http_200",
        "fallback": "web_search 知乎热榜",
    },
    {
        "id": "searxng",
        "name": "SearXNG 搜索",
        "level": "P1",
        "type": "http",
        "url": "http://localhost:4000",
        "timeout": 5,
        "check": "http_200",
        "fallback": "web_search 直接",
    },
    {
        "id": "proxy",
        "name": "本地代理 127.0.0.1:10808",
        "level": "P1",
        "type": "proxy",
        "host": "127.0.0.1",
        "port": 10808,
        "timeout": 5,
        "check": "connect",
        "fallback": "直连（部分源可能被墙）",
    },
    # P2: 补充源
    {
        "id": "trends24",
        "name": "Trends24 Twitter趋势",
        "level": "P2",
        "type": "http",
        "url": "https://trends24.in/",
        "timeout": 15,
        "check": "http_200",
        "fallback": "跳过",
    },
    {
        "id": "github_trending",
        "name": "GitHub Trending",
        "level": "P2",
        "type": "http",
        "url": "https://github.com/trending",
        "timeout": 10,
        "check": "http_200",
        "fallback": "跳过",
    },
]


def load_state():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"last_check": None, "results": {}, "downgrade_active": {}}


def save_state(state):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def check_http(source):
    url = source["url"]
    timeout = source.get("timeout", 10)
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status == 200, resp.status
    except urllib.error.HTTPError as e:
        # 403 is "reachable but blocked" — different from timeout
        if e.code == 403:
            return False, 403
        return False, e.code
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def check_proxy(source):
    host = source["host"]
    port = source["port"]
    timeout = source.get("timeout", 5)
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0, "connected" if result == 0 else f"refused ({result})"
    except Exception as e:
        return False, str(e)


def run_check(source):
    check_type = source.get("check", "http_200")
    if check_type == "http_200":
        ok, detail = check_http(source)
    elif check_type == "connect":
        ok, detail = check_proxy(source)
    else:
        ok, detail = False, "unknown check type"
    return ok, detail


def run_checks(quick=False):
    now = datetime.datetime.now().isoformat()
    results = {}
    downgrade_active = {}

    for src in SOURCES:
        if quick and src["level"] != "P0":
            continue

        source_id = src["id"]
        print(f"  [{src['level']}] {src['name']}...", end=" ", flush=True)

        ok, detail = run_check(src)
        status = "✅" if ok else "❌"
        detail_str = f"({detail})" if not ok else ""
        print(f"{status} {detail_str}")

        results[source_id] = {
            "ok": ok,
            "detail": str(detail),
            "checked_at": now,
            "level": src["level"],
            "name": src["name"],
        }

        # Auto-downgrade logic
        if not ok and src["level"] == "P0":
            # P0 failed → flag as downgraded
            downgrade_active[source_id] = {
                "original_level": "P0",
                "fallback": src["fallback"],
                "since": now,
            }
            if src["fallback"] and src["fallback"] != "无":
                print(f"     ↳ 降级: 使用 {src['fallback']}")
        elif ok and src["level"] == "P0":
            # P0 recovered → clear downgrade if was active
            pass  # will be cleared from state below

    return results, downgrade_active


def upgrade_letter(level):
    """Determine if a P0 source that's now working should be upgraded back."""
    # We need at least 2 consecutive successful checks to re-upgrade
    return 2


def cmd_full():
    print("热点刀锋 数据源健康检查")
    print("=" * 60)
    print()

    state = load_state()
    results, downgrade_active = run_checks(quick=False)

    # Merge with previous state for upgrade logic
    prev_results = state.get("results", {})
    prev_downgrades = state.get("downgrade_active", {})

    # Check for recovery: P0 source was down, now up
    now = datetime.datetime.now().isoformat()
    for src_id, result in results.items():
        if result["ok"] and src_id in prev_downgrades:
            # It was down, now it's up
            since = prev_downgrades[src_id].get("since", now)
            try:
                since_dt = datetime.datetime.fromisoformat(since)
                hours_down = (datetime.datetime.now() - since_dt).total_seconds() / 3600
                print(f"  ↳ {result['name']} 恢复上线 (已宕机 {hours_down:.1f} 小时)")
            except:
                pass
            # Remove from downgrade list
            del downgrade_active[src_id]

    # Carry over still-failing downgrades
    for src_id, dg in prev_downgrades.items():
        if src_id not in results:
            results[src_id] = {"ok": False, "detail": "cached", "checked_at": dg.get("since", now), "level": "P0", "name": dg.get("name", src_id)}
            downgrade_active[src_id] = dg
        elif not results[src_id]["ok"]:
            downgrade_active[src_id] = dg  # still failing

    # Summary
    print()
    p0_total = sum(1 for s in SOURCES if s["level"] == "P0")
    p0_ok = sum(1 for s in SOURCES if s["level"] == "P0" and results.get(s["id"], {}).get("ok"))
    p1_total = sum(1 for s in SOURCES if s["level"] == "P1")
    p1_ok = sum(1 for s in SOURCES if s["level"] == "P1" and results.get(s["id"], {}).get("ok"))

    print("=" * 60)
    print(f"  P0 源: {p0_ok}/{p0_total} 可用")
    print(f"  P1 源: {p1_ok}/{p1_total} 可用")

    if downgrade_active:
        print(f"  降级中: {len(downgrade_active)} 个源")
        for src_id, dg in downgrade_active.items():
            name = results.get(src_id, {}).get("name", src_id)
            print(f"    - {name} → {dg['fallback']}")
    else:
        print("  降级: 无")

    state["last_check"] = now
    state["results"] = results
    state["downgrade_active"] = downgrade_active
    save_state(state)

    # Return exit code for cron/scripting
    if p0_ok < p0_total:
        print(f"\n  ⚠️ 警告: {p0_total - p0_ok} 个 P0 源不可用，评分/抓取会受影响")
        return 1
    return 0


def cmd_quick():
    print("快速检查 (P0源)")
    print("=" * 40)
    state = load_state()
    results, downgrade_active = run_checks(quick=True)
    state["last_check"] = datetime.datetime.now().isoformat()
    for k, v in results.items():
        state["results"][k] = v
    for k, v in downgrade_active.items():
        state["downgrade_active"][k] = v
    save_state(state)
    print(f"\n完成。上次完整检查: {state.get('last_check', '从未')[:16]}")


def cmd_status():
    state = load_state()
    if not state.get("last_check"):
        print("从未运行过健康检查。先运行 health-check.py")
        return

    print(f"最后检查: {state['last_check'][:19]}")
    print()
    results = state.get("results", {})
    for level in ("P0", "P1", "P2"):
        level_sources = [s for s in SOURCES if s["level"] == level]
        if not level_sources:
            continue
        print(f"  [{level}]")
        for src in level_sources:
            r = results.get(src["id"], {})
            ok = r.get("ok", "?")
            status = "✅" if ok is True else ("❌" if ok is False else "❓")
            detail = r.get("detail", "")
            detail_str = f" ({detail})" if detail and ok is False else ""
            print(f"    {status} {src['name']}{detail_str}")

    downgrades = state.get("downgrade_active", {})
    if downgrades:
        print(f"\n  降级中:")
        for src_id, dg in downgrades.items():
            print(f"    - {dg.get('name', src_id)} → {dg['fallback']}")


def cmd_cron():
    """Cron mode: run full check, output JSON report."""
    exit_code = cmd_full()
    state = load_state()
    print()
    print("--- JSON ---")
    print(json.dumps({
        "timestamp": state["last_check"],
        "p0_ok": sum(1 for s in SOURCES if s["level"] == "P0" and state.get("results", {}).get(s["id"], {}).get("ok")),
        "p0_total": sum(1 for s in SOURCES if s["level"] == "P0"),
        "downgraded": len(state.get("downgrade_active", {})),
        "all_ok": len(state.get("downgrade_active", {})) == 0,
    }, ensure_ascii=False))
    return exit_code


def main():
    if len(sys.argv) < 2:
        cmd_full()
        return

    cmd = sys.argv[1]
    if cmd == "--quick":
        cmd_quick()
    elif cmd == "--status":
        cmd_status()
    elif cmd == "--cron":
        sys.exit(cmd_cron())
    else:
        print(f"未知: {cmd}")
        print("用法: python3 health-check.py [--quick|--status|--cron]")
        sys.exit(1)


if __name__ == "__main__":
    main()