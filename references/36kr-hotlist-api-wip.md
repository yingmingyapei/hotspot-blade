# 36氪热榜API（已确认 ✅ 2026-06-09）

> ✅ API端点已确认可用，已集成到 hotlist_scraper.py 作为第6个数据源。
> 更新日期：2026-06-09
> 状态：**已确认，无需Cookie，公开API**

## 确认的API端点

```
POST https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot
Content-Type: application/json
Referer: https://36kr.com/

Body: {"partner_id":"wap","param":{"siteId":1,"platformId":2}}
```

**关键特性：**
- **无需Cookie**：公开API，无需任何认证
- 请求方式：POST（不是GET）
- 返回：50条热榜文章，按热度排序
- 数据结构非常干净：标题、作者、阅读量、点赞、收藏、评论

## 已排除的错误端点

| 端点 | 结果 | 说明 |
|------|------|------|
| `https://36kr.com/api/newsflash` | ❌ 返回2020年旧数据 | 快讯接口，不是热榜 |

## 返回数据结构

```json
{
  "code": 0,
  "data": {
    "hotRankList": [
      {
        "itemId": 3844116655278598,
        "itemType": 10,
        "templateMaterial": {
          "itemId": 3844116655278598,
          "widgetTitle": "标题文本",
          "authorName": "作者名",
          "statRead": 45761,
          "statPraise": 168,
          "statCollect": 55,
          "statComment": 3,
          "statFormat": "168点赞"
        },
        "route": "detail_article?itemId=3844116655278598",
        "publishTime": 1780903771082
      }
    ]
  }
}
```

## 踩坑：curl returncode 56

curl返回exit code 56（部分数据），但stdout中JSON完整可解析。
原代码 `result.returncode != 0` 直接返回失败。
**修复**：移除returncode检查，直接try JSON parse。

## 用户Cookie信息（备用，当前不需要）

| Cookie | 域 | 有效期 | 作用 |
|--------|-----|--------|------|
| `krnewsfrontcc` | .36kr.com | 2027-06-09 | JWT认证令牌 |
| `krtoken` | .36kr.com | 2027-06-09 | 会话令牌 |
| `userId` | .36kr.com | 会话 | 用户ID：6408365 |

Cookie存储在 `~/.hermes/cookies/hotlist-cookies.json` 的 `"36kr"` 键下，但API不需要。
