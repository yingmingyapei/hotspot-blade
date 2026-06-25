# 头条号自动发布技术方案

> 2026-06-10 实测沉淀：Cookie注入 + Browserbase远程浏览器 + Playwright本地方案的技术对比和选型建议。

---

## 一、Cookie注入登录（Browserbase）

Browserbase远程浏览器支持通过JavaScript注入Cookie实现免登录。

### 工作流程

```
1. 导航到 toutiao.com（建立session）
2. 通过 browser_console 注入Cookie
3. 导航到 mp.toutiao.com（Cookie生效，跳过登录）
4. 操作发布页面
```

### 关键Cookie列表

| Cookie名 | 用途 | 域名 |
|-----------|------|------|
| sessionid | 会话ID | .toutiao.com |
| sid_guard | 会话守卫 | .toutiao.com |
| sid_tt | 会话令牌 | .toutiao.com |
| sso_uid_tt | SSO用户ID | .toutiao.com |
| toutiao_sso_user | SSO用户 | .toutiao.com |
| uid_tt | 用户ID | .toutiao.com |
| odin_tt | 设备标识 | .toutiao.com |
| tt_webid | Web标识 | .toutiao.com |
| sid_ucp_v1 | UCP会话 | .toutiao.com |
| passport_auth_status | 认证状态 | .toutiao.com |
| passport_csrf_token | CSRF令牌 | .toutiao.com |

### 注意事项

- Cookie有效期约2个月（sid_guard到2026-08-04）
- 每次新浏览器会话需要重新注入
- 注入前必须先导航到toutiao.com域名（建立session）
- 注入后需要导航到mp.toutiao.com才能生效

---

## 二、Browserbase vs Playwright 对比

| 维度 | Browserbase（远程） | Playwright（本地） |
|------|-------------------|-------------------|
| **页面加载** | ✅ 正常（真实浏览器指纹） | ❌ 头条号SPA超时（headless模式） |
| **Cookie注入** | ✅ 通过browser_console | ✅ 通过context.add_cookies() |
| **文件上传** | ❌ 沙箱隔离，无法访问本地文件 | ✅ set_input_files()直接注入本地路径 |
| **反爬检测** | ✅ 真实浏览器指纹，低风险 | ⚠️ headless模式易被检测 |
| **资源占用** | 远程服务器 | 本地CPU/内存 |
| **网络延迟** | 有（远程操作） | 无（本地操作） |

### 核心矛盾

- Browserbase能正常加载头条号页面，但**无法上传本地文件**
- Playwright能上传本地文件，但**headless模式下头条号页面加载超时**

---

## 三、文件上传方案

### 方案A：Playwright set_input_files()（推荐）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    context.add_cookies(cookies)
    page = context.new_page()
    
    # 访问发布页
    page.goto('https://mp.toutiao.com/profile_v4/weitoutiao/publish')
    
    # 点击图片按钮触发文件选择器
    with page.expect_file_chooser() as fc_info:
        page.click('text=图片')
    file_chooser = fc_info.value
    file_chooser.set_files('/path/to/image.png')
```

**优点**：直接注入本地文件路径，无需系统文件选择器
**缺点**：headless模式下头条号页面加载超时

### 方案B：input[type="file"].set_input_files()

```python
# 如果页面有隐藏的file input
file_input = page.query_selector('input[type="file"]')
file_input.set_input_files('/path/to/image.png')
```

**优点**：更直接，不需要触发文件选择器
**缺点**：头条号的图片按钮可能不暴露file input

### 方案C：拖拽上传

```python
# 创建DataTransfer对象模拟拖拽
page.evaluate('''() => {
    const dt = new DataTransfer();
    // 需要先获取File对象
    const file = new File([buffer], 'image.png', {type: 'image/png'});
    dt.items.add(file);
    const dropEvent = new DragEvent('drop', {dataTransfer: dt});
    document.querySelector('.drop-zone').dispatchEvent(dropEvent);
}''')
```

**优点**：绕过文件选择器
**缺点**：需要先将图片转为base64/ArrayBuffer，实现复杂

---

## 四、AIMedia架构分析（可借鉴）

### 项目信息

- GitHub: Anning01/AIMedia（2.2k stars）
- 架构: Django后端 + PySide6桌面端
- 自动化: Selenium + Chrome
- AI: 智谱AI + Stable Diffusion

### 核心流程

```
热榜抓取（6个来源） → AI生成文章 → AI生成配图 → Selenium自动发布
```

### 可借鉴点

1. **Selenium文件上传**：通过`input[type="file"].send_keys(local_path)`直接注入文件路径
2. **AI自动生成配图**：根据文章内容自动生成配图，提高点击率30-50%
3. **抖音热点数据源**：抖音热搜跟头条推荐算法用户画像高度重合

### 不值得借鉴

- 重型架构（Django + PySide6太重）
- 智谱AI（MiMo足够）
- 微信支付/登录（商业化功能）

---

## 五、推荐方案：混合架构

```
Browserbase（远程浏览器）        本地Playwright
├── 页面导航、登录态管理          ├── 文件上传（set_input_files）
├── 内容填写、按钮点击            ├── 本地文件读取
└── 发布确认                      └── 注入到远程页面
```

### 实现思路

1. 用Browserbase完成页面导航、Cookie注入、内容填写
2. 用Playwright在本地读取图片文件
3. 通过某种方式将图片传递给Browserbase（待研究）

### 替代方案

- **非headless模式**：用VcXsrv提供X11显示服务器，Playwright用非headless模式运行
- **Selenium替代Playwright**：Selenium对headless模式的支持更成熟
- **API直发**：研究头条号是否有发布API（绕过浏览器）

---

## 六、GitHub自动发布工具参考

| 工具 | Stars | 支持平台 | 技术栈 | 图片上传 |
|------|-------|---------|--------|---------|
| dreammis/social-auto-upload | 12.4k | 抖音/小红书/视频号/B站 | Playwright | ✅ |
| Anning01/AIMedia | 2.2k | 头条号/小红书/公众号 | Selenium | ✅ |
| iniwap/AIWriteX | 1.2k | 公众号/小红书/百家号 | Python | ✅ |
| RyanYipeng/SyncCaster | 404 | 掘金/CSDN/知乎/公众号 | Chrome扩展 | ✅ |
| guanyang/super-publisher | 20 | 头条号/公众号 | Agent插件 | ✅ |

**最成熟的方案**：social-auto-upload（12k星），但不支持头条号
**支持头条号且最完整**：AIMedia（2.2k星）
**Agent集成方向**：super-publisher（为AI Agent设计）
