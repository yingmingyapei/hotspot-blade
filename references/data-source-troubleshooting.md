# 数据源健康检查与故障排查

## HN Firebase API SSL 超时问题

**症状**：`urllib.request.urlopen` 连接 `hacker-news.firebaseio.com` 时 SSL handshake 超时

**根因**：WSL 环境下 urllib 的 SSL 握手与 Firebase 服务器兼容性差

**解决方案**：改用 `curl_cffi` 库，带 `impersonate='chrome'` 参数

```python
# ❌ 失败
import urllib.request
resp = urllib.request.urlopen('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=15)

# ✅ 成功
from curl_cffi import requests
resp = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', impersonate='chrome', timeout=15)
```

**适用场景**：所有 Firebase Realtime Database API 调用

---

## 百度热搜抓取

**命令**：
```python
import urllib.request
import re

req = urllib.request.Request('https://top.baidu.com/board?tab=realtime', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
resp = urllib.request.urlopen(req, timeout=15)
text = resp.read().decode('utf-8', errors='replace')
titles = re.findall(r'"word":"([^"]+)"', text)
```

**返回**：52条热搜数据，实时更新，无需登录

---

## Buzzing.cc 抓取

**推荐方法**：`curl_cffi` + 正则提取

```python
from curl_cffi import requests
import re

resp = requests.get('https://buzzing.cc', impersonate='chrome', timeout=15)
titles = re.findall(r'>([^<]{20,200})<', resp.text)
```

**过滤规则**：
- 长度 > 15 字符
- 不以 http/https 开头
- 排除导航文本（buzzing.cc, ↑, PH Upvotes, HN Points 等）

---

## opencli 命令在定时任务中的行为

**关键发现**（2026-05-13 实测）：
- `opencli zhihu hot`、`opencli weibo hot` 等命令**依赖 Extension 连接**
- 定时任务/headless 环境中 Extension 未连接，命令会超时（30s+）
- **不要依赖 opencli 命令做定时任务数据抓取**

**替代方案**：
| 数据源 | opencli 命令 | 替代方案 |
|--------|-------------|----------|
| 知乎热榜 | `opencli zhihu hot` ❌ | curl_cffi 直接调用知乎 API |
| 微博热搜 | `opencli weibo hot` ❌ | 百度热搜替代 |
| Hacker News | `opencli hackernews top` ❌ | HN Firebase API + curl_cffi |
| 36氪热榜 | `opencli 36kr hot` ⚠️ | 返回旧数据，不可靠 |

---

## 数据源优先级（2026-05-21 更新）

| 优先级 | 数据源 | 状态 | 说明 |
|--------|--------|------|------|
| P1 | 百度热搜 | ✅ 稳定 | urllib 直连，52条/次，无需登录 |
| P2 | Buzzing.cc | ✅ 稳定 | curl_cffi，1200+条，海外信息差 |
| P3 | HN Firebase | ✅ 稳定（需 curl_cffi） | 500条，科技垂直 |
| P4 | YouMind X爆款 | ⚠️ 需代理 | SOCKS5 代理，289篇/日 |
| P5 | opencli 命令 | ❌ 定时任务不可用 | 仅交互模式可用 |

---

## 健康检查脚本模板

```python
import subprocess
import json

def check_data_source(name, cmd, expected_min=3):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45)
        if result.returncode == 0 and len(result.stdout.strip()) > 10:
            try:
                data = json.loads(result.stdout)
                count = len(data) if isinstance(data, list) else 1
                if count >= expected_min:
                    print(f'✅ {name}：{count} 条数据')
                else:
                    print(f'⚠️ {name}：数据量不足 ({count} < {expected_min})')
            except json.JSONDecodeError:
                print(f'✅ {name}：返回非 JSON 数据（可能是文本格式）')
        else:
            print(f'❌ {name}：命令执行失败或返回空')
    except subprocess.TimeoutExpired:
        print(f'⏰ {name}：超时')
    except Exception as e:
        print(f'❌ {name}：错误 - {e}')

# 执行检查
check_data_source('百度热搜', 'python3 -c "..."')
check_data_source('Buzzing.cc', 'python3 -c "..."')
check_data_source('HN Firebase', 'python3 -c "..."')
```
