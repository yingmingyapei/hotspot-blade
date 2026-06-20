# 平台排除记录

## 已排除平台

### 头条热榜（2026-06-09 排除）
- **原因**：用户要求排除
- **API**：`GET https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc`
- **状态**：fetch_toutiao 函数已从 hotlist_scraper.py 中移除
- **替代**：36氪热榜作为科技/商业类内容补充

### 小红书（2026-06-09 确认不可用）
- **原因**：无热榜功能
- **实测结果**：
  - 小红书已取消热榜功能（有用户笔记明确说"小红书热榜已经无了"）
  - 搜索"热搜"只返回用户生成内容，不是官方热榜
  - 探索页是个性化推荐，不是全站热榜
  - curl 调用 edith.xiaohongshu.com API 返回 code=300011 "当前账号存在异常"
- **Cookie 测试**：web_session + id_token 注入成功，但 API 仍拒绝非浏览器请求
- **结论**：无法程序化抓取，排除

### 雪球（2026-06-04 排除）
- **原因**：xueqiu.com 返回 503 反爬虫
- **状态**：从未加入 hotlist_scraper.py

## 当前数据源（5平台）

| 平台 | 需Cookie | 请求方式 | 状态 |
|------|---------|---------|------|
| 知乎热榜 | ✅ | GET | 稳定 |
| 微博热搜 | ✅ | GET | 稳定 |
| B站热门 | ✅ | GET | 稳定 |
| 36氪热榜 | ❌ | POST | 稳定（最可靠） |
| 百度热搜 | ❌ | GET | 稳定 |

## opencli 浏览器命令（非数据采集用途）

opencli browser 仍可用于打开网页和交互操作：
```bash
opencli browser <session> open <url>   # 打开网页
opencli browser <session> state        # 获取页面状态
opencli browser <session> extract      # 提取页面内容
```

语法：`opencli browser <session> <command>`，session 是自定义的会话名。
