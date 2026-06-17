# v3.5 部署与 Cookie 配置指南

> 更新日期：2026-06-09

## 部署步骤（从 GitHub 拉取 v3.5 更新）

```bash
# 1. 如果本地 SKILL.md 有改动，先 stash
cd ~/.hermes/skills/hotspot-blade
git stash
git pull origin main

# 2. 部署抓取脚本到 Hermes scripts 目录
cp ~/.hermes/skills/hotspot-blade/scripts/hotlist_scraper.py ~/.hermes/scripts/

# 3. 创建 Cookie 目录和空壳文件
mkdir -p ~/.hermes/cookies
# 如果 Cookie 文件不存在，创建空壳
```

## Cookie 配置

### 文件位置
`~/.hermes/cookies/hotlist-cookies.json`

### 格式
```json
{
  "zhihu": "z_c0=...; _xsrf=...; d_c0=...",
  "bilibili": "SESSDATA=...; bili_jct=...; DedeUserID=...",
  "weibo": "SUB=...; SUBP=...; WBPSESS=...; XSRF-TOKEN=...",
  "updated": "2026-06-09"
}
```

### 从 Chrome DevTools 提取 Cookie

用户通常从 Chrome DevTools → Application → Cookies 复制粘贴原始数据。需要提取关键字段：

**微博关键 Cookie：**
- `SUB` — 登录凭证（.weibo.com）
- `SUBP` — 子会话（.weibo.com）
- `WBPSESS` — 会话 Cookie（weibo.com）
- `XSRF-TOKEN` — CSRF 令牌（weibo.com）
- `ALF` — 过期时间戳（可选）
- `SCF` — 安全 Cookie（可选）

**知乎关键 Cookie：**
- `z_c0` — 登录凭证（最核心）
- `_xsrf` — CSRF 令牌
- `d_c0` — 设备标识

**B站关键 Cookie：**
- `SESSDATA` — 登录凭证（最核心）
- `bili_jct` — CSRF 令牌
- `DedeUserID` — 用户 UID

### 保存方式

用 `write_file` 写入 JSON，或用 Python 脚本：
```python
import json
data = {"zhihu": "", "bilibili": "", "weibo": "<extracted_cookie_string>", "updated": "2026-06-09"}
with open("/root/.hermes/cookies/hotlist-cookies.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### ⚠️ 已知陷阱：Shell heredoc 中的特殊字符

Cookie 值包含 `=`、`"`、`=` 等特殊字符，用 shell heredoc 写入时可能被截断或转义。**推荐用 Python 脚本写入**，不要用 `cat > file << 'EOF'`。

验证方法：
```bash
python3 -c "
import json
with open('/root/.hermes/cookies/hotlist-cookies.json') as f:
    d = json.load(f)
# 检查关键字段是否存在
for platform in ['zhihu', 'weibo', 'bilibili']:
    val = d.get(platform, '')
    print(f'{platform}: {len(val)} chars, empty={not val}')
"
```

## 定时任务同步

v3.5 更新后，必须通过 `cronjob update` 同步定时任务 prompt：
- 新 prompt 使用 `python3 ~/.hermes/scripts/hotlist_scraper.py` 替代 opencli
- 移除了 opencli 铁律相关指令
- 加载 skills: `hotspot-blade`, `article-polish-master`
