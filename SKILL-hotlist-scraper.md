---
name: hotlist-scraper
title: 热榜采集器 v2.0
description: 通过 curl_cffi 浏览器指纹模拟 + Cookie fallback 采集热榜数据（知乎/微博/B站/36氪/百度），输出结构化JSON。不含选题评分和写作逻辑。
author: Hermes
keywords: [热榜, 数据采集, curl_cffi, 知乎, 微博, B站, 36氪, 百度]
requires:
  bins:
    - python3
    - curl
  python:
    - curl_cffi
---

# 热榜采集器 v2.0

> 职责单一：curl_cffi 浏览器指纹模拟直连API，返回结构化JSON。不做评分，不做写作。

## 核心改进（v2.0）

- **curl_cffi** `impersonate="chrome"` 模拟浏览器 TLS 指纹，无需 Cookie
- Cookie 文件作为 fallback（需要登录态的平台）
- 自动重试（2次）+ curl_cffi 失败自动 fallback 到 legacy 模式
- 36氪因 API 兼容问题默认用 legacy 模式

## 一、执行命令

```bash
# 采集全部5平台（curl_cffi模式，自动fallback）
python3 ~/.hermes/scripts/hotlist_scraper.py --json --limit 50

# 采集单个平台
python3 ~/.hermes/scripts/hotlist_scraper.py -p zhihu --json

# 旧版curl+Cookie模式（fallback）
python3 ~/.hermes/scripts/hotlist_scraper.py --legacy --json
```

## 二、支持的5平台

| 平台 | 方式 | Cookie | 说明 |
|------|------|--------|------|
| 知乎热榜 | curl_cffi GET | 可选 | `zhihu.com/api/v3/feed/topstory/hot-lists/total` |
| 微博热搜 | curl_cffi GET | 可选 | `weibo.com/ajax/side/hotSearch` |
| B站热门 | curl_cffi GET | 可选 | `api.bilibili.com/x/web-interface/popular` |
| 36氪热榜 | curl POST（legacy） | 不需要 | `gateway.36kr.com` — curl_cffi兼容问题，自动用curl |
| 百度热搜 | curl_cffi GET | 不需要 | `top.baidu.com/api/board` |

**v2.0变更**：知乎/微博/B站/百度优先用 curl_cffi（浏览器指纹模拟），Cookie 文件作为 fallback。36氪因 API 兼容问题固定用 legacy curl。

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
| curl_cffi 请求失败 | 自动 fallback 到 legacy curl+Cookie 模式 |
| curl exit code ≠ 0 | 先 JSON parse，不要检查 returncode（36氪常返回 code 56 但数据完整）|
| Cookie 过期 | curl_cffi 模式下无需 Cookie；legacy 模式需重新导出 |
| 平台不可用 | 记录故障，跳过该平台，至少3个平台成功才继续 |

## 五、前序准备

```bash
# 检查 curl_cffi（必需）
python3 -c "import curl_cffi; print(curl_cffi.__version__)"

# 检查 Cookie（可选，legacy fallback 用）
ls -la ~/.hermes/cookies/hotlist-cookies.json

# 检查脚本
python3 ~/.hermes/scripts/hotlist_scraper.py --help
```

## Pitfalls

### 1. stdout 混合输出
**问题**：脚本将进度消息和JSON都输出到stdout，重定向后JSON解析失败。
**防御**：进度消息输出到stderr，JSON输出到stdout。`--json` 模式下 stdout 只有 JSON。

### 2. 百度热搜 JSON 解析
**问题**：百度热搜 API 返回双层嵌套结构，解析需先取 `data.cards` 再遍历。
**防御**：直接用 hotlist_scraper.py 封装好的函数，不要自行拼请求。

### 3. Cookie 过期（v2.0 已缓解）
**问题**：旧版 curl+Cookie 方案中，微博 Cookie 有效期约2周。
**防御**：v2.0 用 curl_cffi 浏览器指纹模拟，大部分平台不再需要 Cookie。36氪用 legacy curl 也不需要 Cookie。

### 4. 36氪 API 兼容性
**问题**：36氪 gateway API 对 curl_cffi 的 impersonate 参数有兼容问题。
**防御**：36氪固定用 legacy curl POST 模式，不受 curl_cffi 影响。