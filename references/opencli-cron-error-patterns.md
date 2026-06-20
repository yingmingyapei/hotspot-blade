# opencli 定时任务错误模式与修复

> 2026-06-04 四轮 cron 执行中提取的6类错误

## 错误1: opencli daemon start 命令不存在

**日志**: `error: unknown command 'start' (Did you mean restart?)`
**根因**: Agent 执行了不存在的子命令
**正确**: `opencli daemon restart`（如果需要重启）
**预防**: SKILL.md 已标注"禁止执行 daemon start"

## 错误2: Agent 从未调用 opencli

**日志**: Agent 直接用 urllib/curl 抓取数据
**根因**: SKILL.md 有115处 Python 降级代码诱导 Agent
**预防**: 物理删除 Python 代码，不能只靠"禁止"声明

## 错误3: 深夜 Chrome 未运行

**日志**: Daemon: not running, Extension: not connected
**根因**: 深夜23点 Windows 端 Chrome 未启动
**预防**: 使用站点适配器直接命令（`opencli zhihu hot`等），不需要 Chrome

## 错误4: 安全审批阻塞

**日志**: pending_approval — cat /mnt/c/... 需要确认
**根因**: cron 模式下无法交互审批
**预防**: 改用 read_file 工具替代 cat

## 错误5: hermes send 超时

**日志**: Telegram send failed: Timed out
**根因**: 消息体过长（700+中文字符）
**预防**: 控制单条消息 ≤500中文字符

## 错误6: API 连接中断

**日志**: APIConnectionError — 小米 API 连接失败
**根因**: 网络波动或 API 服务瞬时异常
**预防**: 内置重试机制自动恢复，无需人工干预

## 核心教训

1. **cron job prompt 和模板文件是独立的** — 改模板不改 prompt，Agent 行为不变
2. **弱模型会照搬 SKILL.md 中的命令** — 包括故障排除中的"解决：xxx"
3. **铁律不能只靠声明** — 必须物理删除诱惑代码
4. **opencli 本身几乎不会出错** — 问题通常在 Agent 的错误操作
5. **站点适配器直接命令不需要 Chrome** — 深夜/无人值守也能用
