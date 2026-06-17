# Cookie 配置实战经验（2026-06-09）

## Cookie 文件位置

`~/.hermes/cookies/hotlist-cookies.json`

## Cookie 获取流程

1. 在 Chrome 中登录目标网站
2. F12 → Application → Cookies → 复制关键 Cookie
3. 用 Python 脚本写入 JSON（避免 shell heredoc 特殊字符问题）
4. 运行 `python3 ~/.hermes/scripts/hotlist_scraper.py --platform <name> --limit 3 --json` 验证

## 各平台关键 Cookie

### 知乎（有效期约5个月）
- `z_c0` — 登录凭证（最核心）
- `_xsrf` — CSRF 防护令牌
- `_zse_ck` — 反爬加密 Cookie（值很长，含 `/+=` 等特殊字符）
- `d_c0` — 设备标识符
- `q_c1` — 会话标识
- `SESSIONID` — 会话 ID

### 微博
- `SUB` — 登录凭证（最核心）
- `SUBP` — 子会话
- `WBPSESS` — 会话 Cookie
- `XSRF-TOKEN` — CSRF 令牌（同时需要在请求头中带 `X-XSRF-TOKEN`）
- `ALF` — 自动登录凭证
- `SCF` — 安全 Cookie

### B站（有效期约6个月）
- `SESSDATA` — 登录凭证（最核心，含 URL 编码 `%2C` `%2A`）
- `bili_jct` — CSRF 令牌
- `DedeUserID` — 用户 UID
- `DedeUserID__ckMd5` — UID 校验
- `buvid3` / `buvid4` — 设备标识

### 头条 / 百度
- 无需 Cookie，公开 API

## ⚠️ 坑：Shell heredoc 写入 Cookie 会损坏特殊字符

**症状**：用 `cat > file.json << 'EOF'` 写入含 `...`、`=`、`+`、`/` 的 Cookie 值后，值被截断或替换。

**根因**：heredoc 中的 `...` 可能被 bash 展开为 glob，`=` 在某些上下文被解释。

**正确做法**：用 Python 脚本写入：
```python
import json
data = {"zhihu": "...", "weibo": "...", "bilibili": "...", "updated": "2026-06-09"}
with open("/root/.hermes/cookies/hotlist-cookies.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**验证方法**：
```python
import json
with open("/root/.hermes/cookies/hotlist-cookies.json") as f:
    d = json.load(f)
# 检查关键字段是否存在
assert "z_c0=" in d["zhihu"]
assert "SESSDATA=" in d["bilibili"]
assert "SUB=" in d["weibo"]
```

## ⚠️ 坑：Cookie 过期排查

**症状**：脚本返回空数据或报错，但昨天还能用。

**排查步骤**：
1. `python3 ~/.hermes/scripts/hotlist_scraper.py --platform <name> --limit 1 --json`
2. 如果返回 `"error": "请求失败"` → Cookie 过期
3. 去 Chrome 重新登录 → 复制新 Cookie → 更新 JSON 文件

**各平台 Cookie 有效期**：
- 知乎 z_c0: ~5个月
- B站 SESSDATA: ~6个月
- 微博 SUB: ~1年
- 但**主动退出登录会立即失效**

## 部署 checklist

```
□ ~/.hermes/cookies/hotlist-cookies.json 存在且非空
□ 知乎 Cookie 包含 z_c0
□ 微博 Cookie 包含 SUB
□ B站 Cookie 包含 SESSDATA
□ 脚本 python3 ~/.hermes/scripts/hotlist_scraper.py 可执行
□ 5个平台全部返回 count > 0
□ 定时任务 prompt 中的脚本路径正确
```
