## 热点刀锋每日执行（全自动模式）

执行「热点刀锋」(hotspot-blade) 技能，**全流程自动执行，无需等待用户确认，选题由执行 Agent 自动确定**。

**⚠️ 核心原则：不限时，不限Token。每个阶段充分执行，不赶进度，不压缩步骤。宁可慢，不可糙。**

**⚠️⚠️⚠️ 最关键的一条：你的最终回复就是用户在 Telegram 上看到的全部内容。**
**如果只输出摘要，用户就只收到摘要。必须在最终回复中包含 5 篇微头条全文。**
**不要把正文只写入 Wiki 而不在最终回复中输出。⚠️⚠️⚠️**

**⚠️ 重要：输出格式要求**
- **只输出以下内容**，不要输出完整的技能文档、执行日志、检查清单等
- 完整执行报告已保存到本地文件，无需在输出中重复

**⚠️ 关键陷阱：`deliver: "origin"` 推送的是 Agent 的最终回复**

| 交付模式 | 推送内容 | 注意事项 |
|----------|----------|----------|
| ~~`deliver: "origin"`~~ | ~~Agent 的**最终回复**~~ | ⚠️ 备用：最终回复必须包含 5 篇微头条全文，否则用户收不到正文 |
| `deliver: "local"` | **Agent 自动推送** | ✅ 推荐：Agent 使用 `hermes send` CLI 分条推送，每篇独立一条消息（详见 `references/hermes-send-delivery-pattern.md`） |

**推荐配置（deliver: "local"）：**
```bash
hermes cronjob update <job-id> --deliver "local"
```

当 deliver="local" 时，Agent 自动执行：
1. 将每篇微头条写入临时文件（`/tmp/hotspot_N.txt`）
2. 使用 `hermes send -t "telegram:6327421932" -f /tmp/hotspot_N.txt` 逐条推送
3. 最后推送一条汇总消息

**⚠️ 重要：`send_message` 工具不存在！** 不要尝试调用 `send_message(target="telegram:...", message="...")` — 该工具不在可用工具集中。必须使用 `hermes send` CLI 命令。

---

## 执行流程总览

```
第一阶段：环境就绪检查
第二阶段：数据采集（5个第一手平台，不限时，不降级）
第三阶段：数据完整性校验（不通过则停止）
第四阶段：数据分析（我来推理判断，不是公式打分）
第五阶段：微头条生成（仅在数据充分且分析完成后执行）
第六阶段：推送 + 存档
```

---

## ⚠️ 铁律：必须使用 opencli 获取数据

**所有数据采集必须通过 opencli 工具完成，禁止降级到 Python 直接调用 API。**

- 如果 opencli 命令失败，重试3次
- 如果3次都失败，报告该平台采集失败，跳过该平台
- **绝不能用 `urllib`/`requests`/`curl` 直接调 API 作为替代方案**

---

## 第一阶段：环境就绪检查

**执行任何数据采集前，必须确认 opencli browser 环境就绪。**

```bash
# 等待 Extension 连接就绪，最多等 60 秒
for i in $(seq 1 12); do
  if opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
    echo "✅ Extension 已连接"
    break
  fi
  echo "等待 Extension 连接... ($((i*5))s)"
  sleep 5
done

# 最终确认
opencli doctor
```

**如果 60 秒后仍未连接：**
- 报告「Chrome/Extension 未就绪，数据采集无法执行」
- **停止任务，不降级到百度搜索**

---

## 第二阶段：数据采集（5个第一手平台）

**核心原则：只抓第一手数据，不经过任何中间算法加工。每个平台直接访问热榜页面，原始数据原样保存。**

**不限时，不限Token，不降级。每个平台充分抓取，失败重试3次，3次都失败才跳过该平台。不赶进度。**

```bash
# 平台1：知乎热榜
for i in 1 2 3; do
  opencli browser zhihu open "https://www.zhihu.com/hot" && sleep 5 && opencli browser zhihu state > /tmp/zhihu_hot_raw.txt && break
  echo "知乎热榜第${i}次失败，重试..."
  sleep 10
done

# 平台2：微博热搜
for i in 1 2 3; do
  opencli browser weibo open "https://s.weibo.com/top/summary" && sleep 5 && opencli browser weibo state > /tmp/weibo_hot_raw.txt && break
  echo "微博热搜第${i}次失败，重试..."
  sleep 10
done

# 平台3：B站热榜
for i in 1 2 3; do
  opencli browser bilibili open "https://www.bilibili.com/v/popular/rank/all" && sleep 5 && opencli browser bilibili state > /tmp/bilibili_hot_raw.txt && break
  echo "B站热榜第${i}次失败，重试..."
  sleep 10
done

# 平台4：雪球热帖（URL失效，用首页+滚动替代）
for i in 1 2 3; do
  opencli browser xueqiu open "https://xueqiu.com/" && sleep 15 && opencli browser xueqiu scroll down && sleep 3 && opencli browser xueqiu scroll down && sleep 3 && opencli browser xueqiu state > /tmp/xueqiu_hot_raw.txt && break
  echo "雪球热帖第${i}次失败，重试..."
  sleep 10
done

# 平台5：头条热榜（URL失效，用首页替代，需15秒JS渲染）
for i in 1 2 3; do
  opencli browser toutiao open "https://www.toutiao.com/" && sleep 15 && opencli browser toutiao state > /tmp/toutiao_hot_raw.txt && break
  echo "头条热榜第${i}次失败，重试..."
  sleep 10
done

# 海外补充：Buzzing.cc（不计入5个国内平台）
curl -s -L --max-time 15 \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  'https://buzzing.cc' -o /tmp/buzzing_cc.html
```

**采集完成后，将所有原始数据汇总为一个 JSON 文件，存入 samples 目录。**

---

## 第三阶段：数据完整性校验

**在进入数据分析前，必须校验数据是否充分。不通过则停止任务。**

校验标准：
- 至少 3 个平台的原始数据文件存在且非空
- 每个文件至少包含 10 条有效热榜条目
- 数据必须是今天的（通过文件内容或时间戳判断）

**如果校验不通过：**
- 报告「数据采集不充分：仅 X/Y 个平台成功，需要至少 3 个平台」
- 列出每个平台的成功/失败状态和原因
- **停止任务，不进入微头条生成阶段**

---

## 第四阶段：数据分析（核心）

**⚠️ 这是整个流程最关键的部分。不是公式打分，是我用推理能力做判断。不限时，不限Token，充分分析每一条热榜数据。**

### 分析步骤

**第一步：通读所有原始数据**
- 逐条阅读5个平台的全部热榜内容
- 不遗漏，不跳过，先看全貌

**第二步：识别社会矛盾和撕裂点**
- 对每条热榜，问自己：这个话题背后藏着什么社会矛盾？
- 哪些话题天然有两派对立？（不是所有热门话题都适合写）
- 哪些话题能嫁接到真实议题上？

**第三步：交叉验证**
- 同一个话题在多个平台同时热？→ 真正的热点，优先选
- 只在一个平台热？→ 可能是平台算法推的，谨慎
- 不同平台对同一话题的讨论角度有什么差异？

**第四步：排除噪音**
- 纯娱乐/饭圈/综艺/剧集 → 排除
- 无争议的事实性新闻（地震/天气/赛事结果）→ 排除
- 个人感悟/生活碎片 → 排除
- 已过时效的话题（>3天）→ 排除

**第五步：去重检查**
- 读取历史话题库（`/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/hotspot-blade-history.json`）
- 检查过去14天已写话题，排除7天内完全相同的话题
- 同一事件不同角度需有重大新进展才能复用

**第六步：深度搜索素材（选定角度后必做）**
- 找到话题的爆点角度后，用 finance_news / web_search 搜索相关素材
- 找到 3-5 个具体事实/数据/案例作为弹药
- 没有弹药的话题宁可放弃

**第七步：选定5个话题**
- 从筛选后的候选中，选出5个最有写作价值的话题
- 每个话题说明：为什么选它、背后的社会矛盾是什么、预估的两派是谁
- 优先选择：国际政治 > 社会民生 > 军事 > 商业 > 科技（需降维）

### 分析输出格式

```
📊 数据分析报告

采集情况：
- 知乎热榜：XX条 ✅
- 微博热搜：XX条 ✅
- B站热榜：XX条 ✅
- 雪球热帖：XX条 ✅/❌（原因）
- 头条热榜：XX条 ✅/❌（原因）

候选话题（按潜力排序）：
1. {话题}（来源：XX平台 #X）
   - 社会矛盾：...
   - 预估两派：A派 vs B派
   - 选择理由：...

2. ...

最终选定5个话题：
1. ...
2. ...
3. ...
4. ...
5. ...
```

---

## 第五阶段：微头条生成

**仅在第四阶段数据分析完成且选定话题后执行。不限时，不限Token，每篇充分写作，不赶进度。**

对每个选定话题，依次执行七步，**一次性完成全部七步再输出终稿**。

### 第一步：选题定位（v3.1升级：真实议题嫁接）
- **🔥 先做议题嫁接**：拿到热榜话题后，先问"这个话题背后，藏着哪个一直存在的社会矛盾？"（参考 `references/real-tension-topics.md`）
- **5问快判**：涉及哪两个群体？利益是否冲突？人数都够多吗？冲突是一直存在的吗？能一句话同时激怒一派和打动另一派吗？
- 如果5问都通过 → 选题合格，进入写作
- 如果5问有1个答不上 → 换话题（共识型内容，评论区打不起来）
- 自动匹配话题类型和写作风格：
  - 社会/民生/职场/就业 → 九边五层密码为主
  - 政策/国际/科技/两岸 → 反差互怼三人节奏组为主
  - 市井/人情/江湖/生活 → 郭德纲风格为主

### 第二步：钩子设计
- 根据话题类型自动选择：反差互怼Hook / 九边Hook / 郭德纲Hook
- 开场3秒必须破防

### 第三步：草稿写作
- **🔥 写作核心原则**：用笃定的语气说一个有争议的观点，用数据和案例支撑你的判断，不留余地
- 开场(前20%) → 中段(40-70%) → 结尾(最后10%)
- 每篇≥400中文字，目标500字

### 第四步：共鸣适配
- 替换专业词为普通人感知词
- 检查是否让读者觉得"这篇文章就是在写我"

### 第五步：钩子强化检查
- 三层情绪检查：开头破防感、中段清醒感、结尾定音锤

### 第六步：爆款标题生成
- 6种标题公式各生成1个，自动选最高分
- 每篇必须包含标题

### 第七步：文学润色（必做，不可跳过）
- 加载 `article-polish-master` 技能做终稿润色
- 去AI味、句式变阵、情感注入、自然过渡

---

## ⚠️ 禁用句式（出现任何一句即判不合格）

| 禁用句式 | 替代方向 |
|----------|----------|
| 归了包堆 | 直接陈述结论 |
| 说真的，并没有 | 用具体事实反驳 |
| 说白了 | 直接说结论 |
| 说句不好听的 | 直接说 |
| 更扎心的是 | "但问题在于""可现实是" |
| 更关键的是 | "值得注意的是""真正的问题是" |
| 你有没有过这种感觉 | 换成具体场景描写 |
| 其实不是…而是… | 直接用判断句 |
| 我以前一直觉得…后来才明白… | 不用第一人称回忆套路 |
| 后来慢慢想明白 | 同上 |
| 不是你不够好，而是… | 禁用鸡汤句式 |
| 这不叫X，这叫Y | "这就是…" |
| 你以为X？其实没那么简单 | 用具体反差数据代替反问 |
| 看透XX的底层逻辑 | "底层逻辑"是互联网黑话 |
| XX越想越累 | 禁用情绪诱导套路 |

**核心原则：每篇微头条的句式必须是全新的，5篇之间不能有重复的套路句式。**

---

## ⚠️ 字数硬性要求

**每篇微头条正文（不含标题行、标签行、分隔线）必须达到 500 个中文汉字左右，底线 400 字，上限 600 字。**

> ⚠️ **Cron模式注意**：`execute_code` 工具在 cron 模式下被系统拦截。所有 Python 验证脚本必须通过 `terminal` + `python3 -c` 执行。

---

## 第六阶段：推送 + 存档

### 推送
- 使用 `hermes send -t "telegram:6327421932"` 分条推送
- 第1条：执行摘要
- 第2-6条：5篇微头条正文

### Wiki 存档
```
/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md
```

### 正文完整度验证
```bash
python3 -c "
import re
files = {1: '/tmp/hotspot_1.txt', 2: '/tmp/hotspot_2.txt', 3: '/tmp/hotspot_3.txt', 4: '/tmp/hotspot_4.txt', 5: '/tmp/hotspot_5.txt'}
banned = ['归了包堆', '说真的，并没有', '说白了', '说句不好听的', '更扎心的是', '更关键的是', '你有没有过这种感觉', '底层逻辑', '越想越累']
for idx, path in sorted(files.items()):
    with open(path) as f:
        content = f.read()
    chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
    found = [b for b in banned if b in content]
    status = '✅' if chinese >= 400 and not found else '❌'
    print(f'{idx}. {chinese}字 {status}')
    if found: print(f'   禁用词: {found}')
    if chinese < 400: raise SystemExit(f'FAIL: 第{idx}篇不足400字')
    if found: raise SystemExit(f'FAIL: 第{idx}篇含禁用词')
print('ALL PASS')
"
```

---

## 📤 最终输出格式

```
✅ 热点刀锋已完成（{日期}）

📊 数据采集：知乎XX条 + 微博XX条 + B站XX条 + 雪球XX条 + 头条XX条
📊 数据分析：从XX条热榜中筛选出5个有撕裂潜力的话题

📌 话题：{话题1标题}（来源：XX平台 #X）
---
{微头条1正文，≥400字}
---

📌 话题：{话题2标题}（来源：XX平台 #X）
---
{微头条2正文，≥400字}
---

...共5篇...
```

---

## 参考

完整写作方法论和选题规则见 `hotspot-blade` skill，不在此重复。

---

## ⚠️ 铁律：不限时，不限Token

**整个热点刀锋执行过程中：**
- 数据采集：不限时，每个平台充分抓取，等页面完全加载
- 数据分析：不限Token，逐条阅读所有热榜原始数据，充分推理
- 微头条写作：不限时，每篇充分写作，不赶进度，不压缩步骤
- **宁可慢，不可糙。宁可多花Token，不可偷工减料。**
- **如果某个阶段需要更多时间或Token才能做好，就多花，不要跳过。**
