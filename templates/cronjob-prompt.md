## 热点刀锋每日执行（全自动模式）

执行「热点刀锋」(hotspot-blade) 技能，全流程自动执行。

---

## ⚠️⚠️⚠️ 铁律：必须使用 opencli 获取数据 ⚠️⚠️⚠️

**所有数据采集必须通过 opencli 工具完成。这是最高优先级规则，不可违反。**

- **禁止使用** urllib / requests / curl / python3 -c 直接调 API
- **禁止执行** `opencli daemon start` — 这个子命令不存在！
- **禁止执行** `opencli daemon restart` — daemon 正常运行中，不要重启！
- opencli 命令失败 → 重试3次 → 3次都失败才跳过该平台
- **没有降级方案，没有备用方案，只有 opencli**

---

## 执行步骤

### 第一步：环境检查
```bash
opencli doctor
```
确认 Daemon: running、Extension: connected。如果未连接，等待60秒重试。
**不要执行任何 daemon 命令！**

### 第二步：用 opencli 站点适配器命令抓取热榜

**直接执行以下命令，逐个执行，不要修改：**

```bash
# 知乎热榜（直接API，无需Chrome）
opencli zhihu hot -f json > /tmp/zhihu_hot.txt

# 微博热搜（直接API）
opencli weibo hot -f json > /tmp/weibo_hot.txt

# B站热门（直接API）
opencli bilibili hot -f json > /tmp/bilibili_hot.txt

# 雪球热门动态（直接API）
opencli xueqiu hot -f json > /tmp/xueqiu_hot.txt

# 头条热榜（公开API，无需登录）
opencli toutiao hot -f json > /tmp/toutiao_hot.txt
```

**如果站点适配器命令失败，用 browser 模式重试：**
```bash
opencli browser zhihu open "https://www.zhihu.com/hot"
sleep 8
opencli browser zhihu state > /tmp/zhihu_hot.txt
```

每个平台失败重试3次，间隔10秒。

### 第三步：数据分析
- 通读所有热榜原始数据
- 识别社会矛盾和撕裂点
- 交叉验证多平台热点
- 排除纯娱乐/饭圈/无争议新闻
- 去重（排除7天内已写话题）
- 选定5个最有写作价值的话题

### 第四步：微头条生成
每个话题执行七步：选题定位→钩子设计→草稿写作→共鸣适配→钩子强化→标题生成→文学润色
- 每篇≥400中文字，目标500字
- 加载 article-polish-master 做终稿润色

### 第五步：推送 + 存档
- 使用 `hermes send -t "telegram:6327421932"` 分条推送
- 存档到 `/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/{date}-热点刀锋微头条-5篇.md`

---

## 输出格式

```
✅ 热点刀锋已完成（{日期}）

📊 数据采集：知乎XX条 + 微博XX条 + B站XX条 + 雪球XX条 + 头条XX条

📌 话题1：{标题}
---
{正文≥400字}
---

📌 话题2：{标题}
---
{正文≥400字}
---

...共5篇...
```
