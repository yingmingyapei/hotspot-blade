# curl+Cookie 多平台热榜API数据源（v3.7 主力方案）

> 来源：2026-06-09 热点刀锋架构迁移（opencli→curl+Cookie+Python）。
> 核心脚本：`~/.hermes/scripts/hotlist_scraper.py`
> Cookie文件：`~/.hermes/cookies/hotlist-cookies.json`

## 为什么放弃opencli

opencli链路：Agent→Daemon→Chrome Extension→Chrome→API（5个环节）。任何一个环节出问题就全链路失败。
curl+Cookie链路：Agent→API（1个环节）。直接用Cookie头调API，不依赖Chrome/Daemon/Extension。

## 各平台API端点

| 平台 | API URL | 关键Cookie | 需要代理 | 备注 |
|------|---------|-----------|---------|------|
| **知乎热榜** | `https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50` | `z_c0`, `d_c0`, `_zse_ck`, `_xsrf` | 否 | 返回JSON数组，每条有`target.title`和`detail_text` |
| **微博热搜** | `https://weibo.com/ajax/side/hotSearch` | XSRF-TOKEN (cookie+header) | 否 | 返回`data.realtime`数组，`word`是标题，`num`是热度 |
| **B站热门** | `https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1` | `SESSDATA` | 否 | 返回`data.list`数组，`title`+`stat.view`是核心字段 |
| **头条热榜** | ~~`https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc`~~ | 无 | 否 | **已排除（2026-06-09 用户要求）** |
| **百度热搜** | `https://top.baidu.com/api/board?platform=wise&tab=realtime` | 无 | 否 | 返回`data.cards[0].content[0].content`（双层嵌套！），每条有`word`和`hotScore` |
| **36氪热榜** | `POST https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot` | 无需Cookie | 否 | POST请求，body `{"partner_id":"wap","param":{"siteId":1,"platformId:2}}`，返回`data.hotRankList`数组 |

## ⚠️ 百度API双层嵌套陷阱（2026-06-09 实测）

百度热搜API返回结构是双层嵌套：
```json
{
  "data": {
    "cards": [
      {
        "content": [
          {
            "content": [
              {"word": "标题", "hotScore": "123456", ...},
              ...
            ]
          }
        ]
      }
    ]
  }
}
```
解析时必须用 `cards[0].content[0].content` 获取实际数组，不是 `cards[0].content`。

## ✅ 36氪热榜API（2026-06-09 确认）

**正确端点**：`POST https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot`
- **无需Cookie**，公开API
- Body: `{"partner_id":"wap","param":{"siteId":1,"platformId":2}}`
- 返回`data.hotRankList`数组，每条有`templateMaterial.widgetTitle`（标题）、`statRead`（阅读量）、`statPraise`（点赞）

**注意**：`/api/newsflash`是快讯接口，返回旧数据，不是热榜。

## Cookie管理

### 知乎Cookie四件套
| Cookie | 作用 | 有效期 | 说明 |
|--------|------|--------|------|
| `z_c0` | 登录令牌（JWT） | ~5个月 | httpOnly+Secure，document.cookie写不进去 |
| `d_c0` | 设备标识符 | 长期 | 设备指纹 |
| `_zse_ck` | 反爬加密Cookie | 长期 | 加密后的请求签名 |
| `_xsrf` | CSRF令牌 | 会话 | 用于POST请求防CSRF |

### B站Cookie
| Cookie | 作用 | 有效期 |
|--------|------|--------|
| `SESSDATA` | 登录会话 | ~6个月 |
| `bili_jct` | CSRF令牌 | 同SESSDATA |

### 微博Cookie
| Cookie | 作用 | 说明 |
|--------|------|------|
| XSRF-TOKEN | CSRF防护 | 需同时在Cookie和`X-XSRF-TOKEN`请求头中带 |

### 36氪Cookie（2026-06-09 新增）
| Cookie | 作用 | 有效期 | 说明 |
|--------|------|--------|------|
| `krnewsfrontcc` | JWT认证令牌 | 2027-06-09 | 核心认证Cookie，格式`eyJ0eXAiOiJKV1Q...` |
| `krtoken` | 会话令牌 | 2027-06-09 | 配合JWT使用 |
| `userId` | 用户ID | 会话 | 值：6408365 |
| `_waftokenid` | WAF反爬令牌 | 短期 | base64编码含加密签名，需定期刷新 |

## 知乎vs B站Cookie架构对比

- **知乎**：JWT护照模式——一个加密token（z_c0）代表身份，无状态验证
- **B站**：机场安检模式——加密会话ID + 多层设备指纹 + CSRF令牌 + 风控令牌，有状态验证
- **36氪**：JWT+会话混合模式——`krnewsfrontcc`(JWT)为主认证，`krtoken`为会话绑定，`_waftokenid`为WAF层防护

## curl调用示例

```bash
# 知乎热榜
curl -s 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50' \
  -H 'Cookie: z_c0=xxx; d_c0=xxx; _zse_ck=xxx; _xsrf=xxx'

# 微博热搜
curl -s 'https://weibo.com/ajax/side/hotSearch' \
  -H 'Cookie: XSRF-TOKEN=xxx; ...' \
  -H 'X-XSRF-TOKEN: xxx'

# B站热门
curl -s 'https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1' \
  -H 'Cookie: SESSDATA=xxx'

# 头条热榜（已排除，无需Cookie）
# curl -s 'https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc'

# 百度热搜（无需Cookie）
curl -s 'https://top.baidu.com/api/board?platform=wise&tab=realtime'

# 36氪热榜（无需Cookie，POST请求）
curl -s -X POST 'https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot' \
  -H 'Content-Type: application/json' \
  -H 'Referer: https://36kr.com/' \
  -d '{"partner_id":"wap","param":{"siteId":1,"platformId":2}}'
```

## Cookie过期检测与更新

```bash
# 知乎：检查z_c0是否有效
curl -s 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=5' \
  -H 'Cookie: z_c0=xxx' | jq '.data | length'
# 返回数字=有效，返回空或错误=过期

# B站：检查SESSDATA是否有效
curl -s 'https://api.bilibili.com/x/web-interface/popular?ps=5&pn=1' \
  -H 'Cookie: SESSDATA=xxx' | jq '.data.list | length'
```

Cookie过期后需要用户重新登录浏览器获取新Cookie，然后更新 `~/.hermes/cookies/hotlist-cookies.json`。

## 过期时间参考

| 平台 | Cookie | 过期时间（本次） |
|------|--------|----------------|
| 知乎 | z_c0 | 2026-11-15 |
| B站 | SESSDATA | 2026-12-05 |
| 微博 | 需定期刷新 | 不确定 |
| 36氪 | krnewsfrontcc | 2027-06-09 |
| 36氪 | krtoken | 2027-06-09 |

## 注意事项

1. httpOnly Cookie（如z_c0、SESSDATA）无法通过浏览器document.cookie获取，只能从浏览器开发者工具Network面板手动复制
2. 微博的XSRF-TOKEN需要同时在Cookie和请求头中携带，否则返回403
3. 头条和百度API无需Cookie，是最稳定的数据源
4. 如脚本报错"JSON decode error"，通常是Cookie过期导致返回登录页面HTML
5. **36氪热榜无需Cookie**，POST请求 `gateway.36kr.com` 即可，是最稳定的数据源之一
6. **小红书没有热榜功能**（2026-06-09 实测确认）——已取消，搜索"热搜"只返回用户笔记而非官方排名。探索页是个性化推荐，无法作为全站热榜数据源。不要尝试集成小红书热榜。
7. **小红书API有反爬检测**——用curl直接调用edith.xiaohongshu.com的API会返回`code: 300011 "当前账号存在异常"`，必须在浏览器中携带完整Cookie才能访问。
