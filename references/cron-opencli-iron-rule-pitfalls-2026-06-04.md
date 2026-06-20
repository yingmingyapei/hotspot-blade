# opencli 铁律执行失败案例与修复

记录热点刀锋定时任务中 opencli 铁律反复失败的完整排查过程。

## 时间线

### 第一轮（2026-06-04 21:59）
- **现象**：Agent 从未调用 opencli，用 urllib 直接抓取百度热搜
- **根因**：cron job prompt（4.5KB）不含铁律声明，且包含 `python3 -c "import urllib"` 代码
- **修复**：更新 prompt，添加铁律声明

### 第二轮（2026-06-04 22:20）
- **现象**：Agent 卡在 `opencli daemon start`，之后尝试 curl 抓取百度热搜
- **根因**：SKILL.md 第 386 行有 `解决：opencli daemon start`
- **修复**：改为"报告失败，停止任务"

### 第三轮（2026-06-04 22:30）
- **现象**：Agent 再次执行 `opencli daemon start`，尝试 curl 直接抓取
- **根因**：SKILL.md 中仍有 115 处 Python/urllib 代码"诱导"Agent
- **修复**：物理删除所有 Python 降级代码（1421 行）

### 第四轮（2026-06-04 22:50）
- **现象**：Agent 执行 `opencli daemon start`，尝试 curl 抓取百度热搜
- **根因**：SKILL.md 第 268 行有"以下抓取命令采用 Python 直连方案，无需 opencli"
- **修复**：改为"所有数据采集必须通过 opencli browser 完成"

## 关键教训

1. **cron job prompt 和模板文件是独立的** — 改模板不改 prompt，Agent 行为不变
2. **弱模型会照搬 SKILL.md 中的命令** — 包括故障排除中的"解决：xxx"
3. **铁律不能只靠声明** — 必须物理删除 SKILL.md 中的诱惑代码
4. **prompt 越短越好** — 1.6KB 精简版比 13KB 模板版效果好
5. **反复失败时停止调试，直接执行** — 用户耐心有限

## 最终配置

- prompt 长度：~1800 字符
- 铁律位置：最前面，三重警告
- SKILL.md Python 代码：0 处
- opencli 命令数：103 处
- `opencli daemon start`：仅在"不要执行"的警告中出现
