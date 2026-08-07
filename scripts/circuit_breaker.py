#!/usr/bin/env python3
"""
circuit_breaker.py — 热点刀锋数据源熔断器

状态持久化：~/.hermes/config/circuit_breaker.json
熔断规则：连续失败 >= 2 次 → 熔断 24 小时 → 下次健康检查先探测，恢复后重置

用法（接入 health_check / fetch_hotlists 前调用）：
    from circuit_breaker import is_tripped, record_failure, record_success, get_status

    if is_tripped("知乎热榜"):
        print("跳过：熔断中")
    else:
        ok = do_fetch()
        record_success("知乎热榜") if ok else record_failure("知乎热榜")
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

STATE_FILE = Path.home() / ".hermes" / "config" / "circuit_breaker.json"
TRIP_THRESHOLD = 2       # 连续失败 N 次就熔断
TRIP_DURATION_H = 24     # 熔断多久（小时）


def _load() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def is_tripped(source: str) -> bool:
    """是否处于熔断期"""
    state = _load()
    entry = state.get(source)
    if not entry:
        return False
    tripped_at = entry.get("tripped_at", 0)
    if tripped_at == 0:
        return False
    elapsed_h = (time.time() - tripped_at) / 3600
    if elapsed_h >= TRIP_DURATION_H:
        # 熔断期已过，先标记为"恢复探测中"（由调用方决定实际结果）
        return False
    return True


def record_failure(source: str):
    """记录一次失败；连续 ≥ TRIP_THRESHOLD 次则触发熔断"""
    state = _load()
    entry = state.setdefault(source, {"fail_count": 0, "tripped_at": 0})
    entry["fail_count"] = entry.get("fail_count", 0) + 1
    if entry["fail_count"] >= TRIP_THRESHOLD:
        entry["tripped_at"] = time.time()
    _save(state)


def record_success(source: str):
    """成功后重置失败计数和熔断状态"""
    state = _load()
    state[source] = {"fail_count": 0, "tripped_at": 0}
    _save(state)


def get_status() -> dict:
    """返回所有源的状态摘要（用于健康检查打印）"""
    state = _load()
    report = {}
    now = time.time()
    for name, entry in state.items():
        fc = entry.get("fail_count", 0)
        tripped_at = entry.get("tripped_at", 0)
        if tripped_at > 0:
            remaining_h = max(0, TRIP_DURATION_H - (now - tripped_at) / 3600)
            if remaining_h > 0:
                report[name] = {
                    "status": f"熔断中（剩余 {remaining_h:.1f}h）",
                    "fail_count": fc,
                }
                continue
        report[name] = {"status": "正常", "fail_count": fc}
    return report


if __name__ == "__main__":
    # CLI 调用：python3 circuit_breaker.py [--status|source]
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "--status":
        for name, info in get_status().items():
            print(f"{info['status']:<20} {name:<20} (fail {info['fail_count']})")
    elif len(sys.argv) >= 3 and sys.argv[1] == "--trip":
        record_failure(sys.argv[2])
        print(f"[+] {sys.argv[2]} 失败计数 +1")
    elif len(sys.argv) >= 3 and sys.argv[1] == "--ok":
        record_success(sys.argv[2])
        print(f"[+] {sys.argv[2]} 已重置")
    else:
        print(get_status())
