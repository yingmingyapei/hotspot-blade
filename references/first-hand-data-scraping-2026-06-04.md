# 第一手数据采集方案（2026-06-04 确立）

## 核心原则

**只用第一手数据，禁止使用百度搜索等二手数据源。**

百度搜索返回的结果是百度算法加工过的，不是原始热榜。必须直接去各平台热榜页面抓取原始数据，筛选判断由 Agent 自己做。

- ❌ 百度搜索"知乎热榜" → 二手数据
- ✅ 直接访问 zhihu.com/hot → 第一手数据

## 5个第一手数据源（国内）

| # | 平台 | 入口 | 数据性质 | 状态 |
|---|------|------|---------|------|
| 1 | 知乎热榜 | zhihu.com/hot | 知乎用户真实投票排序 | ✅ 已验证 19条 |
| 2 | 微博热搜 | s.weibo.com/top/summary | 微博实时搜索热度 | ✅ 已验证 50条 |
| 3 | B站热榜 | bilibili.com/v/popular/rank/all | B站播放/弹幕/投币综合排序 | 待验证 |
| 4 | 雪球热帖 | xueqiu.com/hot/list | 散户真实讨论热度 | 待验证（反爬） |
| 5 | 头条热榜 | toutiao.com/hot-board | 直接命中头条用户兴趣 | 待验证 |

百度热搜降级为备用——只有以上5个全部失败时才用。

## 统一采集方式：opencli browser

全部通过 opencli browser 模式采集，Chrome 登录态复用：

```bash
# 通用模式
opencli browser <session> open "<url>"
sleep 5
opencli browser <session> state
```

## 已验证的采集记录

### 知乎热榜（2026-06-04 验证）

```bash
opencli browser zhihu open "https://www.zhihu.com/hot"
sleep 5
opencli browser zhihu state
```

- 结果：19条热榜，含排名、标题、热度值
- 前置条件：Chrome 运行 + 知乎登录态（yingmingyapei）
- 数据样例：`samples/zhihu-hot-2026-06-04.json`

### 微博热搜（2026-06-04 验证）

```bash
opencli browser weibo open "https://s.weibo.com/top/summary"
sleep 5
opencli browser weibo state
```

- 结果：50条热搜，含排名、标题、热度值、标签（热/新/辟谣/剧集/综艺）
- 前置条件：Chrome 运行 + 微博登录态（yingmingyapei）
- 数据样例：`samples/weibo-hot-2026-06-04.json`
- 注意：state 输出中热度值在 `<span>` 标签内，标签在 `<i>` 标签内

## 数据采集注意事项

1. **不限时、不限 token** — 数据要充分、实时、最新，不催不截断
2. **失败重试** — 某个 session 名失败时可换 session 名重试
3. **数据完整性校验** — 采集后检查条数是否合理（知乎~20条，微博~50条）
4. **页面加载等待** — sleep 5 是最低要求，复杂页面可能需要更长

## 雪球反爬应对方案

雪球有较强反爬，优先级：
1. opencli browser（Chrome 真实浏览器，最难检测）
2. 雪球 API + Cookie（先 browser 拿 Cookie，再 Python 请求 API）
3. curl_cffi impersonate（模拟 TLS 指纹）

## 两阶段 Cron 架构（讨论中）

将热点刀锋拆分为两个独立 cron job：

```
Job 1: 数据采集（agent模式，不限时）
  └── 逐平台 opencli browser 抓取
  └── 汇总写入 JSON 文件
  └── 失败重试，不降级

Job 2: 微头条生成（等 Job 1 完成后）
  └── 读取 Job 1 输出
  └── 校验数据完整性
  └── 选题 → 写作 → 推送
```

优势：故障隔离、数据可复用、Job 更薄。
