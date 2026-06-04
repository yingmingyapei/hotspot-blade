# 数据源审计报告 - 2026-06-02

> 本次审计基于头条号数据诊断结果，重新评估各数据源的头条适配性。

---

## 一、数据源可用性

| 数据源 | 可用性 | 抓取方式 | 登录态要求 | 定时任务兼容 |
|--------|--------|---------|-----------|-------------|
| 百度热搜 | ✅ | urllib直接抓取 | 无 | ✅ |
| 头条站内热榜 | ✅ | opencli browser | Chrome登录态 | ⚠️ 需Chrome运行 |
| 知乎热榜 | ✅ | opencli browser / 百度搜索间接 | Chrome登录态 | ⚠️ 需Chrome运行 |
| 微博热搜 | ✅ | opencli browser / 百度搜索间接 | Chrome登录态 | ⚠️ 需Chrome运行 |
| Buzzing.cc | ✅ | curl→文件→Python | 无 | ✅ |
| YouMind | ✅ | Python脚本+代理 | 无（需HTTP代理） | ✅ |
| HN Firebase | ✅ | urllib直接抓取 | 无 | ✅（已弃用） |

---

## 二、opencli登录态行为

**关键发现**：opencli browser复用Chrome浏览器的登录态。

### 验证结果（2026-06-02）

| 平台 | Chrome登录态 | opencli结果 | 热榜数据 |
|------|-------------|-------------|---------|
| 知乎 | ✅ 已登录 | 自动登录成功 | ✅ 20条热榜正常显示 |
| 微博 | ❌ 未登录 | 需手动登录 | 登录后✅ 50条热搜正常显示 |
| 头条 | ✅ 已登录 | 自动登录成功 | ✅ 内容管理/评论/数据正常 |

**定时任务环境注意事项**：
- 如果Chrome未运行，opencli无法复用登录态
- 解决方案：确保Chrome在后台运行，或降级到百度搜索间接获取

---

## 三、数据源权重配置（v3.3）

| 数据源 | 权重 | 定位 | 头条适配性 |
|--------|------|------|-----------|
| 百度热搜 | 30% | 国内大众热点 | ⭐⭐⭐ |
| 头条站内热榜 | 25% | 直接命中头条用户 | ⭐⭐⭐⭐⭐ |
| 知乎热榜 | 20% | 深度社会议题 | ⭐⭐⭐⭐ |
| 微博热搜 | 10% | 舆情风向标 | ⭐⭐⭐ |
| Buzzing.cc | 10% | 海外信息差 | ⭐⭐ |
| YouMind | 5% | 海外爆款追踪 | ⭐⭐ |
| ~~HN Firebase~~ | 已弃用 | 科技向不适配 | ⭐ |

---

## 四、HN Firebase弃用原因

**实测数据**：
- Claude Code和Codex文章：28展现，0阅读，0%点击率
- 科技类内容整体互动率：0.06%

**结论**：头条用户对纯科技内容不感兴趣，HN Firebase的科技向内容不适配头条用户画像。

---

## 五、知乎/微博百度搜索间接获取

当Chrome未运行或登录态失效时，使用百度搜索间接获取：

```bash
# 知乎热榜
python3 -c "
import urllib.request, re
url = 'https://www.baidu.com/s?wd=知乎热榜+今日+热门话题'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
text = resp.read().decode('utf-8')
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
topics = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if len(re.sub(r'<[^>]+>', '', t).strip()) > 5]
for i, t in enumerate(topics[:15]):
    print(f'#{i+1} {t[:80]}')
"

# 微博热搜
python3 -c "
import urllib.request, re
url = 'https://www.baidu.com/s?wd=微博热搜+今日+热门话题'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
text = resp.read().decode('utf-8')
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', text, re.DOTALL)
topics = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if len(re.sub(r'<[^>]+>', '', t).strip()) > 5]
for i, t in enumerate(topics[:15]):
    print(f'#{i+1} {t[:80]}')
"
```

---

## 六、头条号实测数据（选题类型×点击率）

| 选题类型 | 点击率 | 代表文章 | 结论 |
|---------|--------|---------|------|
| 国际政治/外交 | 10.8%-13.7% | PMI文章(304阅读)、比特币文章(127阅读) | 最高，优先选择 |
| 社会民生 | 5%-10% | 渣打裁员(0.29%互动率) | 第二优先 |
| 军事/国防 | 3%-5% | 鹰击20(热词加持) | 适度选择 |
| 商业/财经 | 1%-3% | 日系车暴雷 | 需降维 |
| 科技/AI | 0%-0.14% | Claude Code(28展现0阅读) | 慎用，必须降维 |

---

## 七、优化闭环

```
每日 8:00 热点刀锋执行
    ↓
使用当前数据源权重+选题权重
    ↓
生成5篇微头条
    ↓
每周一 12:00 toutiao-weekly执行
    ↓
分析上周数据（点击率/互动率）
    ↓
自动调整选题权重和标题公式
    ↓
下周一热点刀锋使用新权重
```
