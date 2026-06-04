# 热点刀锋两阶段 Cronjob 架构设计（2026-06-04）

## 问题背景

旧方案的三个根因问题：

1. **环境未就绪就开跑** — Chrome/Extension 还没连上，命令直接超时，把环境问题误判为数据源问题
2. **降级太快太彻底** — 一次超时就切百度搜索（二手数据），不重试不排查
3. **数据采集和写作耦合** — 一个 job 做所有事，context 压力大，写作阶段被截断

## 新架构

数据采集和微头条生成整合在同一个 cronjob 内，两阶段控制：

```
热点刀锋定时任务（每天 08:30）
│
├── 第一阶段：环境就绪检查
│   └── 循环等待 Extension 连接，最多等 60 秒
│
├── 第二阶段：数据采集（5个第一手平台）
│   ├── 知乎热榜    opencli browser zhihu open + state
│   ├── 微博热搜    opencli browser weibo open + state
│   ├── B站热榜     opencli browser bilibili open + state
│   ├── 雪球热帖    opencli browser xueqiu open + state
│   └── 头条热榜    opencli browser toutiao open + state
│   每个平台：失败重试3次，不降级
│
├── 数据完整性校验
│   ├── 至少 3 个平台成功 → 继续
│   └── 不足 3 个平台 → 停止，不执行写作
│
├── 第四阶段：数据分析
│   └── Agent 逐条阅读原始热榜，推理判断选题
│
└── 第五阶段：微头条生成（仅在数据充分时执行）
    └── 七步写作 → 推送 Telegram
```

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 只用第一手数据 | 百度搜索返回的是百度算法加工过的二手数据，不是平台原始热榜 |
| 不限时不限Token | 用户明确要求：宁可慢不可糙，不赶进度 |
| 失败重试不降级 | 旧方案一次超时就切百度搜索，丢了一手数据 |
| 环境就绪检查 | 等 Extension 连接再开始，避免超时误判 |
| 数据分析用推理不用公式 | 用户明确要求：用推理能力判断，不是靠关键词匹配打分 |

## 环境就绪检查

```bash
for i in $(seq 1 12); do
  if opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
    echo "✅ Extension 已连接"
    break
  fi
  echo "等待 Extension 连接... ($((i*5))s)"
  sleep 5
done
```

## opencli browser 抓取模式

```bash
# 标准模式：open + sleep + state
opencli browser <session> open "<url>"
sleep 5
opencli browser <session> state > /tmp/<platform>_hot_raw.txt
```

## 已验证的平台（2026-06-04）

| 平台 | 命令 | 状态 |
|------|------|------|
| 知乎热榜 | `opencli browser zhihu open "https://www.zhihu.com/hot"` + state | ✅ 19条 |
| 微博热搜 | `opencli browser weibo open "https://s.weibo.com/top/summary"` + state | ✅ 50条 |
| B站热榜 | `opencli browser bilibili open "https://www.bilibili.com/v/popular/rank/all"` + state | 待验证 |
| 雪球热帖 | `opencli browser xueqiu open "https://xueqiu.com/hot/list"` + state | 待验证 |
| 头条热榜 | `opencli browser toutiao open "https://www.toutiao.com/hot-board/"` + state | 待验证 |

## 教训

1. **Chrome 开机自启已配置但可能有延迟** — cron job 在 08:00 触发时，Chrome + Extension + Daemon 的连接链可能还没建立完成。解决：循环等待。
2. **把环境故障当成数据源故障** — 旧方案超时后直接降级到百度搜索，实际上是环境没准备好。解决：先检查环境，再抓数据。
3. **百度搜索是二手数据** — 百度搜索"知乎热榜"返回的是百度算法排序的结果，不是知乎原始热榜。解决：直接访问平台页面。
