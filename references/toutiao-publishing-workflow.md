# 头条号微头条发布工作流

> 通过浏览器直接发布微头条到头条号，无需第三方工具。

## 前置条件

- 用户提供头条号 Cookie（从浏览器 DevTools 导出）
- Cookie 格式：每行一个 `name\tvalue` 对，或完整的 cookie 字符串

## Cookie 注入流程

### 步骤1：导航到 toutiao.com 主域名

```
browser_navigate → https://www.toutiao.com
```

### 步骤2：通过 console 注入 Cookie

必须在 `.toutiao.com` 域名下执行，否则会被安全策略拦截：

```javascript
// 核心认证 Cookie（必须）
document.cookie = "sessionid=<value>; path=/; domain=.toutiao.com";
document.cookie = "passport_auth_status=<value>; path=/; domain=.toutiao.com";
document.cookie = "passport_csrf_token=<value>; path=/; domain=.toutiao.com";
document.cookie = "sid_guard=<value>; path=/; domain=.toutiao.com";
document.cookie = "sid_tt=<value>; path=/; domain=.toutiao.com";
document.cookie = "sso_uid_tt=<value>; path=/; domain=.toutiao.com";
document.cookie = "toutiao_sso_user=<value>; path=/; domain=.toutiao.com";
document.cookie = "uid_tt=<value>; path=/; domain=.toutiao.com";
document.cookie = "odin_tt=<value>; path=/; domain=.toutiao.com";
document.cookie = "tt_webid=<value>; path=/; domain=.toutiao.com";

// SSO 相关（增强登录态）
document.cookie = "session_tlb_tag=<value>; path=/; domain=.toutiao.com";
document.cookie = "sid_ucp_v1=<value>; path=/; domain=.toutiao.com";
document.cookie = "sid_ucp_sso_v1=<value>; path=/; domain=.toutiao.com";
```

### 步骤3：导航到发布页面

```
browser_navigate → https://mp.toutiao.com/profile_v4/weitoutiao/publish
```

如果跳转到登录页，说明 Cookie 已过期，需要用户重新提供。

## 发布流程

### 步骤4：输入内容

1. `browser_snapshot` 确认页面加载完成
2. 找到编辑器元素（placeholder: "有什么新鲜事想告诉大家？"）
3. `browser_click` 点击编辑器获取焦点
4. `browser_type` 输入完整微头条内容

### 步骤5：发布

1. `browser_vision` 确认内容完整显示
2. 找到"发布"按钮
3. `browser_click` 点击发布
4. `browser_vision` 确认发布成功（页面跳转到内容管理列表，新内容显示"审核中"）

## 陷阱

### Cookie 过期
- 头条号 Cookie 有效期约 1-2 个月
- 如果导航到 mp.toutiao.com 跳转到登录页，说明 Cookie 过期
- 解决：请用户重新导出 Cookie

### 编辑器输入
- 头条号使用富文本编辑器，`browser_type` 可以正常输入
- 输入完成后字数会自动显示在编辑器下方
- 不需要手动添加话题标签，系统会自动匹配

### 发布后状态
- 发布成功后页面自动跳转到内容管理列表
- 新内容状态为"审核中"
- 审核通过后进入推荐池，通常几分钟到几小时不等

## 数据驱动选文指南

当热点刀锋生成多篇候选时，按以下优先级选择发布：

| 维度 | 权重 | 说明 |
|------|------|------|
| 钱包距离 | 30% | 离读者钱包越近越好（零距离：房价工资物价；近距离：日常消费） |
| 反驳成本 | 25% | 读者能一句话反驳 → 评论多 → 算法推得猛 |
| 物件锚点 | 15% | 必须有读者生活中见过的具体"东西" |
| 话题时效性 | 15% | 当天热榜 > 昨天 > 更早 |
| 情绪共鸣 | 15% | 愤怒 > 无奈 > 讽刺 > 无感 |

### 选文自检清单

```
□ 这篇内容有没有一个具体的、读者生活中见过的"东西"？
□ 核心观点，读者能不能用一句话反驳？
□ 读完之后，会不会有人觉得"你胡说"？
□ 这个"你胡说"的人群够不够大（>20%读者）？
□ 发布时间是否在流量高峰（早7-9/晚7-10）？
```
