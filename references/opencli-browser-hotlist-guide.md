# opencli browser 热榜抓取实操指南

> 更新日期：2026-06-04
> 基于实际抓取经验总结

## 已验证可用的热榜URL

| 平台 | URL | 状态 | 数据量 |
|------|-----|------|--------|
| 知乎热榜 | `https://www.zhihu.com/hot` | ✅ 可用 | 19条，含标题+热度值 |
| 微博热搜 | `https://s.weibo.com/top/summary` | ✅ 可用 | 50条，含标题+热度值+标签 |
| B站热榜 | `https://www.bilibili.com/v/popular/rank/all` | ✅ 可用 | 20+条 |
| 雪球首页 | `https://xueqiu.com/` | ⚠️ 需滚动 | 热门话题10条 + feed流文章 |
| 头条首页 | `https://www.toutiao.com/` | ⚠️ 需等待 | 热搜3-8条 + 正文流文章 |

## 失效URL（返回404）

| 平台 | 失效URL | 替代方案 |
|------|---------|---------|
| 雪球热帖 | `https://xueqiu.com/hot/list` → 404 | 用首页 `https://xueqiu.com/`，滚动后提取"热门话题"区域 |
| 头条热榜 | `https://www.toutiao.com/hot-board/` → 404 | 用首页 `https://www.toutiao.com/`，等待15秒后提取"头条热榜"区域 |

## 环境前置条件

**每次执行前必须检查：**
```bash
opencli doctor
# 预期：[OK] Daemon: running + [OK] Extension: connected
```

**如果 Extension 未连接，循环等待：**
```bash
for i in $(seq 1 12); do
  opencli doctor 2>/dev/null | grep -q "Extension: connected" && break
  sleep 5
done
```

**超时根因分析：**
- Chrome 未启动 → chrome-startup.bat 未执行
- Extension 未连接 → Chrome 刚启动，Extension 还没初始化
- Daemon 未运行 → systemd 服务未启动
- **正确做法：等环境就绪再跑，不要降级到百度搜索**

## 各平台数据提取方法

### 知乎热榜
```bash
opencli browser zhihu open "https://www.zhihu.com/hot"
sleep 5
opencli browser zhihu state > /tmp/zhihu_hot_raw.txt
```
state 输出格式：标题在 `title=` 字段，热度值在 `热` 标签附近

### 微博热搜
```bash
opencli browser weibo open "https://s.weibo.com/top/summary"
sleep 5
opencli browser weibo state > /tmp/weibo_hot_raw.txt
```
state 输出格式：标题在 `<a href=/weibo?q=...>标题</a>` 中，热度在 `<span>` 中
提取命令：`grep -oP '(?<=<a href=/weibo\?q=)[^>]+>[^<]+' file | sed 's/.*>//'`

### B站热榜
```bash
opencli browser bilibili open "https://www.bilibili.com/v/popular/rank/all"
sleep 5
opencli browser bilibili state > /tmp/bilibili_hot_raw.txt
```

### 雪球（需滚动）
```bash
opencli browser xueqiu open "https://xueqiu.com/"
sleep 15  # JS渲染需要更长时间
opencli browser xueqiu scroll down
sleep 3
opencli browser xueqiu scroll down
sleep 3
opencli browser xueqiu state > /tmp/xueqiu_hot_raw.txt
```
热门话题在 `<h3>热门话题</h3>` 后的 table 中，格式：`| 序号 | [标题](链接) |`
热股榜在 `<h3>热股榜</h3>` 后

### 头条（需等待JS渲染）
```bash
opencli browser toutiao open "https://www.toutiao.com/"
sleep 15  # JS渲染需要更长时间
opencli browser toutiao state > /tmp/toutiao_hot_raw.txt
```
热搜在 `aria-label=热搜` 区域，格式：`<a aria-label=标题 href=/trending/.../?rank=N />`
额外数据：正文流中有更多文章标题

## JS渲染等待时间

| 平台 | 最小等待 | 推荐等待 | 说明 |
|------|---------|---------|------|
| 知乎 | 5秒 | 5秒 | 静态渲染，快 |
| 微博 | 5秒 | 5秒 | 静态渲染，快 |
| B站 | 5秒 | 8秒 | 轻度JS |
| 雪球 | 10秒 | 15秒+滚动 | 重度JS，需要滚动触发feed加载 |
| 头条 | 10秒 | 15秒 | 重度JS，热搜区域延迟加载 |

## 常见问题

### opencli browser 命令超时
- 检查 Chrome 是否在 Windows 端运行
- 检查 Extension 是否连接（`opencli doctor`）
- 重试，等待环境就绪

### 页面返回404
- URL可能已失效，尝试平台首页
- 检查是否需要登录态

### state 输出内容太少
- JS渲染未完成，增加等待时间
- 尝试滚动页面触发更多内容加载
- 部分平台（雪球、头条）需要15秒以上等待

### 数据提取困难
- state 输出是DOM树格式，不是纯文本
- 用 grep/正则提取标题和关键信息
- 不同平台的DOM结构不同，需要针对性处理
