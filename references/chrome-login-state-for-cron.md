# Chrome开机自启动 + 定时任务登录态保持

> **问题**：定时任务执行时，opencli browser需要Chrome登录态才能抓取知乎/微博/头条等平台。
> 如果Chrome没有运行，opencli browser会启动新实例，没有登录态。

## 解决方案：Chrome开机自启动

### 设置步骤

1. 打开Windows启动文件夹：`Win + R` → 输入 `shell:startup` → 回车
2. 创建启动脚本：

**文件路径**：
```
C:\Users\<username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\chrome-startup.bat
```

**文件内容**：
```bat
@echo off
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --no-first-run --no-default-browser-check
```

### 效果

- ✅ 开机时Chrome自动启动
- ✅ Chrome启动后保持登录态（如果之前登录过）
- ✅ 定时任务执行时可以复用登录态

### 需要登录的平台

| 平台 | 登录方式 | 登录态有效期 |
|------|---------|-------------|
| 知乎 | 手机验证码/微信扫码 | 几周到几个月 |
| 微博 | 手机验证码/微信扫码 | 几周到几个月 |
| 今日头条 | 手机验证码/微信扫码 | 几周到几个月 |
| 小红书 | 手机验证码/微信扫码 | 几周到几个月 |
| 抖音 | 手机验证码/微信扫码 | 几周到几个月 |
| Twitter/X | 手机验证码/Google登录 | 几周到几个月 |
| YouTube | Google登录 | 几周到几个月 |

### 注意事项

1. **保持Chrome在后台运行**：不要关闭Chrome，否则定时任务无法复用登录态
2. **登录态有效期**：各平台登录态通常会保持几周到几个月
3. **如果登录态过期**：需要手动重新登录
4. **定时任务执行前检查**：可以在定时任务prompt中加入检查Chrome是否运行的步骤

### 定时任务执行时的降级策略

如果Chrome没有运行（opencli browser失败）：
- 知乎：降级到百度搜索间接获取
- 微博：降级到百度搜索间接获取
- 今日头条：降级到百度搜索间接获取
- 小红书：跳过（无备用方案）
- 抖音：跳过（无备用方案）

### WSL环境注意事项

- WSL中无法直接启动Chrome GUI
- Chrome必须在Windows侧运行
- opencli browser通过Browser Bridge扩展连接Windows侧的Chrome
- 确保Browser Bridge扩展已安装并启用
