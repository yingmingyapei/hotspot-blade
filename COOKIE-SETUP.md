# Cookie 配置说明

热点刀锋 v3.5 使用 curl + Cookie + Python 直接调用各平台 API，需要配置 Cookie 文件。

## Cookie 文件位置

```
~/.hermes/cookies/hotlist-cookies.json
```

## 文件格式

```json
{
  "zhihu": "z_c0=...; _xsrf=...; d_c0=...; ...",
  "bilibili": "SESSDATA=...; bili_jct=...; DedeUserID=...",
  "weibo": "SUB=...; SUBP=...; ...",
  "updated": "2026-06-09"
}
```

## 如何获取 Cookie

1. 在 Chrome 中登录目标网站
2. 按 F12 打开开发者工具
3. 切换到 Application 标签
4. 左侧 Storage 下展开 Cookies
5. 点击目标域名
6. 复制所有 Cookie 的 name=value，用分号连接

## 各平台关键 Cookie

### 知乎（有效期约5个月）
- `z_c0` — 登录凭证（最核心）
- `_xsrf` — CSRF 防护令牌
- `_zse_ck` — 反爬加密 Cookie
- `d_c0` — 设备标识符

### B站（有效期约6个月）
- `SESSDATA` — 登录凭证（最核心）
- `bili_jct` — CSRF 防护令牌
- `DedeUserID` — 用户 UID

### 微博
- `SUB` — 登录凭证
- `SUBP` — 子会话
- `WBPSESS` — 会话 Cookie

## Cookie 失效场景

- **主动退出登录** → Cookie 立即失效（服务器端注销）
- **直接关浏览器** → Cookie 仍然有效
- **Cookie 到期** → 需要重新获取

## 安全提示

⚠️ Cookie 文件包含登录凭证，不要提交到 Git 仓库
⚠️ 不要分享给他人
⚠️ 定期检查 Cookie 是否过期
