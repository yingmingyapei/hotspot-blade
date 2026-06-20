# 微博 & 知乎 API 数据采集模式

> 来源：2026-06-08 实战验证。使用 Cookie + curl 直接调平台 API，无需 opencli/Chrome。
> 适用于：热点刀锋数据采集、舆情监控、热榜抓取。

## 微博热搜 API

### 接口
```
GET https://weibo.com/ajax/side/hotSearch
```

### 必要请求头
```
Cookie: <完整Cookie链>
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Referer: https://weibo.com
X-XSRF-TOKEN: <XSRF-TOKEN值>
```

### 关键 Cookie
| Cookie | 作用 | 必要性 |
|--------|------|--------|
| SUB | 登录认证令牌 | ✅ 核心 |
| WBPSESS | 会话状态 | ✅ 核心 |
| XSRF-TOKEN | CSRF 防护（需同时放入请求头 X-XSRF-TOKEN） | ✅ POST请求必须 |

### 返回数据结构
```json
{
  "ok": 1,
  "data": {
    "hotgov": { "name": "#置顶话题#" },
    "hotgovs": [...],
    "realtime": [
      {
        "word": "话题名",
        "num": 1730196,         // 热度值
        "label_name": "热",     // 标签：热/新/商
        "realpos": 1,           // 真实排名
        "is_ad": 1              // 是否广告
      }
    ]
  }
}
```

### curl 示例
```bash
curl -s 'https://weibo.com/ajax/side/hotSearch' \
  -H 'Cookie: SUB=xxx; WBPSESS=xxx; XSRF-TOKEN=xxx' \
  -H 'User-Agent: Mozilla/5.0 ...' \
  -H 'Referer: https://weibo.com' \
  -H 'X-XSRF-TOKEN: xxx' | python3 -m json.tool
```

### 注意事项
- XSRF-TOKEN 需要同时出现在 Cookie 和 X-XSRF-TOKEN 请求头中
- Cookie 中的 XSRF-TOKEN 值可能被截断，需确保完整
- 返回的 `num` 字段是热度值，`realpos` 是去除广告后的真实排名
- `is_ad=1` 的条目是广告，选题时需排除

---

## 知乎热榜 API

### 接口
```
GET https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50
```

### 必要请求头
```
Cookie: <完整Cookie链>
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Referer: https://www.zhihu.com/hot
```

### 关键 Cookie
| Cookie | 作用 | 必要性 | httpOnly |
|--------|------|--------|----------|
| **z_c0** | 登录认证令牌（JWT格式） | ✅ 核心 | ✅ 是 |
| _xsrf | CSRF 防护令牌 | ✅ POST请求必须 | ❌ 否 |
| d_c0 | 设备标识符 | ✅ 绑定会话 | ❌ 否 |
| _zse_ck | 反爬加密 Cookie | ✅ API调用必须 | ❌ 否 |
| q_c1 | 会话追踪 | 🟡 建议带 | ❌ 否 |
| SESSIONID | 会话 ID | 🟡 建议带 | ❌ 否 |
| BEC | 负载均衡 | 🟡 建议带 | ❌ 否 |

### z_c0 说明
- 知乎的 JWT 登录凭证，有效期约5个月
- 格式：`2|1:0|10:<timestamp>|4:z_c0|92:<base64_payload>|<hex_signature>`
- 有 httpOnly + secure 标记，不能通过 `document.cookie` 设置
- 获取方式：浏览器开发者工具 → Application → Cookies → `.zhihu.com` → z_c0

### 返回数据结构
```json
{
  "data": [
    {
      "target": {
        "title": "问题标题",
        "excerpt": "问题描述前200字",
        "answer_count": 338,
        "follower_count": 937
      },
      "detail_text": "369 万热度"
    }
  ]
}
```

### curl 示例
```bash
curl -s 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50' \
  -H 'Cookie: z_c0=xxx; _xsrf=xxx; d_c0=xxx; _zse_ck=xxx' \
  -H 'User-Agent: Mozilla/5.0 ...' \
  -H 'Referer: https://www.zhihu.com/hot'
```

### 浏览器 Cookie 注入（用于 opencli browser）
当需要通过浏览器访问知乎时，可以用 `document.cookie` 注入非 httpOnly 的 Cookie：
```javascript
// 可注入的 Cookie（非 httpOnly）
document.cookie = '_xsrf=xxx; domain=.zhihu.com; path=/';
document.cookie = 'd_c0=xxx; domain=.zhihu.com; path=/';
document.cookie = 'z_c0=xxx; domain=.zhihu.com; path=/';
// 注意：z_c0 虽然标记 httpOnly，但部分浏览器环境下 document.cookie 可以设置
```

验证注入结果：访问 `https://www.zhihu.com`，页面标题应显示未读消息数（如 "(37 封私信 / 8 条消息) 首页 - 知乎"）。

---

## 知乎热榜 API（更稳定的备用方案）

如果 `/api/v3/feed/topstory/hot-lists/total` 返回空，尝试：
```
GET https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true
```

或使用知乎搜索 API 间接获取热榜：
```
GET https://www.zhihu.com/api/v4/search_v3?t=general&q=热榜&correction=1&offset=0&limit=20
```
