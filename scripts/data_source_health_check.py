# 数据源稳定性检查脚本

> 用于热点刀锋定时任务执行前的数据源健康检查。每次执行前必须运行此脚本。

## 使用方法

```bash
cd ~/.hermes/skills/productivity/hotspot-blade/scripts
python3 data_source_health_check.py
```

## 脚本内容

```python
#!/usr/bin/env python3
"""
热点刀锋 - 数据源健康检查脚本
用于定时任务执行前检查所有数据源的可用性。
"""

import json
import subprocess
import sys
from datetime import datetime

def check_opencli_source(name, cmd, timeout=30):
    """检查opencli数据源"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if len(data) >= 3:
                    return {'status': 'ok', 'count': len(data), 'message': f'成功获取{len(data)}条数据'}
                else:
                    return {'status': 'warning', 'count': len(data), 'message': f'数据量不足：{len(data)}条'}
            except json.JSONDecodeError:
                return {'status': 'error', 'count': 0, 'message': '返回数据格式错误'}
        else:
            return {'status': 'error', 'count': 0, 'message': '命令执行失败'}
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'count': 0, 'message': f'命令超时({timeout}s)'}
    except Exception as e:
        return {'status': 'error', 'count': 0, 'message': f'错误：{str(e)}'}

def check_buzzing_cc():
    """检查Buzzing.cc数据源"""
    try:
        from curl_cffi import requests
        import re
        resp = requests.get('https://buzzing.cc', impersonate='chrome', timeout=15)
        titles = re.findall(r'>([^<]{20,200})<', resp.text)
        seen = set()
        exclude_patterns = [
            r'http[s]?://',
            r'\.buzzing\.cc$',
            r'www\.[a-z]+\.[a-z]+$',
            r'↑',
            r'HN\s*Points',
            r'^Show\s*HN:',
            r'^I\s+switched',
            r'^The\s+Old\s+Guard',
            r'^Buzzing\s*-',
            r'^用中文浏览',
            r'^本站并非官方网站',
            r'^最后更新于',
            r'^Twitter\s*@',
        ]
        for t in titles:
            t = t.strip()
            if t and t not in seen and len(t) > 15 and not t.startswith('http') and not t.startswith('//'):
                exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, t, re.IGNORECASE):
                        exclude = True
                        break
                if not exclude:
                    seen.add(t)
                    if len(seen) >= 5:
                        break
        if len(seen) >= 3:
            return {'status': 'ok', 'count': len(seen), 'message': f'成功提取{len(seen)}个标题'}
        else:
            return {'status': 'warning', 'count': len(seen), 'message': f'只提取到{len(seen)}个标题'}
    except Exception as e:
        return {'status': 'error', 'count': 0, 'message': f'错误：{str(e)}'}

def main():
    """主函数"""
    print(f'=== 热点刀锋数据源健康检查 ===')
    print(f'检查时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    # 检查opencli数据源
    opencli_sources = [
        ('知乎热榜', 'opencli zhihu hot -f json --limit 5'),
        ('微博热搜', 'opencli weibo hot -f json --limit 5'),
        ('36氪热榜', 'opencli 36kr hot -f json --limit 5'),
        ('v2ex热榜', 'opencli v2ex hot -f json --limit 5'),
    ]

    results = {}
    for name, cmd in opencli_sources:
        result = check_opencli_source(name, cmd)
        results[name] = result
        if result['status'] == 'ok':
            print(f'✅ {name}：{result["message"]}')
        elif result['status'] == 'warning':
            print(f'⚠️ {name}：{result["message"]}')
        elif result['status'] == 'timeout':
            print(f'⏰ {name}：{result["message"]}')
        else:
            print(f'❌ {name}：{result["message"]}')

    print()

    # 检查Buzzing.cc
    print('检查 Buzzing.cc...')
    buzzing_result = check_buzzing_cc()
    results['Buzzing.cc'] = buzzing_result
    if buzzing_result['status'] == 'ok':
        print(f'✅ Buzzing.cc：{buzzing_result["message"]}')
    elif buzzing_result['status'] == 'warning':
        print(f'⚠️ Buzzing.cc：{buzzing_result["message"]}')
    else:
        print(f'❌ Buzzing.cc：{buzzing_result["message"]}')

    print()

    # 统计结果
    ok_count = sum(1 for r in results.values() if r['status'] == 'ok')
    total_count = len(results)

    print(f'=== 检查结果 ===')
    print(f'正常数据源：{ok_count}/{total_count}')

    if ok_count < 3:
        print('❌ 警告：可用数据源不足3个，建议等待数据源恢复后再执行')
        sys.exit(1)
    elif ok_count < total_count:
        print('⚠️ 注意：部分数据源不可用，将使用备用方案')
        sys.exit(0)
    else:
        print('✅ 所有数据源正常，可以执行')
        sys.exit(0)

if __name__ == '__main__':
    main()
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
