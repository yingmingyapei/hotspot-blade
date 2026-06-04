# 平台登录态与热榜抓取实测记录 - 2026-06-02

> 通过 opencli browser 工具复用 Chrome 登录态，逐一测试国内主流社交平台的热榜抓取可行性。

---

## 测试结果汇总

| 平台 | 登录状态 | 热榜URL | 数据质量 | 可靠性 |
|------|---------|---------|---------|--------|
| 知乎 | ✅ 已登录 | `https://www.zhihu.com/hot` | 20条热榜+热度值 | ⭐⭐⭐⭐⭐ |
| 微博 | ✅ 已登录 | `https://s.weibo.com/top/summary` | 50条热搜+热度值 | ⭐⭐⭐⭐⭐ |
| 今日头条 | ✅ 已登录 | `https://www.toutiao.com` (首页含热榜) | 10条热榜+热点新闻 | ⭐⭐⭐⭐⭐ |
| 小红书 | ✅ 已登录 | `https://www.xiaohongshu.com/explore` | 推荐流（无传统热榜） | ⭐⭐⭐⭐ |
| 抖音 | ✅ 已登录 | `https://www.douyin.com/hot` | 50条热榜+热度值 | ⭐⭐⭐⭐⭐ |
| 雪球 | ✅ 已登录 | `https://xueqiu.com/hot` | ❌ 503错误 | ⭐ (不可用) |

---

## 关键发现

### 1. opencli browser 复用 Chrome 登录态

- 前提：Chrome 必须在后台运行，且已登录目标平台
- opencli browser 会自动复用 Chrome 的 cookie/session
- **无需在定时任务中重新登录**
- 如果 Chrome 未运行，会启动新实例，无登录态

### 2. Chrome 开机自启动

已配置 Windows 启动文件夹批处理脚本：
```
路径：C:\Users\yingm\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\chrome-startup.bat
内容：start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --no-first-run --no-default-browser-check
```

### 3. 雪球反爬机制

- 雪球 `/hot` 页面返回 HTTP 503
- 即使已登录也无法访问热榜页面
- 建议：跳过雪球，用百度搜索"雪球热榜"间接获取财经类话题
- 雪球主要是投资理财社区，头条用户对财经类兴趣有限（点击率1%-3%）

### 4. 小红书无传统热榜

- 小红书没有像微博/抖音那样的热榜页面
- 推荐流（`/explore`）即为热门内容
- 提取推荐流标题作为选题来源

---

## 各平台抓取命令

### 知乎热榜
```bash
# 方案1：opencli browser（需Chrome登录态）
opencli browser toutiao open "https://www.zhihu.com/hot"
sleep 5
opencli browser toutiao extract

# 方案2：百度搜索间接获取（无需登录态）
python3 -c "
import urllib.request, re
url = 'https://www.baidu.com/s?wd=知乎热榜+今日+热门话题'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
text = resp.read().decode('utf-8')
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
for i, t in enumerate([re.sub(r'<[^>]+>', '', x).strip() for x in titles if len(re.sub(r'<[^>]+>', '', x).strip()) > 5][:15]):
    print(f'  #{i+1} {t[:80]}')
"
```

### 微博热搜
```bash
# 方案1：opencli browser（需Chrome登录态）
opencli browser toutiao open "https://s.weibo.com/top/summary"
sleep 5
opencli browser toutiao extract

# 方案2：百度搜索间接获取
python3 -c "
import urllib.request, re
url = 'https://www.baidu.com/s?wd=微博热搜+今日+热门话题'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
text = resp.read().decode('utf-8')
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
for i, t in enumerate([re.sub(r'<[^>]+>', '', x).strip() for x in titles if len(re.sub(r'<[^>]+>', '', x).strip()) > 5][:15]):
    print(f'  #{i+1} {t[:80]}')
"
```

### 今日头条热榜
```bash
opencli browser toutiao open "https://www.toutiao.com"
sleep 5
opencli browser toutiao extract
# 热榜在页面右侧"头条热榜"区域
```

### 小红书推荐流
```bash
opencli browser toutiao open "https://www.xiaohongshu.com/explore"
sleep 5
opencli browser toutiao extract
# 推荐流即热门内容，提取标题作为选题来源
```

### 抖音热榜
```bash
opencli browser toutiao open "https://www.douyin.com/hot"
sleep 5
opencli browser toutiao extract
# 50条热榜，含热度值
```

---

## 数据源权重配置（v3.3）

| 数据源 | 权重 | 定位 | 抓取方式 |
|--------|------|------|---------|
| 百度热搜 | 30% | 国内大众热点 | urllib直接抓取 |
| 头条站内热榜 | 25% | 直接命中头条用户 | opencli browser |
| 知乎热榜 | 20% | 深度社会议题 | opencli browser / 百度搜索 |
| 微博热搜 | 10% | 舆情风向标 | opencli browser / 百度搜索 |
| Buzzing.cc | 10% | 海外信息差 | curl下载 |
| YouMind | 5% | 海外爆款 | Python脚本 |

---

## 故障降级策略

| 故障场景 | 降级方案 |
|---------|---------|
| Chrome未运行 | 降级到百度搜索间接获取 |
| 知乎/微博抓取失败 | 权重重新分配：百度45% + 头条35% + Buzzing15% + YouMind5% |
| 头条站内抓取失败 | 权重重新分配：百度45% + 知乎25% + 微博15% + Buzzing10% + YouMind5% |
| 雪球503错误 | 跳过雪球，用百度搜索间接获取财经类话题 |
| 所有opencli browser失败 | 降级到百度+Buzzing+YouMind（纯API方案） |
