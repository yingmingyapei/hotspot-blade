# 海外信息差深度文章工作流（2026-06-10 实战沉淀）

## 适用场景

每日产出1篇投资/宏观深度文章，基于海外信息源挖掘国内未覆盖的信息差话题。

## 数据源（按可靠性排序）

### 已验证有效

1. **Hacker News API**（firebaseio.com，无需认证，全年稳定）
   - Top Stories: `curl -sL "https://hacker-news.firebaseio.com/v0/topstories.json"`（取前30个ID）
   - 单篇详情: `curl -sL "https://hacker-news.firebaseio.com/v0/item/{id}.json"`
   - 注意: API不带分数/评论数，需要用Jina Reader读取整页

2. **Jina Reader + HN 首页**（无需Cookie）
   - `curl -sL "https://r.jina.ai/https://news.ycombinator.com" -H "Accept: text/markdown"`
   - 返回结果含: 分数、评论数、发布时间、域名、作者
   - 可以解析出 Top 30 的故事标题、链接和元数据

3. **Jina Reader + HN 单帖讨论**
   - `curl -sL "https://r.jina.ai/https://news.ycombinator.com/item?id={id}" -H "Accept: text/markdown"`
   - 返回评论内容，可直接引用读者观点

4. **Jina Reader + 外部文章**
   - 对 HN 链接到的外部文章（The Decoder, Techdirt, Ars Technica, GitHub, Cupertino Lens等）基本可用
   - ⚠️ NYT、Reuters、Bloomberg、WSJ 等付费站点返回403

### 已验证无效（2026-06-10 状态）

- **Reddit API**（包括旧版 `old.reddit.com/.json`）→ 403（反爬升级）
- **Jina Reader + Reddit** → 403（被一起屏蔽）
- 需要 Reddit 开发者 OAuth2 Token 才能恢复

## 话题筛选流程

### Step 1: 扫描 HN Top 30

用 Jina Reader 读取 `news.ycombinator.com`，提取所有故事。

### Step 2: 识别高信息差话题

按以下优先级评估话题：

| 优先级 | 话题类型 | 判定标准 | 示例 |
|--------|---------|---------|------|
| ★★★★★ | AI/科技法规裁决 | 国内几乎无覆盖，但有可平移分析价值 | 德国法院判谷歌为AI内容负责 |
| ★★★★ | 安全/隐私/制裁 | 国内讨论空间有限，信息差大 | Let's Encrypt禁止受制裁地区证书 |
| ★★★★ | 科技巨头商业模式变化 | 商业逻辑可平移分析 | Apple折叠屏的开发者生态策略 |
| ★★★ | 宏观/金融政策 | 国内有覆盖但海外视角不同 | 美联储政策、贸易谈判新进展 |
| ★★ | AI模型能力更新 | 国内科技媒体已覆盖，需要独特角度 | Claude Fable 5发布（已有中文报道） |
| ★ | 纯技术/科研论文 | 太技术，不适合头条粉丝画像 | FPGA上的KAN网络 |

### Step 3: 深度调研

选定话题后，读取：
1. HN帖子原文链接（Jina Reader）
2. HN评论讨论（获取热门观点和争议点）
3. 同一话题的其他相关HN故事（交叉验证）

### Step 4: 文章结构

按九边风格（toutiao-viral-writing skill）写深度文章：

```
标题: 数据反差型或悬念型，必须有具体数字
开头: 直接抛出反常识结论或震撼数据（数字暴击）
中段: 
  - 事件描述（海外发生了什么）
  - 数据佐证（具体数字和分析）
  - 传导链分析（为什么会这样）
  - 对国内投资者的启示（把话筒指向读者）
结尾: 
  - 冷幽默或预言式收尾
  - 具体追问（"中国每年AI搜索调用量是多少？如果...你猜这个成本谁来买单？"）
字数: 1500-2500字
```

### Step 5: 保存

保存到 `/mnt/c/Users/yingm/OneDrive/文档/海外信息差/{YYYY-MM-DD}.md`

格式:
```yaml
---
title: 文章标题
date: YYYY-MM-DD
source: Hacker News / 具体来源
topic: 投资/宏观/AI监管
tags: [标签1, 标签2]
---

（正文）
```

## 参考案例

2026-06-10: "德国法院判谷歌为AI回答'说错话'买单——一场可能重塑全球AI产业的判决"
- HN话题: German ruling declares Google liable for false answers in AI Overviews (451pts, 244 comments)
- 交叉话题: Claude Fable 5发布 (2159pts), CEOs who think AI replaces employees are bad CEOs (628pts)
- 核心观点: 91%准确率×85亿次搜索=每天1.53亿错误答案；AI生成内容是"谷歌自己的话"不是搜索结果
