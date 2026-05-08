# 安装指南 (INSTALL.md)

> 热点刀锋技能安装详细指南

---

## 前置依赖

### 1. Hermes Agent

确保已安装 [Hermes Agent](https://hermes-agent.nousresearch.com) 最新稳定版：

```bash
hermes --version
```

### 2. opencli

安装 opencli CLI 工具（≥ 1.7.14）：

```bash
npm install -g @jackwener/opencli@latest

# 验证版本
opencli --version
```

启动 daemon：

```bash
opencli daemon start
```

### 3. Python 环境

需要 Python 3.10+ 及 `curl_cffi` 库：

```bash
pip install curl_cffi
```

---

## 安装步骤

### 方式一：Git Clone（推荐）

```bash
# 1. Clone 仓库
git clone https://github.com/yingmingyapei/hotspot-blade.git

# 2. 创建技能目录（如不存在）
mkdir -p ~/.hermes/skills/productivity

# 3. 软链接到技能目录
ln -s $(pwd)/hotspot-blade ~/.hermes/skills/productivity/hotspot-blade

# 4. 验证安装
hermes skill view hotspot-blade
```

### 方式二：手动复制

```bash
# 1. 下载或复制整个 hotspot-blade 目录
# 2. 放入 ~/.hermes/skills/productivity/
# 3. 确保目录结构完整
```

---

## 验证安装

### 1. 检查技能加载

```bash
hermes skill view hotspot-blade
```

预期输出 SKILL.md 内容。

### 2. 检查 opencli 连接

```bash
opencli doctor
```

预期输出：
```
[OK] Daemon: running on port 19825
[OK] Extension: connected
[OK] Connectivity: connected
```

### 3. 测试数据源

```bash
# 测试微博热搜（无需登录态）
opencli weibo hot -f json --limit 3

# 测试 36氪热榜
opencli 36kr hot -f json --limit 3
```

---

## 配置

### 1. Chrome 扩展（可选，用于知乎热榜）

知乎热榜需要 Chrome 登录态：

1. 打开 Chrome，访问 `chrome://extensions`
2. 确保 Browser Bridge 扩展已启用
3. 在 Chrome 中登录知乎账号

### 2. 定时任务配置

见 [USAGE.md](USAGE.md) 定时任务章节。

---

## 常见问题

### Q: opencli daemon 启动失败？

```bash
# 检查端口占用
lsof -i :19825

# 重启 daemon
opencli daemon stop && opencli daemon start
```

### Q: 技能加载失败？

```bash
# 检查软链接
ls -la ~/.hermes/skills/productivity/hotspot-blade

# 重新创建软链接
rm ~/.hermes/skills/productivity/hotspot-blade
ln -s $(pwd)/hotspot-blade ~/.hermes/skills/productivity/hotspot-blade
```

---

## 下一步

- [使用指南](USAGE.md) - 详细使用说明
- [故障排查](TROUBLESHOOTING.md) - 常见问题解决方案
