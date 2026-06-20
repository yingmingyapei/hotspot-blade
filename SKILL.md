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
hotlist-scraper → topic-scorer → 选Top 5 → 认知落差引擎 → toutiao-viral-writing → article-polish-master + retired-phrase-scanner（并行） → 推送
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

**步骤2.5：认知落差检测（新增 v4.2）**
- 加载 `references/cognitive-gap-engine-2026-06-20.md`
- 对每个入选话题执行：找读者默认共识 → 生成颠覆前提的假设
- 如果话题存在可翻的前提，将假设注入后续写作；如果无，跳过
- 输出：每个话题的默认共识 + 颠覆假设（<200 token/话题）

**步骤3：写作（加载 toutiao-viral-writing + russell-flip-arsenal）**
- 每个话题调用 toutiao-viral-writing 的七步流程
- 每篇**500字**左右（v4.2从600下调），纯文本输出
- 结构：反常识判断→拆解（现象嵌入其中，不独立成段）→冷幽默收束
- **必做**：加载 russell-flip-arsenal，慎用"战争即无聊"引擎（翻得太刻意）。优先用"占有vs创造"
- **铁律**：翻转观点已内化为己用，文中决口不提"某某说过""某学者认为"——思想是作者的

**步骤4：润色 + 质量验证（可并行 v4.2，实测省16.7%）**
- 润色：加载 article-polish-master，AI味检测、句式变阵、情感注入
- 质量验证（与润色并行）：运行 retired-phrase-scanner.py 扫描禁用语
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

## v4.2 方向：反馈闭环（IA讨论）

详见 `references/ia-feedback-loop-discussion-2026-06-20.md`。核心诊断：topic-scorer评分有效性从未验证。方案优先级：权重规则表 > Telegram bot标签 > 统计回归。

## v4.2 认知落差引擎（新增写作技术）

详见 `references/cognitive-gap-engine-2026-06-20.md`。17轮辩论中IA提出的最大发现——在评分和写作之间插入"颠覆默认前提"步骤。翻立场不如翻前提。命中率预估提升 10-30% → 40-60%。

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

### 14. 图片提示词必须先加载技能（反模式#3，已犯11次）

**问题**：用户说"生成图片提示词"时，直接写英文prompt跳过了 `article-to-image-prompt` 技能加载。

**2026-06-20复发记录**：同一会话连续3次违规——用户先后提交3篇文章要求"生成图片提示词"（外卖补贴大战、AI比人便宜、日本签证费涨5倍），每次都直接输出英文prompt，未加载技能。复发模式：写稿惯性太强，写完文章→自然过渡到"顺便生成图"→跳过技能。

**防御**：**写完文章的最后一段之前，先扫描用户原始请求中是否包含"生成图片/配图/prompt/提示词/封面"。如果命中，在输出文章正文最后一句时立即刹车——不输出图片提示词。先 `skill_view('article-to-image-prompt')`。铁律：即使"能写好prompt"也必须走技能流程。这不是能力问题，是流程纪律问题。

### 15. 脚本文件不能混入markdown文档（2026-06-20 IA反馈）
**问题**：`data_source_health_check.py` 前20行是markdown文档（标题、用法、代码块标记），导致IA语法检查失败。
**防御**：`.py` 文件只包含纯Python代码。使用说明、故障表格等放在 `references/` 下的 `.md` 文件中。同步前先验证：`python3 -c "import ast; ast.parse(open('file.py').read())"`。

---

### 15. 脚本文件混入markdown文档（2026-06-20，IA反馈）

**问题**：`data_source_health_check.py` 前 20 行是 markdown 文档（`> 用于热点刀锋...`），不是 Python 代码，导致 IA 端 Python 语法检查失败。

**防御**：
- 脚本文件（`.py`）必须是纯 Python 代码，第一行 `#!/usr/bin/env python3`
- 使用说明、故障策略等文档放在 `references/` 目录下的 `.md` 文件中
- 脚本的 docstring（`"""..."""`）是合法的 Python 注释，可以保留
- 每次 scp 后验证：`python3 -c "import ast; ast.parse(open('script.py').read())"`

---

## v4.2 优化方向（2026-06-20 WSL+IA联合辩论结论）

> 详见 `references/ia-debate-v42-full-2026-06-20.md`。11轮结构化辩论产出5个维度的诊断和方案。

| # | 诊断 | 结论 | 优先级 |
|---|------|------|--------|
| 1 | 反馈闭环断裂 | 选题评分从未验证。建权重规则表 | P0 |
| 2 | 思想密度不足 | article-polish-master 灌水感。降字数 600→500 + 现象嵌入拆解结构 | P0 |
| 3 | "战争即无聊"引擎翻得太硬 | 砍掉或慎用。保留"占有vs创造"。不翻比硬翻好 | P1 |
| 4 | 管路速度瓶颈 | 润色+禁用语扫描并行化，实测省 16.7%（非 30%） | P1 |
| 5 | MiMo 评分漏好题 | 三层评分：规则粗筛→MiMo 打分→DeepSeek 终审 | P2 |

**字数策略修正**：
- 模式B写作从 600 字降至 **500 字**
- 结构从"现象→反常识判断→层层拆解→冷幽默收束"压缩为"反常识判断(30字)→拆解含现象(350字)→冷幽默收束(120字)"
- 砍掉独立开头段，将现象作为拆解的血肉嵌入
- 已验证：IA 被逼用"日本签证费涨5倍"写 400 字范例，结构可行但偏紧；500 字给拆解环节更多呼吸空间

**翻转引擎裁决**：
| 引擎 | 判决 |
|------|------|
| 占有 vs 创造 | ✅ 保留 |
| 冲动驱动论 | — |
| 教育即偏见 | — |
| 战争即无聊 | ❌ 砍掉/慎用 |

---

### 17. 反馈闭环断裂（2026-06-20 IA诊断）

**问题**：topic-scorer 用 MiMo 评分选热点，但评分有效性从未被验证。P0-P3 所有优化都是"写前优化"，数据从不回流到评分系统。花钱让 DeepSeek 出稿，却不知道哪些选题是雷、哪些是金。

**防御**：
1. 建权重修正规则表——某类选题连续 3 次反馈"爆"，手动上调权重
2. Telegram bot 推标签（爆/平/冷）建立最小反馈锚点
3. 长期用统计回归剥离选题质量变量

### 18. 润色环节缺少思想密度检测（2026-06-20 IA诊断）

**问题**：toutiao-viral-writing 初稿出现"一个观点扩成五段"的灌水时，article-polish-master 只会让文字更顺滑，把灌水感包装得更好看。缺一个"思想密度检测"介入点。

**防御**：
1. **源头解决**：降字数 600→500，从 prompt 约束倒逼模型压缩信息
2. **结构压缩**：将"现象"嵌入"拆解"中作为例证，不独立成段
3. 可选方案（暂不实施）：LLM 做段落级因果递进检测或 Python 规则扫描每段新增信息量

### 19. 认知落差引擎缺少事实侧数据则退化为模型猜测（2026-06-20 32轮辩论结论）

**问题**：认知落差引擎（Gap-Hunter）需要两类输入——情绪侧（热搜标题+评论）和事实侧（统计数据+权威来源）。现有hotlist-scraper只覆盖情绪侧50%输入。没有事实侧，引擎无法做"热搜观点 vs 事实数据"的对比——只能让DeepSeek猜哪里可能有落差，产出的认知落差不可信。

**实锤**：第18轮IA用引擎跑3个话题产出了高质量假设，但第29轮承认"不接入外部数据，本质是模型自己在猜"。Round 25-27单prompt实验同时验证：事实核查+语气校准+认知深度三件事无法在一个线性prompt中兼顾。

**防御**：
- 短期：认知落差引擎只用于"明显存在反常识话题"的场景，不硬翻
- 中期：接入事实侧数据源——NewsAPI（英文）、GDELT（全球）、mx-search（中文财经）
- 运行时检测：Gap-Hunter产出后检查是否引用了具体数据——无引用的落差标注为"推测性落差"，降低权重
- 别假装有数据——宁可跳过认知落差步骤，也不输出没有事实支撑的"假反转"

### 20. 讨论节奏：不要主动暂停（2026-06-20 用户明确指令）

**问题**：WSL在跨轮次讨论中频繁停下来做总结、询问方向。用户明确说"不要停，我没说停就不要停""你怎么一轮一轮的，要讨论到底"。

**防御**：跨轮次讨论中，除非用户说"停"或"换话题"，否则持续推下一轮。不要在中间插入"要不要继续？"这类询问。总结和方向确认只在用户主动要求时做。


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

### 15. 子技能更新后必须验证整条链路（2026-06-20）
**问题**：改了hotlist_scraper.py后，没有检查hotspot-blade的cron prompt是否引用了新脚本路径。子技能更新可能打破父技能的流程。
**防御**：子技能更新后，检查所有父技能的引用是否仍然有效。建立依赖关系表，变更时逐条验证。

### 16. 多技能生态升级先扫描再动手（2026-06-20）
**问题**：8+个技能组成的生态，禁用语清单在5处维护版本各不同，v4.1方案重复3遍，Pitfalls有重复。
**防御**：升级前完整扫描所有子技能+脚本+参考文档，列出不一致清单。单一信源原则：同一份数据只在一处维护，其他地方引用。

### 15. 脚本文件不能混入markdown文档（2026-06-20 IA反馈）
**问题**：`data_source_health_check.py` 前20行是markdown文档（"> 用于热点刀锋..."），导致Python语法检查失败。
**防御**：脚本文件只放纯Python代码。文档/说明/使用方法放在 `references/` 下的独立.md文件中。创建脚本时检查：第一个非空行必须是 `#!/usr/bin/env python3` 或 `# -*-` 或 `import`。

---

## 写作质量优化原则

1. **具体模板代替抽象要求** — "第一段写冲突"而不是"写吸引人"
2. **禁用语前置禁止** — 统一清单见 `references/banned-phrases-unified.md`，扫描脚本见 `scripts/retired-phrase-scanner.py`
3. **反共识观点+具体案例** — 模型不爱写但读者爱看
4. **强模型写初稿，弱模型只做格式整理** — 后置润色治标不治本
5. **去重不要交给LLM** — 用Python逻辑硬匹配
