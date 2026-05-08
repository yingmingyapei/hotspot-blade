# zhīhū API登录态要求 — Pitfall记录

> 记录zhīhū热榜API的登录态要求和解决方案

## 问题描述

`opencli zhihu hot` 命令需要Chrome浏览器中zhīhū账号的登录状态。在以下环境中会失败：
- 定时任务环境（无Chrome登录态）
- headless环境
- Chrome未登录zhīhū

## 症状

```
# 未登录时
$ opencli zhihu hot -f json --limit 5
[返回401 Unauthorized或空数据]

# 已登录时
$ opencli zhihu hot -f json --limit 5
[正常返回热榜数据]
```

## 验证方法

```bash
# 1. 检查opencli状态
opencli doctor

# 2. 测试zhīhū热榜
opencli zhihu hot -f json --limit 5

# 3. 如果失败，检查Chrome是否登录zhīhū
# 在Chrome中访问 https://www.zhihu.com/hot 确认登录状态
```

## 解决方案

### 方案1：手动登录（交互模式）
1. 运行 `opencli browser open "https://www.zhihu.com/hot"`
2. 在Chrome中手动登录zhīhū账号
3. 登录后重新测试 `opencli zhihu hot -f json`

### 方案2：curl_cffi备用方案
```python
from curl_cffi import requests
import json

resp = requests.get(
    'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10',
    impersonate='chrome',
    timeout=15
)
if resp.status_code == 200:
    data = resp.json()
    for item in data.get('data', []):
        target = item.get('target', {})
        title = target.get('title', '')
        print(f'  - {title}')
else:
    print(f'API返回状态码：{resp.status_code}')
```

### 方案3：使用替代数据源
```bash
# 使用v2ex热榜替代
opencli v2ex hot -f json --limit 10
```

## 影响范围

- **受影响**：`opencli zhihu hot` 命令
- **不受影响**：`opencli weibo hot`、`opencli 36kr hot`、`opencli v2ex hot`

## 建议

1. **定时任务环境**：优先使用备用方案（curl_cffi）或替代数据源
2. **交互模式**：先手动登录，再使用opencli命令
3. **故障处理**：zhīhū热榜失败时，自动切换到v2ex热榜

## 相关文件

- `scripts/data_source_health_check.py`：数据源健康检查脚本
- `references/hotlist-sources-audit-2026-05-07.md`：数据源审计报告
