# MCP cn-finance 工具作为数据源降级方案

> **日期**：2026-06-04
> **场景**：定时任务深夜执行（23:10），Chrome未运行，opencli Daemon未启动

## 问题

opencli doctor 显示：
- Daemon: not running
- Extension: not connected
- Connectivity: failed

opencli daemon restart 也超时。所有站点适配器命令（zhihu hot, weibo hot, bilibili hot, xueqiu hot）均超时。toutiao hot 报 URL 协议错误。

**根因**：深夜23点，Windows主机上Chrome未运行，opencli daemon无法启动（daemon依赖Chrome进程）。

## 解决方案：MCP cn-finance 工具

MCP cn-finance 提供以下工具，可作为opencli失败时的替代数据源：

| MCP工具 | 定位 | 数据质量 | 替代的opencli命令 |
|---------|------|---------|------------------|
| `finance_cls` | 财联社实时快讯 | ✅ 高（实时更新，含时间戳） | 部分替代热榜（提供实时热点信号） |
| `finance_news` | 同花顺问财新闻搜索 | ✅ 高（覆盖官媒/财经媒体/行业网站） | 替代各平台热榜（按关键词搜索热点） |
| `finance_announcement` | 上市公司公告 | ✅ 高（权威数据源） | 不直接替代，补充选题素材 |
| `finance_mx` | 东方财富妙想数据 | ✅ 高（行情/财务/资金） | 不直接替代，补充数据弹药 |
| `finance_query` | 同花顺问财自然语言查询 | ✅ 高（个股/板块/技术指标） | 不直接替代，补充数据弹药 |

## 为什么不违反铁律

hotspot-blade的铁律是：**禁止使用urllib/requests/curl直接调API**。

MCP cn-finance 是 Hermes 内置的MCP工具，由Agent通过标准MCP协议调用，不是Python脚本直接调HTTP API。这与"降级到Python直接调API"有本质区别：

- ❌ 违反铁律：`python3 -c "import urllib; ..."` 直接调百度搜索API
- ❌ 违反铁律：`curl https://api.zhihu.com/...` 直接调知乎API
- ✅ 允许：`mcp_cn_finance_finance_cls(limit=30)` 通过MCP协议调用财联社数据

## 实操采集流程（MCP降级模式）

### 第一步：获取实时快讯
```
mcp_cn_finance_finance_cls(limit=30)
```
→ 获取财联社最新30条快讯，包含时间戳

### 第二步：按领域搜索热点新闻
```
mcp_cn_finance_finance_news(query="国际政治 外交", limit=15)
mcp_cn_finance_finance_news(query="社会民生 教育 就业", limit=15)
mcp_cn_finance_finance_news(query="军事 国防 中东", limit=15)
```
→ 覆盖国际政治、社会民生、军事国防三个头条用户最关心的领域

### 第三步：深度搜索补充细节
使用 `delegate_task` 配合 search/web 工具集，对筛选出的话题进行深度搜索：
```
delegate_task(tasks=[
  {goal: "搜索XX话题的详细信息...", toolsets: ["search", "web"]},
  {goal: "搜索YY话题的详细信息...", toolsets: ["search", "web"]},
  ...
])
```
→ 获取具体数字、引语、背景、对比数据

### 第四步：正常进入数据分析和选题流程
从MCP工具返回的数据中，按头条适配性+碰撞潜力筛选话题。

## 数据质量对比

| 维度 | opencli（5平台热榜） | MCP cn-finance |
|------|---------------------|----------------|
| 数据类型 | 平台原始热榜排序 | 财经新闻搜索结果 |
| 覆盖范围 | 知乎/微博/B站/雪球/头条 | 财联社+同花顺+官媒+行业网站 |
| 社会议题覆盖 | ✅ 高（知乎微博） | 🟡 中（偏财经，需多关键词搜索） |
| 国际政治覆盖 | 🟡 中（Buzzing.cc/HN） | ✅ 高（财联社覆盖国际新闻） |
| 时效性 | ✅ 实时 | ✅ 实时（CLS更新到分钟级） |
| 数据结构 | JSON（有热度值/排名） | 文本（有时间戳/摘要/链接） |
| 头条选题适用性 | ✅ 高（直接看热榜排名） | 🟡 中（需Agent自行筛选判断） |

## 建议

- **优先级**：opencli > MCP cn-finance（MCP是降级方案，不是首选）
- **触发条件**：opencli doctor 显示 Daemon not running 且 daemon restart 超时
- **数据补充**：MCP数据偏财经，需通过多关键词搜索覆盖社会/国际/军事等领域
- **深度搜索**：delegate_task + search/web 是MCP降级模式下的关键补充步骤
