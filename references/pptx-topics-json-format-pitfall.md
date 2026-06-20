# PPT生成脚本topics JSON格式陷阱（2026-06-15实测）

## 症状

`generate_topic_report_pptx.py` 报错 `KeyError: 0` 或 `TypeError: list indices must be integers or slices, not str`。

## 根因

脚本的 `build_report()` 直接接受一个扁平话题列表（list of dict），但常见做法是把话题包装在 `{"topics": [...], "date": "..."}` 对象中。

### 错误做法

```python
# ❌ 包装成对象
topics_json = {"topics": [...], "date": "2026-06-15"}
json.dump(topics_json, f)
# 传给脚本后 build_report() 收到的是 dict 不是 list → KeyError
```

### 正确做法

```python
# ✅ 直接存为扁平列表
topic_list = [
  {"title": "...", "score": 9.3, "scores": {...}, ...},
  {"title": "...", ...},
]
json.dump(topic_list, f)
# 传给脚本后 build_report() 直接取用 → 正常
```

## 为什么容易踩坑

1. `hotlist_scraper.py` 的 JSON 输出是一个 dict（按平台分类）—— Agent 自然沿用相同结构。
2. PPT 脚本的 `build_report()` 签名是 `build_report(topics, ...)`，不检查 `topics` 的类型，直接在 `topics[0]` 上取 `['title']`——传入 dict 时报 `KeyError: 0`（因为 dict key 不是 0 而是 'topics'）。
3. 错误信息不直观：`KeyError: 0` 看不出是格式问题。

## 防御

1. 保存 topics JSON 时直接用 `json.dump(topics_list)`，不要包装。
2. 如果必须包装（如需要日期字段），分两步：存 date 到另一个文件，或存 topic_list 时在文件名中包含日期。
3. 生成后验证：`python3 -c "import json; data=json.load(open('file.json')); print(type(data))"` 应该显示 `<class 'list'>` 而不是 `<class 'dict'>`。

---

## 额外的字段名陷阱（2026-06-17实测）

### 症状

```python
# ❌ KeyError: 'grade' 
# 如果使用了 topic['rating'] 而不是 topic['grade']
grade_color = ACCENT_GREEN if topic['grade'] == 'S' else ACCENT_YELLOW
```

### 根因

脚本 `draw_topic_block()` 硬编码以下字段名，使用不同字段名（如 `rating` 替代 `grade`）会报 `KeyError`：

| 脚本要求的字段名 | 容易误用的字段名 | 报错位置 |
|---|---|---|
| `grade` | `rating`, `grade_level`, `level` | `draw_topic_block()` — grade_color 计算行 |
| `score` | `total`, `total_score` | 同上 — 显示 `总分: X/10` |
| `scores` key = **中文** | 英文如 `wallet`、`refute` | `draw_topic_block()` — 标签直接打印到PPT |
| `object_detail` | `object_desc`, `object` | 可选字段，缺省时显示空（不报错但内容缺失） |

### `scores` 字典的 key 必须是中文

脚本遍历 `topic['scores'].items()` 并将 key 直接作为文本标签渲染到 PPT 上：

```python
for label, score in topic['scores'].items():
    draw_score_bar(tf2, label, score)  # label = "钱包距离" 直接打印
```

所以必须用中文 key：

```python
# ✅ 正确
scores = {"钱包距离": 10, "反驳成本": 9, "物件锚点": 10, "头条适配": 10, "天然分裂": 8}

# ❌ 错误——PPT会显示"wallet 8/10"而非"钱包距离 8/10"
scores = {"wallet": 10, "refute": 9, "object": 10, "toutiao": 10, "split": 8}
```

### 防御

1. 写入 topics JSON 前验证字段名：检查 `grade` 不是 `rating`，`score` 是 float 不是 str。
2. 验证 `scores` 的 key 与评分维度中文名完全一致。
3. 可选字段（`object_detail`, `split_detail`, `reason`）缺省时脚本用 `.get()` 安全访问，但建议尽量提供以丰富PPT内容。
