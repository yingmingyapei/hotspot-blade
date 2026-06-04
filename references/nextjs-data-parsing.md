# Next.js `__next_f.push` 嵌入式数据解析技巧

> 适用于：从 Next.js SSR/SSG 页面中提取服务端注入的数据（JSON-LD、页面 props 等）

## 问题

Next.js 页面的数据不是直接写在 HTML 标签里，而是嵌在 `<script>` 标签的 `self.__next_f.push([1,"..."])` 调用中，JSON 值被双重转义（`\"` → `\\\"`）。

## 解析步骤

```python
import re

# Step 1: 提取所有 push 块内容
# 匹配 self.__next_f.push([1,"...escaped content..."])
pushes = re.findall(
    r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html
)

# Step 2: 拼接所有块 + 反转义
full = "".join(pushes).replace('\\"', '"')

# Step 3: 用正则匹配目标数据结构
# 示例：匹配 {"id":123,"slug":"xxx","title":"yyy",...}
pattern = r'"id":(\d+),"slug":"([^"]+)","title":"([^"]*)"'
for m in re.finditer(pattern, full):
    print(m.group(1), m.group(2), m.group(3))
```

## 关键细节

1. **不要直接在整个 HTML 上做正则**：数据是 JSON-escaped 的，直接匹配会失败
2. **必须先提取 push 块 → 拼接 → 反转义**，然后再匹配
3. **push 块可能跨多个 `<script>` 标签**：同一个 JSON 对象可能被拆到多个 push 调用中
4. **去重**：同一个文章/对象可能出现在多个 push 块中（日榜、周榜、主列表），用 id 去重

## 调试技巧

```python
# 查看 push 块数量和总长度
pushes = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
print(f'Found {len(pushes)} push blocks, total {sum(len(p) for p in pushes)} chars')

# 查看反转义后的内容片段
full = "".join(pushes).replace('\\"', '"')
# 搜索关键词定位数据区域
for m in re.finditer(r'articles', full):
    print(f'  "articles" at offset {m.start()}: ...{full[m.start():m.start()+100]}...')
```

## 已知站点

| 站点 | URL | 数据内容 | 脚本 |
|------|-----|---------|------|
| YouMind | youmind.com/zh-CN/landing/x-viral-articles | X/Twitter 爆款文章（289篇/日） | `scripts/youmind_viral_scraper.py` |
