# hermes send 交付模式（2026-05-31 验证）

## 核心发现

`send_message` 工具**不存在**于 Agent 可用工具集中。cronjob prompt 中所有 `send_message(target="telegram:6327421932")` 指令均无法执行。

**实际可用的 Telegram 推送方式**：`hermes send` CLI 命令。

## hermes send 用法

```bash
# 从文件推送
hermes send -t "telegram:6327421932" -f /tmp/article.txt

# 直接推送文字
hermes send -t "telegram:6327421932" "消息内容"

# 查看可用目标
hermes send --list
```

## 关键特性

- 复用 Gateway 的 Telegram 凭证（config.yaml + .env）
- 不需要 LLM 运行，不需要 Agent 循环
- 不需要 Gateway 运行
- 支持 bot-token 平台（Telegram/Discord/Slack/Signal）

## 代理穿透

如果 Telegram API 需要代理，`hermes send` 会复用 `config.yaml` 中配置的 `telegram.proxy_url`。

## 验证记录

- 2026-05-31 12:32：第二轮执行，6/6 消息全部推送成功
- 消息格式：每篇微头条独立写入 `/tmp/hotspot_N.txt`，然后 `hermes send -f` 推送
- 推送速度：每条 < 3 秒

## 推荐工作流

```bash
# 逐篇推送
for i in 1 2 3 4 5; do
  cat > /tmp/hotspot_${i}.txt << 'EOF'
{微头条正文}
EOF
  hermes send -t "telegram:6327421932" -f /tmp/hotspot_${i}.txt
done

# 推送汇总
hermes send -t "telegram:6327421932" "✅ 热点刀锋完成 | 5篇已推送"
```
