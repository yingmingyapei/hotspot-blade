#!/usr/bin/env python3
"""Save Zhihu Hot list fetched via opencli browser as structured data."""
import json
from datetime import datetime

SKILL_DIR = "/home/yingming/.hermes/skills/productivity/hotspot-blade"

hot_data = [
    {'rank': 1, 'title': '中国裁判马宁升任世界杯主裁，他的「卡牌大师」风格会给赛事带来哪些看点？', 'heat': '471万', 'url': 'https://www.zhihu.com/question/2045411005296005155'},
    {'rank': 2, 'title': '如何看待 FIFA 发言人称与央视达成的世界杯及多项赛事协议金额创历史纪录？', 'heat': '287万', 'url': 'https://www.zhihu.com/question/2045547417521624977'},
    {'rank': 3, 'title': '唐僧为什么不抠一块脚皮给妖怪吃？', 'heat': '247万', 'url': 'https://www.zhihu.com/question/13500139412'},
    {'rank': 4, 'title': '腾讯云宣布 DeepSeek-V4 系列模型降价，最高降幅达 97.5%，将带来哪些影响？', 'heat': '207万', 'url': 'https://www.zhihu.com/question/2045220633466725057'},
    {'rank': 5, 'title': '深圳商场工作人员讥讽顾客「穷逛」，称「K11 不是服务这类没钱的人」，反映出哪些问题？', 'heat': '185万', 'url': 'https://www.zhihu.com/question/2044770207110009136'},
    {'rank': 6, 'title': '如何看待黄石市铁山区仅 4.1 万人口却维持全套区级行政架构？', 'heat': '175万', 'url': 'https://www.zhihu.com/question/2044481174496621452'},
    {'rank': 7, 'title': '胡彦斌一个月开发出 App，AI 时代将给普通人带来哪些机会？', 'heat': '166万', 'url': 'https://www.zhihu.com/question/2044389352550164119'},
    {'rank': 8, 'title': '孙正义重登亚洲首富，称 AI 才刚起步，体量有望达到互联网热潮 50 倍', 'heat': '147万', 'url': 'https://www.zhihu.com/question/2045380781644763655'},
    {'rank': 9, 'title': '如何评价 Codex 与 ChatGPT 两个独立 App 合并，这一举动有什么影响？', 'heat': '109万', 'url': 'https://www.zhihu.com/question/2045440339406762131'},
    {'rank': 10, 'title': '《给阿嬷的情书》主题曲《月下煮茶》因填词稀烂被各大知名填词人吐槽', 'heat': '107万', 'url': 'https://www.zhihu.com/question/2044530953813545270'},
    {'rank': 11, 'title': '《武林外传》小郭属于顶级的家庭背景，为什么起了郭芙蓉这种比较俗的名字？', 'heat': '105万', 'url': 'https://www.zhihu.com/question/2021168298528650460'},
    {'rank': 12, 'title': '双汇创始人父子 10 年掏空式分红 517 亿，金额甚至超越公司净利润', 'heat': '100万', 'url': 'https://www.zhihu.com/question/2045195329071309428'},
    {'rank': 13, 'title': '中国为什么能提前预测到碳排放是一个局？', 'heat': '99万', 'url': 'https://www.zhihu.com/question/2044940702971336256'},
    {'rank': 14, 'title': 'Valve 创始人纽厄尔驳斥 Steam 垄断指控，称「玩家有丰富的游戏购买渠道」', 'heat': '98万', 'url': 'https://www.zhihu.com/question/2045091353588131084'},
    {'rank': 15, 'title': '比特币自 4 月以来首次跌破 7 万美元关口，以太坊跌破 2000 美元', 'heat': '97万', 'url': 'https://www.zhihu.com/question/2045160987662321150'},
    {'rank': 16, 'title': '父母离婚前妈妈将五岁儿子近 30 万存款取走，法院判其返还', 'heat': '96万', 'url': 'https://www.zhihu.com/question/2045263892373140679'},
    {'rank': 17, 'title': '阿迪文案「在城里办事」被玩梗，品牌回应 adi 办的都是 das', 'heat': '94万', 'url': 'https://www.zhihu.com/question/2045135455197161291'},
    {'rank': 18, 'title': '杭州亚运电竞国家队工作人员称朱开没有做好准备', 'heat': '90万', 'url': 'https://www.zhihu.com/question/2044897841349399469'},
    {'rank': 19, 'title': 'OpenAI 遭美国州政府起诉，ChatGPT 涉嫌帮助策划校园枪击案', 'heat': '新', 'url': 'https://www.zhihu.com/question/2045160976878680020'},
]

now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
today = datetime.now().strftime('%Y-%m-%d')

output = {
    'source': '知乎热榜',
    'fetched_at': now,
    'method': 'opencli browser zhihu open "https://www.zhihu.com/hot" + state',
    'prerequisites': 'Chrome running + Zhihu login state (yingmingyapei)',
    'total_items': 19,
    'items': hot_data
}

import os
samples_dir = os.path.join(SKILL_DIR, 'samples')
os.makedirs(samples_dir, exist_ok=True)

json_path = os.path.join(samples_dir, f'zhihu-hot-{today}.json')
with open(json_path, 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

md_path = os.path.join(samples_dir, f'zhihu-hot-{today}.md')
with open(md_path, 'w') as f:
    f.write(f'# 知乎热榜 {today}\n\n')
    f.write(f'抓取时间：{now}\n')
    f.write(f'抓取方式：`opencli browser zhihu open "https://www.zhihu.com/hot"` → state\n')
    f.write(f'前置条件：Chrome 运行中 + 知乎登录态（yingmingyapei）\n')
    f.write(f'共 {len(hot_data)} 条\n\n')
    f.write('| # | 话题 | 热度 |\n')
    f.write('|---|------|------|\n')
    for item in hot_data:
        title_escaped = item['title'].replace('|', '\\|')
        f.write(f"| {item['rank']} | {title_escaped} | {item['heat']} |\n")

print(f'JSON: {json_path}')
print(f'MD:   {md_path}')
print(f'Done: {len(hot_data)} items')