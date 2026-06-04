# 热点刀锋 GitHub 发布记录

> 2026-05-08 热点刀锋技能发布到 GitHub 的完整过程记录

---

## 发布概览

| 项目 | 详情 |
|------|------|
| **仓库地址** | https://github.com/yingmingyapei/hotspot-blade |
| **发布方式** | GitHub API + HTTPS Token 认证 |
| **提交次数** | 3 commits |
| **文件大小** | ~150KB |

---

## 发布流程

### 1. 敏感信息清理

- ✅ 移除 references 中的个人 IP 地址 (110.81.32.232)
- ✅ 移除 SKILL.md 中的硬编码 Windows 路径
- ✅ references 文件名去日期化
- ✅ 添加注意事项标注测试文档的时效性

### 2. 仓库结构创建

```
hotspot-blade/
├── README.md
├── LICENSE (MIT)
├── SKILL.md
├── .gitignore
├── docs/
│   ├── INSTALL.md
│   ├── USAGE.md
│   └── TROUBLESHOOTING.md
├── templates/
│   └── cronjob-prompt.md
├── scripts/
│   ├── data_source_health_check.py
│   └── patch_skill_md.py
├── references/
│   ├── hotlist-sources-audit.md
│   ├── optimization-summary.md
│   ├── optimization-test-report.md
│   ├── tophub-captcha-failure.md
│   └── zhihu-login-requirement.md
└── examples/
    └── sample-output.md
```

### 3. GitHub 仓库创建

使用 GitHub API 创建（gh CLI 未安装）：

```bash
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token ghp_XXX" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"hotspot-blade","description":"多平台热榜抓取 + 爆款微头条一键生成技能","private":false}'
```

### 4. 推送代码

```bash
# 配置 credential helper
git config credential.helper store
echo "https://yingmingyapei:TOKEN@github.com" >> ~/.git-credentials

# 推送
git push -u origin main

# 安全清理
rm -f ~/.git-credentials
git remote set-url origin git@github.com:yingmingyapei/hotspot-blade.git
```

### 5. 添加仓库标签

```bash
curl -s -X PUT https://api.github.com/repos/yingmingyapei/hotspot-blade/topics \
  -H "Authorization: token ghp_XXX" \
  -H "Accept: application/vnd.github.mercy+json" \
  -d '{"names":["hermes-agent","skill","content-generation","web-scraping","automation","python","chinese","social-media"]}'
```

### 6. 添加封面图

```bash
# 设计 SVG 封面图
# 转换 SVG → PNG
python3 -c "
import cairosvg
cairosvg.svg2png(url='docs/cover.svg', write_to='cover.png', output_width=1280, output_height=640)
"

# 提交
git add cover.png docs/cover.svg
git commit -m "feat: add GitHub repository cover image"
git push
```

---

## 遇到的问题及解决

### 问题 1：SSH 连接失败

**症状：** `Permission denied (publickey)`

**解决：**
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
```

### 问题 2：gh CLI 未安装

**解决：** 使用 GitHub API 创建仓库

### 问题 3：HTTPS 推送 TLS 错误

**症状：** `GnuTLS recv error (-110)`

**解决：** 重试或使用 credential.helper store

### 问题 4：中文文字在 SVG 中渲染失败

**症状：** 中文显示为方块

**解决：** 在 SVG 中指定系统字体 `WenQuanYi Zen Hei`

---

## 提交历史

```
de155c4 fix: regenerate cover image with Chinese font support
64f58a4 feat: add GitHub repository cover image
6a58f54 feat: 热点刀锋技能初始版本
```

---

## 后续维护建议

1. **定期更新 README** — 保持项目描述最新
2. **添加 GitHub Actions** — 自动运行健康检查脚本
3. **启用 Discussions** — 方便用户交流
4. **创建 Release** — 发布 v1.0.0 版本
5. **监控数据源状态** — 各平台 API 可能变动

---

## 相关文档

- [github-skill-publish 技能](https://github.com/yingmingyapei/hotspot-blade) - GitHub 技能发布工作流
- [github-cover-image.md](references/github-cover-image.md) - 封面图生成指南
- [github-token-auth.md](references/github-token-auth.md) - Token 认证模式记录
