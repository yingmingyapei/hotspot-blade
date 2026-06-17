---
name: hotlist-scraper
title: 热榜采集器
description: 通过 curl+Cookie 直连5平台API采集热榜数据（知乎/微博/B站/36氪/百度），输出结构化JSON。不含选题评分和写作逻辑。
author: Hermes
keywords: [热榜, 数据采集, curl, Cookie, 知乎, 微博, B站, 36氪, 百度]
requires:
  bins:
    - python3
    - curl
---

# 热榜采集器

> 职责单一：curl+Cookie 直连API，返回结构化JSON。不做评分，不做写作。

## 一、执行命令

```bash
# 采集全部5平台
python3 ~/.hermes/scripts/hotlist_scraper.py --json --limit 50

# 采集单个平台
python3 ~/.hermes/scripts/hotlist_scraper.py -p zhihu --json
```

## 二、支持的5平台

| 平台 | 方式 | Cookie | 说明 |
|------|------|--------|------|
| 知乎热榜 | curl GET | 不需要 | `zhihu.com/api/v3/feed/topstory/hot-lists/total` |
| 微博热搜 | curl GET | 需要 | `weibo.com/ajax/side/hotSearch` |
| B站热门 | curl GET | 不需要 | `api.bilibili.com/x/web-interface/popular` |
| 36氪热榜 | curl POST | 不需要 | `gateway.36kr.com/api/mis/nav/home/nav/rank/hot` |
| 百度热搜 | curl GET | 不需要 | `top.baidu.com/board` |

Cookie文件：`~/.hermes/cookies/hotlist-cookies.json`

## 三、输出JSON结构

```json
{
  "zhihu": {
    "platform": "zhihu",
    "count": 50,
    "items": [{"rank": 1, "title": "...", "heat": "1000万", "url": "...", "answers": 123}]
  },
  "weibo": { "platform": "weibo", "count": 50, "items": [...] },
  "bilibili": { "platform": "bilibili", "count": 50, "items": [...] },
  "36kr": { "platform": "36kr", "count": 50, "items": [...] },
  "baidu": { "platform": "baidu", "count": 50, "items": [...] }
}
```

**陷阱：** 顶层key是平台名（`zhihu`），不是`platforms`数组。解析时用`data.keys()`获取平台列表。

## 四、故障处理

| 问题 | 处理 |
|------|------|
| curl exit code ≠ 0 | 先 JSON parse，不要检查 returncode（36氪常返回 code 56 但数据完整）|
| Cookie 过期 | 重新导出 Cookie 到 `~/.hermes/cookies/hotlist-cookies.json` |
| 平台不可用 | 记录故障，跳过该平台，至少3个平台成功才继续 |

## 五、前序准备

```bash
# 检查 Cookie
ls -la ~/.hermes/cookies/hotlist-cookies.json

# 检查脚本
python3 ~/.hermes/scripts/hotlist_scraper.py --help
```

## Pitfalls

### 1. stdout 混合输出
**问题**：脚本将进度消息和JSON都输出到stdout，重定向后JSON解析失败。
**防御**：先保存原始输出到文件，再提取JSON部分：`python3 scraper.py --json > /tmp/raw.txt && python3 -c "import json; d=json.load(open('/tmp/raw.txt')); json.dump(d, open('/tmp/hotlist_data.json','w'))"`

### 2. 百度热搜 JSON 解析
**问题**：百度热搜 API 返回双层嵌套结构，解析需先取 `data.cards` 再遍历。
**防御**：直接用 hotlist_scraper.py 封装好的函数，不要自行拼 curl。

### 3. Cookie 过期
**问题**：微博 Cookie 有效期约2周，过期后 API 返回空数据。
**防御**：每月重新导出 Cookie。失败时记录跳过，不用二手数据源替代。