#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 data_poems.js - 供诗词优选独立页面使用
"""

import os
import re
import json

POEM_FILE = '冰雪诗词_规范格式.txt'
OUTPUT_FILE = 'data_poems.js'


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

        # 配图
        image_matches = re.findall(r'图片[一二三四五六七八九十\d]', block)
        image_files = [f'{i+1:02d}.jpg' for i in range(len(image_matches))]

        poems.append({
            'poem_id': poem_id,
            'title': title,
            'genre': genre,
            'date': date,
            'body': body,
            'image_files': image_files
        })
    return poems


def main():
    print("=" * 60)
    print("  生成 data_poems.js")
    print("=" * 60)

    if not os.path.exists(POEM_FILE):
        print(f"❌ 找不到诗词文件：{POEM_FILE}")
        input("按回车退出...")
        return

    print("\n📖 正在解析诗词文件...")
    poems = parse_poems(POEM_FILE)
    print(f"✅ 解析完成：共 {len(poems)} 首诗词")

    # 生成 JS 文件
    js_content = 'const POEMS_DATA = ' + json.dumps(poems, ensure_ascii=False) + ';'
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"\n✅ 已生成：{OUTPUT_FILE}")
    print(f"   文件大小约 {os.path.getsize(OUTPUT_FILE) // 1024} KB")
    input("\n按回车退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")