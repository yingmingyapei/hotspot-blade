# Cron Hint 硬编码导致 deliver:local 无法自动推送

## 故障时间

2026-05-30

## 症状

热点刀锋 cronjob 配置 `deliver: "local"` 后，Agent 不会调用 `send_message` 推送微头条到 Telegram。
执行成功（`last_status: ok`），Wiki 文件已生成，但用户收不到推送。

## 根因

`cron/scheduler.py` 第1092-1105行，`_build_job_prompt()` 函数**无条件**注入固定 cron_hint：

```python
cron_hint = (
    "[IMPORTANT: You are running as a scheduled cron job. "
    "DELIVERY: Your final response will be automatically delivered "
    "to the user — do NOT use send_message or try to deliver "
    "the output yourself..."
)
prompt = cron_hint + prompt
```

这段指令对**所有** deliver 模式都一样：

| deliver 模式 | 实际行为 | cron_hint 指令 | 结果 |
|-------------|---------|---------------|------|
| `origin` | 系统自动推送 final reply | "do NOT use send_message" | ✅ 正确 |
| `local` | 系统不推送，需 Agent 调 send_message | "do NOT use send_message" | ❌ 矛盾！Agent 被禁止推送 |
| `platform:chat_id` | 系统自动推送到指定目标 | "do NOT use send_message" | ✅ 正确 |

## 修复方案

修改 `cron/scheduler.py` 的 `_build_job_prompt()` 函数，根据 `deliver` 配置动态生成不同 cron_hint：

```python
# 替换原来的固定 cron_hint（约第1092-1105行）
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
        "the output yourself. Just produce your report/output as your "
        "final response and the system handles the rest. "
        "SILENT: If there is genuinely nothing new to report, respond "
        "with exactly \"[SILENT]\" (nothing else) to suppress delivery. "
        "Never combine [SILENT] with content — either report your "
        "findings normally, or say [SILENT] and nothing more.]\n\n"
    )
```

## 修复后需重启 Gateway

修改 `scheduler.py` 后必须重启 Gateway 才能生效：

```bash
# 重启 Gateway
hermes gateway restart
# 或手动 kill 后重启
pkill -f "gateway run"
hermes gateway run
```

## 验证步骤

1. 确认 scheduler.py 已修改
2. 重启 Gateway
3. 手动触发 cronjob：`hermes cronjob run <job-id>`
4. 检查 Telegram 是否收到分条推送的微头条

## 影响范围

所有使用 `deliver: "local"` 的 cronjob 都受影响。修复后，这些 cronjob 的 Agent 会自动使用 send_message 推送内容。

## 与其他 deliver 模式的交互

- `deliver: "origin"` → 系统推送到会话，Agent 不应调 send_message（保持不变）
- `deliver: "local"` → 系统不推送，Agent 应调 send_message（修复后）
- `deliver: "telegram:chat_id"` → 系统推送到指定目标，Agent 不应调 send_message（保持不变）
- `deliver: "all"` → 系统推送到所有连接的频道，Agent 不应调 send_message（保持不变）
