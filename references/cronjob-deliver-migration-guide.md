# Cronjob Deliver 迁移指南：origin → local

> 记录日期: 2026-05-30
> 适用场景: 任何需要将 cronjob 从 `deliver: "origin"` 迁移到 `deliver: "local"` 的任务

## 为什么要迁移

`deliver: "origin"` 推送的是 Agent 的**最终回复**，不是技能的所有产出。如果 Agent 只在最终回复中输出摘要，用户收不到正文。

## 迁移步骤

### 1. 更新 deliver 配置

```bash
hermes cronjob update <job_id> --deliver "local"
```

### 2. 确认技能内有 send_message 调用

`deliver: "local"` 模式下，执行报告保存到本地文件，不会自动推送到任何平台。技能内部必须显式调用 `send_message` 工具推送结果。

检查 `templates/cronjob-prompt.md` 中是否有推送步骤。

### 3. 立即执行验证

使用 `cronjob run` 触发立即执行，验证推送是否正常：

```bash
hermes cronjob run <job_id>
```

**⚠️ `cronjob run` 行为说明**：
- 触发**立即执行**，不影响原定调度计划
- `next_run_at` 字段可能暂时显示当前执行时间，但原计划时间不变
- 执行完成后 `next_run_at` 会恢复为原计划时间

## 推送方式对比

| 配置 | 推送内容 | 推送时机 | 适用场景 |
|------|----------|----------|----------|
| `deliver: "origin"` | Agent 最终回复 | 执行完成后自动 | 简单输出，Agent 会把所有内容放在最终回复 |
| `deliver: "local"` | 不自动推送 | 需要技能内 send_message | 复杂输出，需要分条推送或精确控制格式 |
| `deliver: "all"` | Agent 最终回复 | 推送到所有已连接平台 | 多平台同步 |

## 常见问题

**Q: 修改 deliver 后需要重新创建任务吗？**
A: 不需要，`hermes cronjob update` 直接修改现有任务。

**Q: `cronjob run` 会跳过今天的定时执行吗？**
A: 不会。手动触发和定时执行是独立的。如果手动触发后还在同一调度窗口内，定时执行仍会触发。

**Q: 如何确认任务正在执行？**
A: 检查输出目录：
```bash
ls -la ~/.hermes/cron/output/<job_id>/ | tail -5
```
