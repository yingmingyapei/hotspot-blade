# Cron Scheduler `deliver: "local"` 修复记录

> 日期：2026-05-30
> 根因：`cron/scheduler.py` 的 `_build_job_prompt()` 无条件注入 "do NOT use send_message" 指令

## 问题

`cron/scheduler.py` 第1092-1105行硬编码了 `cron_hint`：

```python
cron_hint = (
    "[IMPORTANT: You are running as a scheduled cron job. "
    "DELIVERY: Your final response will be automatically delivered "
    "to the user — do NOT use send_message or try to deliver "
    "the output yourself..."
)
```

这个指令对所有 cronjob 统一注入，不根据 `deliver` 配置变化：
- `deliver: "origin"` → 系统自动推送，Agent 不应使用 send_message ✅
- `deliver: "local"` → 系统不推送，Agent 应该使用 send_message ❌（被禁止了）

## 修复

将硬编码改为动态判断：

```python
deliver = job.get("deliver", "local")
if deliver == "local":
    cron_hint = (
        "[IMPORTANT: You are running as a scheduled cron job. "
        "DELIVERY: Your output will be saved locally only. "
        "You SHOULD use the send_message tool to deliver important content "
        "(like articles, reports, or summaries) to the user via Telegram. "
        "Push content in multiple messages if needed (e.g., one message per article). "
        "SILENT: If there is genuinely nothing new to report, respond "
        "with exactly \"[SILENT]\" (nothing else) to suppress delivery. "
        "Never combine [SILENT] with content — either report your "
        "findings normally, or say [SILENT] and nothing more.]\n\n"
    )
else:
    cron_hint = (
        "[IMPORTANT: You are running as a scheduled cron job. "
        "DELIVERY: Your final response will be automatically delivered "
        "to the user — do NOT use send_message or try to deliver "
        "the output yourself..."
    )
```

## 验证

修复后测试（2026-05-30 07:51）：
- 输出文件：100KB，包含5篇完整微头条
- Telegram推送：6条消息全部成功（msg_id: 2772-2777）
- cron_hint内容确认：第2059行显示 "You SHOULD use the send_message tool"

## 影响范围

所有使用 `deliver: "local"` 的 cronjob 都受益：
- hotspot-blade（每日热点刀锋）
- OpenCLI更新检查

## 关键原则

1. `deliver: "local"` + `send_message` = 分条推送，体验更好
2. `deliver: "origin"` = 系统自动推送最终回复
3. 修改 `scheduler.py` 后需要重启 Gateway 才能生效
