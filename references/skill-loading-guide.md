# 热点刀锋技能加载指南（2026-07-07）

## 问题背景
热点刀锋（hotspot-blade）是一个独立 GitHub 仓库（`~/hotspot-blade`），其子技能（toutiao-viral-writing、russell-flip-arsenal 等）存放在仓库内的 `skills/` 和 `references/` 目录，**不在** `~/.hermes/skills/` 中。

## 加载方式

### 方式1：skill_view（推荐）
```
skill_view(name='toutiao-viral-writing')
```
注意：子技能需要先安装到 `~/.hermes/skills/` 才能被 skill_view 识别。

### 方式2：直接读取文件
```
read_file(path='/home/yingming/hotspot-blade/skills/toutiao-viral-writing/SKILL.md')
```

### 方式3：复制安装
```bash
cp -r ~/hotspot-blade/skills/* ~/.hermes/skills/
```

## Pitfall
- 不要在 hotspot-blade 仓库外创建同名技能，会导致版本不一致
- 修改 hotspot-blade 中的技能后，需要同步到 `~/.hermes/skills/`
- git push 前记得同步：`cp -r ~/hotspot-blade/skills/* ~/.hermes/skills/` && `cd ~/hotspot-blade && git add . && git commit -m "sync" && git push`