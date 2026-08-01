#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冰雪诗词数字图书馆 - 最终完美版
彻底修复图片显示问题：直接根据正文中的“图片X”标记生成 R2 标准文件名列表
"""
import os
import re
import json
import boto3
from datetime import datetime
import html as html_mod

# ============================================================
# 配置区
# ============================================================
POEM_FILE = '冰雪诗词_规范格式.txt'
REPORT_FILE = '冰雪诗词全集_分析评价报告.txt'
IMAGE_DIR = '冰雪诗词_全部图片'
OUTPUT_HTML = 'index.html'
R2_BASE = 'https://pub-1f89bdd823e748d3b468bb1566f0c2a5.r2.dev'
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL', '')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'poem-audio-cache')

GENRES = ['五绝', '五律', '七绝', '七律', '词牌诗词']
THEMES = [
    '家国情怀与时代歌咏', '山水田园与闲居雅趣', '亲情友情与人间至爱',
    '四时风光与节气流转', '羁旅思乡与行吟纪游', '感怀人生与自省述志',
    '咏物寄意与比兴抒怀', '怀古咏史与读文有感', '节日庆典与民俗风情',
    '唱和应酬与赠友之作'
]

FRIENDLY_LINKS = [
    {'name': '搜韵', 'url': 'https://sou-yun.cn/'},
    {'name': '诗词吾爱', 'url': 'https://www.52shici.com/'},
    {'name': '古诗词网', 'url': 'https://www.gushiwen.cn/'},
    {'name': '微信公众号', 'type': 'qrcode', 'img': 'gzh_qr.jpg'},
    {'name': '抖音视频', 'type': 'qrcode', 'img': 'douyin_qr.jpg'},
]

# ============================================================
# 诗词解析（核心修复：不再依赖本地文件夹，直接解析正文标记）
# ============================================================
def parse_poems(filepath, image_dir):
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
                # 如果 genre 为空，检查是否属于标准体裁
        if not genre:
            if title in ['五绝', '五律', '七绝', '七律']:
                genre = title
            else:
                # 不是标准体裁，也不是有“·”的，则保留标题作为词牌名
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
                # 过滤掉“图片X”这类标记，防止它们混入正文
                if not stripped.startswith('图片') and stripped != '(无配图)':
                    body_lines.append(stripped)
        body = '\n'.join(body_lines)
        themes = classify_themes(title + ' ' + body)

                # ★★★ 核心修复：直接对原始的 block 进行查找，防止“图片1”在正文被过滤 ★★★
        image_matches = re.findall(r'图片[一二三四五六七八九十\d]', block)
        image_files = [f'{i+1:02d}.jpg' for i in range(len(image_matches))]
        # ================================================================

        poems.append({
            'poem_id': poem_id,
            'title': title,
            'genre': genre,
            'date': date,
            'body': body,
            'themes': themes,
            'image_files': image_files  # 直接传入标准文件名列表
        })
    return poems

def classify_themes(text):
    keywords_map = {
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
    matched = []
    for theme, keywords in keywords_map.items():
        for kw in keywords:
            if kw in text:
                matched.append(theme)
                break
    if not matched:
        matched.append('感怀人生与自省述志')
    return matched

def load_report(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "暂无分析报告。"

# ===== 扫描 R2 视频目录（供统一播放器使用） =====
def scan_r2_directory(prefix):
    """扫描 R2 指定前缀，返回文件名列表"""
    files = []
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        resp = s3.list_objects_v2(Bucket=R2_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                key = obj['Key']
                fname = key.split('/')[-1]
                if fname and fname.lower().endswith(('.mp4', '.webm', '.mkv', '.mov')):
                    files.append(fname)
        print(f"✅ 扫描 {prefix} 完成，发现 {len(files)} 个视频")
    except Exception as e:
        print(f"⚠️ 扫描 {prefix} 失败: {e}")
    return files

# ============================================================
# HTML生成
# ============================================================
def generate_html(poems, report_text):
    
    # ===== 公共变量序列化 =====
    poems_json = json.dumps(poems, ensure_ascii=True)
    report_text_escaped = html_mod.escape(report_text)
    report_escaped = json.dumps(report_text_escaped, ensure_ascii=True)
    links_json = json.dumps(FRIENDLY_LINKS, ensure_ascii=True)
    genres_json = json.dumps(GENRES, ensure_ascii=True)
    themes_json = json.dumps(THEMES, ensure_ascii=True)
    r2_base = R2_BASE

    # ===== 新增：读取使用说明（独立生成 manual_escaped） =====
    manual_text = "（暂无使用说明文件，请检查同级目录下的 使用说明.txt）"
    manual_file = '使用说明.txt'
    if os.path.exists(manual_file):
        try:
            with open(manual_file, 'r', encoding='utf-8') as f:
                manual_text = f.read()
        except Exception as e:
            print(f"⚠️ 读取使用说明失败：{e}")
    manual_escaped = json.dumps(manual_text, ensure_ascii=True)
    # ===== 新增：扫描健身视频（独立生成 fitness_json） =====
    fitness_videos = []
    try:
        import boto3
        s3_check = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        resp = s3_check.list_objects_v2(Bucket=R2_BUCKET_NAME, Prefix='fitness/')
        if 'Contents' in resp:
            for obj in resp['Contents']:
                key = obj['Key']
                fname = key.split('/')[-1]
                if fname and fname.lower().endswith(('.mp4', '.webm', '.mkv', '.mov')):
                    fitness_videos.append(fname)
        print(f"✅ 扫描到健身视频：{len(fitness_videos)} 个")
    except Exception as e:
        print(f"⚠️ 扫描健身视频目录失败（不影响主体功能）：{e}")
    fitness_json = json.dumps(fitness_videos, ensure_ascii=True)
    # ===== 新增：将爷孙诗语视频列表也一并注入 =====
    video_files = scan_r2_directory('videos/')   # 复用扫描函数
    video_files_json = json.dumps(video_files, ensure_ascii=True)
    # ===== 此后才是拼接 HTML 的长字符串 =====
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
<title>冰雪诗词 · 数字图书馆</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "楷体", KaiTi, serif; background: #e8f0e3; color: #2c2c2c; display: flex; flex-direction: column; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #2e7d32, #1b5e20); color: #f0f7e6; padding: 10px 20px; display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; }}
.header h1 {{ font-size: 1.6em; letter-spacing: 6px; font-weight: normal; text-align: center; }}
.header-info {{ display: flex; align-items: center; gap: 8px; font-size: 0.8em; opacity: 0.95; flex-wrap: wrap; justify-content: center; }}
.header-info p {{ margin: 0; line-height: 1.4; text-align: center; }}
.header-info .detail-link {{ color: #fdd835; cursor: pointer; text-decoration: none; font-weight: bold; }}

.main {{ display: flex; flex: 1; }}

.left-panel {{ width: 120px; background: #fce4e4; display: flex; flex-direction: column; flex-shrink: 0; border-right: 2px solid #f0c0c0; }}
.left-panel .panel-title {{ background: #f8d0d0; color: #a33; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; text-align: center; font-weight: bold; cursor: pointer; }}
.right-panel {{ width: 120px; background: #e4ecfc; display: flex; flex-direction: column; flex-shrink: 0; border-left: 2px solid #c0c8f0; }}
.right-panel .panel-title {{ background: #d0d8f8; color: #36c; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; text-align: center; font-weight: bold; cursor: pointer; }}
.center-panel {{ width: 120px; display: flex; flex-direction: column; flex-shrink: 0; border-left: 2px solid #f0e0a0; border-right: 2px solid #f0e0a0; background: #fef9e7; }}
.center-panel .panel-title {{ background: #fef0c0; color: #a80; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; text-align: center; font-weight: bold; }}

.left-menu, .right-menu {{ flex: 1; overflow-y: auto; padding: 0; }}
.center-buttons {{ flex: 1; display: flex; flex-direction: column; gap: 5px; align-items: center; padding: 8px; overflow-y: auto; position: relative; }}

.menu-title {{ padding: 6px 8px; cursor: pointer; font-size: 0.78em; letter-spacing: 1px; transition: 0.2s; border-radius: 3px; margin: 0 4px; background: #f8d0d0; color: #a33; text-align: center; font-weight: bold; }}
.menu-title:hover {{ background: #f0b0b0; }}
.menu-title.active {{ background: #e8a0a0 !important; color: #722 !important; box-shadow: inset 0 0 0 2px #a33; }}
.right-panel .menu-title {{ background: #d0d8f8; color: #36c; }}
.right-panel .menu-title:hover {{ background: #b8c8f0; }}
.right-panel .menu-title.active {{ background: #a0b8e8 !important; color: #148 !important; box-shadow: inset 0 0 0 2px #36c; }}

.submenu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; background: #fdf0f0; margin: 0 4px; border-radius: 0 0 3px 3px; }}
.right-panel .submenu {{ background: #f0f4fd; }}
.submenu.open {{ max-height: 300px; }}
.submenu a {{ display: inline-block; padding: 5px 6px; color: #6b5050; text-decoration: none; font-size: 0.7em; letter-spacing: 1px; cursor: pointer; border-radius: 2px; margin: 1px 2px; background: #fef6f6; white-space: nowrap; }}
.right-panel .submenu a {{ color: #505a6b; background: #f8fafe; }}
.submenu a:hover {{ background: #f0d0d0; }}
.right-panel .submenu a:hover {{ background: #c8d8f0; }}
.submenu a.active {{ background: #e8c0c0 !important; color: #522 !important; font-weight: bold; }}
.right-panel .submenu a.active {{ background: #a0b8e0 !important; color: #124 !important; font-weight: bold; }}

.center-buttons button {{ width: 105px; padding: 6px 4px; background: #4caf50; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75em; letter-spacing: 1px; transition: 0.2s; }}
.center-buttons button:hover {{ background: #388e3c; }}
.links-wrapper {{ position: relative; width: 105px; }}
.links-wrapper > button {{ width: 100%; }}
.links-submenu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; background: #e8f5e9; border-radius: 0 0 4px 4px; position: absolute; top: 100%; left: 0; width: 100%; z-index: 10; }}
.links-submenu.open {{ max-height: 300px; }}
.links-submenu a {{ display: block; padding: 6px 12px; color: #2c3e50; text-decoration: none; font-size: 0.75em; letter-spacing: 1px; border-bottom: 1px solid #c8e6c9; }}
.links-submenu a:hover {{ background: #c8e6c9; }}

.content {{ flex: 1; padding: 15px 25px; overflow-y: auto; background: #f5fbe8; }}

.poem-card {{ background: #fffef9; border-radius: 8px; padding: 20px 24px; margin-bottom: 22px; box-shadow: 0 1px 8px rgba(0,0,0,0.05); border-left: 3px solid #8bc34a; overflow: auto; position: relative; }}
.poem-title {{ color: #2e7d32; font-size: 1.15em; margin-bottom: 6px; font-weight: normal; letter-spacing: 2px; text-align: left; }}
.poem-author {{ font-size: 0.95em; color: #4a5568; margin-bottom: 2px; letter-spacing: 2px; text-align: left; }}
.poem-date {{ font-size: 0.85em; color: #6b7b8d; margin-bottom: 10px; letter-spacing: 1px; text-align: left; }}
.poem-body {{ font-size: 1.1em; line-height: 2.1; white-space: pre-wrap; font-family: "楷体", KaiTi, serif; margin-top: 0; overflow: auto; }}

.history-intro {{ background: linear-gradient(135deg, #fef9e7, #fefce8); padding: 14px 20px; border-radius: 8px; margin-bottom: 15px; border: 2px dashed #d4a853; text-align: center; }}
.history-intro p {{ color: #a08030; font-size: 1em; letter-spacing: 2px; }}

.poem-img-float {{ float: right; width: 280px; max-height: 420px; overflow-y: auto; margin-left: 16px; margin-bottom: 8px; padding: 4px; background: #fafaf5; border-radius: 6px; border: 1px solid #e8e0d0; clear: none; }}
.poem-img-float img {{ width: 100%; max-height: 200px; object-fit: scale-down; border-radius: 4px; margin-bottom: 6px; border: 1px solid #e0d5c1; cursor: pointer; display: block; }}
.poem-img-float img:last-child {{ margin-bottom: 0; }}
.poem-img-float.single-img img {{ max-height: none; }}
.poem-img-float.single-img {{ max-height: none; overflow-y: visible; }}

.img-toggle-btn, .edit-btn, .comment-btn {{ display: inline-block; margin-top: 8px; margin-right: 8px; padding: 5px 0; background: #8bc34a; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; letter-spacing: 1px; text-align: center; }}
.edit-btn, .comment-btn {{ background: #f0ad4e; }}
.edit-btn:hover, .comment-btn:hover {{ background: #ec971f; }}
.img-toggle-btn {{ background: #8bc34a; width: 6em; max-width: 6em; }}
.edit-btn, .comment-btn {{ width: 3em; }}
.share-btn {{ width: 3em; }}
.btn-recite {{ background: #8bc34a; color: #fff; padding: 5px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; letter-spacing: 1px; }}
.btn-recite:hover {{ background: #689f38; }}
.btn-analyze {{ background: #5b8db8; color: #fff; padding: 5px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; letter-spacing: 1px; }}
.btn-analyze:hover {{ background: #3a6d96; }}
.button-group {{ margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
.poem-comment-area {{ margin-top: 12px; padding-top: 8px; border-top: 1px dashed #e0d5c8; display: none; }}
.poem-comment-area.active {{ display: block; }}

.back-to-top {{ display: none; position: fixed; bottom: 30px; right: 30px; width: 44px; height: 44px; background: #4caf50; color: #fff; border: none; border-radius: 50%; font-size: 1.2em; cursor: pointer; z-index: 998; box-shadow: 0 2px 10px rgba(0,0,0,0.2); transition: 0.3s; }}
.back-to-top:hover {{ background: #388e3c; }}

.modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.15); z-index: 999; justify-content: center; align-items: center; }}
.modal.active {{ display: flex; }}

.report-modal-content {{ background: #fefefe; margin: 30px auto; padding: 30px; width: 50%; min-width: 500px; max-height: 80vh; overflow-y: auto; border-radius: 8px; white-space: pre-wrap; font-size: 0.9em; line-height: 1.8; position: relative; }}

.search-modal-content {{ background: #fefefe; position: absolute; top: 40px; left: 3%; width: 15%; min-width: 300px; max-height: 85vh; overflow-y: auto; border-radius: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.3); cursor: default; }}
.search-modal-header {{ cursor: move; background: #4caf50; color: #fff; padding: 10px 16px; margin: 0 0 14px 0; border-radius: 8px 8px 0 0; font-size: 1em; letter-spacing: 2px; user-select: none; }}
.search-modal-header .modal-close {{ float: right; cursor: pointer; color: #fff; font-size: 22px; }}
.search-row {{ margin-bottom: 10px; padding: 0 10px; }}
.search-row .hint {{ font-size: 0.75em; color: #888; margin-bottom: 3px; padding-left: 4px; }}
.search-row input {{ padding: 7px 10px; width: 100%; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; }}
.search-row input.short {{ width: 47%; display: inline-block; }}
.search-row .between {{ margin: 0 3%; }}
.search-row select {{ padding: 7px 10px; width: 60%; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; background: #fff; }}
.search-row .ci-pai-input {{ display: none; width: 35%; margin-left: 8px; padding: 7px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; }}
.search-row .ci-pai-select {{
    width: 60%;
    padding: 7px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9em;
    display: none;
}}
.search-row .ci-pai-select:focus {{
    border-color: #4caf50;
    outline: none;
}}
.search-btn {{ padding: 8px 24px; background: #4caf50; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.95em; letter-spacing: 2px; margin-left: 10px; }}
.search-btn:hover {{ background: #388e3c; }}

.guestbook-modal-content {{ background: #fefefe; margin: 30px auto; padding: 24px; width: 50%; max-width: 600px; max-height: 80vh; overflow-y: auto; border-radius: 8px; position: relative; }}
.guestbook-modal-content .modal-close {{ position: absolute; top: 12px; right: 18px; font-size: 1.8em; cursor: pointer; color: #999; background: none; border: none; line-height: 1; }}
.guestbook-modal-content .modal-close:hover {{ color: #333; }}
.guestbook-modal-content h3 {{ color: #2e7d32; margin-bottom: 16px; letter-spacing: 2px; }}

#aiPoemModal .guestbook-modal-content {{ background: #fce4e4; border-radius: 16px; padding: 20px 24px; width: 50%; max-width: 550px; max-height: 85vh; overflow-y: auto; border: 1px solid #f0d0d0; position: relative; }}
#aiPoemModal .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 1px solid #e8c8c8; }}
#aiPoemModal .modal-header h3 {{ font-size: 1.1rem; font-weight: normal; color: #a33; margin: 0; }}
#aiPoemModal .modal-header .modal-close {{ font-size: 1.4rem; cursor: pointer; color: #c66; line-height: 1; }}
#aiPoemModal .modal-header .modal-close:hover {{ color: #a33; }}
#aiPoemModal .compact-row {{ display: flex; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }}
#aiPoemModal .compact-row .label {{ width: 60px; flex-shrink: 0; font-weight: bold; font-size: 0.9rem; color: #a33; }}
#aiPoemModal .compact-row .control {{ flex: 1; }}
#aiPoemModal .compact-row select,
#aiPoemModal .compact-row input {{ width: 100%; padding: 8px 10px; border: 1px solid #e0c0c0; border-radius: 8px; font-size: 0.9rem; background: #fffef9; }}
#aiPoemModal .two-cols {{ display: flex; gap: 20px; margin-bottom: 16px; }}
#aiPoemModal .two-cols .compact-row {{ flex: 1; margin-bottom: 0; }}
#aiPoemModal .ci-pai-group {{ margin-bottom: 16px; }}
#aiPoemModal .prompt-section {{ display: flex; flex-wrap: wrap; margin-bottom: 8px; }}
#aiPoemModal .prompt-label {{ width: 60px; flex-shrink: 0; padding-top: 8px; font-weight: bold; font-size: 0.9rem; color: #a33; }}
#aiPoemModal .prompt-textarea {{ flex: 1; }}
#aiPoemModal .prompt-textarea textarea {{ width: 100%; padding: 8px 10px; border: 1px solid #e0c0c0; border-radius: 8px; font-size: 0.9rem; resize: vertical; height: 110px; background: #fffef9; }}
#aiPoemModal .button-row {{ margin-top: 4px; margin-bottom: 20px; padding-left: 60px; }}
#aiPoemModal .generate-btn {{ background-color: #a33; color: white; border: none; padding: 8px 20px; border-radius: 30px; font-size: 0.9rem; cursor: pointer; transition: background 0.2s; }}
#aiPoemModal .generate-btn:hover {{ background-color: #722; }}
#aiPoemModal .ai-poem-result {{ background: #fff8f0; border-radius: 12px; padding: 14px; margin-top: 8px; border: 1px solid #e8d0d0; font-size: 0.9rem; line-height: 1.65; white-space: pre-wrap; max-height: 260px; overflow-y: auto; display: none; }}
#aiPoemModal .ai-poem-result.show {{ display: block; }}
#aiPoemModal .copy-btn {{ background: #c96; color: #fff; border: none; padding: 5px 14px; border-radius: 20px; font-size: 0.75rem; margin-top: 10px; cursor: pointer; }}

.recite-player-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 2000; justify-content: center; align-items: center; padding: 20px; }}
.recite-player-overlay.active {{ display: flex; }}
.recite-player {{ background: #fffef9; border-radius: 16px; padding: 20px 24px; width: 92%; max-width: 700px; max-height: 85vh; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 10px 50px rgba(0,0,0,0.4); cursor: move; }}
.recite-player .player-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0; cursor: move; }}
.recite-player .player-header h3 {{ color: #2e7d32; font-size: 1.1em; letter-spacing: 2px; }}
.recite-player .player-header .close-btn {{ font-size: 1.6em; cursor: pointer; color: #888; background: none; border: none; line-height: 1; }}
.recite-player .player-header .close-btn:hover {{ color: #333; }}
.recite-player .player-content {{ flex: 1; overflow-y: auto; padding-right: 4px; }}
.recite-player .player-content .poem-text {{ white-space: pre-wrap; line-height: 2; font-family: "楷体", KaiTi, serif; font-size: 1.05em; color: #2c2c2c; }}
.recite-player .player-content .analysis-text {{ white-space: pre-wrap; line-height: 1.8; font-family: "楷体", KaiTi, serif; font-size: 0.95em; color: #4a5568; margin-top: 12px; padding-top: 12px; border-top: 1px dashed #e0d5c8; display: none; }}
.recite-player .player-content .analysis-text.show {{ display: block; }}
.recite-player .player-content .status-label {{ font-size: 0.8em; color: #888; margin-top: 4px; }}
.recite-player .player-controls {{ display: flex; align-items: center; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e8e0d0; flex-shrink: 0; flex-wrap: wrap; }}
.recite-player .player-controls button {{ padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; transition: 0.2s; }}
.recite-player .player-controls .ctrl-play {{ background: #4caf50; color: #fff; }}
.recite-player .player-controls .ctrl-play:hover {{ background: #388e3c; }}
.recite-player .player-controls .ctrl-play.paused {{ background: #f0ad4e; }}
.recite-player .player-controls .ctrl-play.paused:hover {{ background: #ec971f; }}
.recite-player .player-controls .ctrl-stop {{ background: #e0e0e0; color: #333; }}
.recite-player .player-controls .ctrl-stop:hover {{ background: #ccc; }}
.recite-player .player-controls .progress-bar {{ flex: 1; min-width: 100px; height: 6px; background: #e0e0e0; border-radius: 3px; position: relative; cursor: pointer; }}
.recite-player .player-controls .progress-bar .progress-fill {{ height: 100%; background: #2e7d32; border-radius: 3px; width: 0%; transition: width 0.2s; }}
.recite-player .player-controls .time-display {{ font-size: 0.8em; color: #888; min-width: 80px; text-align: center; }}
@media (max-width: 768px) {{
    .recite-player {{ padding: 14px 16px; width: 96%; max-height: 92vh; }}
    .recite-player .player-controls {{ gap: 8px; }}
    .recite-player .player-controls button {{ padding: 5px 10px; font-size: 0.8em; }}
    .recite-player .player-content .poem-text {{ font-size: 0.95em; }}
}}

.analysis-modal-content {{ background: #fffef9; margin: 0; padding: 28px 32px; width: 50%; max-width: 700px; max-height: 80vh; overflow-y: auto; border-radius: 12px; position: relative; box-shadow: 0 10px 40px rgba(0,0,0,0.3); cursor: move; }}
.analysis-modal-content .modal-close {{ position: absolute; top: 12px; right: 18px; font-size: 1.8em; cursor: pointer; color: #999; background: none; border: none; line-height: 1; }}
.analysis-modal-content .modal-close:hover {{ color: #333; }}
.analysis-modal-content h3 {{ color: #2e7d32; margin-bottom: 16px; letter-spacing: 2px; }}
.analysis-modal-content .analysis-text {{ white-space: pre-wrap; line-height: 1.8; font-family: "楷体", KaiTi, serif; font-size: 0.95em; color: #2c2c2c; }}

.video-gallery-modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1100; justify-content: center; align-items: center; padding: 20px; }}
.video-gallery-modal.active {{ display: flex; }}
.video-gallery-content {{ background: #f5fbe8; border-radius: 16px; padding: 20px 24px; width: 92%; max-width: 900px; max-height: 90vh; overflow-y: auto; position: relative; box-shadow: 0 10px 50px rgba(0,0,0,0.5); }}
.video-gallery-content .close-btn {{ position: sticky; top: 0; float: right; font-size: 1.8em; cursor: pointer; color: #888; background: #f5fbe8; border: none; padding: 0 8px; z-index: 10; }}
.video-gallery-content .close-btn:hover {{ color: #333; }}
.video-gallery-content h2 {{ color: #2e7d32; margin-bottom: 12px; letter-spacing: 3px; }}
.video-gallery-content .video-controls {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; align-items: center; }}
.video-gallery-content .video-controls button {{ padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; }}
.video-gallery-content .video-controls .btn-play {{ background: #4caf50; color: #fff; }}
.video-gallery-content .video-controls .btn-play:hover {{ background: #388e3c; }}
.video-gallery-content .video-controls .btn-random {{ background: #f0ad4e; color: #fff; }}
.video-gallery-content .video-controls .btn-random:hover {{ background: #ec971f; }}
.video-gallery-content .video-controls .btn-stop {{ background: #e0e0e0; color: #333; }}
.video-gallery-content .video-controls .btn-stop:hover {{ background: #ccc; }}
.video-gallery-content .video-controls input {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85em; width: 80px; }}
.video-gallery-content .video-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; margin-bottom: 12px; max-height: 200px; overflow-y: auto; }}
.video-gallery-content .video-list .v-item {{ padding: 6px 10px; background: #fffef9; border-radius: 4px; cursor: pointer; font-size: 0.85em; border: 1px solid #e0d5c1; text-align: center; transition: 0.2s; }}
.video-gallery-content .video-list .v-item:hover {{ background: #e8f5e9; border-color: #8bc34a; }}
.video-gallery-content .video-list .v-item.active {{ background: #8bc34a; color: #fff; border-color: #8bc34a; }}
.video-gallery-content .video-player-area {{ background: #1a1a2e; border-radius: 8px; padding: 10px; min-height: 300px; display: flex; align-items: center; justify-content: center; }}
.video-gallery-content .video-player-area video {{ width: 100%; max-height: 60vh; border-radius: 4px; }}
.video-gallery-content .video-player-area .placeholder {{ color: #888; font-size: 1em; }}
.video-gallery-content .video-status {{ margin-top: 8px; font-size: 0.85em; color: #888; text-align: center; }}

.footer {{ background: #1b5e20; color: #c8e6c9; text-align: center; padding: 10px; font-size: 0.8em; letter-spacing: 1px; flex-shrink: 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 20px; }}
.footer .counter {{ font-size: 0.9em; }}
.footer .qrcode-container img {{ width: 80px; height: 80px; border-radius: 4px; }}

#guestbookModal .guestbook-modal-content {{ background: #fef9e7; }}
.tk-preview {{ display: none !important; }}
.tk-footer a {{ pointer-events: none; color: inherit !important; text-decoration: none !important; }}
.tk-submit-action-icon, .OwO, .OwO-logo, [class*="OwO"], .tk-upload-btn, [class*="upload"] {{ display: none !important; }}

.custom-edit-modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 10000; }}
.custom-edit-content {{ background: #fffef9; border-radius: 16px; padding: 20px; width: 90%; max-width: 500px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
.custom-edit-content textarea {{ width: 100%; height: 200px; padding: 12px; font-size: 1rem; line-height: 1.6; font-family: "楷体", KaiTi, serif; border: 1px solid #d0c0a0; border-radius: 8px; resize: vertical; }}
.custom-edit-content .btn-group {{ display: flex; gap: 12px; justify-content: flex-end; margin-top: 16px; }}
.custom-edit-content button {{ padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }}
.custom-edit-content .save-btn {{ background: #4caf50; color: white; }}
.custom-edit-content .cancel-btn {{ background: #ccc; color: #333; }}

@media screen and (max-width: 1024px) {{
    body {{ min-height: 100vh; height: auto; overflow-x: hidden; overflow-y: auto; -webkit-overflow-scrolling: touch; font-size: 16px; }}
    .header {{ padding: 8px 12px; gap: 4px; }}
    .header h1 {{ font-size: 1.2em; letter-spacing: 3px; }}
    .header-info {{ font-size: 0.7em; flex-wrap: wrap; justify-content: center; text-align: center; }}
    .main {{ flex-direction: column; flex: none; width: 100%; }}
    .left-panel, .center-panel, .right-panel {{ width: 100%; max-height: none; border: none; flex-shrink: 0; flex: none; padding: 4px 0; }}
    .left-panel {{ border-bottom: 1px solid #f0c0c0; }}
    .right-panel {{ border-bottom: 1px solid #c0c8f0; }}
    .center-panel {{ border-bottom: 1px solid #f0e0a0; }}
    .left-panel .panel-title, .right-panel .panel-title, .center-panel .panel-title {{ font-size: 0.85em; padding: 8px 0; cursor: pointer; user-select: none; }}
    .left-menu, .right-menu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; position: relative; }}
    .left-menu.open, .right-menu.open {{ max-height: 800px; }}
    .left-panel .panel-title::after {{ content: ' ▼'; font-size: 0.6em; }}
    .right-panel .panel-title::after {{ content: ' ▼'; font-size: 0.6em; }}
    .mobile-second-row {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 4px 6px; }}
    .mobile-second-row .menu-title {{ font-size: 0.75em; padding: 6px 4px; margin: 0; border-radius: 4px; width: calc(20% - 5px); text-align: center; display: inline-block; min-width: 50px; }}
    .mobile-theme-row {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 4px 6px; }}
    .mobile-theme-row .menu-title {{ font-size: 0.72em; padding: 5px 3px; margin: 0; border-radius: 4px; width: calc(20% - 5px); text-align: center; display: inline-block; min-width: 55px; }}
    .submenu-fixed-area {{ position: relative; min-height: 50px; }}
    .submenu {{ position: absolute; top: 0; left: 0; width: 100%; display: none; flex-wrap: wrap; gap: 3px; padding: 4px 6px; justify-content: center; background: #fdf0f0; border-radius: 0 0 3px 3px; }}
    .right-panel .submenu {{ background: #f0f4fd; }}
    .submenu.open {{ display: flex; }}
    .submenu a {{ font-size: 0.7em; padding: 4px 5px; margin: 0; white-space: nowrap; }}
    .center-buttons {{ flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 5px; padding: 6px 8px; }}
    .center-buttons button {{ width: auto; padding: 7px 10px; font-size: 0.78em; min-width: 60px; }}
    .center-buttons {{ position: relative; }}
    .links-wrapper {{ position: static; width: auto; }}
    .links-submenu {{ position: static; display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 4px; max-height: 0; overflow: hidden; background: #e8f5e9; border-radius: 4px; margin-top: 4px; transition: max-height 0.3s ease; }}
    .links-submenu.open {{ max-height: 200px; }}
    .links-submenu a {{ display: inline-block; width: auto; padding: 4px 8px; font-size: 0.7em; border: none; background: #d4e0d0; margin: 2px; }}
    .content {{ flex: none; width: 100%; padding: 8px 10px; overflow-y: visible; }}
    .poem-card {{ padding: 12px 14px; margin-bottom: 12px; }}
    .poem-title {{ font-size: 1em; }}
    .poem-author {{ font-size: 0.9em; }}
    .poem-date {{ font-size: 0.8em; }}
    .poem-body {{ font-size: 0.95em; line-height: 1.9; }}
    .poem-img-float {{ float: none; width: 100% !important; max-width: 100% !important; margin: 8px 0 !important; max-height: none !important; }}
    .poem-img-float img {{ max-height: 200px !important; }}
    .img-toggle-btn, .edit-btn, .comment-btn {{ font-size: 0.75em; }}
    .button-group {{ margin-top: 8px; }}
    .search-modal-content {{ width: 90%; left: 5%; min-width: auto; position: fixed; top: 50px; }}
    .search-row select {{ width: 80%; }}
    .search-row .ci-pai-input {{ width: 80%; margin-left: 0; margin-top: 4px; }}
    .guestbook-modal-content, .report-modal-content, .analysis-modal-content {{ width: 95%; min-width: auto; padding: 14px; margin: 15px auto; }}
    .history-intro p {{ font-size: 0.85em; }}
    .footer {{ font-size: 0.7em; padding: 8px; gap: 10px; }}
    .footer .qrcode-container img {{ width: 60px; height: 60px; }}
    .back-to-top {{ bottom: 20px; right: 20px; width: 38px; height: 38px; font-size: 1em; }}
    #aiPoemModal .guestbook-modal-content {{ width: 95% !important; max-width: 95% !important; }}
    #aiPoemModal .compact-row .label {{ width: 55px; font-size: 0.85rem; }}
    #aiPoemModal .prompt-label {{ width: 55px; font-size: 0.85rem; }}
    #aiPoemModal .button-row {{ padding-left: 55px; }}
    #aiPoemModal .two-cols {{ flex-direction: column; gap: 12px; }}
    .custom-edit-content textarea {{ height: 280px; font-size: 1rem; }}
    .modal, .recite-player-overlay {{ align-items: flex-start; padding-top: 20px; }}
    .modal-content, .recite-player, .search-modal-content, .analysis-modal-content {{ max-height: 90vh; overflow-y: auto; -webkit-overflow-scrolling: touch; }}
    input:focus, select:focus, textarea:focus {{ scrollIntoView: smooth; }}
    .recite-player .player-content {{ max-height: 50vh; }}
    .video-gallery-content {{ padding: 14px 16px; width: 96%; max-height: 95vh; }}
    .video-gallery-content .video-list {{ grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); max-height: 150px; }}
    .video-gallery-content .video-controls {{ gap: 6px; }}
    .video-gallery-content .video-controls input {{ width: 60px; }}
    .video-gallery-content .video-player-area {{ min-height: 200px; }}
    .poem-comment-area {{ max-width: 100%; overflow-x: hidden; }}
    .tk-comments {{ max-width: 100%; }}
}}

@media screen and (max-width: 480px) {{
    .header h1 {{ font-size: 1.1em; letter-spacing: 2px; }}
    .center-buttons button {{ font-size: 0.72em; padding: 6px 8px; }}
    .poem-body {{ font-size: 0.9em; }}
    #aiPoemModal .compact-row .label {{ width: 50px; font-size: 0.8rem; }}
    #aiPoemModal .prompt-label {{ width: 50px; font-size: 0.8rem; }}
    #aiPoemModal .button-row {{ padding-left: 50px; }}
    #aiPoemModal .generate-btn {{ padding: 6px 16px; font-size: 0.85rem; }}
    .custom-edit-content textarea {{ height: 320px; }}
    .video-gallery-content .video-list {{ grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); }}
}}

/* ===== 使用说明弹窗 ===== */
#manualModal .guestbook-modal-content {{
    background: #fefce8;
    max-width: 750px !important;
    border-radius: 16px;
    padding: 24px 28px;
    position: relative;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}}
#manualModal .modal-close {{
    position: absolute;
    top: 12px;
    right: 18px;
    font-size: 1.8em;
    cursor: pointer;
    color: #999;
    background: none;
    border: none;
    line-height: 1;
}}
#manualModal .modal-close:hover {{ color: #333; }}
#manualModal h3 {{ color: #2e7d32; margin-bottom: 16px; letter-spacing: 2px; }}
#manualModal .manual-content {{
    background: #fff;
    border-radius: 8px;
    padding: 16px 20px;
    max-height: 60vh;
    overflow-y: auto;
    white-space: pre-wrap;
    font-size: 0.95em;
    line-height: 1.8;
    color: #333;
    border: 1px solid #e8e0d0;
}}

/* ===== 闲来听诗全屏浮层（浅绿主题） ===== */
.fullscreen-overlay {{
    display: none;
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 2000;
    justify-content: center;
    align-items: center;
}}
.fullscreen-overlay.active {{ display: flex; }}

.fullscreen-content {{
    background: #e8f5e9; /* 浅绿背景 */
    border-radius: 12px;
    padding: 18px 22px;
    width: 92%;
    max-width: 1200px;  /* 增大窗口 */
    max-height: 98vh;
    overflow-y: auto;
    position: relative;
    box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    border: 1px solid #c8e6c9;
    display: flex; flex-direction: column; gap: 2px;
}}
.fullscreen-content .close-btn {{
    position: absolute;
    top: 10px;
    right: 16px;
    font-size: 1.5em;
    cursor: pointer;
    color: #555;
    background: none;
    border: none;
    z-index: 10;
}}
.fullscreen-content .close-btn:hover {{ color: #000; }}
.fullscreen-content h2 {{
    color: #2e7d32;
    margin: 0 0 10px 0;
    letter-spacing: 2px;
    font-size: 0.85em;
    display: inline-block;
}}

.xianlai-header-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 6px;
    align-items: center;
}}

.mode-selector {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}}
.mode-selector button {{
    padding: 3px 10px;
    border: 1px solid #a5d6a7;
    border-radius: 14px;
    background: #c8e6c9; /* 未选中浅绿 */
    cursor: pointer;
    font-size: 0.7em;
    color: #2e7d32;
    transition: 0.2s;
    white-space: nowrap;
}}
.mode-selector button:hover {{
    background: #a5d6a7;
    color: #1b5e20;
}}
.mode-selector button.active {{
    background: #388e3c; /* 选中深绿 */
    color: #fff;
    border-color: #388e3c;
}}

.mode-panel {{
    display: none; /* 关键修复：默认隐藏 */
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
    justify-content: flex-start;
    padding: 6px 10px;
    margin-bottom: 6px;
    background: #f1f8e9;
    border-radius: 6px;
}}
.mode-panel.active {{
    display: flex; /* 激活时显示为 flex 布局 */
}}
.mode-panel p {{
    color: #33691e;
    font-size: 0.8em;
    margin: 0;
    line-height: 1.4;
}}
.mode-panel.active {{ display: block; }}
.mode-panel p {{
    color: #33691e;
    font-size: 0.8em;
    margin: 0 0 6px 0;
}}

.mode-panel .sub-options {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 0;
}}
.mode-panel .sub-options button {{
    padding: 3px 10px;
    border: 1px solid #a5d6a7;
    border-radius: 4px;
    background: #c8e6c9;
    cursor: pointer;
    font-size: 0.7em;
    color: #2e7d32;
    transition: 0.2s;
}}
.mode-panel .sub-options button:hover {{ background: #a5d6a7; }}
.mode-panel .sub-options button.selected {{
    background: #388e3c;
    color: #fff;
    border-color: #388e3c;
}}

.btn-primary {{
    background: #388e3c;
    color: #fff;
    border: none;
    padding: 5px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    letter-spacing: 1px;
    transition: 0.2s;
    font-weight: bold;
}}
.btn-primary:hover {{ background: #2e7d32; }}

.triple-search-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    margin-top: 4px;
}}
.triple-search-row input,
.triple-search-row select {{
    padding: 4px 8px;
    border: 1px solid #a5d6a7;
    border-radius: 4px;
    font-size: 0.75em;
    background: #f1f8e9;
    color: #2e7d32;
    flex: 1;
    min-width: 70px;
}}
.triple-search-row input.short {{ flex: 0.4; min-width: 60px; }}
.triple-search-row .btn-search {{
    padding: 4px 12px;
    background: #388e3c;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75em;
    font-weight: bold;
}}
.triple-search-row .btn-search:hover {{ background: #2e7d32; }}
.triple-search-row .ci-pai-input {{ display: none; }}
.status-msg {{ color: #33691e; font-size: 0.8em; padding: 4px 0; }}

.player-area {{
    background: #f1f8e9;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 6px;
    /* ★★★ 新增：让它占据剩余的全部高度 ★★★ */
    flex: 1;
    display: flex;
    flex-direction: column;
}}
.player-area .current-info {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 4px;
}}
.player-area .current-info .title {{
    font-size: 0.95em;
    font-weight: bold;
    color: #2e7d32;
}}
.player-area .current-info .progress {{
    font-size: 0.75em;
    color: #666;
}}
.player-area .controls {{
    display: flex;
    gap: 8px;
    align-items: center;
    margin: 4px 0 6px 0;
    flex-wrap: wrap;
}}
.player-area .controls button {{
    padding: 3px 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75em;
    transition: 0.2s;
}}
.player-area .controls .play-btn {{
    background: #388e3c;
    color: #fff;
    font-weight: bold;
}}
.player-area .controls .play-btn:hover {{ background: #2e7d32; }}
.player-area .controls .ctrl-btn {{
    background: #c8e6c9;
    color: #2e7d32;
}}
.player-area .controls .ctrl-btn:hover {{ background: #a5d6a7; color: #1b5e20; }}
.player-area .text-display {{
    background: #ffffff;
    border-radius: 4px;
    padding: 8px 12px;
    /* ★★★ 移除固定高度，改为自动填满剩余空间 ★★★ */
    flex: 1;
    overflow-y: auto;
    font-family: "楷体", KaiTi, serif;
    line-height: 1.8;
    font-size: 0.85em;
    color: #333;
    white-space: pre-wrap;
}}
.player-area .text-display .label {{ color: #666; font-size: 0.8em; font-family: "Microsoft YaHei", sans-serif; }}
.player-area .text-display .label {{ color: #666; font-size: 0.8em; font-family: "Microsoft YaHei", sans-serif; }}

@media (max-width: 768px) {{
    .fullscreen-content {{ padding: 12px 14px; width: 96%; max-height: 92vh; }}
    .xianlai-header-row {{ gap: 6px; }}
    .mode-selector button {{ font-size: 0.6em; padding: 2px 6px; }}
    .triple-search-row input {{ min-width: 50px; font-size: 0.7em; }}
    .player-area .text-display {{ max-height: 130px; font-size: 0.8em; }}
}}

/* ★★★ 竖屏满屏播放（严格按指导） ★★★ */
#videoPlayerModal.fullscreen-active {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    height: 100dvh !important;
    z-index: 9999 !important;
    background: #000 !important;
    margin: 0 !important;
    border-radius: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    padding: 0 !important;
}}
#videoPlayerModal.fullscreen-active .modal-content {{
    width: 100% !important;
    max-width: none !important;
    height: 100% !important;
    max-height: none !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
}}
#videoPlayerModal.fullscreen-active #vVideoPlayer {{
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;
    max-height: none !important;
    position: relative !important;
    z-index: 1 !important;
    background: transparent !important;
}}
#videoPlayerModal.fullscreen-active #vVideoPlayer.portrait {{
    object-fit: cover !important;  /* 竖屏裁切填满 */
}}
#videoPlayerModal.fullscreen-active #vVideoPlayer.landscape {{
    object-fit: contain !important;  /* 横屏完整显示 */
}}
#videoPlayerModal.fullscreen-active #vVideoPlayerBg {{
    display: block !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    filter: blur(20px) brightness(0.6) !important;
    transform: scale(1.1) !important;
    pointer-events: none !important;
    z-index: 0 !important;
}}
#videoPlayerModal.fullscreen-active .v-ctrl-btn {{
    position: absolute !important;
    bottom: 30px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    background: rgba(0,0,0,0.6) !important;
    backdrop-filter: blur(5px) !important;
    border-radius: 30px !important;
    padding: 6px 16px !important;
    gap: 12px !important;
    z-index: 10000 !important;
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
}}
#videoPlayerModal.fullscreen-active .v-ctrl-btn .fullscreen-btn {{
    background: #c0392b !important;
    color: #fff !important;
    border: none;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.9rem;
}}
#videoPlayerModal.fullscreen-active .v-ctrl-btn .fit-btn {{
    background: #2980b9 !important;
    color: #fff !important;
    border: none;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.9rem;
    display: inline-block !important;
}}

/* ===== 爷孙健身浮层 ===== */
#fitnessModal .guestbook-modal-content {{
    background: #e8f5e9;
    max-width: 850px !important;
    border-radius: 16px;
    padding: 20px 24px;
    position: relative;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}}
#fitnessModal .modal-close {{
    position: absolute;
    top: 12px;
    right: 18px;
    font-size: 1.8em;
    cursor: pointer;
    color: #888;
    background: none;
    border: none;
    line-height: 1;
}}
#fitnessModal .modal-close:hover {{ color: #333; }}
#fitnessModal h3 {{ color: #2e7d32; margin-bottom: 16px; letter-spacing: 2px; }}
#fitnessModal .control-row {{
    display: flex;
    gap: 10px;
    align-items: center;
    margin: 15px 0;
    flex-wrap: wrap;
}}
#fitnessModal .control-row select {{
    flex: 1;
    min-width: 150px;
    padding: 6px 10px;
    border: 1px solid #a5d6a7;
    border-radius: 4px;
    background: #f1f8e9;
    color: #2e7d32;
}}
#fitnessModal .control-row .btn-primary {{
    background: #388e3c;
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    letter-spacing: 1px;
    transition: 0.2s;
}}
#fitnessModal .control-row .btn-primary:hover {{ background: #2e7d32; }}
#fitnessModal .control-row .btn-warning {{
    background: #f0ad4e;
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    letter-spacing: 1px;
}}
#fitnessModal .control-row .btn-warning:hover {{ background: #ec971f; }}
#fitnessModal .control-row .btn-danger {{
    background: #d9534f;
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    letter-spacing: 1px;
}}
#fitnessModal .control-row .btn-danger:hover {{ background: #c9302c; }}
#fitnessModal .video-wrapper {{
    background: #000;
    border-radius: 6px;
    padding: 6px;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
#fitnessModal .video-wrapper video {{
    width: 100%;
    max-height: 60vh;
    border-radius: 4px;
    display: none;
}}
#fitnessModal .video-wrapper .placeholder {{
    color: #888;
    font-size: 0.9em;
}}
</style>
</head>
<body>

<div class="header">
  <h1>冰雪诗词 · 数字图书馆</h1>
  <div class="header-info">
    <p>诗人冰雪，2019年9月至2026年3月创作古典诗词共{len(poems)}首，涵盖五绝、五律、七绝、七律及百余种词牌。<span class="detail-link" onclick="openReport()">... 详情请点击</span></p>
  </div>
</div>

<div class="main">

<div class="left-panel">
  <div class="panel-title" id="leftPanelTitle">按体裁搜索</div>
  <div class="left-menu" id="leftSidebar"></div>
</div>

<div class="center-panel">
  <div class="panel-title">综合功能区</div>
  <div class="center-buttons" id="centerButtons">
    <button onclick="openManual()">📖 使用说明</button>
    <button onclick="openSearch()">🔍 三重检索</button>
    <button onclick="showTodayPoems()">📅 今日诗词</button>
    <button onclick="showTopPoems()">🔥 热门诗词</button>
    <!--<button onclick="openVideoPlayer('video')">👴👧 爷孙诗语</button>
    <button onclick="openVideoPlayer('fitness')">💪 爷孙健身</button>
    -->
    <button onclick="window.open('player.html?type=videos', '_blank')">🎬 爷孙诗语</button>
    <button onclick="window.open('player.html?type=fitness', '_blank')">💪 爷孙健身</button>
    <button onclick="openXianLai()">🎵 闲来听诗</button>
    <button onclick="openAiPoem()">🤖 AI写诗</button>
    <button onclick="exportEditedData()">📤 导出修改</button>
    <button onclick="openGuestbook()">📝 访客留言</button>
    <!--<div class="links-wrapper">-->
      <button onclick="toggleLinks()">🔗 相关链接</button>
      <div class="links-submenu" id="linksSubmenu"></div>
    <!--</div>-->
  </div>
</div>

<div class="right-panel">
  <div class="panel-title" id="rightPanelTitle">按内容搜索</div>
  <div class="right-menu" id="rightSidebar"></div>
</div>

<div class="content" id="content">
<p style="text-align:center; color:#888; margin-top:100px; font-size:1.1em;">🌸 正在加载诗词...</p>
</div>
</div>

<button class="back-to-top" id="backToTop" onclick="scrollToTop()" title="返回顶部">⬆</button>

<div class="footer">
  <span>冰雪诗词数字图书馆 © 2026 | 共收录 {len(poems)} 首诗词</span>
  <span class="counter">累计访问：<span id="totalVisitorCount">加载中</span> 次</span>
  <span class="counter">今日访客：<span id="todayVisitorCount">加载中</span> 人</span>
  <span style="display:inline-block; margin:0 8px;">
    <button onclick="shareWebsite()" style="background:#4caf50; color:#fff; border:none; padding:4px 12px; border-radius:16px; font-size:0.7rem; cursor:pointer;">📤 分享</button>
  </span>
  <div class="qrcode-container" title="扫码访问冰雪诗词">
    <img src="qrcode.jpg" alt="网站二维码" onerror="this.parentElement.innerHTML='<span style=color:#a0c0a0;font-size:0.7em;>📷二维码</span>'">
  </div>
</div>

<!-- 报告弹窗 -->
<div class="modal" id="reportModal">
<div class="report-modal-content">
<span class="modal-close" onclick="closeReport()">&times;</span>
<div id="reportText"></div>
</div>
</div>

<!-- 三重检索弹窗 -->
<div class="modal" id="searchModal">
<div class="search-modal-content" id="searchModalContent">
<div class="search-modal-header" id="searchModalHeader">🔍 三重检索<span class="modal-close" onclick="closeSearch()">&times;</span></div>
<div class="search-row"><div class="hint">体裁</div>
<select id="searchGenreSelect" onchange="toggleCiPaiInput(this)">
    <option value="">全部体裁</option>
    <option value="五绝">五绝</option>
    <option value="五律">五律</option>
    <option value="七绝">七绝</option>
    <option value="七律">七律</option>
    <option value="其他词牌">其他词牌</option>
</select>
<!-- ★★★ 替换为下拉菜单 ★★★ -->
<select id="searchGenreCiPai" class="ci-pai-select" style="display:none; width:60%; padding:7px 10px; border:1px solid #ccc; border-radius:4px; font-size:0.9em;">
    <option value="">请选择词牌名</option>
    <option value="踏莎行">踏莎行</option>
    <option value="鹧鸪天">鹧鸪天</option>
    <option value="浣溪沙">浣溪沙</option>
    <option value="临江仙">临江仙</option>
    <option value="蝶恋花">蝶恋花</option>
    <option value="清平乐">清平乐</option>
    <option value="西江月">西江月</option>
    <option value="菩萨蛮">菩萨蛮</option>
    <option value="虞美人">虞美人</option>
    <option value="南乡子">南乡子</option>
    <option value="长相思">长相思</option>
    <option value="卜算子">卜算子</option>
    <option value="采桑子">采桑子</option>
    <option value="减字木兰花">减字木兰花</option>
    <option value="沁园春">沁园春</option>
    <option value="水调歌头">水调歌头</option>
    <option value="念奴娇">念奴娇</option>
    <option value="满江红">满江红</option>
    <option value="苏幕遮">苏幕遮</option>
    <option value="定风波">定风波</option>
    <option value="其他">其他（除前20种之外的所有词牌）</option>
</select>
</div>
<div class="search-row"><div class="hint">时间范围（月 日）</div><input type="text" id="searchStart" class="short" placeholder="起始 如 03 15"><span class="between">至</span><input type="text" id="searchEnd" class="short" placeholder="截止 如 05 20"></div>
<div class="search-row"><div class="hint">关键词（多个用空格隔开）</div><input type="text" id="searchKeywords" placeholder="如：人间 山川"></div>
<button class="search-btn" onclick="doSearch()">开始检索</button>
</div>
</div>

<!-- 留言弹窗 -->
<div class="modal" id="guestbookModal">
<div class="guestbook-modal-content">
<span class="modal-close" onclick="closeGuestbook()">&times;</span>
<h3>📝 访客留言</h3>
<div id="twikoo-global"></div>
</div>
</div>

<!-- AI写诗弹窗 -->
<div class="modal" id="aiPoemModal">
<div class="guestbook-modal-content">
<div class="modal-header">
  <h3>🤖 AI写诗</h3>
  <span class="modal-close" onclick="closeAiPoem()">&times;</span>
</div>
<div>
  <div class="two-cols">
    <div class="compact-row">
      <span class="label">韵律：</span>
      <div class="control">
        <select id="aiRhyme">
          <option value="1">平水韵</option>
          <option value="2">中华新韵</option>
          <option value="3">中华通韵</option>
          <option value="4">词林正韵</option>
        </select>
      </div>
    </div>
    <div class="compact-row">
      <span class="label">体裁：</span>
      <div class="control">
        <select id="aiGenre">
          <option value="1">五绝</option>
          <option value="2">五律</option>
          <option value="3">七绝</option>
          <option value="4">七律</option>
          <option value="5">其他词牌</option>
        </select>
      </div>
    </div>
  </div>
  <div id="ciPaiGroup" class="compact-row ci-pai-group" style="display: none;">
    <span class="label">词牌名：</span>
    <div class="control">
      <input type="text" id="aiCiPai" placeholder="例如：浣溪沙、清平乐">
    </div>
  </div>
  <div class="prompt-section">
    <div class="prompt-label">关键词/描述：</div>
    <div class="prompt-textarea">
      <textarea id="aiPrompt" placeholder="输入几个关键词或用一段话描述诗词内容，例如：春天 思乡 柳絮"></textarea>
    </div>
  </div>
  <div class="button-row">
    <button class="generate-btn" id="generatePoemBtn">生成诗词</button>
  </div>
  <div id="aiPoemResult" class="ai-poem-result">
    <div id="poemOutput"></div>
   # <button id="copyPoemBtn" class="copy-btn" style="display: none;">复制诗词</button>
    <button id="copyPoemBtn" class="copy-btn" style="display: none;">复制诗词</button>
  </div>
</div>
</div>
</div>

<!-- AI朗诵播放浮窗 -->
<div class="recite-player-overlay" id="recitePlayerOverlay">
    <div class="recite-player" id="recitePlayer">
        <div class="player-header">
            <h3 id="reciteTitle">🔊 AI朗诵</h3>
            <button class="close-btn" onclick="closeRecitePlayer()">&times;</button>
        </div>
        <div class="player-content" id="reciteContent">
            <div class="poem-text" id="recitePoemText"></div>
            <div class="analysis-text" id="reciteAnalysisText"></div>
            <div class="status-label" id="reciteStatus">⏳ 加载中...</div>
        </div>
        <div class="player-controls">
            <button class="ctrl-play" id="recitePlayBtn" onclick="toggleRecitePlay()">▶ 播放</button>
            <button class="ctrl-stop" onclick="stopRecite()">⏹ 停止</button>
            <div class="progress-bar" id="reciteProgressBar" onclick="seekRecite(event)">
                <div class="progress-fill" id="reciteProgressFill"></div>
            </div>
            <span class="time-display" id="reciteTimeDisplay">0:00 / 0:00</span>
        </div>
    </div>
</div>

<!-- AI解释浮窗 -->
<div class="modal" id="analysisModal">
    <div class="analysis-modal-content" id="analysisModalContent">
        <span class="modal-close" onclick="closeAnalysis()">&times;</span>
        <h3 id="analysisTitle">📖 诗词解析</h3>
        <div class="analysis-text" id="analysisContent">⏳ 加载中...</div>
    </div>
</div>

<!-- ===== 统一视频播放器浮窗（放大版 + 隐藏下拉菜单） ===== -->
<div class="modal" id="videoPlayerModal">
    <div class="modal-content" style="background: #ffffff; border-radius: 16px; padding: 24px 30px; width: 90%; max-width: 1080px; max-height: 85vh; overflow-y: auto; position: relative; box-shadow: 0 8px 30px rgba(0,0,0,0.2); margin: 30px auto;">
        <span class="modal-close" onclick="closeVideoPlayer()" style="position: absolute; top: 12px; right: 18px; font-size: 1.8em; cursor: pointer; color: #999; background: none; border: none;">&times;</span>
        <div id="videoPlayerContainer" style="padding: 4px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <h3 id="videoPlayerTitle" style="color: #2e7d32; margin:0; font-size:1.4rem;">🎬 视频播放</h3>
            </div>
            <!-- 信息栏（下拉菜单默认隐藏，由JS控制显示） -->
            <div style="background: #eef2f7; border-radius: 8px; padding: 8px 16px; font-size: 0.95rem; color: #555; margin-bottom: 14px; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 8px;">
                📂 当前数据源：<select id="vSourceSelect" onchange="switchVideoSource()" style="display:none; padding:4px 8px; border-radius:4px; border:1px solid #ccc; font-size:0.85rem;">
                    <option value="fitness">💪 爷孙健身</option>
                    <option value="video">👴👧 爷孙诗语</option>
                </select>
                <span id="vSourceLabel" style="font-weight:bold; color:#2c7be5;">💪爷孙 健身</span>
                <span style="color:#ccc; margin:0 4px;">|</span>
                🔍 共 <span id="vTotalCount">0</span> 个视频 <span style="color:#999;">(编号 1 ~ <span id="vMaxNum">0</span>)</span>
                <span style="color:#ccc; margin:0 4px;">|</span>
                <span id="vCurrentInfo" style="color:#2c7be5; font-weight:bold;">📌 当前：无</span>
            </div>
            <!-- 播放模式按钮（字体放大） -->
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; align-items: center; font-size: 0.95rem;">
                <button class="v-mode-btn" id="vBtnSeq" onclick="vPlaySequential()" style="padding:6px 16px; border:none; border-radius:24px; background:#e8ecf1; cursor:pointer; font-size:0.9rem;">▶ 顺序播放</button>
                <button class="v-mode-btn" id="vBtnRand3" onclick="vPlayRandom(3)" style="padding:6px 16px; border:none; border-radius:24px; background:#e8ecf1; cursor:pointer; font-size:0.9rem;">🎲 随机3段</button>
                <button class="v-mode-btn" id="vBtnRand5" onclick="vPlayRandom(5)" style="padding:6px 16px; border:none; border-radius:24px; background:#e8ecf1; cursor:pointer; font-size:0.9rem;">🎲 随机5段</button>
                <button class="v-mode-btn" id="vBtnRand8" onclick="vPlayRandom(8)" style="padding:6px 16px; border:none; border-radius:24px; background:#e8ecf1; cursor:pointer; font-size:0.9rem;">🎲 随机8段</button>
                <div style="display:flex; gap:6px; align-items:center; flex:1; min-width:180px;">
                    <input type="text" id="vCustomInput" placeholder="范围:1-5 或 列表:2 4 7" style="flex:1; padding:6px 12px; border:1px solid #d0d7e0; border-radius:24px; font-size:0.85rem;">
                    <button class="v-mode-btn" id="vBtnCustom" onclick="vPlayCustom()" style="padding:6px 16px; border:none; border-radius:24px; background:#e8ecf1; cursor:pointer; font-size:0.9rem;">指定播放</button>
                </div>
            </div>
            <!-- 视频区（放大） -->
            <div style="background:#000; border-radius:10px; overflow:hidden; margin-bottom:14px;">
                 <video id="vVideoPlayer" style="width:100%; display:block; max-height:500px; object-fit: contain;" controls playsinline webkit-playsinline preload="metadata"></video>
                <!-- ★★★ 新增：用于模糊背景的视频（静音） ★★★ -->
                <video id="vVideoPlayerBg" style="display:none;" muted loop playsinline webkit-playsinline preload="metadata"></video>
                <div id="vPlaceholder" style="color:#aaa; text-align:center; padding:60px 0; background:#1a1a2e; font-size:1.1rem;">👆 选择模式开始播放</div>
            </div>
            <!-- 底部控制（放大） -->
            <div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-bottom:8px;">
                                <!-- ★★★ 新增：全屏切换按钮（默认隐藏） ★★★ -->
                <button class="fullscreen-btn" onclick="exitVideoFullscreen()" style="display:none; background:#c0392b; color:#fff; border:none; padding:6px 16px; border-radius:20px; font-size:0.9rem;">✕ 退出全屏</button>
                <button class="fit-btn" onclick="toggleVideoFit()" style="display:none; background:#2980b9; color:#fff; border:none; padding:6px 16px; border-radius:20px; font-size:0.9rem;">🔄 切换填充</button>
                <button id="vPlayPauseBtn" onclick="vTogglePlayPause()" style="background:#2c7be5; color:#fff; border:none; padding:6px 20px; border-radius:8px; cursor:pointer; min-width:70px; font-size:0.9rem;">⏸ 暂停</button>
                <button onclick="vStopVideo()" style="background:#e74c3c; color:#fff; border:none; padding:6px 20px; border-radius:8px; cursor:pointer; font-size:0.9rem;">⏹ 停止</button>
                <button onclick="vToggleFullscreen()" style="background:#27ae60; color:#fff; border:none; padding:6px 20px; border-radius:8px; cursor:pointer; font-size:0.9rem;">⛶ 全屏</button>
                <button onclick="vRestoreSmall()" style="background:#f0f2f5; border:none; padding:6px 20px; border-radius:8px; cursor:pointer; font-size:0.9rem;">☐ 小屏</button>
            </div>
            <div id="vStatusMsg" style="text-align:center; font-size:0.85rem; color:#888; min-height:24px;">等待操作...</div>
        </div>
    </div>
</div>

<!-- ===== 使用说明弹窗 ===== -->
<div class="modal" id="manualModal">
    <div class="guestbook-modal-content">
        <span class="modal-close" onclick="closeManual()">&times;</span>
        <h3>📖 使用说明</h3>
        <div class="manual-content" id="manualContent"></div>
    </div>
</div>


<!-- ===== 闲来听诗全屏浮层 ===== -->
<div class="fullscreen-overlay" id="xianlaiOverlay">
    <div class="fullscreen-content">
        <button class="close-btn" id="xianlaiCloseBtn">&times;</button>
        <div class="xianlai-header-row">
            <h2>🎵 闲来听诗</h2>
            <div class="mode-selector" id="xianlaiModeSelector">
                <button class="active" data-mode="today">📅 今日诗词</button>
                <button data-mode="random">🎲 随机播放</button>
                <button data-mode="genre">📚 按体裁</button>
                <button data-mode="theme">🏷️ 按内容</button>
                <button data-mode="triple">🔍 三重检索</button>
            </div>
        </div>

        <div class="mode-panel active" id="xianlaiPanelToday">
            <p>自动播放今日诗词（正文+解析），按日期顺序</p>
            <button class="btn-primary" id="xianlaiStartToday">▶ 开始播放</button>
        </div>

        <div class="mode-panel" id="xianlaiPanelRandom">
            <p>从全部诗词中随机抽取</p>
            <div class="sub-options">
                <button data-count="3">3首</button>
                <button data-count="5" class="selected">5首</button>
                <button data-count="8">8首</button>
            </div>
            <button class="btn-primary" id="xianlaiStartRandom" style="margin-top:6px;">▶ 开始播放</button>
        </div>

        <div class="mode-panel" id="xianlaiPanelGenre">
            <p>先选体裁，再选主题 → 随机3首</p>
            <div class="sub-options" id="xianlaiGenreOptions"></div>
            <div class="sub-options" id="xianlaiGenreThemeOptions" style="margin-top:4px;"></div>
            <button class="btn-primary" id="xianlaiStartGenre" style="margin-top:6px;">▶ 开始播放</button>
        </div>

        <div class="mode-panel" id="xianlaiPanelTheme">
            <p>先选主题，再选体裁 → 随机3首</p>
            <div class="sub-options" id="xianlaiThemeOptions"></div>
            <div class="sub-options" id="xianlaiThemeGenreOptions" style="margin-top:4px;"></div>
            <button class="btn-primary" id="xianlaiStartTheme" style="margin-top:6px;">▶ 开始播放</button>
        </div>

        <div class="mode-panel" id="xianlaiPanelTriple">
            <p>自定义组合：体裁 + 日期范围 + 关键词</p>
            <div class="triple-search-row">
                <select id="xianlaiTripleGenre">
                    <option value="">全部体裁</option>
                    <option value="五绝">五绝</option>
                    <option value="五律">五律</option>
                    <option value="七绝">七绝</option>
                    <option value="七律">七律</option>
                    <option value="其他词牌">其他词牌</option>
                </select>
                <input type="text" id="xianlaiTripleCiPai" class="ci-pai-input" placeholder="词牌名" style="display:none; width:100px;">
                <input type="text" id="xianlaiTripleStart" placeholder="起始 03 15" class="short">
                <span style="color:#888;">至</span>
                <input type="text" id="xianlaiTripleEnd" placeholder="截止 05 20" class="short">
                <input type="text" id="xianlaiTripleKeyword" placeholder="关键词" style="flex:0.8;">
                <button class="btn-search" id="xianlaiTripleSearchBtn">检索</button>
            </div>
            <div id="xianlaiTripleResult" class="status-msg">等待检索...</div>
            <button class="btn-primary" id="xianlaiStartTriple" style="margin-top:4px;">▶ 播放检索结果</button>
        </div>

        <!-- 播放器区域 -->
        <div class="player-area" id="xianlaiPlayerArea">
            <div class="current-info">
                <span class="title" id="xianlaiCurrentTitle">等待播放...</span>
                <span class="progress" id="xianlaiCurrentProgress">0:00 / 0:00</span>
            </div>
            <div class="controls">
                <button class="ctrl-btn" id="xianlaiPrevBtn">⏮</button>
                <button class="play-btn" id="xianlaiPlayBtn">▶ 播放</button>
                <button class="ctrl-btn" id="xianlaiNextBtn">⏭</button>
                <button class="ctrl-btn" id="xianlaiStopBtn">⏹</button>
                <span style="font-size:0.75em; color:#888; margin-left:6px;" id="xianlaiTrackIndex">0 / 0</span>
            </div>
            <div class="text-display" id="xianlaiTextDisplay">
                <span class="label">📝 诗词正文 / 解析将在播放时显示...</span>
            </div>
        </div>
    </div>
</div>

<script src="https://unpkg.com/twikoo@1.6.40/dist/twikoo.all.min.js"></script>
<script>
// ============================================================
// 数据区
// ============================================================
const POEMS = {poems_json};
const REPORT_TEXT = {report_escaped};
const FRIENDLY_LINKS = {links_json};
const R2_BASE = '{r2_base}';
const GENRES = {genres_json};
const THEMES = {themes_json};
const FITNESS_VIDEOS = {fitness_json};
const VIDEO_FILES = {video_files_json};
const MANUAL_TEXT = {manual_escaped};
// ★★★ 前20种词牌常量（与下拉菜单严格一致） ★★★
const TOP20 = [
    '踏莎行', '鹧鸪天', '浣溪沙', '临江仙', '蝶恋花',
    '清平乐', '西江月', '菩萨蛮', '虞美人', '南乡子',
    '长相思', '卜算子', '采桑子', '减字木兰花', '沁园春',
    '水调歌头', '念奴娇', '满江红', '苏幕遮', '定风波'
];

const AI_POEM_WORKER_URL = 'https://poem.bingxue2026.com';
const POEM_EDIT_WORKER_URL = 'https://poem-edit.bingxue2026.com';
const EDIT_PASSWORD = "bingxue2026";

const editedPoems = {{}};

// ============================================================
// 工具函数
// ============================================================
function scrollToContent() {{
    const content = document.getElementById('content');
    if (content && window.innerWidth <= 1024) {{
        setTimeout(() => {{ content.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); }}, 150);
    }}
}}

function scrollToTop() {{
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

window.addEventListener('scroll', function() {{
    const btn = document.getElementById('backToTop');
    if (window.scrollY > 300) btn.style.display = 'block';
    else btn.style.display = 'none';
}});

function closeAllLeftAndRightAndLinks() {{
    document.querySelectorAll('[id^="submenu-genre-"]').forEach(s => s.classList.remove('open'));
    const leftMenu = document.getElementById('leftSidebar');
    if (leftMenu && window.innerWidth <= 1024) leftMenu.classList.remove('open');
    document.querySelectorAll('[id^="submenu-theme-"]').forEach(s => s.classList.remove('open'));
    const rightMenu = document.getElementById('rightSidebar');
    if (rightMenu && window.innerWidth <= 1024) rightMenu.classList.remove('open');
    const linksSub = document.getElementById('linksSubmenu');
    if(linksSub) linksSub.classList.remove('open');
    document.querySelectorAll('.menu-title.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.submenu a.active').forEach(el => el.classList.remove('active'));
}}

function beforeCenterAction() {{
    closeAllLeftAndRightAndLinks();
}}

// 包装中心按钮
const originalOpenSearch = window.openSearch;
const originalToggleLinks = window.toggleLinks;
const originalShowTodayPoems = window.showTodayPoems;
const originalOpenGuestbook = window.openGuestbook;
const originalOpenVideoGallery = window.openVideoGallery;
const originalOpenAiPoem = window.openAiPoem;
const originalOpenFitness = window.openFitness;
const originalOpenManual = window.openManual;
const originalExportEditedData = window.exportEditedData;

window.openSearch = function() {{ beforeCenterAction(); if(originalOpenSearch) originalOpenSearch(); }};
window.toggleLinks = function() {{ beforeCenterAction(); if(originalToggleLinks) originalToggleLinks(); }};
window.showTodayPoems = function() {{ beforeCenterAction(); if(originalShowTodayPoems) originalShowTodayPoems(); }};
window.openGuestbook = function() {{ beforeCenterAction(); if(originalOpenGuestbook) originalOpenGuestbook(); }};
window.openVideoGallery = function() {{ beforeCenterAction(); if(originalOpenVideoGallery) originalOpenVideoGallery(); }};
window.openAiPoem = function() {{ beforeCenterAction(); if(originalOpenAiPoem) originalOpenAiPoem(); }};
window.openFitness = function() {{ beforeCenterAction(); if(originalOpenFitness) originalOpenFitness(); }};
window.openManual = function() {{ beforeCenterAction(); if(originalOpenManual) originalOpenManual(); }};
window.exportEditedData = function() {{ beforeCenterAction(); if(originalExportEditedData) originalExportEditedData(); }};

// ★★★ 分享功能（支持手机和电脑） ★★★

function shareWebsite() {{
    var url = window.location.href;
    var content = '🌟 冰雪诗词·数字图书馆\\n📖 2042首古典诗词，AI朗诵体验\\n' + url;

    if (navigator.share) {{
        navigator.share({{
            title: '冰雪诗词·数字图书馆',
            text: '发现一个超赞的诗词网站，收录了2042首冰雪原创诗词，还可以AI朗诵！',
            url: url
        }}).catch(function(err) {{
            var dummy = document.createElement('textarea');
            document.body.appendChild(dummy);
            dummy.value = content;
            dummy.select();
            document.execCommand('copy');
            document.body.removeChild(dummy);
            alert('✅ 网址已复制到剪贴板！请粘贴到微信或朋友圈。');
        }});
    }} else {{
        var dummy = document.createElement('textarea');
        document.body.appendChild(dummy);
        dummy.value = content;
        dummy.select();
        document.execCommand('copy');
        document.body.removeChild(dummy);
        alert('✅ 网址和介绍已复制到剪贴板！请粘贴到微信或朋友圈。');
    }}
}}

// ★★★ 复制单首诗词 ★★★

// ★★★ 复制诗词完整内容（点击后按钮变"已复制"） ★★★
function copyPoemContent(poemId) {{
    var poem = getPoemById(poemId);
    if (!poem) return;
    var content = poem.title + '\\n冰雪\\n' + (poem.date || '') + '\\n' + poem.body;
    
    var btn = document.querySelector('button[onclick*="copyPoemContent(\\'' + poemId + '\\')"]');
    
    var doCopy = function(text) {{
        if (navigator.clipboard) {{
            return navigator.clipboard.writeText(text);
        }} else {{
            return new Promise(function(resolve) {{
                var dummy = document.createElement('textarea');
                document.body.appendChild(dummy);
                dummy.value = text;
                dummy.select();
                document.execCommand('copy');
                document.body.removeChild(dummy);
                resolve();
            }});
        }}
    }};
    
    doCopy(content).then(function() {{
        if (btn) {{
            var originalText = btn.textContent;
            btn.textContent = '已复制';
            btn.style.background = '#66bb6a';
            setTimeout(function() {{
                btn.textContent = originalText;
                btn.style.background = '#8bc34a';
            }}, 1500);
        }}
    }}).catch(function() {{
        if (btn) {{
            btn.textContent = '复制失败';
            setTimeout(function() {{
                btn.textContent = '复制';
            }}, 1500);
        }}
    }});
}}
function sharePoem(poemId) {{
    var poem = getPoemById(poemId);
    if (!poem) return;
    var url = window.location.href.split('?')[0] + '?poem=' + poemId;
    var fullContent = poem.title + '\\n冰雪\\n' + (poem.date || '') + '\\n' + poem.body + '\\n\\n🔗 更多欣赏请点击：' + url;
    if (navigator.share) {{
        navigator.share({{
            title: '分享一首好诗：' + poem.title + ' · 冰雪',
            text: poem.title + '\\n' + poem.body.substring(0, 80) + (poem.body.length > 80 ? '...' : '') + '\\n\\n来自：冰雪诗词·数字图书馆',
            url: url
        }}).catch(function(err) {{
            var dummy = document.createElement('textarea');
            document.body.appendChild(dummy);
            dummy.value = fullContent;
            dummy.select();
            document.execCommand('copy');
            document.body.removeChild(dummy);
            alert('✅ 诗词内容已完整复制到剪贴板！请粘贴到微信或朋友圈。');
        }});
    }} else {{
        var dummy = document.createElement('textarea');
        document.body.appendChild(dummy);
        dummy.value = fullContent;
        dummy.select();
        document.execCommand('copy');
        document.body.removeChild(dummy);
        alert('✅ 诗词内容已完整复制到剪贴板！请粘贴到微信或朋友圈。');
    }}
}}

// ★★★ 分享单首诗词 ★★★

function sharePoemAction(poemId) {{
    // 从全局诗词数据中根据ID查找当前诗词
    var poem = POEMS[poemId];
    if (!poem) return;

    // 提取诗词信息
    var title = poem.title || '';
    var date = poem.date || '';
    var body = poem.body || '';
    //var url = window.location.origin + '/poem/' + poemId + '?from=share';
    var url = window.location.href.split('?')[0] + '?poem=' + poemId + '?from=share';
    // 构建分享文案
    var shareText = '《' + title + '》——冰雪';
    if (date) {{
        shareText += '（' + date + '）';
    }}
    if (body) {{
        var firstLine = body.split('\\n')[0].replace(/[，。！？]/g, '');
        if (firstLine.length > 20) {{
            firstLine = firstLine.substring(0, 20) + '...';
        }}
        shareText += '\\n' + firstLine;
    }}

    // 手机：调用系统原生分享面板
    if (navigator.share) {{
        navigator.share({{
            title: title,
            text: shareText,
            url: url
        }}).catch(function() {{}});
    }} 
    // 电脑：降级为复制链接
    else {{
        var textarea = document.createElement('textarea');
        textarea.value = shareText + '\\n\\n' + url;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('链接已复制到剪贴板，可以粘贴分享给好友');
    }}
}}
// ★★★ 批量获取点赞数（只读查询，不会增加点赞数） ★★★
function fetchLikesForPoems(poemIds) {{
    if (!poemIds || poemIds.length === 0) return;
    fetch('https://poem-ai-explanations.bingxue2026.com/api/likes?ids=' + poemIds.join(','))
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            for (var id in data) {{
                var span = document.getElementById('like-count-' + id);
                if (span) span.textContent = data[id] || 0;
            }}
        }})
        .catch(function(err) {{ /* 静默忽略网络错误 */ }});
}}
// ========== 点赞功能（修复：改为 POST + JSON Body） ==========
function likePoem(poemId) {{
    //console.log('likePoem 被调用，诗号:', poemId);
    var poem = POEMS.find(p => p.poem_id === poemId);
    if (!poem) return;
    var title = poem.title || '';

    var btn = document.getElementById('like-btn-' + poemId);
    var countSpan = document.getElementById('like-count-' + poemId);
    if (!btn || !countSpan) return;

    btn.disabled = true;
    btn.textContent = '⏳';

    // ★★★ 关键修改：用 POST 请求 + JSON Body，匹配新 Worker 的接口 ★★★
    fetch('https://poem-ai-explanations.bingxue2026.com/api/like', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ poem_id: poemId, title: title }})
    }})
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            countSpan.textContent = data.like_count;
            btn.textContent = '👍 ' + data.like_count;
            btn.disabled = false;
            btn.style.background = '#27ae60';
            setTimeout(function() {{ btn.style.background = '#e74c3c'; }}, 500);
        }})
        .catch(function() {{
            btn.textContent = '👍 ' + (countSpan.textContent || '0');
            btn.disabled = false;
        }});
}}
/*
// 页面加载时读取初始点赞数
function loadLikeCounts() {{
    fetch('https://poem-ai-explanations.bingxue2026.com/api/top-poems?limit=100')
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            data.forEach(function(row) {{
                var span = document.getElementById('like-count-' + row.poem_id);
                if (span) span.textContent = row.like_count;
            }});
        }})
        .catch(function() {{}});
}}
*/
function loadLikeCounts() {{
    fetch('https://poem-ai-explanations.bingxue2026.com/api/top-poems?limit=100')
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            data.forEach(function(row) {{
                var span = document.getElementById('like-count-' + row.poem_id);
                if (span) span.textContent = row.like_count;
            }});
        }})
        .catch(function() {{}});
}}

// ========== 热门诗词（近期活跃优先 + 总榜兜底） ==========
function showTopPoems() {{
    fetch('https://poem-ai-explanations.bingxue2026.com/api/top-poems?limit=50')
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            if (!data || data.length === 0) {{
                alert('还没有人点赞，快来成为第一个吧！');
                return;
            }}

            // 计算 7 天前的时间
            var sevenDaysAgo = new Date();
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

            // 近期活跃（7天内有更新）
            var recent = data.filter(function(row) {{
                return row.updated_at && new Date(row.updated_at) >= sevenDaysAgo;
            }});

            // 总榜兜底（其余按原排序，即总赞数降序）
            var rest = data.filter(function(row) {{
                return !row.updated_at || new Date(row.updated_at) < sevenDaysAgo;
            }});
            // 近期活跃内部按点赞数降序排序
            recent.sort(function(a, b) {{ return b.like_count - a.like_count; }});

            // 合并：近期热门在前（已排序），总榜在后（原本就是降序），取前 10
            var merged = recent.concat(rest).slice(0, 10);

            var poemsToShow = [];
            merged.forEach(function(row) {{
                // 匹配诗词数据
                var found = null;
                for (var key in POEMS) {{
                    if (POEMS[key].poem_id === row.poem_id) {{
                        found = POEMS[key];
                        break;
                    }}
                }}
                if (found) {{
                    found._likeCount = row.like_count;
                    poemsToShow.push(found);
                }}
            }});

            if (poemsToShow.length === 0) {{
                alert('暂无热门诗词');
                return;
            }}

            render('🔥 热门诗词（近7天活跃 + 总榜补充）', poemsToShow);
            scrollToContent();
        }})
        .catch(function() {{
            alert('加载失败，请稍后重试');
        }});
}}

// 页面加载时初始化点赞数
loadLikeCounts();
// ============================================================
// 侧边栏构建
// ============================================================
function closeAllSubmenus() {{
    document.querySelectorAll('.submenu').forEach(s => s.classList.remove('open'));
}}
function closeAllLeftSubmenus() {{
    document.querySelectorAll('[id^="submenu-genre-"]').forEach(s => s.classList.remove('open'));
}}
function closeAllRightSubmenus() {{
    document.querySelectorAll('[id^="submenu-theme-"]').forEach(s => s.classList.remove('open'));
}}
function clearAllActive() {{
    document.querySelectorAll('.menu-title.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.submenu a.active').forEach(el => el.classList.remove('active'));
}}

function initDesktopPanelToggle() {{
    const leftTitle = document.getElementById('leftPanelTitle');
    const rightTitle = document.getElementById('rightPanelTitle');
    if (leftTitle) {{
        leftTitle.addEventListener('click', function() {{
            closeAllRightSubmenus();
            const linksSub = document.getElementById('linksSubmenu');
            if(linksSub) linksSub.classList.remove('open');
            closeAllLeftSubmenus();
        }});
    }}
    if (rightTitle) {{
        rightTitle.addEventListener('click', function() {{
            closeAllLeftSubmenus();
            const linksSub = document.getElementById('linksSubmenu');
            if(linksSub) linksSub.classList.remove('open');
            closeAllRightSubmenus();
        }});
    }}
}}

function initMobileMenuToggle() {{
    const leftTitle = document.getElementById('leftPanelTitle');
    const rightTitle = document.getElementById('rightPanelTitle');
    const leftMenu = document.getElementById('leftSidebar');
    const rightMenu = document.getElementById('rightSidebar');
    if (leftTitle && leftMenu) {{
        leftTitle.addEventListener('click', function() {{
            leftMenu.classList.toggle('open');
            document.querySelectorAll('[id^="submenu-theme-"]').forEach(s => s.classList.remove('open'));
            clearAllActive();
        }});
    }}
    if (rightTitle && rightMenu) {{
        rightTitle.addEventListener('click', function() {{
            rightMenu.classList.toggle('open');
            document.querySelectorAll('[id^="submenu-genre-"]').forEach(s => s.classList.remove('open'));
            clearAllActive();
        }});
    }}
}}

function buildLeftSidebar() {{
    const sb = document.getElementById('leftSidebar');
    let html = '';
    html += '<div class="mobile-second-row">';
    GENRES.forEach(g => {{
        html += '<div class="menu-title" onclick="toggleGenreThirdMenu(this,\\'' + g + '\\')">' + g + '</div>';
    }});
    html += '</div>';
    html += '<div class="submenu-fixed-area">';
    GENRES.forEach(g => {{
        html += '<div class="submenu" id="submenu-genre-' + g.replace(/[^a-zA-Z\\u4e00-\\u9fa5]/g, '') + '">';
        THEMES.forEach(th => {{
            html += '<a onclick="showFilteredByGenre(\\'' + g + '\\', \\'' + th + '\\'); setActiveSubmenu(this);">' + th.split('与')[0].slice(0,2) + '</a>';
        }});
        html += '</div>';
    }});
    html += '</div>';
    sb.innerHTML = html;
}}

function buildRightSidebar() {{
    const sb = document.getElementById('rightSidebar');
    let html = '';
    html += '<div class="mobile-theme-row">';
    THEMES.forEach(th => {{
        html += '<div class="menu-title" onclick="toggleThemeThirdMenu(this,\\'' + th + '\\')">' + th.split('与')[0].slice(0,2) + '</div>';
    }});
    html += '</div>';
    html += '<div class="submenu-fixed-area">';
    THEMES.forEach(th => {{
        html += '<div class="submenu" id="submenu-theme-' + th.replace(/[^a-zA-Z\\u4e00-\\u9fa5]/g, '') + '">';
        GENRES.forEach(g => {{
            html += '<a onclick="showFilteredByTheme(\\'' + g + '\\', \\'' + th + '\\'); setActiveSubmenu(this);">' + g + '</a>';
        }});
        html += '</div>';
    }});
    html += '</div>';
    sb.innerHTML = html;
}}

function setActiveSubmenu(el) {{
    const parent = el.parentElement;
    if (parent) parent.querySelectorAll('a.active').forEach(a => a.classList.remove('active'));
    el.classList.add('active');
}}

function toggleGenreThirdMenu(el, genre) {{
    clearAllActive();
    el.classList.add('active');
    showByGenre(genre);
    closeAllRightSubmenus();
    const linksSub = document.getElementById('linksSubmenu');
    if(linksSub) linksSub.classList.remove('open');
    const targetId = 'submenu-genre-' + genre.replace(/[^a-zA-Z\\u4e00-\\u9fa5]/g, '');
    document.querySelectorAll('[id^="submenu-genre-"]').forEach(s => {{
        if (s.id !== targetId) s.classList.remove('open');
    }});
    const target = document.getElementById(targetId);
    if (target) target.classList.toggle('open');
}}

function toggleThemeThirdMenu(el, theme) {{
    clearAllActive();
    el.classList.add('active');
    showByTheme(theme);
    closeAllLeftSubmenus();
    const linksSub = document.getElementById('linksSubmenu');
    if(linksSub) linksSub.classList.remove('open');
    const targetId = 'submenu-theme-' + theme.replace(/[^a-zA-Z\\u4e00-\\u9fa5]/g, '');
    document.querySelectorAll('[id^="submenu-theme-"]').forEach(s => {{
        if (s.id !== targetId) s.classList.remove('open');
    }});
    const target = document.getElementById(targetId);
    if (target) target.classList.toggle('open');
}}

function buildLinksSubmenu() {{
    const container = document.getElementById('linksSubmenu');
    let html = '';
    FRIENDLY_LINKS.forEach(link => {{
        if (link.type === 'qrcode') {{
            html += '<a href="#" onclick="showQRCode(\\'' + link.name + '\\', \\'' + link.img + '\\'); return false;">' + link.name + '</a>';
        }} else {{
            html += '<a href="#" onclick="window.open(\\'' + link.url + '\\', \\'_blank\\'); return false;">' + link.name + '</a>';
        }}
    }});
    container.innerHTML = html;
}}

function toggleLinks() {{
    closeAllSubmenus();
    const ls = document.getElementById('linksSubmenu');
    if(ls) ls.classList.toggle('open');
}}

function showQRCode(title, imgFile) {{
    const c = document.getElementById('content');
    c.innerHTML = `<div style="text-align:center; padding:40px 20px;">
        <h3 style="color:#2e7d32; margin-bottom:20px;">${{title}}</h3>
        <img src="${{imgFile}}" style="max-width:300px; width:100%; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1);" alt="${{title}}">
        <p style="margin-top:10px; color:#888;">请用手机扫码关注</p>
    </div>`;
    scrollToContent();
}}

// ============================================================
// 诗词筛选与展示
// ============================================================
function getPoemById(id) {{
    return POEMS.find(p => p.poem_id === id);
}}

function showByGenre(genre) {{
    let f = genre === '词牌诗词' ? POEMS.filter(p => !['五绝','五律','七绝','七律'].includes(p.genre)) : POEMS.filter(p => p.genre === genre);
    render(genre + ' · 全部', f);
    scrollToContent();
}}

function showByTheme(theme) {{
    let f = POEMS.filter(p => p.themes && p.themes.includes(theme));
    render(theme, f);
    scrollToContent();
}}

function showFilteredByGenre(genre, theme) {{
    let f1 = genre === '词牌诗词' ? POEMS.filter(p => !['五绝','五律','七绝','七律'].includes(p.genre)) : POEMS.filter(p => p.genre === genre);
    let f = f1.filter(p => p.themes && p.themes.includes(theme));
    render(genre + ' · ' + theme.split('与')[0], f);
    scrollToContent();
}}

function showFilteredByTheme(genre, theme) {{
    let f1 = POEMS.filter(p => p.themes && p.themes.includes(theme));
    let f = genre === '词牌诗词' ? f1.filter(p => !['五绝','五律','七绝','七律'].includes(p.genre)) : f1.filter(p => p.genre === genre);
    render(theme.split('与')[0] + ' · ' + genre, f);
    scrollToContent();
}}

// ============================================================
// AI朗诵
// ============================================================
let reciteAudio = null;
let reciteCurrentPoem = null;
let recitePhase = 'idle';
let reciteIsPaused = false;

function recitePoem(poemId) {{
    const poem = getPoemById(poemId);
    if (!poem) {{ alert('未找到诗词'); return; }}

    closeRecitePlayer();

    reciteCurrentPoem = poem;
    recitePhase = 'idle';
    reciteIsPaused = false;

    const overlay = document.getElementById('recitePlayerOverlay');
    overlay.classList.add('active');

    document.getElementById('reciteTitle').textContent = '🔊 AI朗诵 · ' + poem.title;
    document.getElementById('recitePoemText').textContent = poem.body;
    document.getElementById('reciteAnalysisText').classList.remove('show');
    document.getElementById('reciteAnalysisText').textContent = '';
    document.getElementById('reciteStatus').textContent = '⏳ 加载正文音频...';
    document.getElementById('recitePlayBtn').textContent = '▶ 播放';
    document.getElementById('reciteProgressFill').style.width = '0%';
    document.getElementById('reciteTimeDisplay').textContent = '0:00 / 0:00';

    if (reciteAudio) {{
        reciteAudio.pause();
        reciteAudio.src = '';
        reciteAudio = null;
    }}

    const poemUrl = R2_BASE + '/recite/' + poemId + '_poem.mp3';
    reciteAudio = new Audio(poemUrl);

    reciteAudio.ontimeupdate = function() {{
        if (reciteAudio && reciteAudio.duration) {{
            const pct = (reciteAudio.currentTime / reciteAudio.duration) * 100;
            document.getElementById('reciteProgressFill').style.width = pct + '%';
            document.getElementById('reciteTimeDisplay').textContent =
                formatTime(reciteAudio.currentTime) + ' / ' + formatTime(reciteAudio.duration);
        }}
    }};

    reciteAudio.oncanplay = function() {{
        document.getElementById('reciteStatus').textContent = '▶ 正在播放正文...';
        recitePhase = 'poem';
        if (!reciteIsPaused) {{
            reciteAudio.play();
            document.getElementById('recitePlayBtn').textContent = '⏸ 暂停';
        }}
    }};

    reciteAudio.onended = function() {{
        document.getElementById('reciteStatus').textContent = '⏳ 加载解析音频...';
        recitePhase = 'loading_analysis';

        const analysisUrl = R2_BASE + '/recite/' + poemId + '_analysis.txt';
        fetchWithRetry(analysisUrl, {{ cache: 'no-store' }})
            .then(function(text) {{
                document.getElementById('reciteAnalysisText').textContent = text;
                document.getElementById('reciteAnalysisText').classList.add('show');
            }})
            .catch(function() {{
                document.getElementById('reciteAnalysisText').textContent = '⚠️ 加载失败，请稍后重试';
                document.getElementById('reciteAnalysisText').classList.add('show');
            }});

        const analysisAudioUrl = R2_BASE + '/recite/' + poemId + '_analysis.mp3';
        const newAudio = new Audio(analysisAudioUrl);

        newAudio.ontimeupdate = function() {{
            if (newAudio && newAudio.duration) {{
                const pct = (newAudio.currentTime / newAudio.duration) * 100;
                document.getElementById('reciteProgressFill').style.width = pct + '%';
                document.getElementById('reciteTimeDisplay').textContent =
                    formatTime(newAudio.currentTime) + ' / ' + formatTime(newAudio.duration);
            }}
        }};

        newAudio.oncanplay = function() {{
            reciteAudio = newAudio;
            recitePhase = 'analysis';
            document.getElementById('reciteStatus').textContent = '▶ 正在播放解析...';
            document.getElementById('reciteProgressFill').style.width = '0%';
            document.getElementById('reciteTimeDisplay').textContent = '0:00 / ' + formatTime(newAudio.duration);
            if (!reciteIsPaused) {{
                reciteAudio.play();
                document.getElementById('recitePlayBtn').textContent = '⏸ 暂停';
            }}
        }};
        newAudio.onended = function() {{
            recitePhase = 'done';
            document.getElementById('reciteStatus').textContent = '✅ 全部播放完毕';
            document.getElementById('recitePlayBtn').textContent = '▶ 播放';
            document.getElementById('reciteProgressFill').style.width = '100%';
        }};
        newAudio.onerror = function() {{
            recitePhase = 'done';
            document.getElementById('reciteStatus').textContent = '✅ 正文播放完毕（解析音频暂无）';
            document.getElementById('recitePlayBtn').textContent = '▶ 播放';
            document.getElementById('reciteProgressFill').style.width = '100%';
        }};
        newAudio.load();
    }};

    reciteAudio.onerror = function() {{
        document.getElementById('reciteStatus').textContent = '❌ 正文音频加载失败';
        document.getElementById('recitePlayBtn').textContent = '▶ 播放';
        const analysisUrl = R2_BASE + '/recite/' + poemId + '_analysis.txt';
        fetchWithRetry(analysisUrl, {{ cache: 'no-store' }})
            .then(function(text) {{
                document.getElementById('reciteAnalysisText').textContent = text;
                document.getElementById('reciteAnalysisText').classList.add('show');
            }})
            .catch(function() {{
                document.getElementById('reciteAnalysisText').textContent = '⚠️ 加载失败';
                document.getElementById('reciteAnalysisText').classList.add('show');
            }});
        recitePhase = 'done';
    }};

    reciteAudio.load();
}}

function toggleRecitePlay() {{
    if (!reciteAudio) return;
    if (recitePhase === 'done') {{
        closeRecitePlayer();
        if (reciteCurrentPoem) {{
            recitePoem(reciteCurrentPoem.poem_id);
        }}
        return;
    }}
    if (reciteAudio.paused) {{
        reciteAudio.play();
        reciteIsPaused = false;
        document.getElementById('recitePlayBtn').textContent = '⏸ 暂停';
        document.getElementById('reciteStatus').textContent =
            recitePhase === 'poem' ? '▶ 正在播放正文...' : '▶ 正在播放解析...';
    }} else {{
        reciteAudio.pause();
        reciteIsPaused = true;
        document.getElementById('recitePlayBtn').textContent = '▶ 播放';
        document.getElementById('reciteStatus').textContent = '⏸ 已暂停';
    }}
}}

function stopRecite() {{
    if (reciteAudio) {{
        reciteAudio.pause();
        reciteAudio.currentTime = 0;
        document.getElementById('reciteProgressFill').style.width = '0%';
        document.getElementById('reciteTimeDisplay').textContent = '0:00 / 0:00';
    }}
    recitePhase = 'idle';
    reciteIsPaused = false;
    document.getElementById('recitePlayBtn').textContent = '▶ 播放';
    document.getElementById('reciteStatus').textContent = '⏹ 已停止';
}}

function closeRecitePlayer() {{
    if (reciteAudio) {{
        reciteAudio.pause();
        reciteAudio.src = '';
        reciteAudio = null;
    }}
    recitePhase = 'idle';
    reciteIsPaused = false;
    document.getElementById('recitePlayerOverlay').classList.remove('active');
}}

function seekRecite(e) {{
    if (!reciteAudio || !reciteAudio.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    reciteAudio.currentTime = x * reciteAudio.duration;
}}

function formatTime(sec) {{
    if (!sec || isNaN(sec)) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return m + ':' + String(s).padStart(2, '0');
}}

// ============================================================
// AI解诗
// ============================================================
function showAnalysis(poemId) {{
    const poem = getPoemById(poemId);
    if (!poem) {{ alert('未找到诗词'); return; }}

    const modal = document.getElementById('analysisModal');
    document.getElementById('analysisTitle').textContent = '📖 诗词解析 · ' + poem.title;
    document.getElementById('analysisContent').textContent = '⏳ 加载中...';
    modal.classList.add('active');

    const txtUrl = R2_BASE + '/recite/' + poemId + '_analysis.txt';
    fetchWithRetry(txtUrl, {{ cache: 'no-store' }})
        .then(function(text) {{
            document.getElementById('analysisContent').textContent = text;
        }})
        .catch(function(err) {{
            document.getElementById('analysisContent').textContent = '⚠️ 加载失败，请稍后重试';
        }});
}}

function closeAnalysis() {{
    document.getElementById('analysisModal').classList.remove('active');
}}

// ============================================================
// 浮窗拖拽
// ============================================================
function makeDraggable(element) {{
    if (!element) return;
    let isDragging = false;
    let startX, startY, origX, origY;

    element.addEventListener('mousedown', function(e) {{
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = element.getBoundingClientRect();
        origX = rect.left;
        origY = rect.top;
        element.style.position = 'fixed';
        element.style.cursor = 'grabbing';
        e.preventDefault();
    }});

    document.addEventListener('mousemove', function(e) {{
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        element.style.left = (origX + dx) + 'px';
        element.style.top = (origY + dy) + 'px';
        element.style.margin = '0';
    }});

    document.addEventListener('mouseup', function() {{
        if (isDragging) {{
            isDragging = false;
            element.style.cursor = '';
        }}
    }});

    element.addEventListener('touchstart', function(e) {{
        const touch = e.touches[0];
        isDragging = true;
        startX = touch.clientX;
        startY = touch.clientY;
        const rect = element.getBoundingClientRect();
        origX = rect.left;
        origY = rect.top;
        element.style.position = 'fixed';
    }}, {{ passive: true }});

    document.addEventListener('touchmove', function(e) {{
        if (!isDragging) return;
        const touch = e.touches[0];
        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        element.style.left = (origX + dx) + 'px';
        element.style.top = (origY + dy) + 'px';
        element.style.margin = '0';
    }}, {{ passive: true }});

    document.addEventListener('touchend', function() {{
        isDragging = false;
    }}, {{ passive: true }});
}}

// ============================================================
// 核心渲染
// ============================================================
function render(title, poems) {{
    const c = document.getElementById('content');
    if (poems.length === 0) {{ c.innerHTML = '<p style="text-align:center;color:#888;margin-top:60px;">该分类下暂无诗词。</p>'; return; }}
    let h = '<h3 style="margin-bottom:15px;color:#2e7d32;">' + title + '（共' + poems.length + '首）</h3>';
    poems.forEach(p => {{
        const pid = p.poem_id;
        const imgFiles = p.image_files || [];
        h += '<div class="poem-card" style="overflow: auto;">';
        if (imgFiles.length > 0) {{
            const isSingle = imgFiles.length === 1;
            h += '<div class="poem-img-float' + (isSingle ? ' single-img' : '') + '" id="imgs-' + pid + '" style="display:none;">';
            // ★★★ 直接迭代真实文件名列表，不再硬编码 ★★★
            imgFiles.forEach(function(fileName) {{
                const imgUrl = R2_BASE + '/images/' + pid + '/' + fileName;
                h += '<img src="' + imgUrl + '" loading="lazy" onerror="this.style.display= none" alt="配图" onclick="window.open(this.src)">';
            }});
            h += '</div>';
        }}
        h += '<div class="poem-title">' + p.title + '</div>';
        h += '<div class="poem-author">冰雪</div>';
        if (p.date) h += '<div class="poem-date">' + p.date + '</div>';
        var displayBody = (editedPoems[pid] || p.body || '');
        h += '<div class="poem-body" id="body-' + pid + '">' + displayBody.replace(/\\n/g, '<br>') + '</div>';
        if (imgFiles.length > 0) {{
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\'' + pid + '\\')">查看配图(' + imgFiles.length + ')</button>';
        }} else {{
            h += '<span style="display:inline-block;margin-top:8px;margin-right:8px;padding:5px 10px;background:#e0e0e0;color:#888;border-radius:4px;font-size:0.8em;letter-spacing:1px;">没有配图</span>';
        }}
        h += '<button class="like-btn" onclick="likePoem(\\'' + pid + '\\')" style="background:#e74c3c; color:#fff; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; font-size:0.7rem; margin-left:8px;" id="like-btn-' + pid + '">👍 <span id="like-count-' + pid + '">0</span></button>';
        h += '<div class="button-group">';
        h += '<button class="edit-btn" onclick="editPoem(\\'' + pid + '\\')">编辑</button>';
        h += '<button class="comment-btn" onclick="togglePoemComment(\\'' + pid + '\\')">留言</button>';
        h += '<button class="edit-btn share-btn" onclick="copyPoemContent(\\'' + pid + '\\')" style="background:#8bc34a; color:#fff;">复制</button>';
        h += '<button class="edit-btn share-btn" onclick="sharePoemAction(\\'' + pid + '\\')" style="background:#8bc34a; color:#fff;">分享</button>';
        h += '</div>';
        h += '<div class="button-group" style="gap:16px;">';
        h += '<button class="btn-recite" onclick="recitePoem(\\'' + pid + '\\')">🔊 AI朗诵</button>';
        h += '<button class="btn-analyze" onclick="showAnalysis(\\'' + pid + '\\')">📖 AI解诗</button>';
        h += '</div>';
        h += '<div id="poem-comment-' + pid + '" class="poem-comment-area">';
        h += '<div id="twikoo-poem-' + pid + '"></div>';
        h += '</div>';
        h += '</div>';
    }});
    c.innerHTML = h;
    c.scrollTop = 0;
    setTimeout(function() {{ loadLikeCounts(); }}, 300);
}}

function toggleImgs(btn, poemId) {{
    const container = document.getElementById('imgs-' + poemId);
    if (!container) return;

    const isOpen = container.style.display === 'block';
    if (isOpen) {{
        // 收起时，直接隐藏，无需做任何请求
        container.style.display = 'none';
        const count = container.querySelectorAll('img').length;
        btn.textContent = '查看配图(' + count + ')';
    }} else {{
        // 展开时，先显示一个“加载中”的提示
        container.style.display = 'block';
        btn.textContent = '加载中...';
        const imgs = container.querySelectorAll('img');
        let loadedCount = 0;

        // 核心逻辑：一张一张地加载（防止瞬间并发堵塞）
        function loadNext(index) {{
            if (index >= imgs.length) {{
                // 全部加载完毕，恢复按钮文字
                btn.textContent = '收起配图(' + imgs.length + ')';
                return;
            }}
            const img = imgs[index];
            // 如果该图片还未加载成功，绑定加载完成后的回调
            if (!img.complete) {{
                img.onload = function() {{
                    loadedCount++;
                    loadNext(index + 1); // 加载下一张
                }};
                img.onerror = function() {{
                    loadedCount++;
                    loadNext(index + 1); // 即使失败，也继续下一张
                }};
            }} else {{
                // 如果图片已经缓存，complete为true，直接继续下一张
                loadedCount++;
                loadNext(index + 1);
            }}
        }}
        // 从第 0 张开始加载
        loadNext(0);
    }}
}}

// ============================================================
// 今日诗词
// ============================================================
function showTodayPoems() {{
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    const weekDay = weekDays[today.getDay()];
    const matched = POEMS.filter(p => {{ if (!p.date) return false; const parts = p.date.split('.'); return parts[1] === month && parts[2] === day; }});
    const c = document.getElementById('content');
    if (matched.length === 0) {{ c.innerHTML = '<p style="text-align:center;color:#888;margin-top:60px;">今日暂无历史诗词。</p>'; return; }}
    let h = '<div class="history-intro"><p>' + today.getFullYear() + '年' + month + '月' + day + '日 ' + weekDay + ' · 请欣赏</p></div>';
    h += '<h3 style="margin-bottom:15px;color:#2e7d32;">往日今朝（共' + matched.length + '首）</h3>';
    matched.forEach(p => {{
        const pid = p.poem_id;
        const imgFiles = p.image_files || [];  
        h += '<div class="poem-card">';
        if (imgFiles.length > 0) {{
            const isSingle = imgFiles.length === 1;
            h += '<div class="poem-img-float' + (isSingle ? ' single-img' : '') + '" id="imgs-' + pid + '" style="display:none;">';
            // ★★★ 直接迭代真实文件名列表，不再硬编码 ★★★
            imgFiles.forEach(function(fileName) {{
                const imgUrl = R2_BASE + '/images/' + pid + '/' + fileName;
                h += '<img src="' + imgUrl + '" loading="lazy" onerror="this.style.display= none" alt="配图" onclick="window.open(this.src)">';
            }});
            h += '</div>';
        }}
        h += '<div class="poem-title">' + p.title + '</div>';
        h += '<div class="poem-author">冰雪</div>';
        if (p.date) h += '<div class="poem-date">' + p.date + '</div>';
        var displayBody = (editedPoems[pid] || p.body || '');
        h += '<div class="poem-body" id="body-' + pid + '">' + displayBody.replace(/\\n/g, '<br>') + '</div>';
       if (imgFiles.length > 0) {{
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\'' + pid + '\\')">查看配图(' + imgFiles.length + ')</button>';
        }} else {{
            h += '<span style="display:inline-block;margin-top:8px;margin-right:8px;padding:5px 10px;background:#e0e0e0;color:#888;border-radius:4px;font-size:0.8em;letter-spacing:1px;">没有配图</span>';
        }} 
        h += '<button class="like-btn" onclick="likePoem(\\'' + pid + '\\')" style="background:#e74c3c; color:#fff; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; font-size:0.7rem; margin-left:8px;" id="like-btn-' + pid + '">👍 <span id="like-count-' + pid + '">0</span></button>';
        h += '<div class="button-group">';
        h += '<button class="edit-btn" onclick="editPoem(\\'' + pid + '\\')">编辑</button>';
        h += '<button class="comment-btn" onclick="togglePoemComment(\\'' + pid + '\\')">留言</button>';
        h += '<button class="edit-btn share-btn" onclick="copyPoemContent(\\'' + pid + '\\')" style="background:#8bc34a; color:#fff;">复制</button>';
        h += '<button class="edit-btn share-btn" onclick="sharePoemAction(\\'' + pid + '\\')" style="background:#8bc34a; color:#fff;">分享</button>';
        h += '</div>';
        h += '<div class="button-group" style="gap:16px;">';
        h += '<button class="btn-recite" onclick="recitePoem(\\'' + pid + '\\')">🔊 AI朗诵</button>';
        h += '<button class="btn-analyze" onclick="showAnalysis(\\'' + pid + '\\')">📖 AI解诗</button>';
        h += '</div>';
        h += '<div id="poem-comment-' + pid + '" class="poem-comment-area">';
        h += '<div id="twikoo-poem-' + pid + '"></div>';
        h += '</div>';
        h += '</div>';
    }});
        c.innerHTML = h;
        c.scrollTop = 0;
    var ids = matched.map(p => p.poem_id);
    if (ids.length > 0) {{
        setTimeout(function() {{ fetchLikesForPoems(ids); }}, 300);
    }}
}}

// ============================================================
// 诗词编辑
// ============================================================
function showCustomEditDialog(id, currentBody) {{
    return new Promise((resolve) => {{
        const existing = document.querySelector('.custom-edit-modal');
        if (existing) existing.remove();
        const modal = document.createElement('div');
        modal.className = 'custom-edit-modal';
        modal.innerHTML = `
            <div class="custom-edit-content">
                <textarea id="customEditTextarea">${{currentBody.replace(/</g, '&lt;').replace(/>/g, '&gt;')}}</textarea>
                <div class="btn-group">
                    <button class="cancel-btn">取消</button>
                    <button class="save-btn">保存</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        const textarea = modal.querySelector('#customEditTextarea');
        const saveBtn = modal.querySelector('.save-btn');
        const cancelBtn = modal.querySelector('.cancel-btn');
        saveBtn.onclick = () => {{
            const newBody = textarea.value;
            modal.remove();
            resolve(newBody);
        }};
        cancelBtn.onclick = () => {{
            modal.remove();
            resolve(null);
        }};
        textarea.focus();
        setTimeout(() => {{
            textarea.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}, 300);
    }});
}}

function editPoem(id) {{
    // 判断是否为手机端（简单宽高判定）
    var isMobile = window.innerWidth <= 1024;
    
    // 定义一个密码验证后调用的逻辑
    function proceedEdit() {{
        var currentBody = document.getElementById('body-' + id).innerText;
        showCustomEditDialog(id, currentBody).then(function(newBody) {{
            if (newBody !== null && newBody !== currentBody) {{
                document.getElementById('body-' + id).innerHTML = newBody.replace(/\\n/g, '<br>');
                // 更新本地缓存
                editedPoems[id] = newBody;
                // 同步到云端（完全保留原有逻辑）
                fetch(POEM_EDIT_WORKER_URL + '/edit', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ poem_id: id, edited_body: newBody }})
                }}).then(function(response) {{ return response.json(); }})
                .then(function(data) {{
                    if (data.success) alert('✅ 修改已同步到云端');
                }}).catch(function() {{
                    alert('⚠️ 云端同步失败，但本地缓存已更新');
                }});
            }}
        }});
    }}

    // 手机端处理逻辑
    if (isMobile) {{
        // 避免重复生成弹窗
        var existingModal = document.getElementById('mobile-pwd-modal');
        if (existingModal) existingModal.remove();

        var modalHtml = `
            <div id="mobile-pwd-modal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:99999;display:flex;align-items:center;justify-content:center;">
                <div style="background:#fff;padding:20px;border-radius:12px;width:80%;max-width:350px;text-align:center;">
                    <h3 style="color:#2e7d32;margin-bottom:12px;">请输入编辑密码</h3>
                    <input id="mobile-pwd-input" type="password" placeholder="密码" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:6px;margin-bottom:12px;font-size:16px;">
                    <div style="display:flex;gap:10px;justify-content:center;">
                        <button id="mobile-pwd-confirm" style="background:#4caf50;color:#fff;border:none;padding:8px 20px;border-radius:6px;">确定</button>
                        <button id="mobile-pwd-cancel" style="background:#ccc;color:#333;border:none;padding:8px 20px;border-radius:6px;">取消</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        var modal = document.getElementById('mobile-pwd-modal');
        var input = document.getElementById('mobile-pwd-input');
        var confirmBtn = document.getElementById('mobile-pwd-confirm');
        var cancelBtn = document.getElementById('mobile-pwd-cancel');

        var closeModal = function() {{ modal.remove(); }};
        var checkPwd = function() {{
            if (input.value === EDIT_PASSWORD) {{
                closeModal();
                proceedEdit();
            }} else {{
                alert('密码错误，无法编辑。');
            }}
        }};

        confirmBtn.onclick = checkPwd;
        cancelBtn.onclick = closeModal;
        // 支持回车提交
        input.onkeydown = function(e) {{ if (e.key === 'Enter') checkPwd(); }};
        input.focus();
    }} else {{
        // 电脑端保持原有 prompt 逻辑
        var pwd = prompt("请输入编辑密码：");
        if (pwd !== EDIT_PASSWORD) {{
            if (pwd !== null) alert("密码错误，无法编辑。");
            return;
        }}
        proceedEdit();
    }}
}}

// ============================================================
// 评论区（每首诗词下方）
// ============================================================
function loadPoemComment(poemId, containerId) {{
    if (typeof twikoo === 'undefined') {{
        console.error('Twikoo 未加载');
        return;
    }}
    if (window['twikoo_' + poemId]) return;
    twikoo.init({{
        envId: 'https://twikoo.bingxue2026.com',
        el: '#' + containerId,
        path: '/poem/' + poemId,
        lang: 'zh-CN',
        pageSize: 20,
        showPoweredBy: false
    }}).then(() => {{
        window['twikoo_' + poemId] = true;
    }}).catch(err => console.error('评论加载失败', err));
}}

function togglePoemComment(poemId) {{
    const commentArea = document.getElementById('poem-comment-' + poemId);
    if (!commentArea) return;
    if (commentArea.classList.contains('active')) {{
        commentArea.classList.remove('active');
    }} else {{
        commentArea.classList.add('active');
        const containerId = 'twikoo-poem-' + poemId;
        const containerDiv = document.getElementById(containerId);
        if (containerDiv && containerDiv.innerHTML.trim() === '') {{
            loadPoemComment(poemId, containerId);
        }}
    }}
}}

// ===== 统一视频播放器核心逻辑（修复高亮+路径+下拉隐藏） =====
const VIDEO_DATA = {{ 'fitness': FITNESS_VIDEOS.map(f => R2_BASE + '/fitness/' + f), 'video': VIDEO_FILES.map(f => R2_BASE + '/videos/' + f) }};
let vCurrentSource = 'fitness';
let vVideoList = [];
let vTotalVideos = 0;
let vPlaylist = [];
let vCurrentIndex = 0;
let vIsPlaying = false;
let vVideoElement = null;
let vPlaceholder = null;
let vPlayPauseBtn = null;
let vStatusMsg = null;
let vCurrentInfo = null;
let vCustomInput = null;
let vSourceSelect = null;
let vSourceLabel = null;

function initVideoPlayer(source, showSwitch) {{
    vCurrentSource = source || document.getElementById('vSourceSelect').value;
    vVideoList = VIDEO_DATA[vCurrentSource];
    vTotalVideos = vVideoList.length;
    document.getElementById('vTotalCount').textContent = vTotalVideos;
    document.getElementById('vMaxNum').textContent = vTotalVideos;
    document.getElementById('vCurrentInfo').innerHTML = '📌 当前：无';
    document.getElementById('vStatusMsg').textContent = '✅ 已加载 ' + vCurrentSource + '，共 ' + vTotalVideos + ' 个视频';
    // 控制下拉菜单显示
    vSourceSelect = document.getElementById('vSourceSelect');
    vSourceLabel = document.getElementById('vSourceLabel');
    if (showSwitch === false) {{
        vSourceSelect.style.display = 'none';
        vSourceLabel.style.display = 'inline';
        vSourceLabel.textContent = vCurrentSource === 'fitness' ? '💪 爷孙健身' : '👴👧 爷孙诗语';
    }} else {{
        vSourceSelect.style.display = 'inline-block';
        vSourceLabel.style.display = 'none';
    }}
    vStopVideo();
}}

function vSetActive(btnId) {{
    document.querySelectorAll('.v-mode-btn').forEach(b => b.classList.remove('active'));
    if (btnId) document.getElementById(btnId).classList.add('active');
}}

function vClearCustom() {{
    document.getElementById('vCustomInput').value = '';
}}

function switchVideoSource() {{
    vClearCustom();
    document.querySelectorAll('.v-mode-btn').forEach(b => b.classList.remove('active'));
    initVideoPlayer();
}}

function vPlayList(indices) {{
    if (indices.length === 0) {{ document.getElementById('vStatusMsg').textContent = '⚠️ 无可用视频'; return; }}
    vStopVideo();
    vPlaylist = indices.slice();
    vCurrentIndex = 0;
    vIsPlaying = true;
    document.getElementById('vPlayPauseBtn').textContent = '⏸ 暂停';
    document.getElementById('vStatusMsg').textContent = '▶ 开始播放 ' + vPlaylist.length + ' 个视频';
    vPlayCurrent();  // ★★★ 确保这一行完整，不要漏掉函数名 ★★★
}}

function vPlayCurrent() {{
    if (!vIsPlaying || vCurrentIndex >= vPlaylist.length) {{
        vIsPlaying = false;
        document.getElementById('vPlayPauseBtn').textContent = '▶ 播放';
        document.getElementById('vStatusMsg').textContent = '✅ 全部播放完毕';
        document.getElementById('vPlaceholder').style.display = 'block';
        document.getElementById('vVideoPlayer').style.display = 'none';
        document.getElementById('vVideoPlayerBg').style.display = 'none';
        document.getElementById('vCurrentInfo').innerHTML = '📌 当前：播放完毕';
        vClearCustom();
        // 退出模拟全屏
        exitVideoFullscreen();
        return;
    }}
    const idx = vPlaylist[vCurrentIndex];
    const url = vVideoList[idx];
    if (!url) {{ vCurrentIndex++; vPlayCurrent(); return; }}
    document.getElementById('vPlaceholder').style.display = 'none';
    document.getElementById('vVideoPlayer').style.display = 'block';
    let videoEl = document.getElementById('vVideoPlayer');
    let bgEl = document.getElementById('vVideoPlayerBg');
    videoEl.setAttribute('playsinline', '');
    videoEl.setAttribute('webkit-playsinline', '');
    videoEl.setAttribute('preload', 'metadata');
    videoEl.src = url;
    bgEl.src = url;  // 同步背景视频

    // ★★★ 触发模拟全屏 ★★★
    enterVideoFullscreen();

    // ★★★ 播放主视频 ★★★
        // ★★★ 在 play 之前先同步背景时间 ★★★
    bgEl.currentTime = videoEl.currentTime;
    videoEl.play().then(function() {{
        // 启动背景播放
        bgEl.play();
        // 自动检测宽高比，决定初始模式
        // （已在 enterVideoFullscreen 中通过 class 控制，此处不再重复添加）
        document.querySelector('.fullscreen-btn').style.display = 'inline-block';
        document.querySelector('.fit-btn').style.display = 'inline-block';
    }}).catch(function(err) {{
        document.getElementById('vStatusMsg').textContent = '⚠️ 视频播放失败，请检查格式';
    }});

    document.getElementById('vCurrentInfo').innerHTML = '📌 当前：第 ' + (idx+1) + ' 号， ' + (vCurrentIndex+1) + '/' + vPlaylist.length;
    document.getElementById('vStatusMsg').textContent = '▶ 正在播放第 ' + (idx+1) + ' 号';
    videoEl.onended = function() {{ vCurrentIndex++; vPlayCurrent(); }};
    videoEl.onerror = function() {{
        document.getElementById('vStatusMsg').textContent = '⚠️ 第 ' + (idx+1) + ' 号加载失败，跳过';
        vCurrentIndex++; vPlayCurrent();
    }};
}}

// ★★★ 进入全屏（严格按指导） ★★★
function enterVideoFullscreen() {{
    var modal = document.getElementById('videoPlayerModal');
    var video = document.getElementById('vVideoPlayer');
    // 判断横竖屏，添加对应的 class
    if (video.videoHeight && video.videoWidth) {{
        if (video.videoHeight > video.videoWidth) {{
            video.classList.add('portrait');
        }} else {{
            video.classList.add('landscape');
        }}
    }}
    modal.classList.add('fullscreen-active');
    document.body.style.overflow = 'hidden';
    // 显示全屏控制按钮
    document.querySelector('.fullscreen-btn').style.display = 'inline-block';
    document.querySelector('.fit-btn').style.display = 'inline-block';
}}

// ★★★ 退出全屏（严格按指导） ★★★
function exitVideoFullscreen() {{
    var modal = document.getElementById('videoPlayerModal');
    var video = document.getElementById('vVideoPlayer');
    // 移除全屏类
    modal.classList.remove('fullscreen-active');
    document.body.style.overflow = '';
    // ★ 关键：清空所有内联样式，让 CSS 恢复默认控制 ★
    video.style.objectFit = '';
    video.style.width = '';
    video.style.height = '';
    video.classList.remove('portrait', 'landscape');
    // 停止背景视频
    var bg = document.getElementById('vVideoPlayerBg');
    if (bg) {{ bg.pause(); bg.currentTime = 0; }}
    // 隐藏全屏控制按钮
    document.querySelector('.fullscreen-btn').style.display = 'none';
    document.querySelector('.fit-btn').style.display = 'none';
}}

// ★★★ 手动切换填充/完整模式 ★★★
function toggleVideoFit() {{
    var modal = document.getElementById('videoPlayerModal');
    var btn = document.querySelector('.fit-btn');
    if (modal.classList.contains('fit-mode-cover')) {{
        modal.classList.remove('fit-mode-cover');
        btn.textContent = '🔄 填满屏幕';
    }} else {{
        modal.classList.add('fit-mode-cover');
        btn.textContent = '🔄 完整显示';
    }}
}}
function vPlaySequential() {{
    vSetActive('vBtnSeq');
    vClearCustom();
    let indices = Array.from({{length: vTotalVideos}}, (_, i) => i);
    vPlayList(indices);
}}

function vPlayRandom(count) {{
    let btnId = count===3 ? 'vBtnRand3' : count===5 ? 'vBtnRand5' : 'vBtnRand8';
    vSetActive(btnId);
    vClearCustom();
    if (vTotalVideos === 0) {{ document.getElementById('vStatusMsg').textContent = '⚠️ 暂无视频'; return; }}
    let shuffled = Array.from({{length: vTotalVideos}}, (_, i) => i);
    for (let i = shuffled.length - 1; i > 0; i--) {{
        let j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }}
    let indices = shuffled.slice(0, Math.min(count, vTotalVideos));
    vPlayList(indices);
}}

function vPlayCustom() {{
    vSetActive('vBtnCustom');
    const input = document.getElementById('vCustomInput').value.trim();
    if (!input) {{ document.getElementById('vStatusMsg').textContent = '⚠️ 请输入编号或范围'; return; }}
    let indices = [];
    if (input.includes('-')) {{
        let parts = input.split('-');
        let start = parseInt(parts[0]);
        let end = parseInt(parts[1]);
        if (isNaN(start) || isNaN(end) || start < 1 || end > vTotalVideos || start > end) {{
            document.getElementById('vStatusMsg').textContent = '⚠️ 请输入有效范围 (1 ~ ' + vTotalVideos + ')';
            return;
        }}
        for (let i = start - 1; i < end; i++) indices.push(i);
    }} else {{
        let nums = input.split(/\\s+/);
        for (let n of nums) {{
            let idx = parseInt(n) - 1;
            if (!isNaN(idx) && idx >= 0 && idx < vTotalVideos) indices.push(idx);
        }}
        if (indices.length === 0) {{ document.getElementById('vStatusMsg').textContent = '⚠️ 未识别到有效编号'; return; }}
    }}
    vPlayList(indices);
}}

function vTogglePlayPause() {{
    let video = document.getElementById('vVideoPlayer');
    if (!vIsPlaying || video.paused === undefined) {{ vPlaySequential(); return; }}
    if (video.paused) {{ video.play(); document.getElementById('vPlayPauseBtn').textContent = '⏸ 暂停'; }}
    else {{ video.pause(); document.getElementById('vPlayPauseBtn').textContent = '▶ 播放'; }}
}}

function vStopVideo() {{
    vIsPlaying = false;
    let video = document.getElementById('vVideoPlayer');
    video.pause();
    video.currentTime = 0;
    video.src = '';
    video.style.display = 'none';
    document.getElementById('vPlaceholder').style.display = 'block';
    document.getElementById('vPlayPauseBtn').textContent = '▶ 播放';
    document.getElementById('vStatusMsg').textContent = '⏹ 已停止';
    document.getElementById('vCurrentInfo').innerHTML = '📌 当前：已停止';
    vPlaylist = [];
    // ★★★ 新增：停止时自动退出全屏 ★★★
    if (document.fullscreenElement) {{
        document.exitFullscreen();
    }}
}}

function vToggleFullscreen() {{
    var modal = document.getElementById('videoPlayerModal');
    if (modal.classList.contains('fullscreen-active')) {{
        exitVideoFullscreen();
    }} else {{
        enterVideoFullscreen();
    }}
}}

function vRestoreSmall() {{
    if (document.fullscreenElement) document.exitFullscreen();
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
}}

function openVideoPlayer(source) {{
    beforeCenterAction();
    document.getElementById('videoPlayerModal').style.display = 'block';
    document.getElementById('vSourceSelect').value = source || 'fitness';
    document.getElementById('vVideoPlayer').style.display = 'none';
    document.getElementById('vVideoPlayerBg').style.display = 'none';
    document.getElementById('vPlaceholder').style.display = 'block';
    // 确保退出全屏状态
    exitVideoFullscreen();
    initVideoPlayer(source, false);
}}

function closeVideoPlayer() {{
    vStopVideo();
    exitVideoFullscreen();
    document.getElementById('videoPlayerModal').style.display = 'none';
}}

// ============================================================
// AI写诗
// ============================================================
function openAiPoem() {{
    beforeCenterAction();
    const modal = document.getElementById('aiPoemModal');
    modal.style.display = 'block';
    document.getElementById('aiGenre').value = '1';
    document.getElementById('aiCiPai').value = '';
    document.getElementById('aiPrompt').value = '';
    const resultDiv = document.getElementById('aiPoemResult');
    resultDiv.classList.remove('show');
    document.getElementById('poemOutput').innerHTML = '';
    document.getElementById('copyPoemBtn').style.display = 'none';
    document.getElementById('ciPaiGroup').style.display = 'none';
}}

function closeAiPoem() {{
    document.getElementById('aiPoemModal').style.display = 'none';
}}

document.addEventListener('DOMContentLoaded', function() {{
    const genreSelect = document.getElementById('aiGenre');
    if (genreSelect) {{
        genreSelect.addEventListener('change', function() {{
            const ciPaiGroup = document.getElementById('ciPaiGroup');
            ciPaiGroup.style.display = this.value === '5' ? 'flex' : 'none';
        }});
    }}
}});

async function generatePoem() {{
    const rhyme = document.getElementById('aiRhyme').value;
    const genreVal = document.getElementById('aiGenre').value;
    let genreText = '';
    let ciPai = '';
    if (genreVal === '1') genreText = '五绝';
    else if (genreVal === '2') genreText = '五律';
    else if (genreVal === '3') genreText = '七绝';
    else if (genreVal === '4') genreText = '七律';
    else if (genreVal === '5') {{
        ciPai = document.getElementById('aiCiPai').value.trim();
        if (!ciPai) {{
            alert('请输入词牌名');
            return;
        }}
        genreText = ciPai;
    }}
    const promptText = document.getElementById('aiPrompt').value.trim();
    if (!promptText) {{
        alert('请输入关键词或描述');
        return;
    }}
    const resultDiv = document.getElementById('aiPoemResult');
    const poemOutput = document.getElementById('poemOutput');
    const copyBtn = document.getElementById('copyPoemBtn');
    resultDiv.classList.add('show');
    poemOutput.innerText = '✍️ AI 正在创作中，请稍候...';
    copyBtn.style.display = 'none';
    try {{
        const response = await fetch(AI_POEM_WORKER_URL, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                rhyme: rhyme,
                genre: genreText,
                ciPai: ciPai,
                prompt: promptText
            }})
        }});
        const data = await response.json();
        if (data.poem) {{
            poemOutput.innerText = data.poem;
            copyBtn.style.display = 'inline-block';
        }} else {{
            poemOutput.innerText = '生成失败：' + (data.error || '未知错误');
        }}
    }} catch (err) {{
        poemOutput.innerText = '网络错误：' + err.message;
    }}
}}

function copyPoem() {{
    const poemText = document.getElementById('poemOutput').innerText;
    if (!poemText || poemText.includes('正在创作中') || poemText.includes('失败')) return;
    navigator.clipboard.writeText(poemText).then(() => {{
        alert('✅ 诗词已复制到剪贴板');
    }}).catch(() => {{
        alert('复制失败，请手动复制');
    }});
}}

document.addEventListener('DOMContentLoaded', function() {{
    const genBtn = document.getElementById('generatePoemBtn');
    if (genBtn) genBtn.addEventListener('click', generatePoem);
    const copyBtn = document.getElementById('copyPoemBtn');
    if (copyBtn) copyBtn.addEventListener('click', copyPoem);
}});

// ============================================================
// 访客留言
// ============================================================
let globalTwikooInited = false;

function openGuestbook() {{
    beforeCenterAction();
    const modal = document.getElementById('guestbookModal');
    modal.classList.add('active');
    if (!globalTwikooInited && typeof twikoo !== 'undefined') {{
        twikoo.init({{
            envId: 'https://twikoo.bingxue2026.com',
            el: '#twikoo-global',
            path: '/guestbook',
            lang: 'zh-CN',
            pageSize: 30,
            showPoweredBy: false
        }}).then(() => {{
            globalTwikooInited = true;
        }}).catch(err => console.error('全局留言板初始化失败', err));
    }}
}}

function closeGuestbook() {{
    document.getElementById('guestbookModal').classList.remove('active');
}}

// ============================================================
// 报告弹窗
// ============================================================
function openReport() {{
    document.getElementById('reportText').textContent = REPORT_TEXT;
    document.getElementById('reportModal').classList.add('active');
}}

function closeReport() {{
    document.getElementById('reportModal').classList.remove('active');
}}

// ============================================================
// 三重检索
// ============================================================
function toggleCiPaiInput(select) {{
    var ciPaiSelect = document.getElementById('searchGenreCiPai');
    if (select.value === '其他词牌') {{
        ciPaiSelect.style.display = 'inline-block';
        ciPaiSelect.focus();
        // 自动展开下拉（可选，但能提升体验）
        setTimeout(function() {{
            ciPaiSelect.size = 5;
        }}, 100);
        setTimeout(function() {{
            ciPaiSelect.size = 1;
        }}, 3000);
    }} else {{
        ciPaiSelect.style.display = 'none';
        ciPaiSelect.value = '';
    }}
}}

function openSearch() {{
    beforeCenterAction();
    document.getElementById('searchModal').style.display = 'block';
    const select = document.getElementById('searchGenreSelect');
    select.value = '';
    document.getElementById('searchGenreCiPai').style.display = 'none';
    document.getElementById('searchGenreCiPai').value = '';
}}

function closeSearch() {{
    document.getElementById('searchModal').style.display = 'none';
}}

function doSearch() {{
    const select = document.getElementById('searchGenreSelect');
    const ciPaiSelect = document.getElementById('searchGenreCiPai');
    let gStr = '';
    if (select.value === '其他词牌') {{
        gStr = ciPaiSelect.value;
        if (!gStr) {{
            gStr = '其他词牌';
        }}
    }} else if (select.value) {{
        gStr = select.value;
    }}
    const sStr = document.getElementById('searchStart').value.trim();
    const eStr = document.getElementById('searchEnd').value.trim();
    const kStr = document.getElementById('searchKeywords').value.trim();
    let r = POEMS;

    // 体裁匹配
    if (gStr) {{
        if (gStr === '其他词牌') {{
            // 一级菜单选了“其他词牌”，但二级菜单没选具体词牌
            // 先排除四种标准诗体，保留所有词牌（1137首）
            var standard = ['五绝', '五律', '七绝', '七律'];
            r = r.filter(function(p) {{
                return !standard.includes(p.genre);
            }});
            
        }} else if (gStr === '其他') {{
            // ★ 二级菜单选了“其他”
            // 从全部诗词中排除 4 种标准诗体 + 20 种词牌
            var excludeList = [
                '五绝', '五律', '七绝', '七律',
                '踏莎行', '鹧鸪天', '浣溪沙', '临江仙', '蝶恋花',
                '清平乐', '西江月', '菩萨蛮', '虞美人', '南乡子',
                '长相思', '卜算子', '采桑子', '减字木兰花', '沁园春',
                '水调歌头', '念奴娇', '满江红', '苏幕遮', '定风波'
            ];
            
            r = r.filter(function(p) {{
                var genre = p.genre || '';
                for (var j = 0; j < excludeList.length; j++) {{
                    if (genre.indexOf(excludeList[j]) !== -1) {{
                        return false;
                    }}
                }}
                return true;
            }});
            
        }} else {{
            // 精确匹配具体体裁或具体词牌
            if (gStr === '七绝' || gStr === '五绝' || gStr === '七律' || gStr === '五律') {{
                r = r.filter(function(p) {{
                    return p.genre === gStr;
                }});
            }} else {{
                r = r.filter(function(p) {{
                    return p.genre.indexOf(gStr) !== -1;
                }});
            }}
        }}
    }}

    // 日期范围
    let sm = null, em = null;
    if (sStr) {{ const ps = sStr.split(/\\s+/); if (ps.length === 2) sm = [parseInt(ps[0]), parseInt(ps[1])]; }}
    if (eStr) {{ const pe = eStr.split(/\\s+/); if (pe.length === 2) em = [parseInt(pe[0]), parseInt(pe[1])]; }}
    if (sm || em) {{ r = r.filter(p => {{ if (!p.date) return false; const pts = p.date.split('.'); const m = parseInt(pts[1]), d = parseInt(pts[2]); if (sm && (m < sm[0] || (m === sm[0] && d < sm[1]))) return false; if (em && (m > em[0] || (m === em[0] && d > em[1]))) return false; return true; }}); }}

    // 关键词
    if (kStr) {{ const ks = kStr.split(/\\s+/); r = r.filter(p => ks.some(k => (p.title + ' ' + p.body).includes(k))); }}

       closeSearch();
    render('综合检索结果', r);
    scrollToContent();
    
    // ★ 每次检索完成后，清空日期输入框
    document.getElementById('searchStart').value = '';
    document.getElementById('searchEnd').value = '';
}}

// ============================================================
// 拖拽功能（三重检索）
// ============================================================
function initDrag() {{
    const modal = document.getElementById('searchModalContent');
    const header = document.getElementById('searchModalHeader');
    if (!modal || !header) return;
    let isDragging = false, startX, startY, initialLeft, initialTop;
    header.onmousedown = function(e) {{
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = modal.getBoundingClientRect();
        initialLeft = rect.left;
        initialTop = rect.top;
        modal.style.transition = 'none';
        e.preventDefault();
    }};
    document.onmousemove = function(e) {{ if (!isDragging) return; modal.style.left = (initialLeft + e.clientX - startX) + 'px'; modal.style.top = (initialTop + e.clientY - startY) + 'px'; }};
    document.onmouseup = function() {{ isDragging = false; modal.style.transition = ''; }};
}}

// ============================================================
// 初始化
// ============================================================

// ============================================================
// ★★★ 增强版 fetchWithRetry（针对手机端彻底禁用缓存） ★★★
// ============================================================
function fetchWithRetry(url, options, retries, timeout) {{
    retries = retries || 3;
    timeout = timeout || 5000;
    // 强制追加反缓存头
    var headers = options.headers || {{}};
    headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
    headers['Pragma'] = 'no-cache';
    headers['Expires'] = '0';
    var newOptions = Object.assign({{}}, options, {{
        headers: headers,
        mode: 'cors',   // 明确跨域模式
        cache: 'no-store'
    }});
    return new Promise(function(resolve, reject) {{
        var controller = new AbortController();
        var timer = setTimeout(function() {{ controller.abort(); }}, timeout);
        var attempt = function(n) {{
            fetch(url, Object.assign({{}}, newOptions, {{ signal: controller.signal }}))
                .then(function(res) {{
                    clearTimeout(timer);
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.text();
                }})
                .then(resolve)
                .catch(function(err) {{
                    if (n > 0) {{
                        setTimeout(function() {{ attempt(n - 1); }}, 1000);
                    }} else {{
                        clearTimeout(timer);
                        reject(err);
                    }}
                }});
        }};
        attempt(retries);
    }});
}}

// ============================================================
// ★★★ 闲来听诗模块 ★★★
// ============================================================
var xianlaiPlaylist = [];
var xianlaiIndex = 0;
var xianlaiIsPlaying = false;
var xianlaiRandomCount = 5;
var xianlaiSelectedGenre = null;
var xianlaiSelectedGenreTheme = null;
var xianlaiSelectedTheme = null;
var xianlaiSelectedThemeGenre = null;
var xianlaiTripleResults = [];
var xianlaiAudio = null;
var xianlaiTimer = null;

function getGenreDisplay(genre) {{
    var standard = ['五绝', '五律', '七绝', '七律'];
    if (standard.includes(genre)) return genre;
    return '词牌诗词';
}}

function openXianLai() {{
    beforeCenterAction();
    document.getElementById('xianlaiOverlay').classList.add('active');
    initXianlaiPanels();
    switchXianlaiMode('today');
    bindXianlaiEvents();
}}

function closeXianLai() {{
    xianlaiStop();
    if (xianlaiAudio) {{
        xianlaiAudio.pause();
        xianlaiAudio.src = '';
        xianlaiAudio = null;
    }}
    if (xianlaiTimer) {{
        clearTimeout(xianlaiTimer);
        xianlaiTimer = null;
    }}
    xianlaiIsPlaying = false;  
    document.getElementById('xianlaiOverlay').classList.remove('active');
        // ★★★ 新增：关闭时退出全屏 ★★★
    if (document.fullscreenElement) {{
        document.exitFullscreen();
    }}
}}

function bindXianlaiEvents() {{
    document.getElementById('xianlaiCloseBtn').onclick = closeXianLai;
    document.getElementById('xianlaiStartToday').onclick = function() {{ startXianlaiPlay('today'); }};
    document.getElementById('xianlaiStartRandom').onclick = function() {{ startXianlaiPlay('random'); }};
    document.querySelectorAll('#xianlaiPanelRandom .sub-options button').forEach(function(btn) {{
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiPanelRandom .sub-options button').forEach(function(b) {{ b.classList.remove('selected'); }});
            this.classList.add('selected');
            xianlaiRandomCount = parseInt(this.dataset.count);
        }};
    }});
    document.getElementById('xianlaiStartGenre').onclick = function() {{ startXianlaiPlay('genre'); }};
    document.getElementById('xianlaiStartTheme').onclick = function() {{ startXianlaiPlay('theme'); }};
    document.getElementById('xianlaiTripleSearchBtn').onclick = doXianlaiTripleSearch;
    document.getElementById('xianlaiStartTriple').onclick = function() {{ startXianlaiPlay('triple'); }};
    document.getElementById('xianlaiPlayBtn').onclick = xianlaiTogglePlay;
    document.getElementById('xianlaiStopBtn').onclick = xianlaiStop;
    document.getElementById('xianlaiNextBtn').onclick = xianlaiNext;
    document.getElementById('xianlaiPrevBtn').onclick = xianlaiPrev;
}}

function initXianlaiPanels() {{
    var gc = document.getElementById('xianlaiGenreOptions');
    gc.innerHTML = '';
    GENRES.forEach(function(g) {{
        var btn = document.createElement('button');
        btn.textContent = g;
        btn.dataset.genre = g;
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiGenreOptions button').forEach(function(b) {{ b.classList.remove('selected'); }});
            this.classList.add('selected');
            xianlaiSelectedGenre = this.dataset.genre;
            updateXianlaiGenreThemes(xianlaiSelectedGenre);
        }};
        gc.appendChild(btn);
    }});

    var tc = document.getElementById('xianlaiThemeOptions');
    tc.innerHTML = '';
    THEMES.forEach(function(t) {{
        var btn = document.createElement('button');
        btn.textContent = t.length > 6 ? t.slice(0, 4) + '..' : t;
        btn.title = t;
        btn.dataset.theme = t;
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiThemeOptions button').forEach(function(b) {{ b.classList.remove('selected'); }});
            this.classList.add('selected');
            xianlaiSelectedTheme = this.dataset.theme;
            updateXianlaiThemeGenres(xianlaiSelectedTheme);
        }};
        tc.appendChild(btn);
    }});

    document.querySelectorAll('#xianlaiModeSelector button').forEach(function(btn) {{
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiModeSelector button').forEach(function(b) {{ b.classList.remove('active'); }});
            this.classList.add('active');
            switchXianlaiMode(this.dataset.mode);
        }};
    }});
}}

function switchXianlaiMode(mode) {{
    document.querySelectorAll('#xianlaiOverlay .mode-panel').forEach(function(p) {{ p.classList.remove('active'); }});
    var panelMap = {{
        'today': 'xianlaiPanelToday',
        'random': 'xianlaiPanelRandom',
        'genre': 'xianlaiPanelGenre',
        'theme': 'xianlaiPanelTheme',
        'triple': 'xianlaiPanelTriple'
    }};
    var panel = document.getElementById(panelMap[mode]);
    if (panel) panel.classList.add('active');
    xianlaiStop();
    document.getElementById('xianlaiCurrentTitle').textContent = '等待播放...';
    document.getElementById('xianlaiTextDisplay').innerHTML = '<span class="label">📝 选择模式后点击播放...</span>';
}}

function updateXianlaiGenreThemes(genre) {{
    var container = document.getElementById('xianlaiGenreThemeOptions');
    container.innerHTML = '';
    if (!genre) return;
    THEMES.forEach(function(t) {{
        var btn = document.createElement('button');
        btn.textContent = t.length > 8 ? t.slice(0, 6) + '..' : t;
        btn.title = t;
        btn.dataset.theme = t;
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiGenreThemeOptions button').forEach(function(b) {{ b.classList.remove('selected'); }});
            this.classList.add('selected');
            xianlaiSelectedGenreTheme = this.dataset.theme;
        }};
        container.appendChild(btn);
    }});
}}

function updateXianlaiThemeGenres(theme) {{
    var container = document.getElementById('xianlaiThemeGenreOptions');
    container.innerHTML = '';
    if (!theme) return;
    GENRES.forEach(function(g) {{
        var btn = document.createElement('button');
        btn.textContent = g;
        btn.dataset.genre = g;
        btn.onclick = function() {{
            document.querySelectorAll('#xianlaiThemeGenreOptions button').forEach(function(b) {{ b.classList.remove('selected'); }});
            this.classList.add('selected');
            xianlaiSelectedThemeGenre = this.dataset.genre;
        }};
        container.appendChild(btn);
    }});
}}

function toggleXianlaiCiPai(select) {{
    var ciPaiInput = document.getElementById('xianlaiTripleCiPai');
    if (select.value === '其他词牌') {{
        ciPaiInput.style.display = 'inline-block';
    }} else {{
        ciPaiInput.style.display = 'none';
        ciPaiInput.value = '';
    }}
}}

document.getElementById('xianlaiTripleGenre').onchange = function() {{ toggleXianlaiCiPai(this); }};

function doXianlaiTripleSearch() {{
    var select = document.getElementById('xianlaiTripleGenre');
    var ciPaiInput = document.getElementById('xianlaiTripleCiPai');
    var genre = '';
    if (select.value === '其他词牌') {{
        genre = ciPaiInput.value.trim();
    }} else if (select.value) {{
        genre = select.value;
    }}
    var start = document.getElementById('xianlaiTripleStart').value.trim();
    var end = document.getElementById('xianlaiTripleEnd').value.trim();
    var keyword = document.getElementById('xianlaiTripleKeyword').value.trim();

    var results = POEMS;
    if (genre) {{
        var gl = genre.split(/\\s+/);
        results = results.filter(function(p) {{
            var g = getGenreDisplay(p.genre);
            return gl.some(function(s) {{ return g.includes(s) || p.genre.includes(s); }});
        }});
    }}
    if (start) {{
        var parts = start.split(/\\s+/);
        if (parts.length === 2) {{
            var sm = parseInt(parts[0]), sd = parseInt(parts[1]);
            results = results.filter(function(p) {{
                if (!p.date) return false;
                var d = p.date.split('.');
                var pm = parseInt(d[1]), pd = parseInt(d[2]);
                return pm > sm || (pm === sm && pd >= sd);
            }});
        }}
    }}
    if (end) {{
        var parts = end.split(/\\s+/);
        if (parts.length === 2) {{
            var em = parseInt(parts[0]), ed = parseInt(parts[1]);
            results = results.filter(function(p) {{
                if (!p.date) return false;
                var d = p.date.split('.');
                var pm = parseInt(d[1]), pd = parseInt(d[2]);
                return pm < em || (pm === em && pd <= ed);
            }});
        }}
    }}
    if (keyword) {{
        var kw = keyword.split(/\\s+/);
        results = results.filter(function(p) {{
            var text = p.title + ' ' + p.body;
            return kw.some(function(k) {{ return text.includes(k); }});
        }});
    }}
    xianlaiTripleResults = results;
    document.getElementById('xianlaiTripleResult').textContent = '✅ 检索完成，找到 ' + results.length + ' 首诗词';
    if (results.length === 0) {{
        document.getElementById('xianlaiTripleResult').textContent = '⚠️ 没有找到符合条件的诗词';
    }}
}}

function getXianlaiTodayPoems() {{
    var today = new Date();
    var month = String(today.getMonth() + 1).padStart(2, '0');
    var day = String(today.getDate()).padStart(2, '0');
    return POEMS.filter(function(p) {{
        if (!p.date) return false;
        var parts = p.date.split('.');
        return parts[1] === month && parts[2] === day;
    }});
}}

function shuffleArray(arr) {{
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {{
        var j = Math.floor(Math.random() * (i + 1));
        var temp = a[i];
        a[i] = a[j];
        a[j] = temp;
    }}
    return a;
}}

function buildXianlaiPlaylist(mode) {{
    var playlist = [];
    switch (mode) {{
        case 'today':
            playlist = getXianlaiTodayPoems();
            playlist.sort(function(a, b) {{ return a.date.localeCompare(b.date); }});
            break;
        case 'random':
            playlist = shuffleArray(POEMS).slice(0, xianlaiRandomCount);
            break;
        case 'genre':
            if (!xianlaiSelectedGenre) {{ alert('请先选择体裁'); return []; }}
            if (!xianlaiSelectedGenreTheme) {{ alert('请先选择主题'); return []; }}
            var genreFilter = function(p) {{
                var standard = ['五绝', '五律', '七绝', '七律'];
                if (xianlaiSelectedGenre === '词牌诗词') {{
                    // 精确匹配：排除所有标准体裁，只匹配词牌 + 主题
                    return !standard.includes(p.genre) && p.themes && p.themes.indexOf(xianlaiSelectedGenreTheme) !== -1;
                }} else {{
                    return p.genre === xianlaiSelectedGenre && p.themes && p.themes.indexOf(xianlaiSelectedGenreTheme) !== -1;
                }}
            }};
            playlist = POEMS.filter(genreFilter);
            if (playlist.length === 0) {{ alert('该组合下没有诗词'); return []; }}
            playlist = shuffleArray(playlist).slice(0, 3);
            break;
        case 'theme':
            if (!xianlaiSelectedTheme) {{ alert('请先选择主题'); return []; }}
            if (!xianlaiSelectedThemeGenre) {{ alert('请先选择体裁'); return []; }}
            var themeFilter = function(p) {{
                var standard = ['五绝', '五律', '七绝', '七律'];
                if (xianlaiSelectedThemeGenre === '词牌诗词') {{
                    // 精确匹配：排除所有标准体裁，只匹配词牌 + 主题
                    return !standard.includes(p.genre) && p.themes && p.themes.indexOf(xianlaiSelectedTheme) !== -1;
                }} else {{
                    return p.genre === xianlaiSelectedThemeGenre && p.themes && p.themes.indexOf(xianlaiSelectedTheme) !== -1;
                }}
            }};
            playlist = POEMS.filter(themeFilter);
            if (playlist.length === 0) {{ alert('该组合下没有诗词'); return []; }}
            playlist = shuffleArray(playlist).slice(0, 3);
            break;
        case 'triple':
            if (xianlaiTripleResults.length === 0) {{ alert('请先进行检索'); return []; }}
            playlist = xianlaiTripleResults;
            break;
        default:
            return [];
    }}
    return playlist;
}}

function startXianlaiPlay(mode) {{
    xianlaiStop();
    if (xianlaiAudio) {{
        xianlaiAudio.pause();
        xianlaiAudio.src = '';
        xianlaiAudio = null;
    }}
    var playlist = buildXianlaiPlaylist(mode);
    if (playlist.length === 0) {{ alert('没有可播放的诗词'); return; }}
    xianlaiPlaylist = playlist;
    xianlaiIndex = 0;
    xianlaiIsPlaying = true;
        // ★★★ 新增：开始播放时自动全屏 ★★★
    var overlay = document.getElementById('xianlaiOverlay');
    if (overlay.requestFullscreen) {{
        overlay.requestFullscreen();
    }} else if (overlay.webkitRequestFullscreen) {{
        overlay.webkitRequestFullscreen();
    }}
    xianlaiPlayTrack(0);
}}

function xianlaiPlayTrack(index) {{
    if (!xianlaiIsPlaying) return;
    if (index >= xianlaiPlaylist.length) {{
        document.getElementById('xianlaiCurrentTitle').textContent = '✅ 全部播放完毕';
        document.getElementById('xianlaiPlayBtn').textContent = '▶ 播放';
        xianlaiIsPlaying = false;
        // ★★★ 新增：播放完毕退出全屏 ★★★
        if (document.fullscreenElement) {{
            document.exitFullscreen();
        }}
        return;
    }}
    var poem = xianlaiPlaylist[index];
    if (!poem) {{ xianlaiPlayTrack(index + 1); return; }}

    xianlaiIndex = index;
    var poemUrl = R2_BASE + '/recite/' + poem.poem_id + '_poem.mp3';
    var analysisUrl = R2_BASE + '/recite/' + poem.poem_id + '_analysis.mp3';

    document.getElementById('xianlaiCurrentTitle').textContent = poem.title + ' (' + (index + 1) + '/' + xianlaiPlaylist.length + ')';
    document.getElementById('xianlaiTrackIndex').textContent = (index + 1) + ' / ' + xianlaiPlaylist.length;
    document.getElementById('xianlaiPlayBtn').textContent = '⏸ 暂停';

    document.getElementById('xianlaiTextDisplay').innerHTML =
        '<div><span class="label">📝 诗词正文</span></div>' +
        '<div>' + poem.body + '</div>' +
        '<div style="margin-top:6px; border-top:1px dashed #ccc; padding-top:6px;">' +
        '<span class="label">📖 AI解析（加载中...）</span></div>' +
        '<div id="xianlaiAnalysisLoading">⏳ 正在加载解析...</div>';

    var txtUrl = R2_BASE + '/recite/' + poem.poem_id + '_analysis.txt';
    fetch(txtUrl)
        .then(function(res) {{
            if (!res.ok) throw new Error('not found');
            return res.text();
        }})
        .then(function(text) {{
            var el = document.getElementById('xianlaiAnalysisLoading');
            if (el) el.outerHTML = '<div style="margin-top:4px;">' + text + '</div>';
        }})
        .catch(function() {{
            var el = document.getElementById('xianlaiAnalysisLoading');
            if (el) el.outerHTML = '<div style="color:#666;">⚠️ 暂无解析文本</div>';
        }});

    // ★ 彻底销毁旧音频对象，并清除所有事件监听
    if (xianlaiAudio) {{
        xianlaiAudio.oncanplay = null;
        xianlaiAudio.ontimeupdate = null;
        xianlaiAudio.onended = null;
        xianlaiAudio.onerror = null;
        xianlaiAudio.pause();
        xianlaiAudio.src = '';
        xianlaiAudio = null;
    }}

    // 播放正文音频
    var audioPoem = new Audio(poemUrl);
    audioPoem.ontimeupdate = function() {{
        if (audioPoem && audioPoem.duration) {{
            document.getElementById('xianlaiCurrentProgress').textContent =
                formatTime(audioPoem.currentTime) + ' / ' + formatTime(audioPoem.duration);
        }}
    }};
    audioPoem.oncanplay = function() {{
        if (!xianlaiIsPlaying) return;
        audioPoem.play();
        xianlaiAudio = audioPoem;
    }};
    audioPoem.onended = function() {{
        if (!xianlaiIsPlaying) return;
        // 正文结束，加载解析音频
        var audioAnalysis = new Audio(analysisUrl);
        audioAnalysis.ontimeupdate = function() {{
            if (audioAnalysis && audioAnalysis.duration) {{
                document.getElementById('xianlaiCurrentProgress').textContent =
                    formatTime(audioAnalysis.currentTime) + ' / ' + formatTime(audioAnalysis.duration);
            }}
        }};
        audioAnalysis.oncanplay = function() {{
            if (!xianlaiIsPlaying) return;
            audioAnalysis.play();
            xianlaiAudio = audioAnalysis;
        }};
        audioAnalysis.onended = function() {{
            if (!xianlaiIsPlaying) return;
            xianlaiPlayTrack(index + 1);
        }};
        audioAnalysis.onerror = function() {{
            if (!xianlaiIsPlaying) return;
            xianlaiPlayTrack(index + 1);
        }};
        audioAnalysis.load();
    }};
    audioPoem.onerror = function() {{
        if (!xianlaiIsPlaying) return;
        // 正文加载失败，尝试直接播放解析
        var audioAnalysis = new Audio(analysisUrl);
        audioAnalysis.ontimeupdate = function() {{
            if (audioAnalysis && audioAnalysis.duration) {{
                document.getElementById('xianlaiCurrentProgress').textContent =
                    formatTime(audioAnalysis.currentTime) + ' / ' + formatTime(audioAnalysis.duration);
            }}
        }};
        audioAnalysis.oncanplay = function() {{
            if (!xianlaiIsPlaying) return;
            audioAnalysis.play();
            xianlaiAudio = audioAnalysis;
        }};
        audioAnalysis.onended = function() {{
            if (!xianlaiIsPlaying) return;
            xianlaiPlayTrack(index + 1);
        }};
        audioAnalysis.onerror = function() {{
            if (!xianlaiIsPlaying) return;
            xianlaiPlayTrack(index + 1);
        }};
        audioAnalysis.load();
    }};
    audioPoem.load();
}}

function xianlaiTogglePlay() {{
    if (!xianlaiAudio) return;
    if (xianlaiAudio.paused) {{
        xianlaiAudio.play();
        document.getElementById('xianlaiPlayBtn').textContent = '⏸ 暂停';
    }} else {{
        xianlaiAudio.pause();
        document.getElementById('xianlaiPlayBtn').textContent = '▶ 播放';
    }}
}}

function xianlaiStop() {{
    if (xianlaiAudio) {{
        // 清除事件监听
        xianlaiAudio.oncanplay = null;
        xianlaiAudio.ontimeupdate = null;
        xianlaiAudio.onended = null;
        xianlaiAudio.onerror = null;
        xianlaiAudio.pause();
        xianlaiAudio.src = '';
        xianlaiAudio = null;
    }}
    xianlaiIsPlaying = false;
    xianlaiPlaylist = [];
    xianlaiIndex = 0;
    document.getElementById('xianlaiPlayBtn').textContent = '▶ 播放';
    document.getElementById('xianlaiCurrentTitle').textContent = '已停止';
    document.getElementById('xianlaiTrackIndex').textContent = '0 / 0';
    document.getElementById('xianlaiTextDisplay').innerHTML = '<span class="label">📝 播放已停止</span>';
    document.getElementById('xianlaiCurrentProgress').textContent = '0:00 / 0:00';
        // ★★★ 新增：停止时退出全屏 ★★★
    if (document.fullscreenElement) {{
        document.exitFullscreen();
    }}
}}

function xianlaiNext() {{
    if (xianlaiPlaylist.length === 0) return;
    xianlaiStop();
    xianlaiIsPlaying = true;
    xianlaiPlayTrack(Math.min(xianlaiIndex + 1, xianlaiPlaylist.length - 1));
}}

function xianlaiPrev() {{
    if (xianlaiPlaylist.length === 0) return;
    xianlaiStop();
    xianlaiIsPlaying = true;
    xianlaiPlayTrack(Math.max(xianlaiIndex - 1, 0));
}}



// ============================================================
// 导出/备份修改后的诗词数据
// ============================================================
function exportEditedData() {{
    var keys = Object.keys(editedPoems);
    if (keys.length === 0) {{
        alert('暂无编辑过的诗词记录，不需要导出。');
        return;
    }}
    // 构建导出对象
    var data = {{
        export_time: new Date().toLocaleString(),
        poems: editedPoems
    }};
    var jsonStr = JSON.stringify(data, null, 2);
    var blob = new Blob([jsonStr], {{ type: 'application/json' }});
    var url = URL.createObjectURL(blob);
    
    var a = document.createElement('a');
    a.href = url;
    a.download = '冰雪诗词_编辑备份_' + new Date().toISOString().slice(0,10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert('✅ 修改记录已导出为 JSON 文件，请妥善保管！');
}}

// ============================================================
// 使用说明弹窗控制
// ============================================================
function openManual() {{
    beforeCenterAction();
    document.getElementById('manualModal').style.display = 'block';
    document.getElementById('manualContent').textContent = MANUAL_TEXT;
}}

function closeManual() {{
    document.getElementById('manualModal').style.display = 'none';
}}

function init() {{
    buildLeftSidebar();
    buildRightSidebar();
    buildLinksSubmenu();
    initDrag();
    initMobileMenuToggle();
    initDesktopPanelToggle();
    // 修改首页为“今日诗词”
    showTodayPoems();

    const analysisContent = document.getElementById('analysisModalContent');
    if (analysisContent) {{
        makeDraggable(analysisContent);
    }}

    const recitePlayer = document.getElementById('recitePlayer');
    if (recitePlayer) {{
        makeDraggable(recitePlayer);
    }}
}}

window.onclick = function(e) {{
    if (e.target.classList.contains('modal')) {{
        e.target.classList.remove('active');
    }}
}};
window.onload = init;
</script>

<!-- 访客统计 -->
<script>
(function() {{
  const WORKER_URL = 'https://visitor.bingxue2026.com';
  function getSource() {{
// ★ 新增2行：优先检查分享来源
    var search = window.location.search || '';
    if (search.indexOf('from=share') !== -1) return 'share';

    // 以下全部保持原样，一字不改
    var ref = document.referrer || '';
    if (ref.indexOf('baidu.com') !== -1) return 'baidu';
    if (ref.indexOf('toutiao.com') !== -1) return 'toutiao';
    if (ref.indexOf('so.com') !== -1) return '360';
    if (ref.indexOf('sogou.com') !== -1) return 'sogou';
    return 'direct';
  }}
  async function reportVisit() {{
    try {{
      await fetch(WORKER_URL, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ source: getSource() }})
      }});
    }} catch (e) {{}}
  }}
  async function loadStats() {{
    try {{
      var response = await fetch(WORKER_URL);
      var data = await response.json();
      var todayElem = document.getElementById('todayVisitorCount');
      var totalElem = document.getElementById('totalVisitorCount');
      if (todayElem) todayElem.innerText = data.today_visitors || 0;
      if (totalElem) totalElem.innerText = data.total_visitors || 0;
    }} catch (e) {{}}
  }}
  reportVisit().then(function() {{
    setTimeout(loadStats, 1000);
  }});
}})();
</script>

<!-- Twikoo 评论区优化 -->
<script>
(function() {{
  try {{
    localStorage.removeItem('twikoo');
  }} catch(e) {{}}
  window.addEventListener('load', function() {{
    setTimeout(function() {{
      var footerLinks = document.querySelectorAll('.tk-footer a');
      footerLinks.forEach(function(link) {{
        var span = document.createElement('span');
        span.textContent = link.textContent;
        if (link.parentNode) {{
          link.parentNode.replaceChild(span, link);
        }}
      }});
    }}, 600);
  }});
}})();
</script>

</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 最终版HTML已生成：{OUTPUT_HTML}")
    return True


# ============================================================
# 主程序入口
# ============================================================
def main():
    print("=" * 60)
    print("   冰雪诗词 · 最终完美版")
    print("=" * 60)

    if not os.path.exists(POEM_FILE):
        print(f"❌ 找不到诗词库：{POEM_FILE}")
        input("按回车退出...")
        return

    print("📖 正在解析诗词库...")
    poems = parse_poems(POEM_FILE, IMAGE_DIR)
    print(f"✅ 已读取 {len(poems)} 首诗词")

    with_images = sum(1 for p in poems if p['image_files'])
    print(f"✅ {with_images} 首有配图（基于文本标记解析）")

    print("📄 正在加载报告...")
    report_text = load_report(REPORT_FILE)

    print("📄 正在生成HTML...")
    generate_html(poems, report_text)

    print("\n" + "=" * 60)
    print("🎉 生成完成！")
    print("=" * 60)
    print("✅ 包含功能：")
    print("   · 展示、检索、AI朗诵、AI解诗")
    print("   · 爷孙诗语（视频播放）")
    print("   · 爷孙健身（动态下拉+顺序/随机播放）")
    print("   · AI写诗（生成诗词）")
    print("   · 访客留言（Twikoo）")
    print("   · 使用说明弹窗")
    print("   · 编辑数据导出备份")
    print("   · 浮窗拖拽")
    print("=" * 60)
    print("测试方法：")
    print("   双击 启动服务器.bat")
    print("   浏览器访问 http://localhost:8000/index.html")
    print("=" * 60)
    input("按回车退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")