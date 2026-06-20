# opencli browser 打开热榜网站（2026-06-09）

## 用途
在 Chrome 中打开热榜网站供人工浏览/登录，**不用于数据采集**（数据采集用 curl+Cookie）。

## 命令格式
```bash
opencli browser <session-name> open <url>
```

## 5平台URL

| 平台 | session名 | URL |
|------|----------|-----|
| 微博 | weibo | https://weibo.com |
| 知乎 | zhihu | https://www.zhihu.com |
| B站 | bilibili | https://www.bilibili.com |
| 36氪 | kr36 | https://36kr.com |
| 百度 | baidu | https://www.baidu.com |

## 注意事项
1. opencli daemon 必须运行（`opencli doctor` 检查）
2. 如果 extension 断开，需要 `opencli daemon restart`
3. session 名是自定义的，用于后续 `opencli browser <session> <command>`
4. 打开网站后可以用 `opencli browser <session> inject` 注入 Cookie
5. 这只是辅助功能，数据采集主力是 `~/.hermes/scripts/hotlist_scraper.py`

## Windows 打开方式
也可以通过 PowerShell 直接在 Windows 打开 Chrome：
```bash
powershell.exe -Command "Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList 'https://weibo.com','https://www.zhihu.com'"
```
