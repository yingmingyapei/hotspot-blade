# SKILL.md 降级代码清理模式（2026-06-04）

## 问题

hotspot-blade 的 SKILL.md 中积累了 115+ 行 Python/urllib/curl_cffi 降级代码。虽然文件开头有铁律声明"不得使用"，但 Agent（尤其是弱模型）仍被诱导使用 Python 而非 opencli。

## 清理清单

| 类型 | 清理前 | 清理后 |
|------|--------|--------|
| python3 -c 代码块 | 21 处 | 0 |
| urllib 引用 | 47 处 | 0 |
| 降级/备用方案 | 38 处 | 0 |
| curl_cffi | 29 处 | 0 |
| 文件大小 | 88KB (3433行) | 50KB |

## 清理步骤

### 1. 统计问题代码

```bash
grep -c "python3 -c\|urllib\|curl_cffi\|降级.*方案\|备用.*方案" SKILL.md
```

### 2. 用 Python 脚本批量清理

```python
import re

with open('SKILL.md') as f:
    content = f.read()

# 删除 python3 -c 代码块
content = re.sub(
    r'```bash\n#.*?python3 -c.*?```',
    '```bash\n# [已删除] 此处原有 Python 直接调 API 代码，按铁律已移除\n```',
    content, flags=re.DOTALL
)

# 删除 Python 代码块
content = re.sub(
    r'```python\n.*?```',
    '```python\n# [已删除] 此处原有 Python 直接调 API 代码，按铁律已移除\n```',
    content, flags=re.DOTALL
)

# 替换降级策略描述
content = re.sub(
    r'\*\*降级策略\*\*：.*?(?=\n---|\n## |\n\*\*[^降])',
    '**降级策略**：无。只用目标工具，失败则跳过该平台。\n',
    content, flags=re.DOTALL
)

# 逐行清理残留
lines = content.split('\n')
cleaned = []
for line in lines:
    lower = line.lower()
    if any(kw in lower for kw in ['python3 -c', 'urllib', 'curl_cffi']):
        if not any(kw in line for kw in ['禁止', '铁律', '已删除', '不得', '绝不能']):
            cleaned.append(f'<!-- [已清理] 原内容涉及 Python 直接调 API -->')
            continue
    cleaned.append(line)

with open('SKILL.md', 'w') as f:
    f.write('\n'.join(cleaned))
```

### 3. 验证

```bash
# 期望：0 残留
grep -n "python3 -c\|urllib\|curl_cffi" SKILL.md | \
  grep -v "禁止\|铁律\|已删除\|不得\|绝不能\|已清理" | wc -l
```

### 4. 同步到 GitHub

```bash
cd ~/hotspot-blade
cp ~/.hermes/skills/productivity/hotspot-blade/SKILL.md ./SKILL.md
git add -A && git commit -m "fix: 清理降级代码" && git push
```

## 额外步骤：检查矛盾描述

清理代码后，还需要搜索矛盾描述：

```bash
grep -n "降级到\|无需 opencli\|Python 直连\|不用 opencli" SKILL.md | \
  grep -v "禁止\|不要\|不降级\|不使用"
```

这些描述会直接和铁律矛盾，Agent 看到后会认为"可以用 Python"。必须改为一致的描述。

## 关键教训

1. **铁律不能只写声明** — 必须物理删除诱惑代码
2. **"历史参考"对弱模型无效** — 模型看到代码就会用
3. **清理后文件反而更好** — 从 88KB 精简到 50KB，更聚焦
4. **删除量可能很大** — 这次删了 1421 行，但都是噪音
5. **还要检查矛盾描述** — 代码删完了但描述说"用 Python 直连"，一样会诱导 Agent
