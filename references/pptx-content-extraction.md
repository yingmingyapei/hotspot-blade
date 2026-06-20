# PPT 选题报告内容提取

当用户要求"查看""打开""看看"PPT选题报告时，用 python-pptx 提取文本内容展示，不要只报文件路径。

## 提取脚本

```python
from pptx import Presentation

pptx_path = '/mnt/c/Users/yingm/OneDrive/Desktop/选题报告_YYYY-MM-DD.pptx'
prs = Presentation(pptx_path)

for i, slide in enumerate(prs.slides):
    print(f'\n--- 第{i+1}页 ---')
    for shape in slide.shapes:
        if hasattr(shape, 'text') and shape.text.strip():
            print(shape.text[:200])
```

## PPT 结构（8页）

| 页码 | 内容 |
|------|------|
| 1 | 封面（标题+日期） |
| 2 | 数据总览（抓取时间/平台/数量/评分体系） |
| 3 | 评分体系说明（5维度权重） |
| 4-6 | 精选话题详情（每话题含评分条+角度+物件） |
| 7 | 推荐排序（按总分降序） |
| 8 | 下一步行动建议 |

## 输出路径

`/mnt/c/Users/yingm/OneDrive/Desktop/选题报告_{日期}.pptx`

## 陷阱

- python-pptx 需要 python3.10 环境（有 openpyxl 的同一个 venv）
- 如果 shape.text 包含换行符，保留原样展示
- 提取时截断到200字避免输出过长
