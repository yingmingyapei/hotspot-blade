# 数据采集实战经验（2026-06-04 实测）

## opencli browser 各平台实测结果

### 已验证可用的URL

| 平台 | URL | 状态 | 数据量 |
|------|-----|------|--------|
| 知乎热榜 | `https://www.zhihu.com/hot` | ✅ 直接可用 | 19条，875行 |
| 微博热搜 | `https://s.weibo.com/top/summary` | ✅ 直接可用 | 50条，429行 |
| B站热榜 | `https://www.bilibili.com/v/popular/rank/all` | ✅ 直接可用 | 20+条，862行 |

### 需要重试的平台

| 平台 | 原始URL | 问题 | 解决方案 |
|------|---------|------|----------|
| 雪球 | `https://xueqiu.com/hot/list` | 404 | 改用首页 `https://xueqiu.com/`，提取"热门话题"10条 + feed流 |
| 头条 | `https://www.toutiao.com/hot-board/` | 404 | 改用首页 `https://www.toutiao.com/`，提取"头条热榜"区域 |

### JS重渲染网站的抓取技巧

雪球和头条都是重JS渲染的网站，必须：
1. **等待更长时间**：sleep 15 秒（不是5秒）
2. **滚动页面**：`opencli browser <session> scroll down` 触发懒加载
3. **多次state**：滚动后再取state，内容会更多（如雪球从1655行→1726行）
4. **不要因为第一次数据少就放弃**，多尝试几次

### 失败重试策略

```
每个平台：最多重试3次，每次间隔10秒
第1次失败 → 等10秒重试
第2次失败 → 等10秒重试，尝试不同URL
第3次失败 → 记录原因，继续下一个平台
至少3个平台成功才继续
```

## 环境就绪检查（必须在采集前执行）

```bash
# 等待 Extension 连接就绪，最多等 60 秒
for i in $(seq 1 12); do
  if opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
    echo "✅ Extension 已连接"
    break
  fi
  echo "等待 Extension 连接... ($((i*5))s)"
  sleep 5
done
```

**根因**：cron job 执行时 Chrome + Extension + Daemon 的连接链可能还没建立完成。
链条：Windows开机 → chrome-startup.bat启动Chrome → Chrome加载Extension → Extension连接Daemon → Daemon连接WSL

## 不限时，不限Token

整个数据采集过程：不限时，每个平台充分抓取，等页面完全加载，不赶进度。
失败重试，不降级到百度搜索等二手数据源。
