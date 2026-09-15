#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冰雪诗词 - 诗词优选排序（A3 方案：两两比较淘汰赛）
标准体裁按 写景/抒情/其他 三个子类分别排序
"""

import os
import re
import json
import time
import math
import requests

# ============================================================
# 配置区
# ============================================================
POEM_FILE = '冰雪诗词_规范格式.txt'
CACHE_FILE = 'poem_ranking_cache.json'
OUTPUT_FILE = 'poem_rankings.json'

DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

TOP20_CIPAI = [
    '踏莎行', '鹧鸪天', '浣溪沙', '临江仙', '蝶恋花',
    '清平乐', '西江月', '菩萨蛮', '虞美人', '南乡子',
    '长相思', '卜算子', '采桑子', '减字木兰花', '沁园春',
    '水调歌头', '念奴娇', '满江红', '苏幕遮', '定风波'
]

STANDARD_GENRES = ['五绝', '五律', '七绝', '七律']

# 三大类归并
THEME_TO_CATEGORY = {
    '山水田园与闲居雅趣': '写景',
    '四时风光与节气流转': '写景',
    '咏物寄意与比兴抒怀': '写景',
    '家国情怀与时代歌咏': '抒情',
    '亲情友情与人间至爱': '抒情',
    '羁旅思乡与行吟纪游': '抒情',
    '感怀人生与自省述志': '抒情',
    '怀古咏史与读文有感': '其他',
    '节日庆典与民俗风情': '其他',
    '唱和应酬与赠友之作': '其他',
}

# 关键词映射（与主脚本一致）
KEYWORDS_MAP = {
    '家国情怀与时代歌咏': ['国庆', '七一', '八一', '党', '国', '军', '抗疫', '疫情', '白衣', '英雄', '烈士', '主席', '总理', '神舟', '航母', '航天', '奥运', '夺冠', '武汉', '新冠', '钟南山', '北斗', '戍边', '将士', '子弟兵', '阅兵', '两会', '脱贫', '小康'],
    '山水田园与闲居雅趣': ['山', '水', '江', '河', '湖', '海', '银滩', '乳山', '田园', '农家', '庭', '窗', '闲', '幽', '居', '钓', '茶', '酒', '晨练', '散步', '菜园', '垂钓'],
    '亲情友情与人间至爱': ['父', '母', '娘', '亲', '孙', '孙女', '妻', '友', '朋', '同窗', '悼', '哭', '别', '聚', '团圆', '老伴', '孙娃', '若煊', '生日', '祝', '贺', '思念', '怀', '寄'],
    '四时风光与节气流转': ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏', '小满', '芒种', '夏至', '小暑', '大暑', '立秋', '处暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪', '冬至', '小寒', '大寒', '端午', '中秋', '重阳', '除夕', '元宵', '腊八', '小年', '元旦', '七夕'],
    '羁旅思乡与行吟纪游': ['游', '行', '旅', '归', '乡', '思', '忆', '梦', '寄', '望', '别', '新疆', '天山', '青岛', '威海', '京城', '故里', '石门', '唐山', '古冶', '廉州', '旅途', '途中', '路上', '出游', '游记', '动车', '飞行'],
    '感怀人生与自省述志': ['人生', '岁', '老', '病', '伤', '悲', '愁', '苦', '乐', '喜', '欢', '笑', '叹', '悟', '感', '怀', '抒怀', '遣怀', '感怀', '偶感', '偶成', '自嘲', '无题', '闲吟', '随笔', '遣兴', '述怀', '寄怀'],
    '咏物寄意与比兴抒怀': ['咏', '赞', '颂', '松', '竹', '菊', '牡丹', '石榴', '银杏', '芦花', '柳', '蝉', '雁', '鹰', '燕', '月季', '海棠', '兰', '桃', '杏', '荷', '莲', '桂'],
    '怀古咏史与读文有感': ['怀古', '咏史', '读感', '叹', '忆', '记', '祠', '庙', '故居', '草堂', '井冈山', '延安', '长征', '屈原', '李白', '杜甫', '苏轼', '诸葛', '曹操', '岳飞'],
    '节日庆典与民俗风情': ['春节', '过年', '除夕', '元旦', '元宵', '清明', '端午', '中秋', '重阳', '腊八', '小年', '生日', '寿辰', '婚', '满月', '百岁', '周岁', '钻婚', '庆典', '开市', '庙会', '灯会'],
    '唱和应酬与赠友之作': ['和', '步韵', '次韵', '赠', '答', '酬', '寄', '呈', '贺', '祝', '题', '赠友', '寄友', '贺友', '和诗'],
}

COMPARE_PROMPT = """你是一位精通中国古典诗词的资深鉴赏家。请比较以下两首诗词，判断哪一首在整体质量上更优。

评判标准：
1. 意境：画面感是否鲜明，情感是否真挚，是否有余韵
2. 文词：用词是否精准雅致，是否流畅自然
3. 韵律：平仄、押韵是否工整，节奏是否和谐
4. 儒雅：格调是否高雅，是否脱俗

诗词A：
标题：{title_a}
正文：{body_a}

诗词B：
标题：{title_b}
正文：{body_b}

请只回答"A"或"B"，表示你认为更好的那首。如果实在难分高下，回答"平"。"""

# ============================================================
# 主题分类
# ============================================================
def classify_themes(text):
    matched = []
    for theme, keywords in KEYWORDS_MAP.items():
        for kw in keywords:
            if kw in text:
                matched.append(theme)
                break
    if not matched:
        matched.append('感怀人生与自省述志')
    return matched

def get_category(themes):
    """把主题列表归并为写景/抒情/其他"""
    categories = set()
    for t in themes:
        cat = THEME_TO_CATEGORY.get(t)
        if cat:
            categories.add(cat)
    if '写景' in categories:
        return '写景'
    if '抒情' in categories:
        return '抒情'
    return '其他'

# ============================================================
# 诗词解析
# ============================================================
def parse_poems(filepath):
    poems = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = content.split('----------------------------------------')
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        poem_id = ''
        for line in lines:
            m = re.search(r'诗词(\d+)', line)
            if m:
                poem_id = m.group(1)
                break
        if not poem_id:
            continue
        title = ''
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == '冰雪' and i > 0:
                prev = lines[i-1].strip()
                if prev and not prev.startswith('微博ID') and '诗词' not in prev:
                    title = prev
                break
        if not title:
            for line in lines:
                stripped = line.strip()
                if '·' in stripped and not stripped.startswith('微博ID') and '诗词' not in stripped:
                    title = stripped
                    break
        genre = ''
        if '·' in title:
            genre = title.split('·')[0].strip()
        if not genre:
            genre = title
        date = ''
        for line in lines:
            m = re.search(r'(\d{4}\.\d{2}\.\d{2})', line)
            if m:
                date = m.group(1)
                break
        body_lines = []
        found_author = False
        found_date = False
        for line in lines:
            stripped = line.strip()
            if stripped == '冰雪':
                found_author = True
                continue
            if found_author and not found_date:
                if re.match(r'\d{4}\.\d{2}\.\d{2}', stripped):
                    found_date = True
                continue
            if found_date and stripped:
                if not stripped.startswith('图片') and stripped != '(无配图)':
                    body_lines.append(stripped)
        body = '\n'.join(body_lines)
        themes = classify_themes(title + ' ' + body)
        category = get_category(themes)
        poems.append({
            'poem_id': poem_id,
            'title': title,
            'genre': genre,
            'date': date,
            'body': body,
            'themes': themes,
            'category': category
        })
    return poems

def build_groups(poems):
    """构建分组：标准体裁按大类细分，其他体裁整体"""
    groups = {}
    # 四种标准体裁：按体裁+大类
    for g in STANDARD_GENRES:
        for cat in ['写景', '抒情', '其他']:
            groups[f'{g}|{cat}'] = []
    # 20 种词牌
    for cp in TOP20_CIPAI:
        groups[f'词牌|{cp}'] = []
    # 其他词牌
    groups['词牌|其他词牌'] = []

    for poem in poems:
        genre = poem['genre']
        cat = poem['category']
        if genre in STANDARD_GENRES:
            groups[f'{genre}|{cat}'].append(poem)
        elif genre in TOP20_CIPAI:
            groups[f'词牌|{genre}'].append(poem)
        else:
            groups['词牌|其他词牌'].append(poem)

    # 去掉空组
    return {k: v for k, v in groups.items() if len(v) > 0}

# ============================================================
# 缓存管理
# ============================================================
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

# ============================================================
# API 调用
# ============================================================
def call_deepseek(prompt):
    for attempt in range(3):
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0,
                    'max_tokens': 10
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                print(f"    速率限制，等待 {10*(attempt+1)} 秒...")
                time.sleep(10 * (attempt + 1))
            else:
                print(f"    API错误 {response.status_code}")
                time.sleep(3)
        except Exception as e:
            print(f"    网络错误: {e}")
            if attempt < 2:
                time.sleep(3)
    return None

def parse_response(text):
    if not text:
        return '平'
    text = text.strip()
    if '平' in text or '难分' in text:
        return '平'
    has_a = text.startswith('A') or '选A' in text or '选 A' in text
    has_b = text.startswith('B') or '选B' in text or '选 B' in text
    if has_a and not has_b:
        return 'A'
    if has_b and not has_a:
        return 'B'
    return '平'

def compare_poems(poem_a, poem_b, cache):
    key = '|'.join(sorted([poem_a['poem_id'], poem_b['poem_id']]))
    if key in cache:
        return cache[key]
    prompt = COMPARE_PROMPT.format(
        title_a=poem_a['title'],
        body_a=poem_a['body'],
        title_b=poem_b['title'],
        body_b=poem_b['body']
    )
    answer = call_deepseek(prompt)
    judgment = parse_response(answer) if answer else '平'
    cache[key] = judgment
    save_cache(cache)
    time.sleep(0.3)
    return judgment

# ============================================================
# 淘汰赛
# ============================================================
def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def sort_group(poems, cache, group_name):
    n = len(poems)
    if n <= 1:
        return poems[:]
    wins = [0] * n
    total = n * (n - 1) // 2
    done = 0
    for i in range(n):
        for j in range(i+1, n):
            result = compare_poems(poems[i], poems[j], cache)
            if result == 'A':
                wins[i] += 1
            elif result == 'B':
                wins[j] += 1
            else:
                wins[i] += 0.5
                wins[j] += 0.5
            done += 1
            if done % 10 == 0:
                print(f"      进度 {done}/{total}", end='\r')
    print(f"      完成 {total}/{total}      ")
    ranked = sorted(zip(poems, wins), key=lambda x: -x[1])
    return [p for p, w in ranked]

def run_tournament(pool, target, cache, group_name):
    round_num = 0
    while len(pool) > target * 1.3:
        round_num += 1
        groups = chunk(pool, 10)
        total_keep = max(target, int(len(pool) * 0.55))
        keep_per_group = max(2, total_keep // len(groups))
        print(f"    第{round_num}轮：{len(pool)}首 → {len(groups)}组，每组留{keep_per_group}首")
        new_pool = []
        for g in groups:
            ranked = sort_group(g, cache, group_name)
            new_pool.extend(ranked[:keep_per_group])
        pool = new_pool

    if len(pool) > target:
        groups = chunk(pool, 10)
        keep_per_group = max(2, -(-target // len(groups)))
        print(f"    最终轮：{len(pool)}首 → {len(groups)}组，每组留{keep_per_group}首")
        new_pool = []
        for g in groups:
            ranked = sort_group(g, cache, group_name)
            new_pool.extend(ranked[:keep_per_group])
        pool = new_pool

    return pool[:target]

# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 60)
    print("  冰雪诗词 · 诗词优选排序（A3 方案 · 分类版）")
    print("=" * 60)

    if not DEEPSEEK_API_KEY:
        print("❌ 未设置 DEEPSEEK_API_KEY 环境变量")
        input("按回车退出...")
        return

    if not os.path.exists(POEM_FILE):
        print(f"❌ 找不到诗词文件：{POEM_FILE}")
        input("按回车退出...")
        return

    print("\n📖 正在解析诗词文件...")
    poems = parse_poems(POEM_FILE)
    print(f"✅ 解析完成：共 {len(poems)} 首诗词")

    groups = build_groups(poems)
    print(f"\n📊 分组情况（共 {len(groups)} 组）：")
    for name, plist in sorted(groups.items()):
        target = max(math.ceil(len(plist) * 0.1), 5)
        target = min(target, len(plist))
        print(f"  {name}: {len(plist)} 首 → 目标 {target} 首")

    cache = load_cache()
    print(f"\n💾 已加载 {len(cache)} 条比较缓存")

    results = {}
    for group_name, plist in sorted(groups.items()):
        target = max(math.ceil(len(plist) * 0.1), 5)
        target = min(target, len(plist))
        print(f"\n🏁 开始排序：{group_name}（{len(plist)} 首，目标 {target} 首）")
        ranked = run_tournament(plist, target, cache, group_name)
        results[group_name] = [p['poem_id'] for p in ranked]
        print(f"✅ {group_name} 完成，选出 {len(ranked)} 首")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 全部完成！结果已保存到 {OUTPUT_FILE}")
    print(f"💾 比较缓存已保存到 {CACHE_FILE}")
    input("按回车退出...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断。缓存已保存，下次运行可继续。")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")