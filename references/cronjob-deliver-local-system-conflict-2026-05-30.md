# Cronjob deliver="local" 与系统指令冲突故障记录

> **日期**: 2026-05-30
> **任务ID**: 0d5874d5e1fd (每日热点刀锋微头条)
> **故障现象**: 设置 deliver="local" 后，cronjob 执行成功但 Telegram 零推送

---

## 故障时间线

| 时间 | 事件 | 结果 |
|------|------|------|
| 07:18 | 用户要求修改 deliver 配置 | 从 "origin" 改为 "local" |
| 07:19 | 手动触发 `cronjob run` | 任务进入执行队列 |
| 07:23 | 任务执行完成 | ✅ 输出文件 100KB，5篇微头条完整生成 |
| 07:23+ | Telegram 推送 | ❌ 零推送（无摘要、无正文） |
| 07:30 | 人工调用 send_message 分条推送 | ✅ 6条消息成功送达 |

---

## 根因分析

### 问题链条

```
1. 用户设置 deliver: "local"（期望技能内部自主推送）
2. cronjob 系统注入指令："do NOT use send_message or try to deliver the output yourself"
3. Agent 看到系统指令 → 不调用 send_message
4. deliver: "local" 的系统行为 → 只保存本地，不自动推送
5. 结果：Agent 不推 + 系统不推 = 零推送
```

### 系统指令原文

```
[IMPORTANT: You are running as a scheduled cron job.
DELIVERY: Your final response will be automatically delivered to the user
— do NOT use send_message or try to deliver the output yourself.
Just produce your report/output as your final response and the system handles the rest.
SILENT: If there is genuinely nothing new to report, respond with exactly "[SILENT]"
(nothing else) to suppress delivery.]
```

### 矛盾点

| 来源 | 说法 |
|------|------|
| cronjob-prompt.md（技能模板） | "deliver: local 时，需在技能内调用 send_message 分条推送" |
| cronjob 系统指令（注入） | "do NOT use send_message，系统会处理" |

系统指令优先级高于技能模板，Agent 遵循系统指令 → 不调用 send_message。

---

## 执行结果验证

**Agent 实际产出（正常）**：
- 输出文件：`~/.hermes/cron/output/0d5874d5e1fd/2026-05-30_07-23-27.md`（100KB）
- 📌 标记数量：10个（5篇正文 + 格式说明中的示例）
- Wiki 存档：`/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/2026-05-30-热点刀锋微头条-5篇.md`（6.5KB）
- 正文完整度：5篇均 ≥300 中文字符 ✅

**Telegram 收到**：无（deliver="local" + 系统阻止 send_message）

---

## 解决方案

### 方案 A：改回 deliver="origin" + 强制全文输出（推荐）

```bash
hermes cronjob update 0d5874d5e1fd --deliver "origin"
```

在 cronjob prompt 中加粗强调：
```
⚠️ 你的最终回复就是推送给用户的全部内容。
必须在最终回复中包含 5 篇微头条全文。
不要只输出摘要。
```

### 方案 B：保持 deliver="local" + 外部推送机制

需要一个独立的推送步骤（不在 cronjob 内部）：
- cronjob 执行后，读取输出文件
- 提取 5 篇微头条
- 调用 send_message 分条推送

当前无自动触发机制，需人工干预或额外 cron job。

---

## 经验教训

1. **系统指令 > 技能模板**：cronjob 注入的系统指令会覆盖技能文档中的建议
2. **deliver="local" 意味着"完全不推送"**：不仅系统不推，系统还阻止 Agent 推
3. **测试推送不能只看 last_status**：status=ok 不代表用户收到了消息
4. **验证标准**：用户在 Telegram 实际收到完整内容 = 成功，其他一切 = 失败
