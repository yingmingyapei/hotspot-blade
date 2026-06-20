# opencli 诊断与调试（2026-06-04）

## opencli 环境状态检查

```bash
opencli doctor
```

预期输出：
```
[OK] Daemon: running on port 19825
[OK] Extension: connected
[OK] Connectivity: connected
```

## opencli 是正常的——问题通常在 Agent

**关键认知**：opencli 本身几乎不会出问题。当"opencli 不能用"时，通常是：
1. Agent 用了错误的命令（如 `opencli daemon start` 而非 `opencli daemon restart`）
2. Agent 根本没尝试 opencli，直接用了 Python urllib
3. Agent 卡在其他步骤，从未到达 opencli 调用

**验证 opencli 是否正常**：直接在 terminal 中手动执行：
```bash
opencli browser zhihu open "https://www.zhihu.com/hot"
sleep 5
opencli browser zhihu state | head -20
```

如果手动能用但 Agent 不用 → 问题在 prompt/skill，不在 opencli。

## opencli 常用命令

```bash
# 打开网页
opencli browser <profile> open "<url>"
# profile 是任意名称，会创建独立的浏览器会话

# 等待页面加载后获取状态
opencli browser <profile> state

# 滚动页面
opencli browser <profile> scroll down

# 点击元素
opencli browser <profile> click "<selector>"

# 输入文本
opencli browser <profile> type "<selector>" "<text>"
```

## Agent 常犯错误

| 错误 | 原因 | 正确做法 |
|------|------|---------|
| `opencli daemon start` | 命令不存在 | daemon 已在运行，不需要启动 |
| 用 `python3 -c "import urllib"` | SKILL.md 中有降级代码 | 清理 SKILL.md |
| 等待超时后卡死 | 没有超时处理 | 在 prompt 中设置重试次数上限 |
| 只抓一个平台就停止 | prompt 不够明确 | prompt 中列出所有平台的完整命令 |

## 定时任务中使用 opencli 的注意事项

1. **Chrome Extension 必须已连接** — cron job 运行时检查 `opencli doctor`
2. **页面需要等待时间** — 知乎/微博 5-8 秒，头条/雪球 15 秒（JS 渲染）
3. **失败重试** — 每个平台重试 3 次，间隔 10 秒
4. **不要降级** — 失败就跳过，不要用 Python 直接调 API
