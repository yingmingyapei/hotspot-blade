# 头条号(今日头条MP) API 探索记录

## 获取 Cookie
1. 浏览器登录 https://mp.toutiao.com/profile_v4/index
2. F12 → 网络(Network) → 刷新 → 点第一个请求 → 请求标头 → 复制 Cookie
3. 或 F12 → 控制台(Console) → `document.cookie` → 复制

## API 端点测试结果

### ✅ 可用
- `GET /mp/agw/article/list?page=1&page_size=50&sort_type=1`
  - 需要登录 Cookie
  - 返回 `data.articles[]`，按时间倒序
  - `sort_type=1` 按时间排序

### ❌ 返回 404
- `/mp/agw/user_info`
- `/mp/agw/account/get_media_info`
- `/mp/agw/home/overview`
- `/mp/agw/weitoutiao/list`
- `/mp/agw/manage/content/all`
- `/mp/agw/article/wtt_list`
- `/mp/agw/analysis/works_overall`

## article/list 返回的关键字段

| 字段 | 含义 | 备注 |
|------|------|------|
| `title` | 标题 | |
| `create_time` | 创建时间(unix) | |
| `impression_count` | 曝光量 | |
| `go_detail_count_v2` | 阅读量(?) | **⚠️ 用户反馈此数据可能不准确，待验证** |
| `play_effective_count` | 有效播放 | 视频类 |
| `digg_count` | 点赞数 | |
| `comment_count` | 评论数 | |
| `article_type` | 0=文章, 1=微头条 | |
| `is_exclusive` | 首发认证 | |
| `visibility_level` | 推荐可见度 | 15/20/40/45/60 |
| `was_recommended` | 是否被推荐 | 0/1 |
| `status` | 3=已发布 | |
| `content_word_cnt` | 字数 | |

## 已知问题
1. `go_detail_count_v2` 与后台"阅读量"可能不是同一口径——用户明确反馈数据不对
2. 微头条（article_type=1）和文章混在同一个列表里，无法通过参数单独筛选
3. 可能还有其他 API 路径未发现（如数据统计专用接口、微头条专用接口）
4. 平台使用 Garfish 微前端架构，纯 curl 无法获取 SPA 渲染后的数据

## 请求头模板
```
-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
-H 'Referer: https://mp.toutiao.com/profile_v4/index'
```

## 待办
- [ ] 确认正确的"阅读量"字段映射
- [ ] 找到微头条专用 API
- [ ] 找到数据统计/分析 API
- [ ] 尝试抓取 Fiddler/DevTools 中的实际 API 调用来发现更多端点
