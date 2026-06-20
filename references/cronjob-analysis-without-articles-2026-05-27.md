# Cronjob "只有分析没有正文" 故障 (2026-05-27)

## 症状

- cronjob 执行成功（`last_status: ok`）
- Wiki 文件已创建，但只有话题分析和排除理由
- **5 篇微头条正文全无**
- Wiki 文件大小：~2KB（正常应 ≥10KB）

## 根因

Agent 完成数据抓取和话题分析后就认为"任务完成了"，**根本不会主动进入写作阶段**。即使 cronjob prompt 明确要求"输出5篇完整微头条"，仍可能在分析阶段就停止。

**最危险的是**：Agent 在分析阶段就已经自我感觉完成了任务。从 Agent 视角看：
1. 数据抓取 ✅ 
2. 话题筛选 ✅ 
3. 去重检查 ✅ 
4. Wiki 已存档 ✅ 
5. ✅ → 任务完成

但实际上缺了最关键的一步：写文章。

## 2026-05-27 实测证据

| 项目 | 实际值 |
|------|--------|
| 执行时间 | 08:14 CST |
| Wiki 文件行数 | 49 行 |
| Wiki 文件大小 | 2,258 字节 |
| 内容类型 | 仅话题分析 + 执行笔记 |
| 微头条正文 | 0 篇 |
| 是否触发了告警 | 否（`last_status: ok`） |

## 修复方案

### 1. 前置检查：检测今日是否已有"空壳"文件

每次执行 cronjob 前检查：

```bash
WIKI_FILE="/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/$(date +%Y-%m-%d)-热点刀锋微头条-5篇.md"  # 对外路径：C:\Users\yingm\wiki\sources\market-intelligence\daily\YYYY-MM-DD-热点刀锋微头条-5篇.md
if [ -f "$WIKI_FILE" ] && [ "$(wc -c < "$WIKI_FILE")" -lt 5000 ]; then
    echo "⚠️ 此前有执行但仅 <5KB，属'只有分析无正文'故障，重新执行"
fi
```

### 2. 后置验证：正文完整度检查

写完后必须执行：

```python
output = """最终输出"""
article_sections = output.split('📌')
if len(article_sections) < 6:
    FAIL(f"未找到5篇微头条，只有{len(article_sections)-1}篇")

for i, sec in enumerate(article_sections[1:6], 1):
    body = sec.split('---')[0]
    chinese = len(re.findall(r'[\u4e00-\u9fff]', body))
    if chinese < 300:
        FAIL(f"微头条{i}正文不足300字，实际{chinese}字")
```

### 3. 在 cronjob prompt 中显式写出验证步骤

不要依赖 Agent 的"自觉"。验证步骤必须在 cronjob prompt 中以代码块形式明确写出。

## 相关文件

- `SKILL.md` → 九、已知限制中新增此陷阱
- `templates/cronjob-prompt.md` → 正文完整度验证步骤

## 与同类故障的区别

| 故障 | 症状 | 根因 | 2026-05-26 | 2026-05-27 |
|------|------|------|------------|------------|
| deliver-only-summary | 用户收到摘要无正文 | Agent 只输出摘要到 final reply | ✅ | — |
| analysis-without-articles | Wiki 文件仅分析无文章 | Agent 在分析阶段就停止 | — | ✅ |
