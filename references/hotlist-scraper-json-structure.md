# hotlist_scraper.py 输出 JSON 结构

> 记录时间：2026-06-12
> 来源：实际执行 hotlist_scraper.py --json 后解析

## 顶层结构

```json
{
  "zhihu": {"platform": "知乎热榜", "count": 30, "items": [...]},
  "weibo": {"platform": "微博热搜", "count": 50, "items": [...]},
  "bilibili": {"platform": "B站热门", "count": 50, "items": [...]},
  "36kr": {"platform": "36氪热榜", "count": 50, "items": [...]},
  "baidu": {"platform": "百度热搜", "count": 50, "items": [...]}
}
```

**⚠️ 注意**：顶层 key 是平台名（`zhihu`, `weibo` 等），不是 `platforms` 数组。

## 各平台 item 字段

| 平台 | 字段 | 说明 |
|------|------|------|
| 知乎 | `title`, `heat`, `answers`, `url`, `rank` | heat 含"万热度"后缀 |
| 微博 | `word`(标题), `hot_value`, `category`, `url`, `rank` | hot_value 含"万"后缀 |
| B站 | `title`, `author`, `play`, `danmaku`, `rank` | play/danmaku 可能为空字符串 |
| 36氪 | `title`, `author`, `url`, `rank` | 无热度字段 |
| 百度 | `title`, `url`, `rank` | 无热度字段 |

## 解析注意事项

1. B站和36氪、百度的热度字段可能为空或不存在，解析时需做 fallback
2. 微博标题字段是 `word` 不是 `title`
3. 用 `data.keys()` 获取平台列表，用 `data[name]["items"]` 获取条目
