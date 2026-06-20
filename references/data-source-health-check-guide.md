# 数据源健康检查使用说明

> 用于热点刀锋定时任务执行前的数据源健康检查。每次执行前必须运行此脚本。

## 使用方法

```bash
cd ~/.hermes/skills/productivity/hotspot-blade/scripts
python3 data_source_health_check.py
```

## 故障自动切换策略

| 数据源 | 主要命令 | 备用方案1 | 备用方案2 | 故障处理 |
|--------|----------|-----------|-----------|----------|
| 知乎热榜 | `opencli zhihu hot` | curl_cffi直接抓取API | 使用v2ex热榜替代 | 记录故障，继续执行 |
| 微博热搜 | `opencli weibo hot` | 无备用 | 使用36氪热榜替代 | 记录故障，继续执行 |
| Buzzing.cc | curl_cffi抓取 | browser extract | 使用Hacker News替代 | 记录故障，继续执行 |
| 36氪热榜 | `opencli 36kr hot` | 无备用 | 使用v2ex热榜替代 | 记录故障，继续执行 |
| v2ex热榜 | `opencli v2ex hot` | 无备用 | 使用36氪热榜替代 | 记录故障，继续执行 |

## 退出码

- `0`：检查通过，可以执行
- `1`：检查失败，可用数据源不足，建议等待
