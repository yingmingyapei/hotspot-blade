# hotlist_scraper.py 输出解析陷阱（2026-06-09）

## 问题

`hotlist_scraper.py --json` 将进度消息和 JSON 数据都输出到 stdout。重定向到文件时，文件内容是混合的：

```
📡 抓取 知乎热榜...
  ✅ 获取 30 条
📡 抓取 微博热搜...
  ✅ 获取 50 条
...
{
  "zhihu": { ... },
  "weibo": { ... },
  ...
}
```

直接 `json.load()` 会报 `JSONDecodeError`。

## 正确做法

```python
import json

# 1. 先保存原始输出
# python3 ~/.hermes/scripts/hotlist_scraper.py --json > /tmp/hotlist_raw.txt

# 2. 找到第一个 { 开始解析 JSON
with open('/tmp/hotlist_raw.txt') as f:
    raw = f.read()

idx = raw.find('{')
if idx >= 0:
    data = json.loads(raw[idx:])
    # 现在 data 是正常的 dict
```

## 关键点

- **不要检查 returncode**：curl 可能返回非零（如 56）但 stdout 有完整 JSON（见 SKILL.md 中的 curl returncode 陷阱）
- **不要用 pipe to interpreter**：`python3 ... | python3 -c "..."` 会被安全系统拦截（`tirith:pipe_to_interpreter`）
- **正确流程**：先重定向到文件 → 再用 Python 读取文件并提取 JSON

## 参考

- 2026-06-09 实测：5个平台全部成功，知乎30条+微博50条+B站50条+36氪50条+百度50条
