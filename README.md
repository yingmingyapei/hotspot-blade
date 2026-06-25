# 🔥 热点刀锋 v5.0

> **多平台热榜抓取 → 5维度选题评分 → 爆款微头条生成 → 推送Telegram**
>
> 编排器 + 写作技能v5.0.0（三级选题池 + 人设差异化 + 互动全链路 + 算法适配 + 五维复盘 + 产能复用 + 价值纵深）

---

## ✨ 架构

```
hotspot-blade（编排器）
  ├── hotlist-scraper      → 数据采集（curl+Cookie直连5平台API）
  ├── topic-scorer         → 选题评分（5维度：钱包距离/反驳成本/物件锚点/头条适配/天然分裂）
  ├── toutiao-viral-writing → 写作模板v5.0.0（12种句式 + 三级选题 + 人设差异化 + 互动机制 + 算法适配）
  │   ├── toutiao-sentence-patterns → 句式库v5.0.0（7+5种句式，含痛点级/认知级专用）
  │   └── toutiao-topic-engine      → 选题引擎v5.0.0（三级选题池 + 反共识红线）
  ├── russell-flip-arsenal  → 罗素翻转弹药库
  └── article-polish-master → 润色（已有技能）
```

## ✨ 三种工作模式

| 模式 | 触发 | 产出 |
|------|------|------|
| A·选题报告 | cron每天8点自动 | 评分→PPT报告→推送Telegram |
| B·完整写作 | 用户说"写热点" | 评分→写作→推送5篇 |
| C·改写爆款 | 用户丢入文章片段 | 改写成头条爆款→推送1篇 |

---

## 📦 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 热点刀锋编排器 |
| `SKILL-hotlist-scraper.md` | 数据采集子技能（curl+Cookie直连5平台） |
| `SKILL-topic-scorer.md` | 选题评分子技能（5维度+S/A评级+PPT报告） |
| `SKILL-russell-flip-arsenal.md` | 罗素翻转弹药库 |
| `skills/toutiao-viral-writing/` | 写作技能v5.0.0（主技能，含15个参考文件） |
| `skills/toutiao-sentence-patterns/` | 句式库v5.0.0（12种句式） |
| `skills/toutiao-topic-engine/` | 选题引擎v5.0.0（三级选题池+红线） |

---

## 🔄 版本历史

- **v5.0** (2026-06-26) — 写作技能v5.0.0全量升级：三级选题池（热点/痛点/认知）+ 5种新句式 + 人设差异化 + 互动全链路（站队钩子+行为题+正文预判反对）+ 算法适配（前300字结构+黄金15分钟）+ 五维复盘闭环 + 一鱼三吃产能复用 + 评论区置顶价值指引
- v4.2 — 32轮IA辩论结论执行，降字数+砍引擎+认知落差引擎
- v4.0 (2026-06-17) — 精简重构：2690行→130行，拆分3个子技能，新增罗素翻转弹药库
- v3.9.5 — 选题评分实操指南+去重false-positive陷阱
- v3.9 — 5议题融合版，废弃一题三篇模式
- v3.5 — curl+Cookie架构迁移
- v3.4 — 九边Pro爆款规律提炼
- v3.0 — 人群精准定位+撕裂驱动型爆款公式
- v2.0 — 三风格融合版
- v1.0 — 基础热榜抓取+九边风格写作

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
