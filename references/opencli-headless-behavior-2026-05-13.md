# opencli Headless环境行为实测 — 2026-05-13

> 记录opencli在定时任务/headless环境中的真实行为，修正此前"API类命令不依赖Extension"的错误认知。

## 测试环境

- **日期**: 2026-05-13 12:00
- **环境**: WSL (Windows Subsystem for Linux), headless (无Chrome GUI)
- **Daemon**: opencli daemon v1.7.14，运行在 port 19825
- **Extension**: 未连接（headless环境正常现象）

## 实测结果

| 命令 | 结果 | 耗时 |
|------|------|------|
| `opencli doctor` | ❌ 超时 | 30s+ |
| `opencli zhihu hot -f json --limit 5` | ❌ 超时 | 30s+ |
| `opencli weibo hot -f json --limit 5` | ❌ 超时 | 30s+ |
| `opencli daemon restart` | ✅ 成功，提示Extension未连接 | 2s |
| `curl localhost:19825/status` | ✅ 返回 daemon 运行中 | 0.5s |
| `curl -H "X-OpenCLI: true" localhost:19825/` | ✅ 返回 `{"error":"Not found"}` | 0.5s |

## 关键发现

### 1. ALL opencli commands require Extension, not just browser commands

**此前SKILL.md中的错误说法**：
> "opencli 的 API 类命令（zhihu hot -f json、weibo hot -f json）不依赖 Browser Bridge，可直接使用"

**实际行为**：
- opencli daemon 本身可运行并且 curl 可直接访问
- 但所有 opencli CLI 命令（包括 zhihu hot、weibo hot）在 Extension 未连接时都会 **无限等待/超时**
- Daemon 正确处理请求前会等待 Extension 响应

### 2. Daemon restart 不会重新建立 Extension 连接

- `opencli daemon restart` 重启后 Extension 仍然是断开状态
- 需要手动在 Chrome 中开启并连接

## 替代方案（已验证可用）

| 源 | 方法 | 验证 |
|----|------|------|
| **百度热搜** | `urllib → top.baidu.com/board?tab=realtime → 正则提取` | ✅ 52条，实时 |
| **Buzzing.cc** | `urllib → buzzing.cc → 正则提取标题` | ✅ 578条，实时 |
| **Hacker News** | `urllib → hacker-news.firebaseio.com → JSON` | ✅ 500条，实时 |
| 知乎热榜 | 已不可用（需要登录态） | ❌ 401/403 |
| 微博热搜 | 已不可用（需要登录态） | ❌ 403/访客系统 |
| 36氪API | 返回2020年缓存数据 | ⚠️ 不可靠 |

## 建议

1. **定时任务环境中完全跳过 opencli**：所有数据通过 Python 标准库（urllib）直接抓取
2. **opencli 仅用于交互模式**：需要用户手动连接 Extension 后使用
3. **执行检查清单中的 `opencli doctor` 应仅作为"可选步骤"**：不阻塞整体流程
