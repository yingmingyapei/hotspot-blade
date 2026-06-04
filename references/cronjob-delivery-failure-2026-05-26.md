# Cronjob 交付失败根因分析：2026-05-26 热点刀锋

## 故障现象

| 项目 | 状态 |
|------|------|
| Cronjob ID | `0d5874d5e1fd` |
| 执行时间 | 2026-05-26 09:48 |
| 执行状态 | `ok` |
| 交付状态 | `last_delivery_error: null` |
| Telegram 收到内容 | ❌ 仅收到摘要（342 字符），未收到 5 篇微头条 |

## 根因分析

### 关键发现

**Cronjob 的 `deliver: "origin"` 机制是将 Agent 的「最终回复」原样推送到 origin 聊天。**

| 项目 | 实际值 |
|------|--------|
| Agent 最终回复 | 仅执行摘要（342 字符） |
| 5 篇微头条正文 | 写入了 Wiki 文件，但**未包含在最终输出中** |
| 交付内容 | 只有摘要，没有正文 |

### 问题链条

```
1. Cronjob prompt 要求输出 5 篇完整微头条
2. Agent 生成了 5 篇微头条 ✅
3. Agent 写入了 Wiki 存档 ✅
4. Agent 的最终回复只包含摘要 ❌
5. deliver: "origin" 推送了 Agent 的最终回复（仅摘要） ❌
6. 用户收到：只有摘要，没有 5 篇微头条 ❌
```

### 为什么 Agent 没有把 5 篇微头条放入最终输出？

**技能 prompt 的矛盾：**

技能 prompt 的「最终输出格式」要求：
```
📌 微头条① | 【标题】{九边风格爆款标题}
{全文}
...
```

但 Agent 在执行七步工作流时：
- 生成了 5 篇微头条 → 写入 Wiki
- 最终回复 → 只输出了执行摘要

**Agent 可能认为：**
- Wiki 存档已经保存了完整内容
- 最终输出只需要摘要
- 不需要把 5 篇全文再输出一遍

**但这与 cronjob 的 `deliver: "origin"` 机制冲突：**
- `deliver: "origin"` 推送的是 Agent 的**最终回复**
- 如果最终回复只有摘要，推送的就只有摘要

## 解决方案

### 方案 A：修改 cronjob 配置（推荐）

将 `deliver: "origin"` 改为 `deliver: "local"`，然后在技能内使用 `send_message` 工具分条推送：

```bash
hermes cronjob update 0d5874d5e1fd --deliver "local"
```

**优点：**
- 完整执行报告保存到本地
- 技能内调用 `send_message` 分条推送（每篇约 500 字符）
- 避免单次消息过长被 Telegram 截断

### 方案 B：强制 Agent 在最终输出中包含全文

在 cronjob prompt 中明确要求：
```
⚠️ 重要：最终输出必须包含 5 篇微头条全文，不要只输出摘要！
deliver: "origin" 会将你的最终输出推送到 Telegram。
如果只输出摘要，用户将收不到微头条正文。
```

**缺点：**
- 5 篇微头条约 2500 字，单次推送可能接近 Telegram 限制
- 需要确保 Agent 严格遵守输出格式

### 方案 C：混合模式

```
1. deliver: "local" — 完整报告保存到本地
2. 摘要 + 话题列表 → 通过 send_message 推送
3. 5 篇微头条 → 分 5 条消息推送（每条约 500 字符）
```

## 验证步骤

```bash
# 1. 检查 cronjob 配置
hermes cronjob list | grep -A5 "0d5874d5e1fd"

# 2. 检查执行输出
ls -lh ~/.hermes/cron/output/0d5874d5e1fd/

# 3. 检查输出内容
cat ~/.hermes/cron/output/0d5874d5e1fd/2026-05-26_09-48-30.md | tail -50

# 4. 验证 Telegram 网关
hermes send -t telegram "测试推送 ✅"
```

## 教训总结

| 教训 | 说明 |
|------|------|
| `deliver: "origin"` 不是万能 | 它推送的是 Agent 的最终回复，不是技能的所有产出 |
| Agent 可能"聪明过头" | 认为 Wiki 存档就够了，不需要在最终输出中重复 |
| 输出格式要求必须与交付机制匹配 | 如果 `deliver: "origin"`，最终输出必须包含用户需要看到的全部内容 |
| 分条推送体验更好 | 5 篇微头条分 5 条推送，比单次 2500 字更清晰 |

## 修复记录

- **2026-05-26**：发现故障，根因分析完成
- **2026-05-26**：手动重新推送 5 篇微头条给用户
- **待修复**：更新 cronjob 配置为 `deliver: "local"` + 技能内 `send_message` 推送
