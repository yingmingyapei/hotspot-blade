---
name: hotspot-blade
version: 4.1
title: 热点刀锋
description: 热榜采集→选题评分→爆款写作→推送的完整工作流编排器。不重复数据采集和写作逻辑。触发词：「写热点」「抓热榜写微头条」「热点刀锋」
author: Hermes
keywords: [热榜, 热点, 微头条, 爆款, 编排]
requires:
  skills:
    - hotlist-scraper
    - topic-scorer
    - toutiao-viral-writing
    - article-polish-master
    - russell-flip-arsenal
  bins:
    - python3
    - python3.10
    - curl
---

# 热点刀锋（v4.1）

> 职责：编排。加载子技能做具体事，不重复内容。

## 三种工作模式

| 模式 | 触发 | 产出 |
|------|------|------|
| A·选题报告 | cron每天8点自动 | 评分→PPT报告→推送Telegram |
| B·完整写作 | 用户说"写热点" | 评分→写作→推送5篇 |
| C·改写爆款 | 用户丢入文章片段 | 改写成头条爆款→推送1篇 |

---

## 模式A：选题报告（cron）

```flow
hotlist-scraper → topic-scorer → PPT报告 → 推送Telegram
```

**cron prompt 结构：**
- 加载 hotlist-scraper → `python3 ~/.hermes/scripts/hotlist_scraper.py --json --limit 50`
- 加载 topic-scorer → 对每条打分，选Top 10，生成PPT
- 自带去重：读取 `~/.hermes/skills/productivity/hotspot-blade/hotspot-blade-history.json`
- 推送PPT到Telegram：`send_message(target="telegram", message="MEDIA:<ppt路径>")`

---

## 模式B：完整写作

```flow
hotlist-scraper → topic-scorer → 选Top 5 → toutiao-viral-writing → article-polish-master → 推送
```

**执行步骤：**

**步骤1：采集**
```bash
python3 ~/.hermes/scripts/hotlist_scraper.py --json --limit 50
```
→ 保存到 `/tmp/hotlist_data.json`

**步骤2：评分（加载 topic-scorer）**
- 按5维度打分，选Top 5
- 检查历史去重（7天）
- 输出选题确认给用户

**步骤3：写作（加载 toutiao-viral-writing + russell-flip-arsenal）**
- 每个话题调用 toutiao-viral-writing 的七步流程
- 每篇600字左右，纯文本输出
- **必做**：加载 russell-flip-arsenal，对每个话题应用至少1个翻转引擎找角度
- **铁律**：翻转观点已内化为己用，文中决口不提"某某说过""某学者认为"——思想是作者的

**步骤4：润色（加载 article-polish-master）**
- AI味检测、句式变阵、情感注入
- 三宗罪自检

**步骤4.5：质量验证（脚本化）**
```bash
python3 ~/.hermes/skills/productivity/hotspot-blade/scripts/retired-phrase-scanner.py --strict /tmp/article_N.txt
```
- 禁用语扫描：27个禁止词+6个禁止句式+频率检查
- 不通过则回退到步骤4重新润色

**步骤5：推送**
- 每篇作为一条消息推送到Telegram

---

## 模式C：改写爆款

**用户丢入内容时的快速写作模式：**

```flow
用户素材 → toutiao-viral-writing(改写模式) → russell-flip-arsenal(可选) → article-polish-master → 推送
```

改写模式是热点刀锋最强的能力——从已验证的好概念出发，只负责"怎么写得更爆"。实测展现量是原创模式的20倍以上。

---

## 数据文件

| 文件 | 用途 |
|------|------|
| `/tmp/hotlist_data.json` | 热榜采集原始数据 |
| `~/.hermes/skills/productivity/hotspot-blade/hotspot-blade-history.json` | 历史话题库（7天去重） |
| `/mnt/c/Users/yingm/OneDrive/Desktop/选题报告_日期.pptx` | PPT报告 |
| `references/banned-phrases-unified.md` | 禁用语统一清单（27词+6句式） |
| `references/banned-phrases-data.json` | 禁用语机器可读数据 |

## Cron Job ID

模式A（选题报告）：`75b38298aa5e`

## v4.1 升级计划

详见 `references/v41-optimization-plan-2026-06-17.md`。

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | simhash去重脚本化 + 禁用语清单统一 | ✅ 已完成 |
| P1 | curl_cffi替代curl+Cookie + 数字校验脚本 | ✅ 已完成 |
| P2 | 分级模型策略 + cron输出格式标准化 | ✅ 已完成 |
| P3 | Scrapling页面解析 | 观察→已完成（结论：不需要） |

---

## 分级模型策略

| 场景 | 模型 | provider | 理由 |
|------|------|----------|------|
| cron 模式A（选题报告） | mimo-v2.5-pro | xiaomi | 评分筛选不需要强模型，省token |
| cron 模式B（完整写作） | deepseek-chat | deepseek | 写作质量需要强模型 |
| 用户手动触发 | 跟随用户默认模型 | 跟随配置 | 尊重用户选择 |
| 改写爆款（模式C） | 跟随用户默认模型 | 跟随配置 | 改写需要创意 |

**核心原则**：
- 评分/筛选/去重 → 轻量模型（MiMo），0.01元/次
- 创意/写作/润色 → 强模型（DeepSeek），质量优先
- 用户手动触发 → 不覆盖默认模型
- 后置润色治标不治本，**强模型写初稿才是正解**

---

## Cron 输出格式标准

详见 `references/cron-output-format.md`。

**强制规则**：
- 模式A最终回复必须包含：采集统计 + Top N选题列表（含分数） + PPT路径
- 模式B最终回复必须包含：标题 + 正文 + 质量分 + 辣度
- 中间数据写入 `/tmp/hotspot-blade-output.json` 或 `/tmp/hotspot-blade-articles.json`
- 错误时输出：模式 + 失败步骤 + 原因 + 建议

---

## 关键陷阱

### 1. 子技能加载顺序
**问题**：加载子技能消耗上下文。模式A只需加载 hotlist-scraper + topic-scorer，不要加载写作技能。模式B才加载全套。
**防御**：按模式精确加载。不加载不需要的技能。

### 2. cron 执行限制
**问题**：cron模式下 execute_code 被阻断，管道到解释器被安全系统拦截。
**防御**：cron模式用 terminal + python3 -c 或脚本文件，不用 execute_code。也不要用 `| python3` 管道。

### 3. 去重不能交给LLM
**问题**：弱模型（MiMo）在prompt中说"去重"时经常跳过，history.json不更新，导致同一话题反复写。
**防御**：去重必须下沉到脚本层——用 simhash 或编辑距离做硬去重，0 token 0 误判。history.json 记录 SHA256 哈希，脚本先过滤再进入写作流程。LLM 只做最后的内容去重（同一事件的不同角度）。**去重这种机械操作不要交给LLM，写python逻辑硬匹配。**

### 4. 数据源故障不降级
**问题**：某平台API失败时不要用百度搜索等二手数据源替代。百度搜索返回的是百度算法过滤过的二手数据。
**防御**：跳过该平台，记录原因，至少3个平台成功才继续。不找替代。备用方案：opencli-tool 作为 fallback。

### 5. 历史文件首次执行
**问题**：`hotspot-blade-history.json` 首次执行时不存在。
**防御**：检查文件是否存在，不存在则创建空结构 `{"last_updated": "", "topics": []}`。

### 6. 不要混用"量化"一词
**问题**：在内容创作语境中使用"量化"容易被误解为金融量化分析。
**防御**：用"标准化""数值化""具体化"代替"量化"。

### 7. Cookie过期问题
**问题**：curl+Cookie 直连平台API，Cookie容易过期导致采集失败。
**防御**：用 curl_cffi 的 impersonate 参数模拟浏览器指纹，不需要Cookie。比 requests 稳定很多，可绕过 Cloudflare。详见 `bypass-website-anti-bot` 技能。

### 8. 数字编造防护
**问题**：LLM 写热点文章时会编造具体数字/百分比，读者一查就穿帮。
**防御**：1）prompt里明确写"不确定的数据用'据报道''有数据显示'代替具体数字" 2）写作完成后用脚本扫描文章中的数字（正则匹配 \d+%/\d+亿等），与原始数据源对比 3）热点文章尽量少用数据，多用故事和观点。

### 9. prompt用具体模板代替抽象要求
**问题**：prompt写"写吸引人的开头"，弱模型(MiMo)会写出平庸的套话。
**防御**：用具体指令代替抽象要求——"第一段写冲突""开头用反常识判断句""结尾用冷幽默收束"。具体模板比抽象要求有效10倍。

### 10. 弱模型只做格式整理
**问题**：MiMo写初稿AI味重、观点平庸，后置润色(article-polish-master)治标不治本。
**防御**：分级策略——cron模式用MiMo省token（质量凑合），用户手动触发时用强模型(DeepSeek/Claude)出质量。弱模型只做格式整理，不做强模型才能做的创意写作。

### 11. cron输出格式标准化
**问题**：cron模式输出格式不统一，后续处理脚本每次都要适配。
**防御**：cron 输出必须遵循固定模板，不然后续自动化处理全部失效。

### 12. AgnesAI Token 过期导致 Cron 全线失败
**问题**：toutiao-weekly cron job (3992910168b6) 因 AgnesAI token 过期返回 401 错误。
**防御**：写作流程中图片生成设为 optional（失败时跳过），不要让图片生成阻塞文本输出。定期检查 token 有效性。

### 13. 平台反爬虫升级
**问题**：头条/微博/知乎等平台不定期升级反爬虫机制，curl+Cookie 方案突然失效。
**防御**：监控 hotlist-scraper 输出条数，连续 0 条 → 触发告警。curl_cffi 是中期替代方案，极端情况用 browser_navigate 兜底。

### 14. 图片提示词必须先加载技能（反模式#3，已犯8次）
**问题**：用户说"生成图片提示词"时，直接写英文prompt跳过了 `article-to-image-prompt` 技能加载。
**防御**：任何模式（B/C）的输出步骤前，检查用户是否要求"生成图片提示词/配图/封面"。如果匹配 → **立即停止当前输出**，先 `skill_view('article-to-image-prompt')` 加载技能。**铁律**：即使"能写好prompt"也必须走技能流程。

---

## P3分析结论：Scrapling不需要

**2026-06-20 评估结论**：当前5个平台全部使用JSON API，curl_cffi完全够用，Scrapling不增加价值。

| 平台 | 数据方式 | curl_cffi | Scrapling必要性 |
|------|---------|-----------|----------------|
| 知乎 | JSON API | ✅ | 不需要 |
| 微博 | JSON API | ✅ | 不需要 |
| B站 | JSON API | ✅ | 不需要 |
| 36氪 | JSON API | ✅ (legacy) | 不需要 |
| 百度 | JSON API | ✅ | 不需要 |

**何时需要Scrapling**：某平台关闭JSON API、改用HTML渲染时。已创建 `scripts/hotlist_html_fallback.py` 作为HTML降级方案。

**升级路径**：`curl_cffi JSON → HTML Fallback → Scrapling → browser_navigate`

---

## 写作质量优化原则

1. **具体模板代替抽象要求** — "第一段写冲突"而不是"写吸引人"
2. **禁用语前置禁止** — 统一清单见 `references/banned-phrases-unified.md`，扫描脚本见 `scripts/retired-phrase-scanner.py`
3. **反共识观点+具体案例** — 模型不爱写但读者爱看
4. **强模型写初稿，弱模型只做格式整理** — 后置润色治标不治本
5. **去重不要交给LLM** — 用Python逻辑硬匹配
