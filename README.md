# 🔥 热点刀锋 (Hotspot Blade)

> **多平台热榜抓取 + 爆款微头条一键生成**

自动抓取知乎、微博、Buzzing.cc（海外信息差）、36氪、Hacker News 等多平台热榜，按九边适配性评分筛选话题，自动生成5篇爆款微头条。全流程自动化，支持定时任务。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **多源抓取** | 知乎 + 微博 + Buzzing.cc（28个海外媒体）+ 36氪 + HN + IT之家 |
| **智能筛选** | 九边适配性评分（40%）+ 热度（30%）+ 讨论空间（20%）+ 时效性（10%） |
| **故障自动切换** | 数据源健康检查 + 自动降级策略 |
| **爆款写作** | 七步工作流 + 标题A/B测试 + 三宗罪自检 |
| **定时任务** | 全自动执行，无需人工确认 |

---

## 🚀 快速开始

### 前置依赖

- [Hermes Agent](https://hermes-agent.nousresearch.com) (≥ 最新稳定版)
- [opencli](https://github.com/jackwener/opencli) (≥ 1.7.14)
- Python 3.10+ 及 `curl_cffi` 库

### 安装

```bash
# 1. Clone 仓库
git clone https://github.com/yingmingyapei/hotspot-blade.git

# 2. 软链接到 Hermes skills 目录
ln -s $(pwd)/hotspot-blade ~/.hermes/skills/productivity/hotspot-blade

# 3. 验证安装
hermes skill view hotspot-blade
```

### 运行

```bash
# 交互模式
hermes skill run hotspot-blade

# 触发词示例
- "写热点"
- "抓热榜写微头条"
- "热点刀锋"
- "自动写头条"
```

---

## 📊 数据源配置

| 数据源 | 优先级 | 用途 | 命令 |
|--------|--------|------|------|
| 知乎热榜 | ✅ 必抓 | 大众话题，社会议题 | `opencli zhihu hot -f json` |
| 微博热搜 | ✅ 必抓 | 舆情风向标，交叉验证 | `opencli weibo hot -f json` |
| Buzzing.cc | ✅ 强烈推荐 | 海外信息差（28个子站） | curl_cffi + 排除模式 |
| 36氪热榜 | ✅ 推荐 | 科技创业/商业 | `opencli 36kr hot -f json` |
| Hacker News | ✅ 推荐 | 全球科技社区 | `opencli hackernews top -f json` |
| IT之家 | ✅ 推荐 | 数码/消费电子 | `opencli ithome hot` |

> ⚠️ **知乎热榜需要 Chrome 登录态**。定时任务环境请使用备用方案（见文档）。

---

## ⚙️ 定时任务配置

```bash
hermes cronjob create \
  --name "每日热点刀锋微头条" \
  --skill hotspot-blade \
  --prompt "$(cat ~/.hermes/skills/productivity/hotspot-blade/templates/cronjob-prompt.md)" \
  --schedule "30 9 * * *" \
  --deliver "telegram:YOUR_CHAT_ID"
```

---

## 📁 仓库结构

```
hotspot-blade/
├── README.md                    # 仓库入口文档
├── LICENSE                      # MIT 许可证
├── SKILL.md                     # 技能主文档
├── templates/
│   └── cronjob-prompt.md        # 定时任务模板
├── scripts/
│   ├── data_source_health_check.py   # 健康检查脚本
│   └── patch_skill_md.py              # 补丁脚本
├── references/
│   ├── hotlist-sources-audit.md       # 数据源可用性审计
│   ├── optimization-summary.md        # 优化总结
│   ├── optimization-test-report.md    # 测试报告
│   └── zhihu-login-requirement.md     # 知乎登录态说明
└── docs/
    ├── INSTALL.md               # 详细安装指南
    ├── USAGE.md                 # 使用指南
    └── TROUBLESHOOTING.md       # 故障排查
```

---

## 🔧 依赖技能

本技能依赖以下技能，请确保已安装：

| 技能 | 用途 |
|------|------|
| `opencli-tool` | 平台热榜抓取 |
| `toutiao-viral-writing` | 爆款微头条写作（可选参考） |

---

## 📝 核心原则

> **⚠️ 没有稳定的数据源，一切工具都是空幻。**

每次执行前必须进行数据源健康检查，故障时自动切换备用方案，绝不使用过期数据凑合。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 PR。提交前请阅读：
- [INSTALL.md](docs/INSTALL.md) - 安装指南
- [USAGE.md](docs/USAGE.md) - 使用指南
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排查

---

## 📞 联系方式

- GitHub: [yingmingyapei](https://github.com/yingmingyapei)
