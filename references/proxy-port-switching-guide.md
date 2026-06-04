# 代理端口切换指南

> 当用户更换代理软件（V2RayN → SSR → OpenClash 等）时，需要更新所有硬编码的端口引用。

## 核心原则

**`config.yaml` 不是唯一需要更新的地方。** 技能脚本、cronjob prompt、参考文档中都可能硬编码了旧端口。

## 端口映射表

| 代理软件 | SOCKS5 端口 | HTTP 端口 |
|----------|------------|-----------|
| V2RayN | 10808 | 10808 |
| ShadowsocksR (SSR) | 1080 | 1080 |
| OpenClash | 7893 | 7890 |
| Clash | 7890 | 7890 |

## 需要检查的文件清单

### 必须更新（影响功能）

| 文件 | 影响 |
|------|------|
| `skills/productivity/hotspot-blade/scripts/youmind_viral_scraper.py` | YouMind 抓取脚本的默认代理 |
| `skills/productivity/hotspot-blade/scripts/hotspot-blade-push.py` | Telegram 推送脚本的代理 |
| `skills/productivity/hotspot-blade/scripts/data_source_health_check.py` | 数据源健康检查 |
| `skills/productivity/hotspot-blade/templates/cronjob-prompt.md` | 定时任务命令 |
| `config.yaml` (`telegram.proxy_url`) | Gateway 代理配置 |

### 建议更新（影响文档一致性）

| 文件 | 影响 |
|------|------|
| `skills/productivity/hotspot-blade/SKILL.md` | 技能文档中的命令示例 |
| `skills/productivity/hotspot-blade/references/*.md` | 参考文档 |
| `skills/devops/wsl-api-connectivity/SKILL.md` | WSL 代理配置示例 |
| `skills/devops/wsl-windows-localhost-bridge/SKILL.md` | localhost 桥接示例 |
| `skills/devops/telegram-connection-diagnostics/SKILL.md` | Telegram 诊断步骤 |
| `skills/devops/hermes-web-ui-troubleshooting/SKILL.md` | Web UI 排查 |
| `skills/devops/hermes-gateway-systemd-service/SKILL.md` | Gateway 服务配置 |
| `skills/social-media/telegram-gateway-proxy/SKILL.md` | Gateway 代理配置 |

## 自动化检查命令

```bash
# 1. 确认 config.yaml 中的当前端口
grep "proxy_url" ~/.hermes/config.yaml

# 2. 搜索所有硬编码的旧端口（以 10808 为例）
grep -rn "10808" ~/.hermes/skills/

# 3. 搜索所有硬编码的代理配置
grep -rn "socks5://127.0.0.1:" ~/.hermes/skills/

# 4. 验证更新后无残留
grep -rn "10808" ~/.hermes/skills/productivity/hotspot-blade/
# 应返回空
```

## 验证步骤

```bash
# 1. 重新加载代理配置
source ~/proxy-detect.sh

# 2. 测试代理连通性
curl -s --max-time 5 --proxy socks5://127.0.0.1:1080 https://youmind.com | head -c 100

# 3. 运行 YouMind 脚本测试
python3 ~/.hermes/skills/productivity/hotspot-blade/scripts/youmind_viral_scraper.py --limit 3

# 4. 检查 cronjob 是否需要同步更新
hermes cronjob list
```

## 注意事项

1. **cronjob prompt 是独立快照**：修改 skill 后，已创建的 cronjob 不会自动同步，需手动 `hermes cronjob update`
2. **`proxy-detect.sh` 只设置环境变量**：不影响脚本中的硬编码值
3. **优先检查 hotspot-blade 技能**：YouMind 抓取最依赖代理，最容易出问题
4. **SSR 默认端口是 1080**，不是 10808（V2RayN 的端口）
