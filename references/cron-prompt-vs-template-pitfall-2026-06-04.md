# Cron Prompt vs Template 分离陷阱（2026-06-04）

## 问题

修改 `templates/cronjob-prompt.md` 后，cron job 执行时仍然使用旧版 prompt。

## 根因

cron job 的 prompt 在创建时直接写入 `~/.hermes/cron/jobs.json`，与模板文件完全独立。

## 修复

必须用 `cronjob update` 更新 prompt：

```python
cronjob(action='update', job_id='0d5874d5e1fd', prompt='新 prompt 内容')
```

## 教训

- 模板文件（`templates/cronjob-prompt.md`）只是参考，不是运行时配置
- 技能文档（`SKILL.md`）通过 skills 加载，但 cron prompt 优先级更高
- 修改定时任务行为 = 更新 jobs.json = 用 cronjob update
- 修改模板文件 ≠ 更新定时任务

## 验证方法

```python
python3 -c "
import json
with open('/home/yingming/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for job in data.get('jobs', []):
    if '热点刀锋' in job.get('name', ''):
        print(len(job.get('prompt', '')), 'chars')
"
```
