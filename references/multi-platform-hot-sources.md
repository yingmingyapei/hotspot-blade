# 多平台热榜数据源验证记录（2026-06-02）

> 基于实际登录验证，记录各平台热榜的opencli browser抓取方案。

## 验证状态

| 平台 | 状态 | 登录方式 | 热榜URL | 数据量 |
|------|------|---------|---------|--------|
| **知乎热榜** | ✅ 已验证 | Chrome登录态 | `https://www.zhihu.com/hot` | 20条 |
| **微博热搜** | ✅ 已验证 | Chrome登录态 | `https://s.weibo.com/top/summary` | 50条 |
| **今日头条热榜** | ✅ 已验证 | Chrome登录态 | `https://www.toutiao.com` | 10条+热点新闻 |
| **小红书推荐流** | ✅ 已验证 | Chrome登录态 | `https://www.xiaohongshu.com/explore` | 推荐流（无传统热榜） |
| **抖音热榜** | ✅ 已验证 | Chrome登录态 | `https://www.douyin.com/hot` | 50条 |
| **百度热搜** | ✅ 已验证 | 无需登录 | urllib直接抓取 | 52条 |

## 抓取命令

### 知乎热榜
```bash
opencli browser toutiao open "https://www.zhihu.com/hot"
sleep 5
opencli browser toutiao extract
```

### 微博热搜
```bash
opencli browser toutiao open "https://s.weibo.com/top/summary"
sleep 5
opencli browser toutiao extract
```

### 今日头条热榜
```bash
opencli browser toutiao open "https://www.toutiao.com"
sleep 5
opencli browser toutiao extract
```

### 小红书推荐流
```bash
opencli browser toutiao open "https://www.xiaohongshu.com/explore"
sleep 5
opencli browser toutiao extract
```

### 抖音热榜
```bash
opencli browser toutiao open "https://www.douyin.com/hot"
sleep 5
opencli browser toutiao extract
```

## 前提条件

**Chrome必须在后台运行，且已登录目标平台。**

### Chrome开机自启动配置
已创建Windows开机自启动脚本：
```
C:\Users\yingm\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\chrome-startup.bat
```

### 登录态有效期
- 知乎：登录态长期有效（几周到几个月）
- 微博：登录态长期有效
- 今日头条：登录态长期有效
- 小红书：登录态长期有效
- 抖音：登录态长期有效

### 降级策略
如果Chrome未运行或登录态过期：
1. 知乎/微博：降级到百度搜索间接获取
2. 今日头条：降级到百度热搜
3. 小红书/抖音：跳过，使用其他数据源

## 数据源权重配置（v3.3）

| 数据源 | 权重 | 定位 |
|--------|------|------|
| 百度热搜 | 30% | 国内大众热点 |
| 头条站内热榜 | 25% | 直接命中头条用户兴趣 |
| 知乎热榜 | 20% | 深度社会议题，九边风格最佳素材 |
| 微博热搜 | 10% | 舆情风向标，时效性强 |
| Buzzing.cc | 10% | 海外信息差 |
| YouMind X爆款 | 5% | 海外爆款追踪 |

## 注意事项

1. **定时任务环境**：Chrome必须在后台运行，否则opencli browser会失败
2. **登录态维护**：定期检查登录态是否过期，过期需手动重新登录
3. **数据时效性**：热榜数据实时变化，抓取后尽快使用
4. **反爬风险**：频繁抓取可能触发反爬，建议控制频率
