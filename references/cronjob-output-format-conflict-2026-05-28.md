# 热点刀锋 Cron 执行故障：SKILL.md 与 cronjob prompt 格式冲突

## 故障时间线

| 日期 | 事件 | 输出文件 |
|------|------|---------|
| 2026-05-27 | 首次"只有分析无正文"故障 | ✅ 100KB，含5篇正文 |
| 2026-05-28 09:48 | 定时任务执行失败 | ⚠️ 93KB，只有placeholder |
| 2026-05-28 10:41 | 手动 run 触发，结果相同 | ⚠️ 93KB，与上次 diff 仅时间戳 |

## 根因分析

### 表面症状
Agent 生成到「候选话题筛选」阶段就停止，完全没有进入写作阶段。Wiki 文件只有占位符：
```
📌 微头条① | {话题名}
{正文占位符}
```

### 三层根因

#### ① SKILL.md 超重压垮 context（主因）
- SKILL.md 文件大小：**122,367 字符**（122KB）
- cron 模式会加载：skill全文 + cronjob prompt（10KB）+ 执行上下文
- **总 context 远超模型单次输出容量**，Agent 写到一半被截断

#### ② 输出格式章节重复冲突
- `SKILL.md` 第八章「📤 最终输出格式」定义了格式A（`📌 微头条① | {话题名}`）
- `templates/cronjob-prompt.md` 在「第六步」定义了格式B（`📌 微头条① | 【标题】{标题}`）
- **两套格式同时存在于 Agent context**，加上 context 已满，模型不知道用哪套，直接摆烂停在分析阶段

#### ③ deliver 机制与实际输出不匹配
- 当前 cronjob 配置：`deliver: origin`
- 推送内容：**Agent 的最终回复**（即只到分析阶段的截断输出）
- 用户收不到 5 篇正文，只能收到故障报告

## 诊断方法

```bash
# 1. 检查输出文件是否有正文（正常 ≥10KB，「只有分析」≈93KB）
ls -lh ~/.hermes/cron/output/<job_id>/

# 2. 检查正文完整度：正常 5 篇应有 6 个 📌 标记
grep -c "📌" ~/.hermes/cron/output/<job_id>/<output>.md
# 期望值：≥6（5篇正文 + 1个汇总行）
# 故障值：=2 或 =6 但内容是placeholder

# 3. 检查字数：正文完整度
wc -l ~/.hermes/cron/output/<job_id>/<output>.md
# 正常：2000-2500 行
# 故障：≈2283 行（与 09:48 run 完全相同说明没真正执行）

# 4. 检查是否与上次 run 内容相同（确认是否真的执行了新任务）
diff ~/.hermes/cron/output/<job_id>/<date>_09-48-40.md \
      ~/.hermes/cron/output/<job_id>/<date>_10-41-34.md
# 如果 diff 仅时间戳差异，说明两次执行结果相同，是同一个故障

# 5. 今日 Wiki 文件大小检查（判断「只有分析无正文」故障）
SIZE=$(wc -c < /mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/$(date +%Y-%m-%d)-热点刀锋微头条-5篇.md 2>/dev/null || echo "0")
if [ "$SIZE" -gt 0 ] && [ "$SIZE" -lt 10000 ]; then
    echo "⚠️ 今日执行仅 ${SIZE} 字节（正文需≥10KB），属「只有分析无正文」故障"
fi
```

## 完整修复方案

### 步骤1：精简 SKILL.md（减少 context 压力）

**需删除的内容**：
- SKILL.md 第八章「📤 最终输出格式」整个章节（约 2KB）
  - 原因：cronjob prompt 已有独立格式定义，此章节重复且版本旧
- SKILL.md 内所有「输出格式要求」的纯文本重复段落
  - 原因：cronjob prompt 是薄封装版本，Agent 应读 prompt 而非 SKILL.md 的格式说明

**保留的内容**：
- 触发条件、筛选标准、写作风格（三层密码）、三宗罪自检
- 话题→标签映射库、标题公式库
- 所有陷阱说明（这些是重要上下文）

### 步骤2：更新 cronjob 配置

```bash
# 改 deliver 为 local，由 skill 内部 send_message 推送
hermes cronjob update <job_id> --deliver "local"

# 显式固定模型（避免 model 为 null 时用会话默认额度）
hermes cronjob update <job_id> --model "deepseek-v4-flash"
```

### 步骤3：验证修复

```bash
# 触发一次手动执行
hermes cronjob run <job_id>

# 检查输出
sleep 60
grep -c "📌" ~/.hermes/cron/output/<job_id>/$(date +%Y-%m-%d)*.md
# 期望值：≥6
```

## 关键原则

1. **cronjob prompt 是薄封装**：只包含执行要点，不粘贴 skill 全文
2. **SKILL.md 是完整参考**：Agent 通过 skill_view 读取，cron prompt 通过薄模板注入
3. **输出格式只在 prompt 中定义一次**：避免两套格式同时存在于 context
4. **deliver 机制决定推送方式**：`deliver: origin` → Agent 最终回复必须包含正文；`deliver: local` → skill 内部自主推送

## 相关文件

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 完整技能定义（122KB，需精简） |
| `templates/cronjob-prompt.md` | 定时任务薄封装 prompt |
| `scripts/hotspot-blade-push.py` | 分条推送脚本（send_message 实现） |
| `references/cronjob-delivery-failure-2026-05-26.md` | 2026-05-26 Telegram 推送失败案例 |
| `references/cronjob-analysis-without-articles-2026-05-27.md` | 2026-05-27「只有分析无正文」故障记录 |