# Hotspot-Blade v4.1 升级方案（2026-06-17）

> 来源：WSL Hermes + iStoreOS Hermes 联合讨论

## P0（立即做）

### 1. 去重脚本化（simhash）
- 不用LLM做去重，用Python脚本硬匹配
- 方案：simhash或编辑距离计算标题相似度
- history.json记录SHA256哈希，脚本先过滤再进LLM写作
- 核心原则：**去重这种机械操作不要交给LLM，写python逻辑硬匹配**
- 三重防线：
  1. 脚本simhash硬去重（0 token，0误判）
  2. history.json SHA256哈希比对
  3. LLM只做最后的内容去重（同一事件不同角度）

### 2. 禁用语清单更新
合并后的通用AI味检测清单：

**禁止词（18个）：**
值得注意的是 / 在...方面 / 发挥着重要作用 / 不可或缺 / 不仅...更 / 某种意义上 / 从某种角度来看 / 众所周知 / 不可否认 / 毋庸置疑 / 业内人士指出 / 被广泛认为 / 引起了广泛关注 / 背后反映了 / 引发热议 / 在当今这个...的时代 / 扮演着重要角色 / 某种程度上

**禁止句式：**
- "是...的"句式（甲是乙的丙 → 直接说甲做了丙）
- 被字句过多
- 排比三连
- "在当今这个...的时代"开头 → 直接砍

**补充规则（来自iStoreOS Hermes）：**
- "引起了广泛关注" → 5个字的废话，直接说谁关注了
- "背后反映了" → 文章不是论文，不需要揭示"本质"
- "引发热议" → 自己说的热点不需要自证

## P1（本周）

### 3. curl_cffi替代curl+Cookie
- 用curl_cffi的impersonate参数模拟浏览器指纹
- 不需要Cookie，解决Cookie过期问题
- 国内平台（头条/微博）优先用browser_navigate，curl_cffi反而不行
- 参考：bypass-website-anti-bot skill

### 4. 数字校验脚本
- 写作完成后用正则扫描文章中的数字（\d+%/\d+亿等）
- 与原始数据源对比，防止LLM编造数据
- prompt里写"不确定的数据用'据报道''有数据显示'代替具体数字"

## P2（已完成 ✅ 2026-06-20）

### 5. 分级模型策略
- cron模式A（选题报告）用 MiMo（mimo-v2.5-pro / xiaomi），成本低
- cron模式B（完整写作用）用 DeepSeek（deepseek-chat），质量优先
- 用户手动触发时不覆盖，尊重默认模型
- 弱模型只做格式整理，强模型写初稿

### 6. cron输出格式标准化
- 定义统一的JSON输出格式，见 `references/cron-output-format.md`
- 模式A：采集统计 + Top N选题列表 + PPT路径
- 模式B：标题 + 正文 + 质量分 + 辣度
- 中间数据写入 `/tmp/hotspot-blade-output.json`
- 错误时输出：模式 + 失败步骤 + 原因 + 建议

## P3（已完成 ✅ 2026-06-20 — 结论：不需要）

### 7. Scrapling 页面解析
- **评估结论**：curl_cffi 覆盖全部5个平台，Scrapling 不需要
- 5个平台全部使用 JSON API，curl_cffi 完全够用
- 已创建 `scripts/hotlist_html_fallback.py` 作为 HTML 降级方案
- 升级路径：curl_cffi JSON → HTML Fallback → Scrapling → browser_navigate

## 写作质量优化经验（来自iStoreOS Hermes）

1. **具体模板代替抽象要求** — "第一段写冲突"而不是"写吸引人"
2. **禁用语列表写进system prompt** — 不是后置润色，是前置禁止
3. **反共识观点+具体案例** — 模型不喜欢写具体案例但读者爱看
4. **强模型写初稿** — 后置润色治标不治本
5. **防止LLM编数据** — prompt明确写"不确定用据报道代替"，脚本扫描数字

## 巴菲特写作技法融合建议

写投资/商业话题时，用巴菲特的类比法+数据法+冷幽默定性，套九边的"我"视角+追问结尾。
