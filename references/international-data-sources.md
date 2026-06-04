# 国际热点数据源集成

> **目标**：从国外社交平台获取国际热点信息，补充热点刀锋的海外信息差选题。
> **实测日期**：2026-06-02

## 可用数据源

### 1. Twitter/X（✅ 强烈推荐）

**抓取方式**：opencli browser（需Chrome登录态）

**命令语法**：
```bash
# 基础搜索（query是位置参数，不是--query）
opencli twitter search "trending" --limit 10 -f json

# 中文热点
opencli twitter search "中国 OR 热门 OR 热搜" --limit 10 -f json

# 特定用户
opencli twitter search "#AI" --from elonmusk --limit 5 -f json

# 按互动量排序
opencli twitter search "China economy" --top-by-engagement 10 -f json

# 过滤媒体类型
opencli twitter search "breaking news" --has videos --limit 10 -f json

# 排除转推
opencli twitter search "AI" --exclude retweets --limit 10 -f json
```

**返回字段**：id, author, bio, text, created_at, likes, views, url, has_media, media_urls, card, quoted_tweet

**适配性**：
- 国际政治/外交：⭐⭐⭐⭐⭐
- 科技/AI：⭐⭐⭐⭐
- 财经/投资：⭐⭐⭐⭐
- 社会民生：⭐⭐⭐

### 2. YouTube（✅ 推荐）

**抓取方式**：opencli browser（需Chrome登录态）

**命令语法**：
```bash
# 搜索视频
opencli youtube search "中国 2026" --limit 10 -f json

# 英文搜索
opencli youtube search "China economy" --limit 10 -f json

# 获取视频详情
opencli youtube video <video_id> -f json

# 获取视频评论
opencli youtube comments <video_id> --limit 20 -f json

# 获取频道信息
opencli youtube channel <channel_id> -f json
```

**返回字段**：channel, duration, published, rank, title, url, views

**适配性**：
- 国际政治/外交：⭐⭐⭐⭐
- 科技/AI：⭐⭐⭐⭐
- 财经/投资：⭐⭐⭐
- 社会民生：⭐⭐

### 3. Reddit（⚠️ CLI返回空，需用浏览器）

**抓取方式**：opencli browser

**命令语法**：
```bash
# CLI方式（❌ 返回空数组）
opencli reddit hot --limit 10 -f json

# 浏览器方式（✅ 可用）
opencli browser toutiao open "https://www.reddit.com/r/worldnews/"
sleep 5
opencli browser toutiao extract
```

**推荐子版块**：
- r/worldnews - 世界新闻
- r/news - 美国新闻
- r/europe - 欧洲新闻
- r/Economics - 经济学
- r/stocks - 股票
- r/technology - 科技

**适配性**：
- 国际政治/外交：⭐⭐⭐⭐⭐
- 科技/AI：⭐⭐⭐
- 财经/投资：⭐⭐⭐
- 社会民生：⭐⭐

### 4. Facebook（⚠️ 内容质量参差）

**抓取方式**：opencli browser（需Chrome登录态）

**命令语法**：
```bash
opencli facebook search "中国" --limit 10 -f json
opencli facebook feed --limit 10 -f json
```

**注意**：搜索结果内容质量参差，需要筛选。

### 5. Instagram（❌ 命令报错）

**问题**：`opencli instagram explore` 返回JSON解析错误

**替代方案**：用浏览器直接访问
```bash
opencli browser toutiao open "https://www.instagram.com/explore/"
```

## 数据源优先级

| 优先级 | 数据源 | 理由 |
|--------|--------|------|
| P0 | Twitter/X | 信息量大、更新快、互动数据完整 |
| P0 | Reddit | 国际新闻质量高、讨论深度好 |
| P1 | YouTube | 视频内容、有浏览量数据 |
| P2 | Facebook | 内容质量参差，需筛选 |
| P3 | Instagram | 命令报错，需用浏览器 |

## 选题适配性

| 话题类型 | Twitter/X | YouTube | Reddit | 适配性 |
|---------|-----------|---------|--------|--------|
| 国际政治/外交 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 最佳 |
| 科技/AI | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 需降维 |
| 财经/投资 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 需降维 |
| 社会民生 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 一般 |

## 实际案例（2026-06-02）

### Twitter/X 热门话题

| 话题 | 互动 | 选题价值 |
|------|------|---------|
| AiToEarn自媒体变现工具 | 38赞/1823浏览 | ⭐⭐⭐ 科技/副业 |
| 德国之声：中国垃圾焚烧 | 96赞/59782浏览 | ⭐⭐⭐⭐ 社会/环保 |
| A股热门题材汇总 | - | ⭐⭐⭐⭐⭐ 财经/投资 |

### Reddit 热门新闻

| 话题 | 选题价值 |
|------|---------|
| 伊朗停止与美国谈判，封锁霍尔木兹海峡 | ⭐⭐⭐⭐⭐ 国际政治 |
| 基辅遭俄罗斯大规模袭击 | ⭐⭐⭐⭐⭐ 国际政治 |
| 36国起诉普京 | ⭐⭐⭐⭐ 国际政治 |
| 美国轰炸伊朗军事目标 | ⭐⭐⭐⭐⭐ 国际政治 |

### YouTube 热门视频

| 话题 | 浏览量 | 选题价值 |
|------|--------|---------|
| 日本回击中国"新军国主义"指控 | 21,773 | ⭐⭐⭐⭐ 国际政治 |
| 2026年中国经济展望 | 58,961 | ⭐⭐⭐⭐ 财经 |

## 集成建议

在热点刀锋定时任务中，增加国际数据源抓取：

```bash
# 1. Twitter/X 热门（国际政治/科技/财经）
opencli twitter search "trending OR breaking" --limit 10 -f json

# 2. Reddit 世界新闻（国际政治）
opencli browser toutiao open "https://www.reddit.com/r/worldnews/"
sleep 5
opencli browser toutiao extract

# 3. YouTube 中国相关（国际视角）
opencli youtube search "China 2026" --limit 10 -f json
```

**选题权重建议**：
- 国际政治/外交：从Twitter/X和Reddit获取，权重40%
- 科技/AI：从Twitter/X获取，权重5%（需降维）
- 财经/投资：从Twitter/X获取，权重10%
