# opencli 社交媒体平台可用性矩阵

> 更新日期：2026-06-09
> 用途：快速判断哪些 opencli 命令可以直接使用（public），哪些需要 cookie/登录态

## 公开 API（无需 cookie，直接可用）

| 平台 | 命令 | 输出格式 | 备注 |
|------|------|----------|------|
| 今日头条 | `opencli toutiao hot -f json` | JSON 数组 | 稳定，30条热榜，含热度值和URL |
| V2EX | `opencli v2ex hot -f json` | JSON 数组 | 稳定，含标题/节点/回复数/URL |
| Hacker News | `opencli hackernews top -f json` | JSON 数组 | 稳定，含标题/分数/评论数/URL |
| DEV.to | `opencli devto top -f json` | JSON 数组 | 稳定，含标题/反应数/评论数/标签 |
| Stack Overflow | `opencli stackoverflow hot -f json` | JSON 数组 | 稳定，含标题/分数/回答数/标签 |
| 百度贴吧 | `opencli tieba hot -f json` | JSON 数组 | 稳定，含标题/讨论数/描述/URL |
| 36氪 | `opencli 36kr hot -f json` | JSON 数组 | ⚠️ 可能返回旧数据 |

## 需要 cookie（需浏览器登录态）

| 平台 | 命令 | 替代方案 |
|------|------|----------|
| 微博 | `opencli weibo hot -f json` | `opencli weibo search "热搜" -f json`（搜索替代） |
| 知乎 | `opencli zhihu hot -f json` | `opencli zhihu search "热榜" -f json`（搜索替代） |
| B站 | `opencli bilibili hot -f json` | 无直接替代 |
| 小红书 | `opencli xiaohongshu feed -f json` | 无直接替代 |
| 抖音 | `opencli douyin --help` | 无直接替代 |
| Reddit | `opencli reddit hot -f json` | 无直接替代 |
| Twitter/X | `opencli twitter trending -f json` | 无直接替代 |

## 搜索替代策略

当平台的 `hot` 命令需要 cookie 时，可以用 `search` 命令搜索热搜相关关键词作为替代：

```bash
# 微博热搜替代
opencli weibo search "热搜" -f json

# 知乎热榜替代
opencli zhihu search "热榜" -f json
```

**注意**：搜索结果 ≠ 热榜数据。搜索返回的是包含关键词的帖子，不是按热度排序的榜单。但对于发现当前热门话题仍然有价值。

## 快速采集脚本（交互模式）

```bash
# 并行采集所有公开平台
opencli toutiao hot -f json > /tmp/toutiao_hot.json &
opencli v2ex hot -f json > /tmp/v2ex_hot.json &
opencli hackernews top -f json > /tmp/hn_top.json &
opencli devto top -f json > /tmp/devto_top.json &
opencli tieba hot -f json > /tmp/tieba_hot.json &
wait
```

## Browser Bridge 依赖说明

- **公开命令**：直接通过 API 调用，不需要 Browser Bridge 扩展
- **cookie 命令**：需要 Chrome 浏览器运行 + Browser Bridge 扩展已连接
- **检查状态**：`opencli doctor` 查看 Extension 连接状态
- **重启 daemon**：`opencli daemon restart`（注意：`daemon start` 不存在）

## 故障排查

```
错误：Browser Bridge extension not connected
原因：Chrome 未运行或扩展未启用
解决：
  1. 确保 Chrome 已打开
  2. 检查 chrome://extensions 中 OpenCLI 扩展已启用
  3. 运行 opencli daemon restart
  4. 等待15秒后重试

错误：返回空数组 []
原因：需要登录态但未登录
解决：在 Chrome 中登录目标平台，然后重试

错误：Command timeout
原因：网络问题或目标平台反爬
解决：重试3次，间隔10秒
```
