# 热点刀锋 Cronjob 推送模式详解

> 记录日期: 2026-05-30
> 问题根源: cron/scheduler.py 的 cron_hint 硬编码导致 deliver="local" 时 Agent 不推送

## 推送模式对比

| 模式 | deliver 值 | 推送方式 | 适用场景 |
|------|-----------|----------|----------|
| 系统自动推送 | "origin" | 系统将 Agent 最终回复推送到 origin 聊天 | 单条短消息（情报日报等） |
| Agent 主动推送 | "local" | Agent 调用 send_message 分条推送 | 多条长内容（热点刀锋 5 篇微头条） |

## 根因分析 (2026-05-30)

### 问题
`cron/scheduler.py` 的 `_build_job_prompt()` 函数无条件注入：
```
[IMPORTANT: ... do NOT use send_message or try to deliver the output yourself.]
```
无论 `deliver` 设置如何，所有 cronjob 都收到相同指令。

### 影响
- `deliver: "origin"` → 系统推送 Agent 最终回复 → ✅ 正常
- `deliver: "local"` → 系统不推送，但 Agent 被禁止使用 send_message → ❌ 零推送

### 修复
修改 `cron/scheduler.py`，根据 `deliver` 值动态生成 cron_hint：

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
        "the output yourself. Just produce your report/output as your "
        "final response and the system handles the rest. "
        "SILENT: If there is genuinely nothing new to report, respond "
        "with exactly \"[SILENT]\" (nothing else) to suppress delivery. "
        "Never combine [SILENT] with content — either report your "
        "findings normally, or say [SILENT] and nothing more.]\n\n"
    )
```

## 热点刀锋推荐配置

```bash
# deliver 必须设为 local，由 Agent 调用 send_message 分条推送
hermes cronjob update <job-id> --deliver "local"

# model/provider 必须显式指定，不依赖默认值
hermes cronjob update <job-id> --model deepseek-v4-pro --provider deepseek
```

## 推送流程

Agent 执行热点刀锋后，应按以下顺序推送：
1. 摘要消息（数据源 + 5 个话题列表）
2. 微头条① 全文
3. 微头条② 全文
4. 微头条③ 全文
5. 微头条④ 全文
6. 微头条⑤ 全文

每条独立消息，约 500 字符，不会触发 Telegram 4096 字符限制。

## 验证方法

执行后检查输出文件末尾的 "Response" 部分：
```
📤 Telegram推送：6条消息全部成功（msg_id: XXXX-XXXX）
```
如果出现 "零推送" 或没有推送记录，说明 cron_hint 未生效，需检查 scheduler.py 修改。
