# 数据源可靠性跟踪 (Data Source Reliability Tracking)

> Last updated: 2026-06-04
> Tracked via daily cron job observations. Update this file whenever a data source's status changes.

## Status Summary

| Data Source | Status | Trend | Last Verified | Notes |
|-------------|--------|-------|---------------|-------|
| 知乎热榜 (opencli browser) | ✅ Stable | ↑ | 2026-06-04 | 19-20条/次，opencli browser已验证可用 |
| 微博热搜 (opencli browser) | ✅ Stable | ↑ | 2026-06-04 | 50条/次，opencli browser已验证可用 |
| B站热榜 (opencli browser) | ✅ Stable | ↑ | 2026-06-04 | 20+条/次，opencli browser已验证可用 |
| 雪球热帖 (opencli browser) | ⚠️ Partial | → | 2026-06-04 | 首页+滚动可用，hot/list URL返回404，需15秒等待+滚动 |
| 头条热榜 (opencli browser) | ⚠️ Partial | → | 2026-06-04 | 首页可用，hot-board URL返回404，需15秒JS渲染 |
| Baidu Hot Search (urllib) | ✅ Stable | → | 2026-06-02 | 52条/次，备用数据源（二手数据） |
| HN Firebase API | ✅ Stable | → | 2026-05-25 | 500条/次，urllib直连，海外补充 |
| YouMind X爆款 (HTTP/SOCKS5) | ✅ Working | → | 2026-05-25 | 需代理，海外补充 |
| Buzzing.cc (method C) | ⚠️ Reliable via fallback | → | 2026-05-25 | curl_cffi不可用但方法C有效 |

## 数据源架构（2026-06-04 更新）

**核心原则：只用第一手数据，不经过任何中间算法加工。**

5个第一手国内平台（opencli browser 直接访问热榜页面）：
1. 知乎热榜 — zhihu.com/hot
2. 微博热搜 — s.weibo.com/top/summary
3. B站热榜 — bilibili.com/v/popular/rank/all
4. 雪球热帖 — xueqiu.com/hot/list
5. 头条热榜 — toutiao.com/hot-board/

备用数据源（仅在5个平台全部失败时使用）：
- 百度热搜（二手数据，百度算法加工过）
- Buzzing.cc（海外信息差）
- HN Firebase（海外科技）
- **Fallback**: 重试3次，不降级到百度搜索
- **Recommendation**: Best source for trending topics and public sentiment

### B站热榜 (opencli browser)
- **Method**: `opencli browser bilibili open "https://www.bilibili.com/v/popular/rank/all"` + `state`
- **Reliability**: 100% when Chrome is running
- **Data volume**: 20+条 consistently
- **Prerequisites**: Chrome must be running
- **JS渲染**: 轻度，5-8秒足够
- **Recommendation**: 年轻人视角，评论区即弹药库

### 雪球热帖 (opencli browser)
- **Method**: `opencli browser xueqiu open "https://xueqiu.com/"` + scroll + `state`
- **Reliability**: ⚠️ 部分可用
- **已失效URL**: `https://xueqiu.com/hot/list` → 404
- **替代方案**: 首页 `https://xueqiu.com/` + 滚动2次
- **数据量**: 热门话题10条 + feed流文章
- **JS渲染**: 重度，需15秒+滚动触发feed加载
- **Prerequisites**: 需要登录态
- **数据特点**: 偏行业/个股，散户讨论在feed流里需深度提取
- **Recommendation**: 金融垂直，看多vs看空天然是50/50对撞

### 头条热榜 (opencli browser)
- **Method**: `opencli browser toutiao open "https://www.toutiao.com/"` + `state`
- **Reliability**: ⚠️ 部分可用
- **已失效URL**: `https://www.toutiao.com/hot-board/` → 404
- **替代方案**: 首页 `https://www.toutiao.com/`
- **数据量**: 热搜3-8条 + 正文流10+条
- **JS渲染**: 重度，需15秒等待
- **Prerequisites**: 需要登录态
- **数据提取**: 热搜在 `aria-label=热搜` 区域
- **Recommendation**: 直接命中头条用户兴趣

### 今日头条热榜 (opencli browser)
- **Method**: `opencli browser zhihu open "https://www.zhihu.com/hot"` + `state`
- **Reliability**: 100% when Chrome is running with login state
- **Data volume**: 19-20条 consistently
- **Prerequisites**: Chrome must be running, user must be logged in to zhihu.com
- **Fallback**: 重试3次，不降级到百度搜索
- **Recommendation**: Best source for trending topics and public sentiment

### B站热榜 (opencli browser)
- **Method**: `opencli browser bilibili open "https://www.bilibili.com/v/popular/rank/all"` + `state`
- **Reliability**: 100% when Chrome is running
- **Data volume**: 20+条 consistently
- **Prerequisites**: Chrome must be running
- **JS渲染**: 轻度，5-8秒足够
- **Recommendation**: 年轻人视角，评论区即弹药库

### 雪球热帖 (opencli browser)
- **Method**: `opencli browser xueqiu open "https://xueqiu.com/"` + scroll + `state`
- **Reliability**: ⚠️ 部分可用
- **已失效URL**: `https://xueqiu.com/hot/list` → 404
- **替代方案**: 首页 `https://xueqiu.com/` + 滚动2次
- **数据量**: 热门话题10条 + feed流文章
- **JS渲染**: 重度，需15秒+滚动触发feed加载
- **Prerequisites**: 需要登录态
- **数据特点**: 偏行业/个股，散户讨论在feed流里需深度提取
- **Recommendation**: 金融垂直，看多vs看空天然是50/50对撞

### 头条热榜 (opencli browser)
- **Method**: `opencli browser toutiao open "https://www.toutiao.com/"` + `state`
- **Reliability**: ⚠️ 部分可用
- **已失效URL**: `https://www.toutiao.com/hot-board/` → 404
- **替代方案**: 首页 `https://www.toutiao.com/`
- **数据量**: 热搜3-8条 + 正文流10+条
- **JS渲染**: 重度，需15秒等待
- **Prerequisites**: 需要登录态
- **数据提取**: 热搜在 `aria-label=热搜` 区域
- **Recommendation**: 直接命中头条用户兴趣

### 今日头条热榜 (opencli browser)
- **Method**: `opencli browser weibo open "https://s.weibo.com/top/summary"` + `state`
- **Reliability**: 100% when Chrome is running with login state
- **Data volume**: 50条 consistently
- **Prerequisites**: Chrome must be running, user must be logged in to weibo.com
- **Login state**: Long-lived (weeks to months)
- **Fallback**: 百度搜索"微博热搜"间接获取（二手数据）

### 环境就绪检查
- **前置条件**: opencli daemon 运行 + Extension 已连接 + Chrome 已登录目标平台
- **等待机制**: 循环检查 Extension 连接状态，每5秒重试，最多等60秒
- **常见问题**: cron job 触发时 Chrome/Extension 可能还没准备好，需要等待
- **Chrome Auto-Start**: `C:\Users\yingm\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\chrome-startup.bat`

## Data Source Selection Order (v3.4 - 2026-06-04)

Based on reliability observations, the recommended execution order is:

```
1. 知乎热榜 (opencli browser)   — 深度社会议题，九边风格最佳素材
2. 微博热搜 (opencli browser)   — 舆情风向标，热点首发地
3. B站热榜 (opencli browser)    — 年轻人视角，代际冲突源
4. 雪球热帖 (opencli browser)   — 金融垂直，看多vs看空撕裂
5. 头条热榜 (opencli browser)   — 直接命中头条用户兴趣
6. Buzzing.cc (curl→file)       — 海外信息差补充
7. HN Firebase (urllib)          — 海外科技补充
```

## When to Skip

- If Chrome is not running → wait up to 60 seconds, then stop
- If Extension not connected → wait up to 60 seconds, then stop
- If < 3 platforms successfully scraped → stop, report "数据不足"
- If all 5 platforms fail → stop execution, do not use stale/expired data
