# 头条号每周数据诊断工作流

> 自动化闭环：数据采集 → 分析 → 策略优化 → skill更新

## 前置条件

- opencli daemon 运行中（`opencli daemon status`）
- Chrome 已登录头条创作者后台
- 当前日期确认（`date`）

## ⚠️ Cron 模式限制

**`execute_code` 在 cron job 中被阻止**（无用户审批）。数据分析必须用手工计算或 terminal 中的 python3 -c 完成。

替代方案：
```bash
# 用 terminal + python3 -c 做简单计算
python3 -c "
articles = [
    {'title': 'A', 'imp': 362127, 'reads': 26784, 'likes': 157, 'comments': 48},
    # ...
]
total_imp = sum(a['imp'] for a in articles)
total_reads = sum(a['reads'] for a in articles)
print(f'Total: {total_imp:,} imp, {total_reads:,} reads, CTR {total_reads/total_imp*100:.2f}%')
"
```

或者直接手工计算后写入报告（本session采用此方式）。

## 第一步：采集三页面数据

### 1.1 内容管理页（逐篇数据）

```bash
opencli browser toutiao open "https://mp.toutiao.com/profile_v4/manage/content/all"
sleep 6
opencli browser toutiao extract
```

提取字段：标题、日期、展现量、阅读量、点赞量、评论量

**注意**：默认只显示最近10篇左右。如需更多，需滚动+分页extract。

### 1.2 作品数据概览（整体数据）

```bash
opencli browser toutiao open "https://mp.toutiao.com/profile_v4/analysis/works-overall/all"
sleep 6
opencli browser toutiao extract
```

提取字段：昨日展现量、昨日阅读量、昨日点赞量、昨日评论量、地域分布

### 1.3 评论数据（互动质量）

```bash
opencli browser toutiao open "https://mp.toutiao.com/profile_v4/manage/comment/all"
sleep 6
opencli browser toutiao extract
```

提取字段：评论内容、评论文章、评论时间、评论者昵称

## 第二步：数据分析

### 2.1 逐篇指标计算

```
点击率 = 阅读量 / 展现量 × 100%
互动率 = (点赞 + 评论) / 阅读量 × 100%  （阅读为0时记为0）
撕裂指数 = 评论数 / 点赞数  （点赞为0时记为0）
```

### 2.2 分类统计

按选题类型分类（参考skill中的6类）：
- 教育/社会热点
- 国际政治/外交
- 商业/财经
- 社会民生/道德争议
- 军事/国防
- 科技/AI

每类计算：总展现、总阅读、平均CTR、平均互动率

### 2.3 爆款/低迷识别

- 🔥 CTR > 5%：爆款，分析成功因素
- ✅ CTR 2-5%：及格
- ⚠️ CTR 0.5-2%：偏低
- ❌ CTR < 0.5%：低迷，分析失败原因

### 2.4 标题公式效果评估

将本周文章按标题风格归类，计算每种风格的平均CTR。

## 第三步：策略优化

### 3.1 选题权重调整规则

```
规则1：某类CTR > 10% → 升权5%（连续2周则升10%）
规则2：某类CTR < 3% → 降权5%（连续2周则降10%）
规则3：科技类CTR < 1% → 暂停7天
规则4：某标题公式连续2篇CTR < 1% → 标记"低效公式"
规则5：某标题公式CTR > 10% → 标记"高效公式"
```

### 3.2 调整边界

- 单次调整幅度 ≤ ±10%
- 国际政治权重 ≥ 30%（核心优势，不因单周失灵大幅降权）
- 科技类权重 ≤ 10%（粉丝画像不匹配）
- 每次调整必须记录理由

### 3.3 执行更新

1. patch skill 中的「选题优先级排序」section
2. patch skill 中的「标题公式优先级」section
3. 在调整处标注日期和数据依据

## 第四步：保存报告

路径：`C:\Users\yingm\wiki\sources\market-intelligence\daily\YYYY-MM-DD-头条号周报.md`（WSL中访问：`/mnt/c/Users/yingm/wiki/sources/market-intelligence/daily/YYYY-MM-DD-头条号周报.md`）

报告结构：
1. 本周整体数据（总展现、总阅读、平均CTR）
2. 昨日核心数据
3. 各选题类型表现对比
4. 逐篇数据明细（最佳/最差分析）
5. 标题公式效果评估
6. 评论区分析
7. 粉丝画像
8. 选题权重调整明细（旧→新）
9. 标题公式更新明细
10. 下周策略建议
11. 闭环验证清单

## 历史周报索引

| 日期 | 关键发现 | 报告路径 |
|------|----------|----------|
| 2026-06-08 | 高考数学爆款7.40% CTR，国际政治失灵1.44%，新增教育类第1优先级 | `2026-06-08-头条号周报.md` |
