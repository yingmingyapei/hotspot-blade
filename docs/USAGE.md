# 使用指南 (USAGE.md)

> 热点刀锋技能详细使用指南

---

## 使用模式

### 交互模式

用户主动触发，分步骤确认：

```bash
hermes skill run hotspot-blade
```

**流程：**
1. 环境检查
2. 热榜抓取
3. 候选话题展示（等待用户确认）
4. 逐篇生成微头条（每篇确认后再写下一篇）
5. Wiki 存档

### 定时任务模式

全自动执行，无需人工确认：

```bash
hermes cronjob create \
  --name "每日热点刀锋微头条" \
  --skill hotspot-blade \
  --prompt "$(cat ~/.hermes/skills/productivity/hotspot-blade/templates/cronjob-prompt.md)" \
  --schedule "30 9 * * *" \
  --deliver "telegram:YOUR_CHAT_ID"
```

**流程：**
1. 环境检查
2. 数据源健康检查
3. 热榜抓取
4. 自动筛选前5个话题
5. 一次性生成5篇微头条
6. Wiki 存档
7. Telegram 推送

---

## 触发词

以下任一触发词可激活技能：

- "写热点"
- "抓热榜写微头条"
- "热点刀锋"
- "自动写头条"
- "每天热点"
- "帮我找5个热门话题写微头条"

---

## 工作流程详解

### 第一阶段：环境检查

```bash
opencli doctor
```

确认 Daemon + Extension 全绿再继续。

### 第二阶段：热榜抓取

按优先级抓取：

```bash
# 知乎热榜（必抓）
opencli zhihu hot -f json --limit 10

# 微博热搜（必抓）
opencli weibo hot -f json --limit 10

# Buzzing.cc 海外信息差
python3 scripts/data_source_health_check.py buzzing

# 科技垂直补充
opencli 36kr hot -f json
opencli hackernews top -f json
opencli ithome hot
```

### 第三阶段：候选话题筛选

按以下维度评分：

| 维度 | 权重 | 说明 |
|------|------|------|
| 热度 | 30% | 各平台榜单排名，Top 10优先 |
| 九边适配性 | 40% | 是否有明确矛盾/靶向/社会议题 |
| 讨论空间 | 20% | 普通人有话说，能引发评论 |
| 话题时效性 | 10% | 是否有时效性，过了就没意义 |

**排除规则：**
- 纯娱乐/饭圈话题
- 无具体矛盾的事实性新闻
- 太过专业化的小众话题

**多样性规则：** 同一子类话题最多选2个（教育/就业/科技/消费/社会/国际/海外）

### 第四阶段：爆款微头条生成

对每个话题执行七步工作流：

1. **选题定位** - 分析核心矛盾，确定九边式靶向
2. **钩子设计** - 开场/中段/结尾钩子设计
3. **草稿写作 + 快速预览检查** - 九边句式写作，立即检查
4. **共鸣适配** - 替换专业词为普通人感知词
5. **钩子强化检查** - 九边句式七条清单
6. **算法发布检查 + 标题A/B测试** - 3个候选标题评分
7. **润色加固 + 三宗罪自检** - 标准化指标检查

### 第五阶段：存档

存档到 Wiki：

```
<your-wiki-path>/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md
```

---

## 数据源健康检查

执行前自动运行健康检查：

```bash
python3 scripts/data_source_health_check.py
```

**故障自动切换策略：**

| 数据源 | 主要方案 | 备用方案1 | 备用方案2 |
|--------|----------|-----------|-----------|
| 知乎热榜 | opencli zhihu hot | curl_cffi API | v2ex热榜 |
| 微博热搜 | opencli weibo hot | 36氪热榜 | - |
| Buzzing.cc | curl_cffi | browser extract | Hacker News |
| 36氪热榜 | opencli 36kr hot | v2ex热榜 | - |

---

## 输出格式

### 执行报告（定时任务）

```
✅ 热点刀锋已完成（2026-05-08）
📊 抓取：知乎 + 微博 + Buzzing.cc + 36氪/HN/IT之家
🏆 选中话题：
1. {话题1}（{热度} {来源}）
2. {话题2}（{热度} {来源}）
...
📝 5篇终稿已生成，详见 Wiki
```

### 微头条格式

```
📌 微头条① | {话题名}
{全文}

#热点刀锋
```

---

## 配置选项

### Wiki 保存路径

修改 SKILL.md 中的存档路径：

```markdown
<your-wiki-path>/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md
```

### 定时任务推送目标

```bash
--deliver "telegram:YOUR_CHAT_ID"
```

---

## 相关技能

| 技能 | 关系 |
|------|------|
| `opencli-tool` | 依赖 - 热榜抓取 |
| `toutiao-viral-writing` | 参考 - 爆款写作 |

---

## 下一步

- [故障排查](TROUBLESHOOTING.md) - 常见问题解决方案
