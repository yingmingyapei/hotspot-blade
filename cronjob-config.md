# 热点刀锋定时任务配置

## 任务信息

- **任务ID**: `0d5874d5e1fd`
- **任务名称**: 每日热点刀锋微头条
- **调度时间**: 每天 08:00 (`0 8 * * *`)
- **交付模式**: `local`（Agent 自动推送）
- **状态**: 已启用

## 配置详情

```yaml
job_id: 0d5874d5e1fd
name: 每日热点刀锋微头条
skill: hotspot-blade
skills:
  - hotspot-blade
schedule: "0 8 * * *"
repeat: forever
deliver: local
model: mimo-v2.5-pro
provider: xiaomi
enabled: true
state: scheduled
```

## 执行流程

定时任务执行六阶段流程：

1. **环境就绪检查** - 检查 opencli browser 环境
2. **数据采集** - 5个第一手平台（知乎、微博、B站、雪球、头条）
3. **数据完整性校验** - 至少3个平台数据成功
4. **数据分析** - 识别社会矛盾、交叉验证、选定5个话题
5. **微头条生成** - 七步写作流程
6. **推送 + 存档** - 使用 hermes send CLI 分条推送

## 推送目标

- **Telegram**: `telegram:6327421932`
- **推送方式**: Agent 使用 `hermes send` CLI 分条推送

## 存档路径

```
/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md
```

## 相关文件

- `SKILL.md` - 完整技能文档
- `templates/cronjob-prompt.md` - 定时任务提示词模板
- `scripts/` - 数据采集和处理脚本
- `references/` - 参考文档和优化记录

## 管理命令

```bash
# 查看任务状态
hermes cronjob list

# 暂停任务
hermes cronjob update 0d5874d5e1fd --enabled false

# 恢复任务
hermes cronjob update 0d5874d5e1fd --enabled true

# 手动触发执行
hermes cronjob run 0d5874d5e1fd
```

## 更新日志

- **2026-06-04**: 同步最新技能文件和定时任务配置到 GitHub 仓库
- **2026-05-31**: 修复 deliver:local 调度器问题
- **2026-05-30**: 优化六阶段流程，增加数据完整性校验
