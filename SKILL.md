---
name: hotspot-blade
title: 热点刀锋
description: 自动抓取多平台热榜（知乎+微博+Buzzing.cc海外信息差+36氪/HN科技垂直）+ 一键生成5篇爆款微头条。全流程（三模式自动适配）：定时任务=全自动；交互模式=人工确认。触发词：「写热点」「抓热榜写微头条」「热点刀锋」「自动写头条」「每天热点」
author: Hermes
keywords: ["热点", "热榜", "微头条", "爆款", "自动写作", "微博热搜", "知乎热榜", "Buzzing.cc", "海外信息差", "热点抓取", "自动生成", "虎嗅", "36氪", "IT之家", "酷安", "科技热榜"]
requires:
  skills:
    - "opencli-tool"
    - "toutiao-viral-writing"
  bins:
    - opencli
---

# 热点刀锋

> **多平台热榜抓取 + 爆款微头条一键生成**
>
> 核心定位：把"找话题 → 写稿"这个最费时的环节，变成一个标准化、可复用的工作流。
>
> 触发词：「写热点」「抓热榜写微头条」「热点刀锋」「自动写头条」「每天热点」

---

## 一、激活条件

以下任一情况触发本技能：

- 用户说"写热点""抓热榜写微头条""热点刀锋"
- 用户说"自动写头条""每天热点""抓今天的热榜"
- 用户说"帮我找5个热门话题写微头条"
- 用户说"按这个流程写"（当上下文指向热榜写作时）

---

## 二、前置条件检查

执行本技能前，必须确认以下环境：

```bash
# 1. 检查 opencli 是否可用
opencli doctor

# 预期输出：
# [OK] Daemon: running on port 19825
# [OK] Extension: connected
# [OK] Connectivity: connected
```

**如 Daemon 未运行：**
```bash
# Mac/Linux
opencli daemon start

# Windows (WSL)
opencli daemon start
```

**如 Extension 未连接：**
1. 打开 Chrome，访问 `chrome://extensions`
2. 确认 Browser Bridge 扩展已启用
3. 重启 Chrome 后再试

---

## 二点五、数据源稳定性保障（核心原则）

**⚠️ 核心原则：没有稳定的数据源，一切工具都是空幻。**

### 数据源健康检查机制

每次执行前必须进行数据源健康检查：

```bash
# 数据源健康检查脚本
python3 -c "
import json
import subprocess

data_sources = [
    ('知乎热榜', 'opencli zhihu hot -f json --limit 5'),
    ('微博热搜', 'opencli weibo hot -f json --limit 5'),
    ('36氪热榜', 'opencli 36kr hot -f json --limit 5'),
    ('v2ex热榜', 'opencli v2ex hot -f json --limit 5'),
]

for name, cmd in data_sources:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f'✅ {name}：成功获取 {len(data)} 条数据')
            except json.JSONDecodeError:
                print(f'⚠️ {name}：返回数据格式错误')
        else:
            print(f'❌ {name}：命令执行失败')
    except subprocess.TimeoutExpired:
        print(f'⏰ {name}：命令超时')
    except Exception as e:
        print(f'❌ {name}：错误 - {e}')
"
```

### 数据源故障自动切换策略

| 数据源 | 主要命令 | 备用方案1 | 备用方案2 | 故障处理 |
|--------|----------|-----------|-----------|----------|
| 知乎热榜 | `opencli zhihu hot` | curl_cffi直接抓取API | 使用v2ex热榜替代 | 记录故障，继续执行 |
| 微博热搜 | `opencli weibo hot` | 无备用 | 使用36氪热榜替代 | 记录故障，继续执行 |
| Buzzing.cc | curl_cffi抓取 | browser extract | 使用Hacker News替代 | 记录故障，继续执行 |
| 36氪热榜 | `opencli 36kr hot` | 无备用 | 使用v2ex热榜替代 | 记录故障，继续执行 |
| v2ex热榜 | `opencli v2ex hot` | 无备用 | 使用36氪热榜替代 | 记录故障，继续执行 |

### 定时任务环境下的登录态保持

**问题**：定时任务环境无法保持知乎/微博的登录态

**解决方案**：
1. **优先使用API接口**：opencli zhihu hot/weibo hot使用API接口，不依赖登录态
2. **备用方案**：如果API失败，使用curl_cffi直接抓取公开API
3. **降级策略**：如果所有方案失败，使用其他数据源（36氪/v2ex/Buzzing.cc）

### 数据源质量监控

```bash
# 数据源质量检查
python3 -c "
import json
import subprocess

# 检查数据源返回的数据质量
def check_data_quality(data, source_name):
    if not data:
        return False, '数据为空'
    
    if len(data) < 3:
        return False, f'数据量不足：{len(data)}条'
    
    # 检查数据字段完整性
    required_fields = ['title', 'rank']
    for item in data[:3]:
        for field in required_fields:
            if field not in item:
                return False, f'缺少必要字段：{field}'
    
    return True, f'数据质量正常：{len(data)}条'

# 测试数据源
sources = [
    ('知乎热榜', 'opencli zhihu hot -f json --limit 10'),
    ('微博热搜', 'opencli weibo hot -f json --limit 10'),
    ('36氪热榜', 'opencli 36kr hot -f json --limit 10'),
    ('v2ex热榜', 'opencli v2ex hot -f json --limit 10'),
]

for name, cmd in sources:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            is_good, msg = check_data_quality(data, name)
            if is_good:
                print(f'✅ {name}：{msg}')
            else:
                print(f'⚠️ {name}：{msg}')
        else:
            print(f'❌ {name}：命令执行失败')
    except Exception as e:
        print(f'❌ {name}：错误 - {e}')
"
```

### 数据源故障应急预案

**场景1：知乎热榜抓取失败**
- 立即切换到备用方案：curl_cffi直接抓取API
- 如果备用方案失败，使用v2ex热榜替代
- 在执行报告中记录故障原因

**场景2：微博热搜抓取失败**
- 使用36氪热榜替代
- 在执行报告中记录故障原因

**场景3：Buzzing.cc抓取失败**
- 使用browser extract备用方案
- 如果备用方案失败，使用Hacker News替代
- 在执行报告中记录故障原因

**场景4：所有数据源都失败**
- 立即停止执行，发送故障报告
- 不使用过期数据凑合
- 等待数据源恢复后重新执行

### 数据源稳定性检查清单

```
□ 知乎热榜：opencli zhihu hot 成功返回数据
□ 微博热搜：opencli weibo hot 成功返回数据
□ Buzzing.cc：curl_cffi 成功提取标题
□ 36氪热榜：opencli 36kr hot 成功返回数据
□ v2ex热榜：opencli v2ex hot 成功返回数据
□ 数据质量：每个数据源返回≥3条有效数据
□ 故障记录：所有故障都记录到执行报告
```

**⚠️ 定时任务/headless环境特殊处理（Extension无法连接时）：**
- opencli 的 API 类命令（`zhihu hot -f json`、`weibo hot -f json`）**不依赖 Browser Bridge**，可直接使用
- 只有 `opencli browser` 系列命令（open/extract）依赖 Extension
- 因此 Extension 断开并不致命：知乎和微博 API 接口仍能正常抓取
- Buzzing.cc 的 browser extract 会失败 → 直接跳过，用 curl_cffi 正则提取代替
- 执行报告中需注明 Buzzing.cc 抓取失败原因

---

## 三、第一阶段：平台热榜抓取

### 热榜来源价值评级（2026-05-07 三工具实测更新）

| 来源 | 价值 | 说明 | 实测状态 |
|------|------|------|---------|
| 知乎热榜 | ✅ 必抓 | 大众话题，社会议题丰富，九边适配性最高 | opencli zhihu hot ✅ |
| 微博热搜 | ✅ 必抓 | 舆情风向标，与知乎话题交叉验证 | opencli weibo hot ✅ |
| **Buzzing.cc** | **✅ 强烈推荐（新增）** | **28个海外子站聚合（HN/BBC/经济学人/彭博/WSJ/NYT/卫报/FT/路透社/Axios/Nature/Politico等），中文翻译，填补热点刀锋海外信息差空白** | **curl_cffi 200 + browser ✅** |
| 36氪热榜 | ✅ 推荐（tophub替代） | 科技创业/商业话题，与知乎微博重合度低 | `opencli 36kr hot` ✅ |
| Hacker News | ✅ 推荐（tophub替代） | 全球科技社区，英文但内容质量高 | `opencli hackernews top` ✅ |
| newsnow.busiyi.world | ❌ 不推荐 | 本质是知乎+微博内容二次聚合，**三工具验证100%重合**，无增量信息 | 可抓取但冗余 |
| SoPilot.net | ❌ 非热榜工具 | **AI营销SaaS平台**（产品诊断+营销策略+SEO+多平台发布），不是榜单聚合站。X起爆帖监控是子功能需注册 | 可访问但定位错误 |
| 果汁排行榜 | ⚠️ 待修复 | 各类榜单大全，补充小众领域 | **SSL证书过期** |
| AnyKnew | ⚠️ 待修复 | 精细化分类热榜，历史榜单 | **TLS连接错误** |

### ⚠️ 数据实时性铁律（每次执行前必查）

```
执行前必须完成：
1. 执行 date 确认当天日期，非交易日（周末/节假日）需注明数据来源日期
2. 所有热榜数据必须是当天发布的，有明确时间戳
3. 排除"昨天""日前""近期"等模糊时间表述
4. 话题热度必须是当天实时热度，不得使用历史热度数据
5. 数据不满足以上条件时，立即重新抓取，不得凑合使用过期数据
```

### 执行命令

按以下顺序抓取热榜（知乎和微博必抓，Buzzing.cc强烈推荐，36氪/HN科技垂直）：

```bash
# 知乎热榜（✅ 必抓）
opencli zhihu hot -f json

# 微博热搜（✅ 必抓）
opencli weibo hot -f json

# Buzzing.cc 海外信息差（✅ 强烈推荐 — 28个海外媒体聚合，中文翻译）
# 方法A: curl_cffi（无需浏览器，推荐定时任务使用）
python3 -c "
from curl_cffi import requests
import re
resp = requests.get('https://buzzing.cc', impersonate='chrome', timeout=15)
# 优化正则：匹配20-200字符的标题文本，排除URL、短文本、HN Points、网站域名等
titles = re.findall(r'>([^<]{20,200})<', resp.text)
seen = set()
exclude_patterns = [
    r'http[s]?://',  # URL
    r'\.buzzing\.cc$',  # 网站域名
    r'www\.[a-z]+\.[a-z]+$',  # www.开头的域名
    r'↑',  # HN Points格式（包含↑符号）
    r'HN\s*Points',  # HN Points文本
    r'^Show\s*HN:',  # Show HN前缀
    r'^I\s+switched',  # 常见开头
    r'^The\s+Old\s+Guard',  # 常见开头
    r'^Buzzing\s*-',  # Buzzing网站标题
    r'^用中文浏览',  # 中文描述
    r'^本站并非官方网站',  # 免责声明
    r'^最后更新于',  # 更新时间
    r'^Twitter\s*@',  # Twitter标签
]
for t in titles:
    t = t.strip()
    if t and t not in seen and len(t) > 15 and not t.startswith('http') and not t.startswith('//'):
        # 检查是否匹配排除模式
        exclude = False
        for pattern in exclude_patterns:
            if re.search(pattern, t, re.IGNORECASE):
                exclude = True
                break
        if not exclude:
            seen.add(t)
            print(f'  - {t[:120]}')
            if len(seen) >= 30:
                break
"
# 方法B: browser（需Chrome扩展）
opencli browser open "https://buzzing.cc" && sleep 5 && opencli browser extract

# 科技垂直补充（36氪/HN/IT之家）
opencli 36kr hot -f json          # 36氪热榜
opencli hackernews top -f json    # Hacker News英文热榜
opencli ithome hot                # IT之家数码/消费电子
```

**⚠️ 不要用 `head -N` 截断**：该页面总字符数约2万，`head -150` 会漏掉后半部分的子站数据。完整 extract 后再在输出中手动定位各子站区块。

**从 extract 结果中筛选关键子站**（按九边适配性排序）：
- **虎嗅**：商业深度报道，社会议题强，优先选。关键词：「困在重资产里的中国英伟达」「入境游遍地是黄金」「失业的深圳人」
- **36氪**：科技创业/商业，话题新但偏垂直。适合有投资/科技背景的写手
- **IT之家**：数码/消费电子，"张雪机车WSBK夺冠"类话题与机车投资人高度相关
- **酷安**：数码社区真实讨论，科技数码圈层话题
- **少数派**：工具/效率向，受众偏专业，泛用性较弱
- **果壳**：科普向，适合科学类微头条
- **威锋网**：Apple生态，果粉向，泛用性一般
- **Readhub**：科技资讯汇总，适合快速扫热点

> ⚠️ **newsnow.busiyi.world 已验证无增量价值**：内容就是知乎+微博的二次聚合，不值得专门抓取。

### 字段说明

| 平台 | 关键字段 | 热榜字段 |
|------|---------|---------|
| 知乎 | `rank`, `title`, `heat`, `answers`, `url` | 热度值 + 回答数 |
| 微博 | `rank`, `word`, `hot_value`, `category`, `url` | 热值 + 分类标签 |
| B站 | `rank`, `title`, `author`, `play`, `danmaku` | 播放量 + 弹幕数 |
| Reddit | `rank`, `title`, `score`, `comments` | 得分 + 评论数 |

### 常见错误处理

```
错误：空数组 []
原因：Browser Bridge 未连接，或 Reddit 等平台需要登录态
解决：
  1. opencli doctor 检查扩展连接
  2. 在 Chrome 中登录目标平台
  3. 刷新页面确保会话有效

错误：Connection refused
原因：Daemon 未运行
解决：opencli daemon start

错误：Command not found
原因：opencli 未安装
解决：npm install -g @jackwener/opencli

错误：Buzzing.cc 内容提取为空
原因：页面大量 JS 渲染，curl_cffi 只能获取静态 HTML
解决：
  1. 优先用 browser open + extract（需 Chrome 扩展）
  2. 或直接用 curl_cffi 获取后，用正则提取 `>([^<]{20,200})<` 匹配标题文本
  3. Buzzing.cc 的 HN 板块内容在首页首屏，静态 HTML 已包含标题和 HN Points

错误：guozhivip.com/rank 或 anyknew.com 连接失败
原因：SSL 证书过期（guozhivip）或 TLS 连接错误（anyknew），可能是服务器维护
解决：
  1. 跳过该来源，不影响核心产出
  2. 网络恢复后重新评估
```

---

## 四、第二阶段：候选话题筛选

### 筛选标准

从抓取结果中筛选候选话题，按以下维度评分：

| 维度 | 说明 | 权重 |
|------|------|------|
| 热度 | 各平台榜单排名，Top 10优先 | 30% |
| 九边适配性 | 是否有明确矛盾/靶向/社会议题 | 40% |
| 讨论空间 | 普通人有话说，能引发评论 | 20% |
| 话题时效性 | 是否有时效性，过了就没意义 | 10% |

### 九边适配性评级标准

```
★★★★★ 完美靶子：有明确矛盾、可解构的社会议题（双标/话术打脸/利益不对等）
★★★★☆ 良好：有矛盾但需要转换角度
★★★☆☆ 一般：有热度但靶向模糊
★★☆☆☆ 较弱：娱乐向/纯情绪发泄
★☆☆☆☆ 不选：饭圈/艺人日常/无信息量
```

### 筛选排除规则

以下话题直接排除：

- 纯娱乐/饭圈话题（明星日常、粉丝打投）
- B站娱乐向视频（除非有明确社会议题）
- 无具体矛盾的事实性新闻（地震/天气/单纯事件报道）
- 太过专业化的小众话题（普通人无感）

### 话题多样性规则

为避免5篇内容角度重复，同一子类话题最多选2个：

| 子类 | 典型话题 |
|------|---------|
| 教育 | 高考/录取/学区房/教师待遇 |
| 就业 | 裁员/求职/工资/考公 |
| 科技 | AI/手机/数码/互联网 |
| 消费 | 家电/汽车/电商/物价 |
| 社会 | 婚姻/房产/养老/地域歧视 |
| 国际 | 地缘政治/国际贸易/外交 |

如某子类超过2个，降级选其他子类的话题。

### 话题→标签映射库（智能推荐标签）

| 话题子类 | 推荐标签 | 说明 |
|----------|----------|------|
| 教育 | #高考 #教育 #学区房 #教师待遇 | 教育相关话题，标签精准匹配 |
| 就业 | #职场 #裁员 #求职 #工资 #考公 | 就业相关话题，标签覆盖全面 |
| 科技 | #AI #手机 #数码 #互联网 #科技 | 科技相关话题，标签多样 |
| 消费 | #消费 #家电 #汽车 #电商 #物价 | 消费相关话题，标签实用 |
| 社会 | #社会 #婚姻 #房产 #养老 #地域 | 社会相关话题，标签广泛 |
| 国际 | #国际 #地缘政治 #贸易 #外交 | 国际相关话题，标签专业 |
| 海外信息差 | #海外 #信息差 #国际视野 #前沿 | 海外信息差话题，标签独特 |

**标签使用规则：**
- 每篇微头条选择1-3个精准标签
- 优先选择与话题子类匹配的标签
- 可根据具体内容添加细分标签（如#AI可细分为#ChatGPT #大模型等）
- 标签应简洁明了，不超过5个字

### 输出格式

汇总候选话题，按总分排序，输出：

```
## 候选话题汇总

| # | 话题 | 平台 | 热度 | 适配性 | 选择理由 |
|---|------|------|------|--------|---------|
| 1 | xxx | 知乎#2 | 419万 | ★★★★★ | ... |
| 2 | xxx | 知乎#7 | 123万 | ★★★★★ | ... |
```

---

## 五、第三阶段：话题确认（双模式）

### 定时任务模式（默认，跳过确认）
定时任务直接按九边适配性从高到低自动选择前5个候选话题，不等待确认，立即进入七步全流程写作。

### 交互模式（用户主动触发时）
向用户展示候选话题汇总（按九边适配性排序），等待确认后再进入写作阶段。

如用户说"帮我找5个热门话题写微头条"，先展示候选话题，等用户回复数字（如"1、2、3、4、5"）后开始写作。

### 询问话术（仅交互模式）

```
已抓取热榜，筛选出以下候选话题（按九边适配性排序）：

1. [话题A] — 热度X万，★★★★★
   理由：...
2. [话题B] — 热度X万，★★★★★
   理由：...
3. [话题C] — 热度X万，★★★★
   理由：...
...

请确认最终5个话题。如需调整或替换某条，请告诉我。
```

### 用户可能的反馈

- **全部同意** → 直接进入写作阶段
- **替换某条** → 用其他候选话题替换
- **想看更多选项** → 从候选列表中补充说明
- **暂停** → 存档候选话题，下次继续

---

## 六、第四阶段：爆款微头条生成

### 定时任务模式
对每个话题，依次执行七步，**一次性完成全部七步再输出终稿**。不对用户拆分步骤输出，不等待确认，直接生成可直接发布的终稿。

### 交互模式
对确认后的每个话题，按七步工作流生成，每篇完成后展示给用户，确认OK后再写下一篇。

```

对确认后的每个话题，按「爆款刀锋」七步工作流生成：

```
第一步：选题定位
  → 分析话题核心矛盾
  → 确定九边式靶向（怼谁？）
  → 确定情绪方向（无奈/讽刺/愤怒）

第二步：钩子设计
  → 开场：数字暴击 + "说真的，并没有" + 悖论钩子
  → 中段："说白了"定性 + 数据跟进 + "你猜？"
  → 结尾："但更关键的是"递进 + 预言 + 具体追问

第三步：草稿写作 + 快速预览检查
  → 九边版暴风雪开场
  → 九边版胖大山打脸
  → 九边版递进收尾
  → 快速预览检查（草稿完成后立即检查）：
    □ 核心矛盾是否清晰？（一句话能说清）
    □ 九边句式是否自然？（不生硬堆砌）
    □ 数字/细节是否足够？（≥3个具体细节）
    □ 情绪铺垫是否到位？（打脸前有铺垫）
  → 如不达标，立即调整再继续下一步

第四步：共鸣适配
  → 替换专业词为普通人感知词
  → 检查追问是否具体

第五步：钩子强化检查
  → 九边句式七条检查清单

第六步：算法发布检查 + 标题A/B测试 + 算法优化
  → 标题A/B测试：生成3个候选标题，按算法友好度评分
    □ 标题A：数字暴击型（如："3个真相告诉你..."）
    □ 标题B：反差对比型（如："月薪3千和月薪3万的人，区别在这"）
    □ 标题C：悬念提问型（如："为什么年轻人不愿生孩子？"）
  → 标题评分标准：
    - ≤25字，有数字+反差感（+2分）
    - 无"竟然""必须""震惊"等绝对词（+1分）
    - 慎用问号（头条算法打压）（+1分）
    - 包含情绪关键词（无奈/讽刺/愤怒）（+1分）
  → 选择评分最高的标题作为最终标题
  → 标签：1-3个精准标签，基于话题分类推荐
  → 发布时机：基于历史数据推荐最佳时段（早8-9点/午12-13点/晚20-22点）
  → 算法优化三要素：
    □ 开头3秒钩子：前3秒必须抛出核心矛盾或悬念，抓住用户注意力
    □ 中间互动引导：每300字设置一个互动引导（提问/反转/数据冲击）
    □ 结尾行动号召：明确引导用户点赞/评论/转发（如："你觉得呢？""转发给需要的人"）
  → 发布时机详细分析：
    □ 早高峰（8:00-9:00）：通勤时间，用户刷手机频率高，适合发布轻松/娱乐类内容
    □ 午休时间（12:00-13:00）：午休时间，用户有空闲，适合发布深度/思考类内容
    □ 晚高峰（18:00-19:00）：下班时间，用户放松，适合发布社会/生活类内容
    □ 睡前时间（20:00-22:00）：睡前刷手机，用户情绪敏感，适合发布情感/共鸣类内容
    □ 周末全天：用户时间充裕，适合发布长文/深度分析类内容
  → 根据话题类型选择最佳发布时段：
    - 教育/就业类：早高峰或午休时间
    - 科技/消费类：晚高峰或睡前时间
    - 社会/国际类：睡前时间或周末全天
    - 海外信息差类：早高峰（与海外时差同步）

第七步：润色加固
  → 三宗罪自检
  → 保留骨架，磨掉AI味
```

### 九边核心句式速查

```
开场：数字 + "你以为X？并没有。说真的Y。"
打脸：说白了，X不是在干Y，是在干Z。
定性：这不叫X，这叫Y。
冷幽默：[某现象]听了这话，默默X了。
递进：很明显X。但更关键的是Y。
追问：你猜X？Y？还是Z？
数字幽默：数字排比，不用加形容词。
```

### 三宗罪自检（必须过）— 标准化指标

```
第一宗：细节模糊，缺少具象感（细节数≥3个/篇）
  □ 每个关键名词是否有型号/价格/场景细节？
  □ 有没有用"某"字带过的模糊表述？
  □ 标准化检查：整篇微头条中具体细节（数字、品牌、价格、地点等）是否≥3个？

第二宗：逻辑跳脱，过渡生硬（逻辑转折≤2处/篇）
  □ 每个大转折前是否有承上启下的过渡句？
  □ 时间线跳跃是否有交代？
  □ 情绪铺垫是否到位才打脸？
  □ 标准化检查：整篇微头条中逻辑转折点是否≤2处？超过2处需要增加过渡句

第三宗：口语碎句多，表达冗余粗糙（自问自答≤3处，九边句式不堆叠）
  □ 连续短句是否每句都有新信息？
  □ 自问自答是否超过3处？
  □ 九边句式是否集中在不同段落（不堆叠）？
  □ 标准化检查：自问自答句式是否≤3处？九边句式是否分散在不同段落？
```

---

## 七、第五阶段：Wiki存档

### 存档时机

每完成一轮（5篇），自动存档到 Wiki，不遗漏。

### 存档文件命名

```
<your-wiki-path>/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md
```

格式：`{date}-热点刀锋微头条-5篇.md`

> 请将 `<your-wiki-path>` 替换为你的实际 Wiki 保存路径。

### 存档内容模板

```markdown
# 热点刀锋工作日志 {日期}

## 执行信息
- 执行时间：{timestamp}
- 抓取平台：{platforms}
- 最终话题数：{count}个

## 候选话题汇总
{候选话题表}

## 最终确认话题
{确认话题表}

## 生成的微头条

### 微头条①：{话题名}
{全文}

### 微头条②：{话题名}
{全文}
...

## 三宗罪自检记录
{自检表}

## 执行笔记
{任何特殊情况、用户反馈、优化建议}
```

---

## 八、完整执行示例

### 用户输入
```
帮我按热点刀锋流程写5篇微头条
```

### Agent 执行步骤

```
Step 1: 检查环境
  $ opencli doctor
  → [OK] Daemon running, Extension connected

Step 2: 抓取热榜
  $ opencli zhihu hot -f json
  $ opencli weibo hot -f json
  $ opencli bilibili hot -f json
  → 汇总候选话题

Step 3: 筛选候选
  → 按九边适配性排序，输出候选话题表

Step 4: 等待用户确认
  → 用户确认5个话题

Step 5: 逐篇生成（循环5次）
  对每个话题：
    → 选题定位 → 钩子设计 → 草稿写作
    → 共鸣适配 → 钩子强化 → 润色加固
    → 三宗罪自检 → 输出

Step 6: Wiki存档
  → 保存工作日志到 wiki/hotspot-blade/
```

---

## 九、已知限制与注意事项

### 平台限制

| 平台 | 限制 | 应对 |
|------|------|------|
| Reddit | 需要Chrome登录态 | 抓取失败时跳过，换其他平台 |
| B站 | 娱乐向内容多 | 筛选时优先选有社会议题的 |
| 微博 | 娱乐热搜占比高 | 配合知乎热榜交叉验证 |
| Buzzing.cc | JS渲染，curl_cffi只能获取静态HTML | 用browser open+extract（需Chrome扩展）或正则提取静态HTML标题 |
| 全平台 | 话题热度实时变化 | 抓取后尽快使用 |

### 各平台热榜来源实测结论（2026-05-07 19:15 完整实测更新）

经 **scrapling StealthyFetcher + curl_cffi + browser 三种工具交叉验证**，各来源定位与可用性如下：

| 来源 | 定位 | 与知乎微博重合度 | 实际可抓取性 | 实测工具 |
|------|------|---------------|-------------|---------|
| 知乎热榜 | 主力来源，大众社会议题 | — | ✅ API稳定，opencli直接可用 | opencli zhihu hot |
| 微博热搜 | 舆情风向标，交叉验证 | 与知乎有交叉 | ✅ API稳定，opencli直接可用 | opencli weibo hot |
| **Buzzing.cc** | **海外信息差（28个子站：HN/BBC/经济学人/彭博/WSJ/NYT/卫报/FT/路透社/Axios等）** | **几乎不重合** | **✅ curl_cffi 200 + browser 完整内容。是热点刀锋最大增量来源** | curl_cffi + browser |
| newsnow.busiyi.world | 多平台横向聚合 | **100%重合**（知乎+微博二次聚合） | ✅ curl_cffi 200 + browser 完整内容，但**无增量价值** | curl_cffi + browser + opencli |
| SoPilot.net | **AI营销SaaS（非热榜聚合站）** | — | ✅ 可访问，但**不是榜单工具**，是产品诊断+营销策略+SEO内容+多平台发布平台。X起爆帖监控是子功能，需注册账号 | curl_cffi + browser |
| 果汁排行榜 guozhivip.com/rank | 各类榜单大全，小众领域补充 | — | ❌ **SSL证书过期**，curl_cffi CertificateVerifyError | curl_cffi |
| AnyKnew.com | 精细化分类热榜，历史榜单 | — | ❌ **TLS连接错误**，curl_cffi SSLError | curl_cffi |

**推荐替代方案（tophub被拦截后的科技垂直补充）：**
- `opencli 36kr hot -f json` — 36氪热榜，科技创业/商业
- `opencli hackernews top -f json` — Hacker News英文热榜
- `opencli ithome hot` — IT之家，数码/消费电子

**结论（已修订）：热点刀锋标准配置 = 知乎 + 微博 + Buzzing.cc（海外信息差）+ 36氪/HN（科技垂直）。** 四源覆盖国内大众舆论 + 海外信息差 + 科技垂直，已足够支撑每日选题。

### 写作限制

**交互模式：**
1. 必须人工确认话题：不自动写，必须等用户确认后再进入写作
2. 不一次输出全部5篇：逐篇输出，用户确认一篇再写下一篇，便于调整方向
3. 每篇必须过三宗罪自检
4. 不写娱乐/饭圈话题

**定时任务模式（无限制，全自动）：**
1. 不等待用户确认，直接用适配性最高的5个话题
2. 一次性完成全部5篇七步，不拆分步骤输出
3. 每篇必须过三宗罪自检
4. 不写娱乐/饭圈话题

### 质量控制原则

```
不求快，求稳。
不求多，求准。
不求全，求狠。
```

### ⚠️ 陷阱：cronjob prompt 不继承 skill 的默认行为

**症状：** 定时任务每次都在"等待用户确认话题"环节卡住，无法自动产出微头条。

**根因：** cronjob prompt 是一个独立存储的快照。当 skill 更新了"定时任务模式=跳过确认"后，cronjob prompt 里的旧内容不会被自动同步。每次修改 skill 后，必须同步修改 cronjob prompt（`hermes cronjob update`）和 `templates/cronjob-prompt.md`。

**检查方法：** 每次修改 skill 第五/六阶段后，执行 `hermes cronjob list` 确认任务 prompt 与 skill 行为一致。

**正确做法：** 修改 skill 的定时任务行为时，必须同时更新：
1. `templates/cronjob-prompt.md`（模板文件）
2. 当前运行的 cronjob 本身（`hermes cronjob update --job-id <id> --prompt "..."`）

---

## 十、故障排查

### opencli 命令返回空

```bash
# 检查扩展连接
opencli doctor

# 检查 Chrome 是否运行
ps aux | grep chrome

# 重启 Daemon
opencli daemon stop && opencli daemon start

# 检查端口占用
curl localhost:19825/status
```

### 知乎/微博返回 HTML 而非 JSON

```bash
# 清除缓存，重试
opencli zhihu hot -f json --no-cache

# 检查是否为反爬拦截
curl -I "https://www.zhihu.com/api/v4/news/ranking"
```

### 热榜数据过期或抓取失败

```bash
# 指定平台特定端点
opencli zhihu hot --limit 20 -f json

# 知乎热榜备用方案（当opencli zhihu hot失败时）
# 方案1：使用curl_cffi直接抓取知乎热榜API
python3 -c "
from curl_cffi import requests
import json
resp = requests.get('https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10', impersonate='chrome', timeout=15)
if resp.status_code == 200:
    data = resp.json()
    for item in data.get('data', []):
        target = item.get('target', {})
        title = target.get('title', '')
        print(f'  - {title}')
else:
    print(f'  ❌ 知乎热榜API返回状态码：{resp.status_code}')
"

# 方案2：使用备用平台
opencli hackernews top --limit 10 -f json
opencli v2ex hot -f json
```

---

## 十一、定时任务模板

本 skill 支持创建 cronjob 定时执行。

**正确方式：**
定时任务的 prompt 应是**薄封装**，只包含执行要点和流程节点，不重复粘贴 skill 全文。Skill 内容由执行 Agent 在运行时通过 skill_view 读取。

```bash
# 创建定时任务
hermes cronjob create \
  --name "每日热点刀锋微头条" \
  --skill hotspot-blade \
  --prompt "$(cat ~/.hermes/skills/productivity/hotspot-blade/templates/cronjob-prompt.md)" \
  --schedule "30 9 * * *" \
  --deliver "telegram:6327421932"
```

**参考模板：**
`templates/cronjob-prompt.md` — 薄封装版定时任务 prompt，供 cronjob 创建时引用。

---

## 十二、相关Skill

| Skill | 关系 | 用途 |
|-------|------|------|
| `opencli-tool` | 依赖 | 平台热榜抓取 |
| `toutiao-viral-writing` | 依赖 | 爆款微头条写作 |
| `反差互怼式写作模板` | 参考 | 通用议题写作方法论 |
| `article-polish-master` | 可选 | 去AI味终稿润色 |

---

## 十二、执行检查清单

### 定时任务模式

```
□ date 确认当天日期
□ opencli doctor 显示全部 OK
□ 知乎热榜成功返回数据
□ 微博热搜成功返回数据
□ 候选话题已按九边适配性排序（多样性规则已应用）
□ 自动选择前5个话题（无需等待确认）
□ 每篇都经过三宗罪自检
□ 5篇终稿已存档到 Wiki
□ Telegram 推送已发送（执行报告 + 5篇全文）
```

### 交互模式

```
□ opencli doctor 显示全部 OK
□ 知乎热榜成功返回数据
□ 微博热搜成功返回数据
□ 候选话题已按九边适配性排序（多样性规则已应用）
□ 用户已确认最终5个话题
□ 每篇都经过三宗罪自检
□ 工作日志已存档到 Wiki
□ 用户已验收所有5篇微头条
```
