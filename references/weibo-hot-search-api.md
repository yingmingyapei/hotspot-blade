# 微博热搜 API 直接采集方法

> 2026-06-08 实测验证：curl + Cookie 直调微博 AJAX API，结构化 JSON 返回，比 opencli browser 更稳定。

## API 端点

```
GET https://weibo.com/ajax/side/hotSearch
```

## 必需请求头

| Header | 值 | 说明 |
|--------|---|------|
| Cookie | 完整 Cookie 链 | SCF/SINAGLOBAL/SUB/SUBP/ALF/WBPSESS/XSRF-TOKEN 等 |
| User-Agent | 标准浏览器 UA | 必须模拟浏览器 |
| Referer | https://weibo.com | 必须带 |
| X-XSRF-TOKEN | 从 Cookie 中提取 | Cookie 中 XSRF-TOKEN 字段的值 |

## 返回结构

```json
{
  "ok": 1,
  "data": {
    "hotgovs": [...],    // 置顶/头条（政府类）
    "hotgov": {...},     // 单条置顶详情
    "realtime": [        // 实时热搜列表
      {
        "word": "话题名",
        "num": 1730196,          // 热度值
        "label_name": "热/新",   // 标签
        "realpos": 1,            // 真实排名
        "rank": 0,               // 显示排名
        "is_ad": 1,              // 是否广告
        "topic_flag": 1,         // 是否话题
        "flag_desc": "综艺"      // 分类
      }
    ]
  }
}
```

## 关键字段说明

| 字段 | 说明 | 用途 |
|------|------|------|
| `word` | 话题关键词 | 选题标题 |
| `num` | 热度值（万级） | 选题排序 |
| `label_name` | "热"/"新"/"" | 判断时效性 |
| `realpos` | 去除广告后的真实排名 | 精准排序 |
| `is_ad` | 1=广告，0=非广告 | **过滤广告话题** |
| `topic_flag` | 1=有话题页，0=纯关键词 | 决定是否带 # 标签 |
| `flag_desc` | 分类标签（综艺/社会等） | 选题分类过滤 |

## 使用示例

```bash
curl -s 'https://weibo.com/ajax/side/hotSearch' \
  -H 'Cookie: <完整Cookie>' \
  -H 'User-Agent: Mozilla/5.0 ...' \
  -H 'Referer: https://weibo.com' \
  -H 'X-XSRF-TOKEN: <从Cookie提取>' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f\"{i['realpos']:>2} {'[商]' if i.get('is_ad') else '    '} {i['label_name']:>1} {i['num']/10000:>7.1f}万  {i['word']}\") for i in d['data']['realtime'][:20]]"
```

## 与 opencli weibo hot 的对比

| 维度 | curl + AJAX API | opencli weibo hot |
|------|----------------|-------------------|
| 依赖 | 无（只需 curl） | 需要 opencli daemon + Chrome 扩展 |
| Cookie | 需要手动提供 | 可能复用 Chrome 登录态 |
| 返回格式 | 结构化 JSON | 可能是 HTML 解析 |
| 广告过滤 | `is_ad` 字段直接过滤 | 需要自行判断 |
| 稳定性 | 高（直接 API） | 依赖 daemon 状态 |
| 适用场景 | 交互模式（用户提供 Cookie） | 定时任务（Chrome 常驻） |

## 注意事项

1. **Cookie 有效期有限** — ALF 字段有过期时间，过期后需用户重新获取
2. **广告话题必须过滤** — `is_ad=1` 的话题是商业推广（如"王濛京喜喜歌""哈兰德代言王老吉"），不应作为选题
3. **热度值单位** — `num` 是绝对值，通常在 10万-200万 之间
4. **定时任务不适用** — Cookie 会过期，定时任务应继续使用 opencli weibo hot
5. **XSRF-TOKEN 必须** — 不带此头会返回空数据或 403
