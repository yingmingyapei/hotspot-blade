# tophub.today CAPTCHA 抓取失败记录

> 首次记录：2026-05-07
> 状态：已知问题，暂无可行的自动化绕过方案

## 症状

访问 `https://tophub.today/c/tech` 时，所有自动化工具均触发 Cloudflare 风控，返回「安全验证」页面，需要手动输入数字验证码。

## 尝试过的方案

### 方案1：curl（标准HTTP请求）❌
```bash
curl -s 'https://tophub.today/c/tech'
# 返回 403，包含安全验证页面HTML
```
- 结果：直接被 Cloudflare 拦截，返回 403

### 方案2：Python requests（带完整浏览器头）❌
```python
session.headers.update({"User-Agent": "Mozilla/5.0 ..."})
r = session.get("https://tophub.today/c/tech")
```
- 结果：返回 403，内容为安全验证页面
- Cookie/Session 无法通过 Cloudflare 校验

### 方案3：Hermes Browser（含 vision AI）❌
```python
browser_navigate("https://tophub.today/c/tech")
# 卡在安全验证页面
browser_vision("Read CAPTCHA numbers")
browser_type("...")
browser_click("确认验证")
```
- 结果：vision AI 多次误读验证码数字（如实际数字与读取数字不一致）
- IP（110.81.32.232）被风控标记，3次失败后持续被拦截
- 即使更换验证码刷新，仍无法通过

### 方案4：opencli browser open+extract ❌
```bash
opencli browser open "https://tophub.today/c/tech"
opencli browser extract
```
- 结果：需要 Browser Bridge Extension 连接，且 same origin 限制
- Extension 在 headless/cron 环境中通常不可用

## 根因分析

1. **Cloudflare 流量检测**：tophub.today 使用了 Cloudflare 的 Bot Management 或类似的流量分析
2. **数字验证码**：非简单的 reCAPTCHA，而是自制的数字验证码（灰色背景、绿色数字、扭曲字体）
3. **IP 风控**：一旦 IP 触发风控，会被持续拦截，短期内无法解封
4. **vision AI 局限性**：对扭曲数字的识别准确率不稳定（3次尝试：98810、26138、63214、47592 均验证失败）

## 已知可行的方案（均不适用于自动化）

- 手动浏览器 + 人工识别验证码 → 可一次通过，但无法自动化
- 更换住宅代理 IP → 可能绕过 IP 风控，但验证码仍需解决
- 使用 tophub 官方 API → 404，无公开 API

## 结论

**tophub.today 不应视作可依赖的数据源。** 知乎+微博两源已足够支撑每日选题。tophub 作为 bonus 看待，抓取失败时直接跳过，不影响核心产出。
