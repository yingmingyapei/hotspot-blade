#!/usr/bin/env python3
"""
在SKILL.md中添加数据源健康检查脚本的引用
"""
import re

SKILL_PATH = '/home/yingming/.hermes/skills/productivity/hotspot-blade/SKILL.md'

with open(SKILL_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '''### 数据源健康检查机制

每次执行前必须进行数据源健康检查：'''

new_text = '''### 数据源健康检查机制

每次执行前必须进行数据源健康检查。

**快速检查**：运行 `scripts/data_source_health_check.py` 脚本
```bash
python3 ~/.hermes/skills/productivity/hotspot-blade/scripts/data_source_health_check.py
```

**手动检查**：'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open(SKILL_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 脚本引用添加成功")
else:
    print("⚠️ 未找到匹配文本，跳过修改")
