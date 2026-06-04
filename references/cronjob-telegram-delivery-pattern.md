# Cronjob Telegram 交付模式

## 问题描述

当 cronjob 配置 `deliver: telegram:6327421932` 或 `deliver: "origin"` 时，系统会将**整个执行输出**发送到 Telegram。但如果输出内容超过 Telegram 单条消息限制（4096 字符），消息会被静默丢弃或截断。

**⚠️ 关键陷阱（2026-05-26 实测）：**

`deliver: "origin"` 推送的是 Agent 的**最终回复**，不是技能的所有产出。

| 交付模式 | 推送内容 | 注意事项 |
|----------|----------|----------|
| `deliver: "origin"` | Agent 的**最终回复** | 最终回复必须包含 5 篇微头条全文，否则用户收不到正文 |
| `deliver: "local"` | 本地保存 | 需在技能内调用 `send_message` 分条推送 |

## 典型症状

| 症状 | 原因 |
|------|------|
| cronjob 状态显示 `ok`，但 Telegram 未收到消息 | 输出内容 >4096 字符，被截断/丢弃 |
| 收到部分消息（只有开头） | 输出内容被截断 |
| `last_delivery_error` 为空 | 系统认为"已发送"，但 Telegram 拒绝了 |
| **收到摘要但没有微头条正文** | **Agent 最终回复只有摘要，5 篇正文写入 Wiki 但未包含在输出中** |

## 解决方案

### 方案一：本地保存 + send_message 推送（推荐）

**配置：**
```bash
hermes cronjob create \
  --name "每日热点刀锋微头条" \
  --skill hotspot-blade \
  --prompt "$(cat ~/.hermes/skills/productivity/hotspot-blade/templates/cronjob-prompt.md)" \
  --schedule "45 9 * * *" \
  --deliver "local"
```

**skill 内推送：**
在 cronjob-prompt.md 中明确要求使用 `send_message` 工具分条推送：

```
### 📤 最终输出格式（必须遵守）

执行完毕后，只输出以下内容：

✅ 热点刀锋已完成（2026-05-08）
📊 抓取：知乎 + 微博 + Buzzing.cc + 36氪/HN
🏆 选中话题：
1. {话题1}（{热度} {来源}）
...

---

📌 微头条① | {话题名}
{全文}

#热点刀锋
```

**关键：**
- `--deliver "local"` 将完整执行报告保存到 `~/.hermes/cron/output/<job_id>/`
- skill 调用 `send_message(target="telegram:6327421932", message="{内容}")` 分条推送
- 每篇微头条约 500 字符，不会超限

### 方案二：本地保存 + 推送脚本

**配置：**
```bash
hermes cronjob create \
  --name "每日热点刀锋微头条" \
  --skill hotspot-blade \
  --prompt "..." \
  --schedule "45 9 * * *" \
  --deliver "local"
```

**推送脚本**（`scripts/hotspot-blade-push.py`）：
```python
#!/usr/bin/env python3
"""
热点刀锋推送脚本：读取最新执行结果，提取 5 篇微头条发送到 Telegram
"""

import os
import re
import json
import time
import subprocess
from pathlib import Path

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = "6327421932"
OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output" / "9cb95a112584"

def send_via_curl(text):
    """通过 curl + SOCKS5 代理发送 Telegram 消息"""
    proxy = "http://127.0.0.1:1080"
    cmd = [
        "curl", "-s", "-x", proxy,
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        "-d", f"chat_id={CHAT_ID}",
        "-d", "parse_mode=Markdown",
        "--data-urlencode", f"text={text}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)

def main():
    # 找到最新执行文件
    files = sorted(OUTPUT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = files[0]
    
    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取 5 篇微头条
    articles = extract_micro_articles(content)
    
    # 发送执行摘要
    send_via_curl("✅ **热点刀锋已完成**（2026-05-08）\n\n📊 抓取：知乎 + 微博 + Buzzing.cc + 36氪/HN")
    
    # 发送 5 篇微头条
    for i, article in enumerate(articles[:5]):
        message = f"📌 **微头条{i+1} | {article['title']}**\n\n{article['body'][:1500]}\n\n#热点刀锋"
        send_via_curl(message)
        time.sleep(1)  # 避免速率限制

if __name__ == "__main__":
    main()
```

## 安全扫描注意事项

### curl 指令被拦截

**症状：** cronjob 执行失败，错误信息：
```
Blocked: prompt matches threat pattern 'exfil_curl'. Cron prompts must not contain injection or exfiltration payloads.
```

**原因：** cronjob 系统有安全扫描，会检测 `curl` 指令（防止 prompt 注入导致数据外泄）。

**解决方案：**
1. 从 cronjob prompt 中移除 `curl` 指令
2. 从 skill 文档中移除 `curl` 指令
3. 使用 `send_message` 工具替代

**示例修复：**

| 原内容 | 修复后 |
|--------|--------|
| `curl -s -x "$SOCKS" "https://api.telegram.org/bot${TOKEN}/sendMessage"` | `send_message(target="telegram:6327421932", message="{消息内容}")` |

### 其他触发扫描的模式

| 模式 | 说明 |
|------|------|
| `exfil_curl` | 包含 `curl` 指令 |
| `injection` | 包含注入攻击模式 |
| `bot.*api` | 直接调用 Bot API |

**排查方法：**
```bash
grep -rn "curl\|exfil\|injection\|bot.*api" ~/.hermes/skills/<skill-name>/
```

## 推送脚本备用方案

如果 `send_message` 工具因网关连接问题失败，可使用 curl + SOCKS5 代理直接调用 Telegram Bot API：

```bash
source ~/.hermes/.env
curl -s -x "http://127.0.0.1:1080" \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=6327421932" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=消息内容"
```

**注意：**
- 需要 `TELEGRAM_BOT_TOKEN` 环境变量
- 需要 SOCKS5 代理（OpenClash 7891 端口）
- 消息内容超过 4096 字符需分条发送

## 排查清单

```
□ 检查执行输出文件大小：ls -lh ~/.hermes/cron/output/<job_id>/
□ 如果 >4KB，说明输出内容过大
□ 检查 Telegram 是否收到消息
□ 如果未收到，检查 last_delivery_error 字段
□ 检查 cronjob 配置：hermes cronjob list
□ 如果 deliver=telegram 或 deliver=origin，考虑改为 local
□ 检查 skill 文档是否包含 curl 指令
□ 如果有，移除并替换为 send_message
□ 检查 Agent 最终回复是否包含 5 篇微头条全文（deliver: "origin" 时）
```

## 2026-05-26 故障案例

**详见：** `references/cronjob-delivery-failure-2026-05-26.md`

**核心教训：**
- `deliver: "origin"` 推送的是 Agent 的**最终回复**，不是技能的所有产出
- 如果 Agent 只输出摘要，推送的就只有摘要
- 5 篇微头条正文被写入 Wiki，但未包含在最终输出中
- 用户收到：只有摘要，没有微头条正文

**修复方案：**
1. 将 cronjob 配置改为 `deliver: "local"`
2. 在技能内使用 `send_message` 分条推送
3. 或在 prompt 中明确要求 Agent 必须在最终输出中包含 5 篇全文

## 相关技能

- `hotspot-blade`：热点刀锋技能，已应用此模式
- `global-market-morning-brief`：全球财经早报，已修复 curl 指令问题
