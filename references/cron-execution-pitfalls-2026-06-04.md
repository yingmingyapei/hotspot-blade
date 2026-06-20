# 热点刀锋 Cron 执行陷阱与经验教训

> 2026-06-04 从两次手动触发执行中提取

## 问题1：Cron Agent 不遵守 opencli-only 规则

**现象**：即使在 SKILL.md 和 cronjob-prompt.md 中添加了"铁律：必须使用 opencli"，cron Agent（mimo-v2.5-pro）在8轮 API 调用中**从未执行 `opencli browser` 命令**。

**Agent 行为路径**：
1. 读取历史话题文件（`hotspot-blade-history.json`）
2. 调用 `mcp_cn_finance_finance_news` 获取新闻
3. 做分析和推理
4. 跳过数据采集阶段，直接进入写作

**根因**：
- SKILL.md 有 50+ 处 Python 直接调 API 的代码片段（urllib/requests/curl_cffi）
- 这些代码作为"备用方案"存在，Agent 选择了阻力最小的路径
- prompt 铁律声明被 SKILL.md 中大量"备用方案"淹没

**教训**：仅在 prompt 中声明铁律不够。SKILL.md 本身的内容必须与铁律一致。

## 问题2：日志无法验证命令执行

**现象**：`agent.log` 只记录 `tool terminal completed (Xs, N chars)`，不记录实际执行的命令。

**影响**：无法确认 cron Agent 是否使用了 opencli，只能从行为推断。

**解决方向**：
- 提高日志级别（DEBUG 可能记录命令）
- 在 cronjob-prompt.md 中要求 Agent 在输出中明确列出执行的命令

## 问题3：GitHub 仓库同步遗漏

**现象**：更新了本地 skill 目录的文件，但没有同步到 GitHub 仓库。

**教训**：hotspot-blade 技能有独立的 GitHub 仓库（`/home/yingming/hotspot-blade`），每次修改必须同步：
```bash
cd /home/yingming/hotspot-blade
cp /home/yingming/.hermes/skills/productivity/hotspot-blade/<file> ./<file>
git add -A && git commit -m "msg" && git push origin main
```

## 问题4：opencli 环境本身没问题

**现象**：第一次执行报告了4个"问题"（opencli daemon start 错误、Daemon 启动失败等）。

**真相**：opencli 一直正常运行（Daemon 在 port 19825，Extension 已连接）。Agent 多此一举去启动一个已在运行的 daemon，然后把这当成了"opencli 有问题"。

**教训**：先验证 `opencli doctor` 状态，再判断是否有问题。不要把 Agent 的错误操作归咎于工具。

## 待解决

- [ ] SKILL.md 中的 Python fallback 代码需要清理或标注为"仅历史参考"
- [ ] cron 执行日志需要增加命令级别的记录
- [ ] 考虑创建独立的 cron-only prompt 模板，不引用完整 SKILL.md
