---
name: skill-library-inconsistency
title: 技能库不一致记录
description: 记录技能列表中可见但不可访问的技能，供后续排查
---

# 技能库不一致记录

## 问题描述

`skills_list` 返回的技能列表中，部分技能无法通过 `skill_view` 访问。

## 已确认案例

| 技能名称 | skills_list | skill_view | 状态 |
|----------|-------------|------------|------|
| `反差互怼式写作模板` | ✅ 可见 | ❌ 返回 "not found" | 不一致 |
| `toutiao-viral-writing` | ✅ 可见 | ✅ 正常加载 | 正常 |

## 可能原因

1. 技能文件存在于 `skills_list` 的索引中，但实际 `SKILL.md` 文件缺失或路径错误
2. 技能目录权限问题
3. 技能注册表与文件系统不同步

## 排查命令

```bash
# 检查技能目录是否存在
ls -la ~/.hermes/skills/反差互怼式写作模板/

# 检查SKILL.md是否存在
cat ~/.hermes/skills/反差互怼式写作模板/SKILL.md

# 检查技能注册表
hermes skills list --json | jq '.[] | select(.name | contains("反差"))'
```

## 影响

- 用户说"按反差互怼式写作模板写"时，技能无法加载
- 当前 workaround：`toutiao-viral-writing` 已内置反差互怼式写作内容，可替代使用

## 备注

`反差互怼式写作模板` 的内容实际上已整合进 `toutiao-viral-writing` 技能（见其 SKILL.md 中的"反差互怼式写作模板"引用），所以暂时不影响使用。但技能库不一致问题需要修复。