# scheduler.py cron_hint 修复（2026-05-30）

## 问题

`cron/scheduler.py` 的 `_build_job_prompt()` 函数无条件注入统一的 `cron_hint`：

```python
# 旧代码（第1092-1105行）
cron_hint = (
    "[IMPORTANT: You are running as a scheduled cron job. "
    "DELIVERY: Your final response will be automatically delivered "
    "to the user — do NOT use send_message or try to deliver "
    "the output yourself..."
)
prompt = cron_hint + prompt
```

这个指令对所有 cronjob 都一样，不根据 `deliver` 配置变化：
- `deliver: "origin"` → 系统自动推送，Agent 不应使用 send_message ✅
- `deliver: "local"` → 系统不推送，Agent 应该使用 send_message ❌（但被禁止了）

## 修复

修改 `_build_job_prompt()` 函数，根据 `deliver` 配置动态生成不同的 `cron_hint`：

```python
# 新代码（第1092-1120行）
deliver = job.get("deliver", "local")
if deliver == "local":
    # For local delivery, the agent should use send_message to push content
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
    # For origin/platform delivery, the system handles delivery automatically
    cron_hint = (
        "[IMPORTANT: You are running as a scheduled cron job. "
        "DELIVERY: Your final response will be automatically delivered "
        "to the user — do NOT use send_message or try to deliver "
        "the output yourself. Just produce your report/output as your "
        "final response and the system handles the rest. "
        "SILENT: If there is genuinely nothing new to report, respond "
        "with exactly \"[SILENT]\" (nothing else) to suppress delivery. "
        "Never combine [SILENT] with content — either report your "
        "findings normally, or say [SILENT] and nothing more.]\n\n"
    )
```

## 验证

2026-05-30 07:51 热点刀锋任务执行结果：
- 输出文件：100KB，2380行，5篇微头条完整
- Telegram 推送：6条消息全部成功（msg_id: 2772-2777）
- 推送内容：1条摘要 + 5篇微头条（每篇独立一条消息）

## 影响范围

此修复影响所有 `deliver: "local"` 的 cron job：
- 热点刀锋（hotspot-blade）
- OpenCLI 更新检查
- 任何未来配置为 `deliver: "local"` 的任务

## 文件位置

- 修改文件：`~/.hermes/hermes-agent/cron/scheduler.py`
- 修改位置：`_build_job_prompt()` 函数，第1092-1120行
