# 故障排查 (TROUBLESHOOTING.md)

> 热点刀锋技能常见问题解决方案

---

## 一、opencli 相关问题

### 1. Daemon 未运行

**症状：** `opencli doctor` 显示 Daemon not running

**解决：**
```bash
opencli daemon start
```

### 2. Extension 未连接

**症状：** `opencli doctor` 显示 Extension not connected

**解决：**
1. 打开 Chrome，访问 `chrome://extensions`
2. 确认 Browser Bridge 扩展已启用
3. 重启 Chrome 后再试

### 3. 命令返回空数组

**症状：** `opencli zhihu hot -f json` 返回 `[]`

**原因：** 知乎需要登录态

**解决：**
```bash
# 1. 检查 opencli 状态
opencli doctor

# 2. 在 Chrome 中登录知乎
opencli browser open "https://www.zhihu.com/hot"

# 3. 手动登录后重试
opencli zhihu hot -f json
```

### 4. 知乎返回 401 Unauthorized

**症状：** API 返回 401

**原因：** 知乎 API 需要登录态认证

**解决：**
- 交互模式：在 Chrome 中手动登录知乎
- 定时任务模式：使用 curl_cffi 备用方案或切换到 v2ex 热榜

---

## 二、数据源抓取问题

### 1. 微博热搜抓取失败

**症状：** `opencli weibo hot` 返回错误或空数据

**解决：**
```bash
# 检查 opencli 版本
opencli --version

# 升级 opencli
npm install -g @jackwener/opencli@latest

# 使用备用方案
opencli 36kr hot -f json
```

### 2. Buzzing.cc 内容为空

**症状：** curl_cffi 或 browser extract 返回空

**原因：** 页面大量 JS 渲染

**解决：**
```bash
# 方法A：使用 browser（需 Chrome 扩展）
opencli browser open "https://buzzing.cc"
sleep 5
opencli browser extract

# 方法B：使用 curl_cffi + 正则提取
python3 -c "
from curl_cffi import requests
import re
resp = requests.get('https://buzzing.cc', impersonate='chrome', timeout=15)
titles = re.findall(r'>([^<]{20,200})<', resp.text)
# ... 过滤逻辑
"
```

### 3. 所有数据源都失败

**症状：** 所有平台抓取都失败

**解决：**
1. 检查网络连接
2. 检查 opencli daemon 状态
3. 检查 IP 是否被风控（尝试切换网络）
4. 记录故障，等待恢复后重试

---

## 三、定时任务问题

### 1. 定时任务卡住等待确认

**症状：** 定时任务在"等待用户确认话题"环节卡住

**原因：** cronjob prompt 未同步技能更新

**解决：**
```bash
# 1. 查看当前 cronjob
hermes cronjob list

# 2. 更新 cronjob prompt
hermes cronjob update --job-id <job_id> --prompt "$(cat ~/.hermes/skills/productivity/hotspot-blade/templates/cronjob-prompt.md)"
```

### 2. 定时任务推送失败

**症状：** Telegram 推送失败

**解决：**
- 检查 Telegram bot 配置
- 确认 chat_id 正确
- 检查网络连通性

---

## 四、写作质量问题

### 1. 微头条 AI 味太重

**解决：**
- 执行第七步"润色加固"
- 过三宗罪自检
- 使用 `article-polish-master` 技能辅助润色

### 2. 标题点击率低

**解决：**
- 执行标题 A/B 测试，选择评分最高的
- 避免使用"竟然""必须""震惊"等绝对词
- 控制标题在 25 字以内

### 3. 内容重复度高

**解决：**
- 检查多样性规则（同一子类最多2个）
- 增加话题子类覆盖范围
- 调整九边适配性评分权重

---

## 五、性能问题

### 1. 执行时间过长

**原因：** 数据源抓取超时

**解决：**
```bash
# 减少抓取数量
opencli zhihu hot -f json --limit 5

# 跳过失败的数据源
# 在 cronjob-prompt.md 中配置跳过策略
```

### 2. 内存占用高

**原因：** 同时抓取多个平台

**解决：**
- 串行抓取，而非并行
- 及时清理中间数据

---

## 六、数据源状态监控

运行健康检查脚本：

```bash
python3 ~/.hermes/skills/productivity/hotspot-blade/scripts/data_source_health_check.py
```

**预期输出：**
```
✅ 知乎热榜：成功获取 X 条数据
✅ 微博热搜：成功获取 X 条数据
⚠️ Buzzing.cc：抓取失败（原因）
...
```

---

## 七、获取帮助

- 查看技能文档：`hermes skill view hotspot-blade`
- 查看参考文档：`references/` 目录
- 提交 Issue：https://github.com/yingmingyapei/hotspot-blade/issues
