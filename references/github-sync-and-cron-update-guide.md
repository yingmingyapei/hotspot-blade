# GitHub 同步与定时任务更新指南（2026-06-09）

## 从 GitHub 拉取热点刀锋更新

### 步骤

```bash
# 1. 进入 skill 目录
cd ~/.hermes/skills/hotspot-blade

# 2. 拉取最新（如有本地修改先 stash）
git stash  # 如需要
git pull origin main

# 3. 同步脚本到全局 scripts 目录
cp scripts/hotlist_scraper.py ~/.hermes/scripts/
cp scripts/hotlist_to_excel.py ~/.hermes/scripts/  # 如有

# 4. 验证脚本可执行
python3 ~/.hermes/scripts/hotlist_scraper.py --limit 1 --json 2>&1 | head -5

# 5. 恢复 stash（如有）
git stash pop  # 如需要
```

## 更新定时任务

当 SKILL.md 或 cronjob-prompt.md 有重大变更时，必须同步更新 cron job：

```bash
# 查看当前定时任务
hermes cronjob list

# 更新 prompt（用新的 cronjob-prompt.md 内容）
hermes cronjob update <job_id> --prompt "$(cat ~/.hermes/skills/hotspot-blade/templates/cronjob-prompt.md)"

# 或用 cronjob 工具直接更新（推荐，支持 skills 参数）
# action=update, job_id=<id>, prompt=<new_prompt>, skills=["hotspot-blade", "article-polish-master"]
```

### ⚠️ 坑：SKILL.md 改了但 cron job prompt 没更新

**症状**：修改了 SKILL.md 中的数据源/规则，但定时任务执行时仍然用旧逻辑。

**根因**：cron job 的 prompt 是创建时的快照，不会自动同步 SKILL.md 的变更。

**正确做法**：每次修改 SKILL.md 的执行逻辑后，同步更新 cron job prompt。

## Hermes Agent 上游同步

### 仓库结构

- **源码仓库**：`/mnt/usb1_2-4/system-data/hermes/hermes-agent`
- **上游（NousResearch）**：origin remote
- **用户 fork（yingmingyapei）**：upstream remote

### 合并用户 fork 更新

```bash
cd /mnt/usb1_2-4/system-data/hermes/hermes-agent

# 设置 git 身份（如未设置）
git config user.email "yingmingyapei@users.noreply.github.com"
git config user.name "wu yingming"

# 拉取 fork 更新
git -c http.proxy="" -c https.proxy="" fetch upstream

# 查看差异数
git log --oneline HEAD..upstream/main | wc -l

# 如有本地修改，先 stash
git stash

# 合并（如有冲突需手动解决）
git merge --no-commit --no-ff upstream/main
# 检查冲突: git diff --cached --stat
# 如无冲突:
git commit -m "merge: sync with yingmingyapei/hermes-agent fork"

# 恢复 stash
git stash pop  # 如需要
```

### ⚠️ 坑：本地 holographic memory 插件修改与上游冲突

**症状**：`git stash` 后合并成功，但 stash 中的 holographic memory 修改可能与上游重复。

**正确做法**：合并后检查上游是否已包含相同修改：
```bash
grep -n "_build_fts_query\|_is_pure_chinese\|backfill_all" plugins/memory/holographic/retrieval.py plugins/memory/holographic/store.py
```
如上游已有，直接 `git stash drop`。

### NousResearch 上游同步（谨慎）

```bash
git -c http.proxy="" -c https.proxy="" fetch origin
git log --oneline HEAD..origin/main | wc -l  # 查看差异数
# 差异太大时不要盲目合并，先检查关键修复
git log --oneline HEAD..origin/main | grep -iE "(memory|cron|skill|model|provider)"
```

## 代理设置

同步 GitHub 时可能需要关闭代理（代理可能需要认证或不可用）：
```bash
git -c http.proxy="" -c https.proxy="" fetch origin
```
