# 热点刀锋 Cron 输出格式标准 v1.0

> 单一信源：所有cron模式的输出必须遵循此格式，确保下游脚本可解析。

---

## 一、模式A：选题报告输出格式

### 最终回复（推送到Telegram）

```
📊 热点刀锋选题报告（{日期}）

采集：{成功平台数}/5 平台，共 {总话题数} 条
去重后：{剩余话题数} 条
入选：{入选数} 条

━━━ Top {N} 选题 ━━━

1️⃣ {标题}（{总分}分 · {评级}）
   钱包{分数} | 反驳{分数} | 锚点{分数} | 适配{分数} | 分裂{分数}
   → {一句话角度}

2️⃣ ...

📎 PPT报告：MEDIA:{ppt路径}
```

### 中间数据文件（/tmp/hotspot-blade-output.json）

```json
{
  "mode": "topic_report",
  "date": "2026-06-20",
  "scrape": {
    "success_platforms": 5,
    "total_items": 250,
    "platforms": {
      "zhihu": {"count": 50, "status": "ok"},
      "weibo": {"count": 50, "status": "ok"},
      "bilibili": {"count": 50, "status": "ok"},
      "36kr": {"count": 50, "status": "ok"},
      "baidu": {"count": 50, "status": "ok"}
    }
  },
  "dedup": {
    "before": 250,
    "after": 180,
    "removed": 70
  },
  "topics": [
    {
      "title": "话题标题",
      "score": 8.5,
      "grade": "S",
      "scores": {
        "wallet_distance": 9,
        "rebuttal_cost": 8,
        "object_anchor": 7,
        "toutiao_fit": 9,
        "natural_split": 8
      },
      "source": "zhihu+weibo",
      "heat": "1000万",
      "angle": "一句话写作角度",
      "reason": "一句推荐理由"
    }
  ]
}
```

---

## 二、模式B：完整写作输出格式

### 最终回复（推送到Telegram，每篇一条消息）

```
🔥 {标题}

{正文，500字左右，纯文本}

━━━
📊 质量分：{score}/100 | 辣度：{微辣/中辣/特辣}
```

### 中间数据文件（/tmp/hotspot-blade-articles.json）

```json
{
  "mode": "full_writing",
  "date": "2026-06-20",
  "scrape": { "同模式A" },
  "dedup": { "同模式A" },
  "articles": [
    {
      "title": "文章标题",
      "content": "正文内容",
      "word_count": 620,
      "topic_score": 8.5,
      "topic_grade": "S",
      "quality_score": 85,
      "spiciness": "中辣",
      "sentence_patterns_used": ["本质剥离刀", "数字即幽默"],
      "angle": "写作角度",
      "russell_engine": "冲动驱动论"
    }
  ]
}
```

---

## 三、模式C：改写爆款输出格式

### 最终回复

```
🔥 {改写后标题}

{改写后正文}

━━━
原文标题：{原标题}
改动点：{1-2句说明}
质量分：{score}/100
```

---

## 四、错误输出格式

任何模式出错时：

```
❌ 热点刀锋执行失败

模式：{A/B/C}
步骤：{失败步骤}
原因：{错误原因}
建议：{修复建议}

已采集数据：{有/无}（如有，路径：/tmp/hotlist_data.json）
```

---

## 五、模型选择规则

| 场景 | 模型 | provider | 理由 |
|------|------|----------|------|
| cron 模式A（选题报告） | mimo-v2.5-pro | xiaomi | 成本低，评分任务不需要强模型 |
| cron 模式B（完整写作） | deepseek-chat | deepseek | 写作质量需要强模型 |
| 用户手动触发 | 跟随用户默认模型 | 跟随配置 | 尊重用户选择 |
| 改写爆款 | 跟随用户默认模型 | 跟随配置 | 改写需要创意 |

**核心原则**：
- 评分/筛选类任务 → 轻量模型（MiMo）
- 创意/写作类任务 → 强模型（DeepSeek/Claude）
- 用户手动触发 → 不覆盖，用默认模型

---

## 维护规则

- 此文件为cron输出格式的唯一权威定义
- 下游处理脚本必须按此格式解析
- 格式变更需更新版本号
