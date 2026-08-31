# FB Reel 下载经验 — 2026-08-29

## 背景
今天下载两个 Facebook Reel，其中一个首次超时后续传秒完成，第二个直接一次成功。

## 关键发现

### 1. 断点续传是核心兜底
- 首次下载因 60s 超时停在 56%（8.2MB/13.94MB）
- 第二次 `yt-dlp` 自动识别 `.part` 文件，从断点续传
- 总耗时：续传部分仅用 3 秒完成
- **结论**：超时不是失败，下次重跑自动接上

### 2. 视频体积小是硬道理
- 两个 Reel 都只有 ~22 秒，720p~1080p
- 文件大小：14.76MB + 18.55MB
- 小文件即使网速一般也秒完

### 3. 无需 Cookie 认证的罕见情况
- 正常 FB Reel 需要完整 Netscape cookie（c_user + xs + sb + datr）
- 这次两个链接都直接返回 DASH 流（av01 编解码）
- **规律**：公开分享链接（share/r/xxx）比私人内容更容易免认证

### 4. 格式选择策略
```
-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
```
- 优先 mp4 + m4a 合并，避免 .webm
- 合并后 yt-dlp 自动删除临时流文件
- 无 ffmpeg 转码开销

### 5. 网络路径干净
- yt-dlp 原生 HTTP，不走 Python urllib
- 不受代理污染（之前 urllib 上传 Telegram 大文件常 ConnectionResetError）

## 操作规范
1. 下载失败先检查是否有 `.part` 文件（未完成的下载）
2. 直接重跑 yt-dlp，它会续传
3. 目标目录：`/mnt/c/Users/yingm/OneDrive/Videos/`
4. 超时设置建议：foreground max 600s，小文件 120s 足够

## 相关 Session
- [来源: session:20260829]
