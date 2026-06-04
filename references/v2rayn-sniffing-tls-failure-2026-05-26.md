# V2rayN Sniffing TLS 握手失败诊断与修复

> **记录日期**: 2026-05-26  
> **问题来源**: YouMind X 爆款文章抓取失败  
> **影响范围**: 所有需要通过 V2rayN 代理访问的 HTTPS 目标

---

## 问题现象

```
curl: (35) error:0A000126:SSL routines::unexpected eof while reading
```

或 Python 脚本中：
```
ssl.SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] unexpected eof while reading
```

---

## 诊断流程

### 第1步：确认代理端口可用

```bash
# 测试 HTTP 代理基础连通性
curl -s --max-time 5 --proxy http://127.0.0.1:10808 https://httpbin.org/ip

# 预期：返回代理出口 IP，如 {"origin": "x.x.x.x"}
```

### 第2步：测试目标网站直连代理

```bash
# 带详细输出测试 YouMind 连接
curl -v --max-time 15 -x http://127.0.0.1:10808 "https://youmind-x.com/viral" 2>&1 | grep -E "SSL|error|Connected|handshake"
```

**成功输出**：
```
* Connected to (nil) (127.0.0.1) port 10808 (#0)
* allocate connect buffer!
* Establish HTTP proxy tunnel to youmind-x.com:443
> CONNECT youmind-x.com:443 HTTP/1.1
< HTTP/1.1 200 Connection established
* Proxy replied 200 to CONNECT request
* CONNECT phase completed!
* TLSv1.3 (OUT), TLS handshake, Client hello
```

**失败输出（sniffing 干扰）**：
```
* Connected to (nil) (127.0.0.1) port 10808 (#0)
* Establish HTTP proxy tunnel to youmind-x.com:443
> CONNECT youmind-x.com:443 HTTP/1.1
< HTTP/1.1 200 Connection established
* Proxy replied 200 to CONNECT request
* CONNECT phase completed!
* TLSv1.3 (OUT), TLS handshake, Client hello (1)
* error:0A000126:SSL routines::unexpected eof while reading
* Closing connection 0
curl: (35) error:0A000126:SSL routines::unexpected eof while reading
```

### 第3步：验证代理节点本身正常

```bash
# 测试其他 HTTPS 网站（如 Google、Twitter）
curl -s --max-time 10 -x http://127.0.0.1:10808 "https://www.google.com" | head -c 200
curl -s --max-time 10 -x http://127.0.0.1:10808 "https://twitter.com" | head -c 200

# 如果这些网站正常，说明代理节点没问题，问题出在 sniffing
```

---

## 根因分析

V2rayN 的 `sniffing` 功能会在 TLS 握手阶段尝试嗅探域名（SNI - Server Name Indication）：

1. **正常流程**：客户端 → CONNECT 隧道 → TLS 握手 → 数据传输
2. **Sniffing 干扰**：客户端 → CONNECT 隧道 → **TLS 握手被嗅探中断** → unexpected eof

当 `sniffing.enabled: true` 时，V2rayN 会在 TLS 握手过程中尝试读取 SNI 信息来确定路由。但某些代理节点/协议组合下，这个嗅探过程会：
- 在 TLS ClientHello 阶段就中断连接
- 导致客户端收到 "unexpected eof while reading" 错误

**为什么 Google/Twitter 正常但 YouMind 失败**：
- 可能是路由规则差异
- 可能是目标服务器 TLS 实现差异
- 但最可能的原因是 sniffing 对某些域名/端口的处理不一致

---

## 解决方案

### ⚠️ 重要限制

V2rayN 配置文件位于 **Windows 文件系统**，WSL 环境无法直接访问/修改。

**配置文件常见位置**：
- `C:\Users\yingm\AppData\Roaming\v2rayN\config.json`
- `C:\ProgramData\v2rayN\core\config.json`
- 或 V2rayN 安装目录下的 `config.json`

### 修复步骤

**1. 找到并打开配置文件**

在 Windows 上找到 `config.json`，用文本编辑器打开。

**2. 修改 sniffing 配置**

找到 `inbounds` 部分，将 `sniffing.enabled` 从 `true` 改为 `false`：

```json
{
  "inbounds": [
    {
      "port": 10808,
      "protocol": "dokodemo-door",
      "settings": {
        "address": "127.0.0.1"
      },
      "sniffing": {
        "enabled": false,
        "destOverride": ["http", "tls"]
      }
    }
  ]
}
```

**3. 重启 V2rayN 核心（必须）**

修改配置后，**必须重启 V2rayN 核心**才能生效：
- 菜单 → 重启核心
- 或退出 V2rayN 后重新打开

**4. 验证修复**

```bash
# 再次测试 YouMind 连接
curl -v --max-time 15 -x http://127.0.0.1:10808 "https://youmind-x.com/viral" 2>&1 | tail -20

# 预期：TLS 握手成功，返回 HTML 内容
```

---

## 为什么禁用 sniffing 是安全的

1. **路由规则已配置**：V2rayN 的 `routing.rules` 已经正确配置了代理规则，不需要 sniffing 来辅助路由
2. **端口已固定**：所有流量都通过 10808 端口，不需要嗅探来区分直连/代理
3. **实测验证**：禁用 sniffing 后，Google/Twitter/YouMind 等所有目标都正常访问

---

## 相关诊断

### 代理协议检测

```bash
# 确认 10808 端口是 HTTP 代理还是 SOCKS5
curl -s --max-time 5 --proxy http://127.0.0.1:10808 https://youmind-x.com | head -c 100
curl -s --max-time 5 --proxy socks5://127.0.0.1:10808 https://youmind-x.com | head -c 100

# V2rayN 混合端口同时支持 HTTP 和 SOCKS5，但脚本应使用 HTTP 格式
```

### 其他代理软件对比

| 代理软件 | 默认端口 | 协议类型 | Sniffing 默认 |
|----------|---------|---------|--------------|
| V2rayN | 10808 | HTTP/SOCKS5 混合 | **enabled=true** |
| Clash | 7890 | HTTP | 默认关闭 |
| Clash | 7893 | SOCKS5 | 默认关闭 |

---

## 经验总结

1. **先诊断后修复**：不要盲目修改配置，先用 curl 详细输出确认问题
2. **验证代理节点**：确保问题不是代理节点本身的问题
3. **重启必做**：修改 V2rayN 配置后必须重启核心
4. **WSL 限制**：WSL 无法直接修改 Windows 配置文件，需用户手动操作

---

## 参考

- V2rayN 官方文档：https://github.com/2dust/v2rayN
- Xray-core sniffing 文档：https://xtls.github.io/config/routing.html#sniffingconfig