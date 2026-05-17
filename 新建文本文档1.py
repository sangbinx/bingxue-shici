import os
import re
import json
from datetime import datetime

# ---------- 配置 ----------
POEM_FILE = '冰雪诗词_规范格式_.txt'
REPORT_FILE = '冰雪诗词全集_分析评价报告.txt'
IMAGE_DIR = '冰雪诗词_全部图片'
RECITE_VIDEO_DIR = '诗词朗诵视频'
FITNESS_VIDEO_DIR = '健身锻炼视频'
OUTPUT_HTML = 'index.html'
# -------------------------

FRIENDLY_LINKS = [
    {'name': '搜韵', 'url': 'https://sou-yun.cn/'},
    {'name': '诗词吾爱', 'url': 'https://www.52shici.com/'},
    {'name': '古诗词网', 'url': 'https://www.gushiwen.cn/'},
]

def parse_poems_with_theme(filepath):
    poems = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = content.split('----------------------------------------')
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        weibo_id = ''
        title_line = ''
        genre = ''
        body = ''
        date_str = ''
        m_id = re.search(r'微博ID：\s*(\d+)', block)
        if m_id:
            weibo_id = m_id.group(1)
        m_date = re.search(r'(\d{4}\.\d{2}\.\d{2})', block)
        if m_date:
            date_str = m_date.group(1)
        lines = block.split('\n')
        author_found = False
        body_started = False
        body_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped == '冰雪':
                author_found = True
                continue
            if not author_found and '·' in stripped and not stripped.startswith('微博ID') and not stripped.startswith('【诗词'):
                title_line = stripped
                parts = stripped.split('·', 1)
                if len(parts) >= 1:
                    genre = parts[0].strip()
            if author_found and body_started:
                if stripped and not stripped.startswith('图片') and stripped != '(无配图)':
                    body_lines.append(stripped)
            if author_found and re.match(r'^\d{4}\.\d{2}\.\d{2}$', stripped):
                body_started = True
        body = '\n'.join(body_lines)
        full_text = title_line + ' ' + body
        poems.append({
            'id': weibo_id,
            'title': title_line,
            'genre': genre,
            'body': body,
            'date': date_str,
            'themes': classify_themes(full_text)
        })
    return poems

def classify_themes(text):
    themes = {
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
    matched_themes = []
    for theme, keywords in themes.items():
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        if count > 0:
            matched_themes.append(theme)
    if not matched_themes:
        matched_themes.append('感怀人生与自省述志')
    return matched_themes

def find_images(poem_id, image_base_dir):
    if not os.path.exists(image_base_dir):
        return []
    for dir_name in os.listdir(image_base_dir):
        if dir_name.startswith(poem_id):
            full_path = os.path.join(image_base_dir, dir_name)
            if os.path.isdir(full_path):
                images = []
                for img_file in sorted(os.listdir(full_path)):
                    if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        images.append(image_base_dir + '/' + dir_name + '/' + img_file)
                return images
    return []

def scan_videos(folder_path):
    videos = []
    if not os.path.exists(folder_path):
        return videos
    for file_name in sorted(os.listdir(folder_path)):
        if file_name.lower().endswith(('.mp4', '.webm', '.mov', '.avi', '.mkv')):
            videos.append({'name': file_name, 'path': folder_path + '/' + file_name})
    return videos

def load_report(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "暂无分析报告。"

def main():
    print("=" * 60)
    print("   正在生成冰雪诗词数字图书馆（手机彻底修复版）...")
    print("=" * 60)
    print("[1/5] 正在读取诗词库...")
    poems = parse_poems_with_theme(POEM_FILE)
    print(f"  ✅ 已读取 {len(poems)} 首诗词")
    print("[2/5] 正在查找图片关联...")
    for poem in poems:
        poem['images'] = find_images(poem['id'], IMAGE_DIR)
    print(f"  ✅ {sum(1 for p in poems if p['images'])} 首诗词有配图")
    print("[3/5] 正在加载分析报告...")
    report_text = load_report(REPORT_FILE)
    print("  ✅ 报告加载完成")
    print("[4/5] 正在扫描视频文件夹...")
    recite_videos = scan_videos(RECITE_VIDEO_DIR)
    fitness_videos = scan_videos(FITNESS_VIDEO_DIR)
    print(f"  ✅ 朗诵视频：{len(recite_videos)} 个，健身视频：{len(fitness_videos)} 个")
    print("[5/5] 正在生成网页文件...")

    poems_json = json.dumps(poems, ensure_ascii=False)
    report_escaped = json.dumps(report_text, ensure_ascii=False)
    recite_videos_json = json.dumps(recite_videos, ensure_ascii=False)
    fitness_videos_json = json.dumps(fitness_videos, ensure_ascii=False)
    links_json = json.dumps(FRIENDLY_LINKS, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>冰雪诗词 · 数字图书馆</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

/* ========== 桌面版样式 ========== */
body {{ font-family: "Microsoft YaHei", "楷体", KaiTi, serif; background: #e8f0e3; color: #2c2c2c; display: flex; flex-direction: column; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #2e7d32, #1b5e20); color: #f0f7e6; padding: 10px 20px; display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; }}
.header h1 {{ font-size: 1.6em; letter-spacing: 6px; font-weight: normal; text-align: center; }}
.header-info {{ display: flex; align-items: center; gap: 8px; font-size: 0.8em; opacity: 0.95; }}
.header-info p {{ margin: 0; line-height: 1.4; }}
.header-info .detail-link {{ color: #fdd835; cursor: pointer; text-decoration: none; font-weight: bold; white-space: nowrap; }}
.header-info .detail-link:hover {{ color: #ffeb3b; text-decoration: underline; }}
.main {{ display: flex; flex: 1; }}
.left-panel {{ width: 120px; background: #fce4e4; display: flex; flex-direction: column; flex-shrink: 0; border-right: 2px solid #f0c0c0; }}
.left-panel .panel-title {{ background: #f8d0d0; color: #a33; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; }}
.right-panel {{ width: 120px; background: #e4ecfc; display: flex; flex-direction: column; flex-shrink: 0; border-left: 2px solid #c0c8f0; }}
.right-panel .panel-title {{ background: #d0d8f8; color: #36c; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; }}
.center-panel {{ width: 120px; display: flex; flex-direction: column; flex-shrink: 0; border-left: 2px solid #f0e0a0; border-right: 2px solid #f0e0a0; background: #fef9e7; }}
.center-panel .panel-title {{ background: #fef0c0; color: #a80; font-size: 0.75em; padding: 6px 0; letter-spacing: 1px; }}
.panel-title {{ text-align: center; font-weight: bold; flex-shrink: 0; }}
.left-menu, .right-menu {{ flex: 1; overflow-y: auto; padding: 0; }}
.center-buttons {{ flex: 1; display: flex; flex-direction: column; gap: 5px; align-items: center; padding: 8px; overflow-y: auto; }}
.menu-item {{ margin-bottom: 1px; }}
.menu-title {{ padding: 6px 8px; cursor: pointer; font-size: 0.78em; letter-spacing: 1px; transition: 0.2s; border-radius: 3px; margin: 0 4px; background: #f8d0d0; color: #a33; text-align: center; font-weight: bold; }}
.menu-title:hover {{ background: #f0b0b0; }}
.right-panel .menu-title {{ background: #d0d8f8; color: #36c; }}
.right-panel .menu-title:hover {{ background: #b8c8f0; }}
.submenu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; background: #fdf0f0; margin: 0 4px; border-radius: 0 0 3px 3px; }}
.right-panel .submenu {{ background: #f0f4fd; }}
.submenu.open {{ max-height: 500px; }}
.submenu a {{ display: block; padding: 5px 12px; color: #6b5050; text-decoration: none; font-size: 0.72em; letter-spacing: 1px; cursor: pointer; border-radius: 2px; margin: 1px 2px; background: #fef6f6; }}
.right-panel .submenu a {{ color: #505a6b; background: #f8fafe; }}
.submenu a:hover {{ background: #f8d0d0; }}
.right-panel .submenu a:hover {{ background: #d0d8f8; }}
.center-buttons button {{ width: 105px; padding: 6px 4px; background: #4caf50; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75em; letter-spacing: 1px; transition: 0.2s; }}
.center-buttons button:hover {{ background: #388e3c; }}
.links-wrapper {{ width: 105px; }}
.links-wrapper > button {{ width: 100%; }}
.links-submenu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; background: #e8f5e9; border-radius: 0 0 4px 4px; }}
.links-submenu.open {{ max-height: 300px; }}
.links-submenu a {{ display: block; padding: 6px 12px; color: #2c3e50; text-decoration: none; font-size: 0.75em; letter-spacing: 1px; border-bottom: 1px solid #c8e6c9; }}
.links-submenu a:hover {{ background: #c8e6c9; }}
.content {{ flex: 1; padding: 15px 25px; overflow-y: auto; background: #f5fbe8; }}
.poem-card {{ background: #fffef9; border-radius: 8px; padding: 20px 24px; margin-bottom: 22px; box-shadow: 0 1px 8px rgba(0,0,0,0.05); border-left: 3px solid #8bc34a; overflow: auto; }}
.poem-title {{ color: #2e7d32; font-size: 1.15em; margin-bottom: 6px; font-weight: normal; letter-spacing: 2px; text-align: left; }}
.poem-author {{ font-size: 0.95em; color: #4a5568; margin-bottom: 2px; letter-spacing: 2px; text-align: left; }}
.poem-date {{ font-size: 0.85em; color: #6b7b8d; margin-bottom: 10px; letter-spacing: 1px; text-align: left; }}
.poem-body {{ font-size: 1.1em; line-height: 2.1; white-space: pre-wrap; font-family: "楷体", KaiTi, serif; margin-top: 0; }}
.history-intro {{ background: linear-gradient(135deg, #fef9e7, #fefce8); padding: 14px 20px; border-radius: 8px; margin-bottom: 15px; border: 2px dashed #d4a853; text-align: center; }}
.history-intro p {{ color: #a08030; font-size: 1em; letter-spacing: 2px; }}
/* 桌面版：图片右浮动 */
.poem-img-float {{ display: none; float: right; width: 280px; max-height: 420px; overflow-y: auto; margin-left: 16px; margin-bottom: 8px; padding: 4px; background: #fafaf5; border-radius: 6px; border: 1px solid #e8e0d0; }}
.poem-img-float.open {{ display: block; }}
.poem-img-float img {{ width: 100%; max-height: 200px; object-fit: scale-down; border-radius: 4px; margin-bottom: 6px; border: 1px solid #e0d5c1; cursor: pointer; display: block; }}
.poem-img-float img:last-child {{ margin-bottom: 0; }}
.poem-img-float.single-img img {{ max-height: none; }}
.poem-img-float.single-img {{ max-height: none; overflow-y: visible; }}
.img-toggle-btn {{ display: inline-block; margin-top: 4px; padding: 5px 14px; background: #8bc34a; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; letter-spacing: 1px; }}
.img-toggle-btn:hover {{ background: #689f38; }}
.back-to-top {{ display: none; position: fixed; bottom: 30px; right: 30px; width: 44px; height: 44px; background: #4caf50; color: #fff; border: none; border-radius: 50%; font-size: 1.2em; cursor: pointer; z-index: 998; box-shadow: 0 2px 10px rgba(0,0,0,0.2); transition: 0.3s; }}
.back-to-top:hover {{ background: #388e3c; }}
.modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.15); z-index: 999; }}
.report-modal-content {{ background: #fefefe; margin: 30px auto; padding: 30px; width: 50%; min-width: 500px; max-height: 80vh; overflow-y: auto; border-radius: 8px; white-space: pre-wrap; font-size: 0.9em; line-height: 1.8; }}
.search-modal-content {{ background: #fefefe; position: absolute; top: 40px; left: 3%; width: 15%; min-width: 300px; max-height: 85vh; overflow-y: auto; border-radius: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.3); cursor: default; }}
.search-modal-header {{ cursor: move; background: #4caf50; color: #fff; padding: 10px 16px; margin: 0 0 14px 0; border-radius: 8px 8px 0 0; font-size: 1em; letter-spacing: 2px; user-select: none; }}
.search-modal-header .modal-close {{ float: right; cursor: pointer; color: #fff; font-size: 22px; }}
.search-row {{ margin-bottom: 10px; padding: 0 10px; }}
.search-row .hint {{ font-size: 0.75em; color: #888; margin-bottom: 3px; padding-left: 4px; }}
.search-row input {{ padding: 7px 10px; width: 100%; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; margin-left: 2px; }}
.search-row input.short {{ width: 47%; display: inline-block; }}
.search-row .between {{ margin: 0 3%; }}
.search-btn {{ padding: 8px 24px; background: #4caf50; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.95em; letter-spacing: 2px; margin-left: 10px; }}
.search-btn:hover {{ background: #388e3c; }}
.video-modal-content {{ background: #fefefe; margin: 20px auto; padding: 20px; width: 85%; max-width: 1200px; height: 85vh; overflow-y: auto; border-radius: 8px; display: flex; flex-direction: column; }}
.video-modal-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-shrink: 0; }}
.video-modal-header h3 {{ color: #2e7d32; letter-spacing: 2px; font-size: 1.1em; }}
.video-body {{ display: flex; flex: 1; gap: 16px; min-height: 0; }}
.video-list-side {{ width: 240px; overflow-y: auto; flex-shrink: 0; border-right: 1px solid #e0d5c1; padding-right: 12px; }}
.video-item {{ padding: 8px 10px; border-radius: 4px; cursor: pointer; font-size: 0.9em; margin-bottom: 4px; transition: 0.2s; }}
.video-item:hover {{ background: #f0f0f0; }}
.video-item.active {{ background: #e8f5e9; font-weight: bold; color: #2e7d32; }}
.video-player-area {{ flex: 1; display: flex; align-items: center; justify-content: center; min-height: 500px; background: #fafafa; border-radius: 6px; }}
.video-player-area p {{ color: #888; font-size: 1.1em; }}
.video-player-area video {{ width: 100%; max-height: 100%; border-radius: 4px; }}
.guestbook-modal-content {{ background: #fefefe; margin: 30px auto; padding: 24px; width: 50%; max-width: 600px; max-height: 80vh; overflow-y: auto; border-radius: 8px; }}
.guestbook-modal-content h3 {{ color: #2e7d32; margin-bottom: 16px; letter-spacing: 2px; }}
.guestbook-msg {{ background: #fdf6ec; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #d4a853; }}
.guestbook-msg .msg-author {{ color: #a08030; font-size: 0.85em; font-weight: bold; }}
.guestbook-msg .msg-time {{ color: #888; font-size: 0.75em; margin-left: 10px; }}
.guestbook-msg .msg-text {{ color: #4a4a4a; font-size: 0.9em; margin-top: 4px; }}
.guestbook-form {{ margin-top: 16px; display: flex; flex-direction: column; gap: 8px; }}
.guestbook-form input, .guestbook-form textarea {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; }}
.guestbook-form textarea {{ height: 80px; resize: vertical; }}
.guestbook-form button {{ width: 100px; padding: 8px; background: #4caf50; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; letter-spacing: 1px; align-self: flex-end; }}
.guestbook-form button:hover {{ background: #388e3c; }}
.footer {{ background: #1b5e20; color: #c8e6c9; text-align: center; padding: 8px; font-size: 0.8em; letter-spacing: 1px; flex-shrink: 0; }}

/* ========== 手机端样式 (max-width: 1024px) ========== */
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
    /* 左右菜单默认折叠 */
    .left-menu, .right-menu {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
    .left-menu.open, .right-menu.open {{ max-height: 800px; }}
    .left-panel .panel-title::after {{ content: ' ▼'; font-size: 0.6em; }}
    .right-panel .panel-title::after {{ content: ' ▼'; font-size: 0.6em; }}
    /* 体裁横向按钮行 */
    .genre-row {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 4px 6px; }}
    .genre-row .menu-title {{ font-size: 0.78em; padding: 6px 8px; margin: 0; border-radius: 4px; min-width: 40px; text-align: center; }}
    /* 内容横向按钮行：每行3个 */
    .theme-row {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 4px 6px; }}
    .theme-row .menu-title {{ font-size: 0.75em; padding: 6px 4px; margin: 0; border-radius: 4px; width: calc(33.33% - 6px); min-width: 80px; text-align: center; }}
    /* 中间功能区按钮 */
    .center-buttons {{ flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 5px; padding: 6px 8px; }}
    .center-buttons button {{ width: auto; padding: 7px 10px; font-size: 0.78em; min-width: 60px; }}
    .links-wrapper {{ width: auto; }}
    /* 手机端隐藏视频和智能体按钮 */
    .center-buttons button[onclick*="openVideoModal"],
    .center-buttons button[onclick*="coze.com"] {{ display: none !important; }}
    /* 子菜单横向排列 */
    .submenu {{ display: flex; flex-wrap: wrap; gap: 3px; padding: 4px 6px; justify-content: center; }}
    .submenu a {{ font-size: 0.72em; padding: 5px 8px; margin: 0; white-space: nowrap; }}
    /* 内容区 */
    .content {{ flex: none; width: 100%; padding: 8px 10px; overflow-y: visible; }}
    .poem-card {{ padding: 12px 14px; margin-bottom: 12px; }}
    .poem-title {{ font-size: 1em; }}
    .poem-body {{ font-size: 0.95em; line-height: 1.9; }}
    /* 手机版：图片在诗词下方，不浮动 */
    .poem-img-float {{ float: none !important; width: 100% !important; max-width: 100% !important; margin: 8px 0 !important; max-height: none !important; }}
    .poem-img-float img {{ max-height: 200px !important; }}
    .search-modal-content {{ width: 90%; left: 5%; min-width: auto; position: fixed; top: 50px; }}
    .video-modal-content {{ width: 95%; height: 90vh; padding: 10px; }}
    .video-body {{ flex-direction: column; }}
    .video-list-side {{ width: 100%; border-right: none; border-bottom: 1px solid #e0d5c1; padding-right: 0; padding-bottom: 6px; max-height: 130px; }}
    .video-player-area {{ min-height: 250px; }}
    .guestbook-modal-content, .report-modal-content {{ width: 95%; min-width: auto; padding: 14px; margin: 15px auto; }}
    .history-intro p {{ font-size: 0.85em; }}
    .footer {{ font-size: 0.7em; padding: 8px; }}
    .back-to-top {{ bottom: 20px; right: 20px; width: 38px; height: 38px; font-size: 1em; }}
}}
@media screen and (max-width: 480px) {{
    .header h1 {{ font-size: 1.1em; letter-spacing: 2px; }}
    .genre-row .menu-title {{ font-size: 0.72em; padding: 5px 6px; min-width: 35px; }}
    .theme-row .menu-title {{ font-size: 0.7em; width: calc(33.33% - 4px); min-width: 70px; }}
    .center-buttons button {{ font-size: 0.72em; padding: 6px 8px; }}
    .poem-body {{ font-size: 0.9em; }}
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
    <button onclick="openSearch()">三重检索</button>
    <button onclick="openVideoModal('recite')">诗词朗诵</button>
    <button onclick="window.open('https://www.coze.com/', '_blank')">诗词创作</button>
    <div class="links-wrapper">
      <button onclick="toggleLinks()">相关链接</button>
      <div class="links-submenu" id="linksSubmenu"></div>
    </div>
    <button onclick="openVideoModal('fitness')">健身视频</button>
    <button onclick="openGuestbook()">访客留言</button>
    <button onclick="showTodayPoems()">今日诗词</button>
  </div>
</div>

<div class="right-panel">
  <div class="panel-title" id="rightPanelTitle">按内容搜索</div>
  <div class="right-menu" id="rightSidebar"></div>
</div>

<div class="content" id="content">
<p style="text-align:center; color:#888; margin-top:100px; font-size:1.1em;">🌸 正在为您准备今日诗词...</p>
</div>
</div>

<button class="back-to-top" id="backToTop" onclick="scrollToTop()" title="返回顶部">⬆</button>

<div class="footer">冰雪诗词数字图书馆 © 2026 | 共收录 {len(poems)} 首诗词</div>

<div class="modal" id="reportModal">
<div class="report-modal-content">
<span class="modal-close" onclick="closeReport()">&times;</span>
<div id="reportText"></div>
</div>
</div>

<div class="modal" id="searchModal">
<div class="search-modal-content" id="searchModalContent">
<div class="search-modal-header" id="searchModalHeader">🔍 三重检索<span class="modal-close" onclick="closeSearch()">&times;</span></div>
<div class="search-row"><div class="hint">体裁（多个用空格隔开）</div><input type="text" id="searchGenre" placeholder="如：七绝 浣溪沙"></div>
<div class="search-row"><div class="hint">时间范围（月 日）</div><input type="text" id="searchStart" class="short" placeholder="起始 如 03 15"><span class="between">至</span><input type="text" id="searchEnd" class="short" placeholder="截止 如 05 20"></div>
<div class="search-row"><div class="hint">关键词（多个用空格隔开）</div><input type="text" id="searchKeywords" placeholder="如：人间 山川"></div>
<button class="search-btn" onclick="doSearch()">开始检索</button>
</div>
</div>

<div class="modal" id="videoModal">
<div class="video-modal-content">
<div class="video-modal-header"><h3 id="videoModalTitle"></h3><span class="modal-close" onclick="closeVideoModal()">&times;</span></div>
<div class="video-body"><div class="video-list-side" id="videoList"></div><div class="video-player-area" id="videoPlayer"><p>👈 请从左侧列表选择视频播放</p></div></div>
</div>
</div>

<div class="modal" id="guestbookModal">
<div class="guestbook-modal-content">
<span class="modal-close" onclick="closeGuestbook()">&times;</span>
<h3>📝 访客留言</h3>
<div id="guestbookMessages"></div>
<div class="guestbook-form">
  <input type="text" id="guestName" placeholder="您的昵称">
  <textarea id="guestMsg" placeholder="写下您想说的话..."></textarea>
  <button onclick="submitGuestbook()">提交留言</button>
</div>
</div>
</div>

<script>
const POEMS = {poems_json};
const REPORT_TEXT = {report_escaped};
const RECITE_VIDEOS = {recite_videos_json};
const FITNESS_VIDEOS = {fitness_videos_json};
const GENRES = ['五绝', '五律', '七绝', '七律', '词牌诗词'];
const THEMES = ['家国情怀与时代歌咏','山水田园与闲居雅趣','亲情友情与人间至爱','四时风光与节气流转','羁旅思乡与行吟纪游','感怀人生与自省述志','咏物寄意与比兴抒怀','怀古咏史与读文有感','节日庆典与民俗风情','唱和应酬与赠友之作'];
const FRIENDLY_LINKS = {links_json};

function closeAllMenus() {{
    document.querySelectorAll('.submenu').forEach(sub => sub.classList.remove('open'));
    document.getElementById('linksSubmenu').classList.remove('open');
    document.querySelectorAll('.left-menu').forEach(m => m.classList.remove('open'));
    document.querySelectorAll('.right-menu').forEach(m => m.classList.remove('open'));
}}

function scrollToContent() {{
    const content = document.getElementById('content');
    if (content && window.innerWidth <= 1024) {{
        setTimeout(() => {{ content.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); }}, 150);
    }}
}}

function scrollToTop() {{
    document.querySelector('.main').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

window.addEventListener('scroll', function() {{
    const btn = document.getElementById('backToTop');
    if (window.scrollY > 300) {{ btn.style.display = 'block'; }}
    else {{ btn.style.display = 'none'; }}
}});

function init() {{
    buildLeftSidebar();
    buildRightSidebar();
    buildLinksSubmenu();
    initDrag();
    initMobileMenuToggle();
    showTodayPoems();
}}

function initMobileMenuToggle() {{
    const leftTitle = document.getElementById('leftPanelTitle');
    const rightTitle = document.getElementById('rightPanelTitle');
    const leftMenu = document.getElementById('leftSidebar');
    const rightMenu = document.getElementById('rightSidebar');
    if (leftTitle && leftMenu) {{
        leftTitle.addEventListener('click', function() {{
            leftMenu.classList.toggle('open');
            if (rightMenu) rightMenu.classList.remove('open');
            document.getElementById('linksSubmenu').classList.remove('open');
        }});
    }}
    if (rightTitle && rightMenu) {{
        rightTitle.addEventListener('click', function() {{
            rightMenu.classList.toggle('open');
            if (leftMenu) leftMenu.classList.remove('open');
            document.getElementById('linksSubmenu').classList.remove('open');
        }});
    }}
}}

// ===== 桌面版侧边栏 =====
function buildLeftSidebar() {{
    const sb = document.getElementById('leftSidebar');
    let html = '';
    // 体裁横向排列行（手机用）
    html += '<div class="genre-row">';
    GENRES.forEach(g => {{
        html += '<div class="menu-title" onclick="showByGenre(\\'' + g + '\\')">' + g + '</div>';
    }});
    html += '</div>';
    // 体裁下的子菜单（电脑版下拉）
    GENRES.forEach(g => {{
        html += '<div class="submenu" id="submenu-genre-' + g.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '') + '">';
        html += '<a onclick="showByGenre(\\'' + g + '\\')">全部' + g + '</a>';
        THEMES.forEach(th => {{
            html += '<a onclick="showFilteredByGenre(\\'' + g + '\\', \\'' + th + '\\')">' + th.split('与')[0] + '</a>';
        }});
        html += '</div>';
    }});
    sb.innerHTML = html;
}}

function buildRightSidebar() {{
    const sb = document.getElementById('rightSidebar');
    let html = '';
    // 内容检索横向排列行（手机用）：每行3个
    html += '<div class="theme-row">';
    THEMES.forEach(th => {{
        html += '<div class="menu-title" onclick="showByTheme(\\'' + th + '\\')">' + th.split('与')[0] + '</div>';
    }});
    html += '</div>';
    // 内容下的子菜单（电脑版下拉）
    THEMES.forEach(th => {{
        html += '<div class="submenu" id="submenu-theme-' + th.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '') + '">';
        html += '<a onclick="showByTheme(\\'' + th + '\\')">全部</a>';
        GENRES.forEach(g => {{
            html += '<a onclick="showFilteredByTheme(\\'' + g + '\\', \\'' + th + '\\')">' + g + '</a>';
        }});
        html += '</div>';
    }});
    sb.innerHTML = html;
}}

// 电脑版：点击体裁标题展开/折叠子菜单
document.addEventListener('click', function(e) {{
    if (e.target.classList.contains('menu-title') && window.innerWidth > 1024) {{
        const submenu = e.target.nextElementSibling;
        if (submenu && submenu.classList.contains('submenu')) {{
            submenu.classList.toggle('open');
        }}
    }}
}});

function buildLinksSubmenu() {{
    const container = document.getElementById('linksSubmenu');
    let html = '';
    FRIENDLY_LINKS.forEach(link => {{
        html += '<a href="#" onclick="window.open(\\'' + link.url + '\\', \\'_blank\\'); return false;">' + link.name + '</a>';
    }});
    container.innerHTML = html;
}}

function toggleLinks() {{
    document.getElementById('linksSubmenu').classList.toggle('open');
}}

function showByGenre(genre) {{
    let f = genre==='词牌诗词' ? POEMS.filter(p=>!['五绝','五律','七绝','七律'].includes(p.genre)) : POEMS.filter(p=>p.genre===genre);
    render(genre+' · 全部', f);
    scrollToContent();
}}

function showByTheme(theme) {{
    let f = POEMS.filter(p => p.themes && p.themes.includes(theme));
    render(theme, f);
    scrollToContent();
}}

function showFilteredByGenre(genre, theme) {{
    let f1 = genre==='词牌诗词' ? POEMS.filter(p=>!['五绝','五律','七绝','七律'].includes(p.genre)) : POEMS.filter(p=>p.genre===genre);
    let f = f1.filter(p => p.themes && p.themes.includes(theme));
    render(genre+' · '+theme.split('与')[0], f);
    scrollToContent();
}}

function showFilteredByTheme(genre, theme) {{
    let f1 = POEMS.filter(p => p.themes && p.themes.includes(theme));
    let f = genre==='词牌诗词' ? f1.filter(p=>!['五绝','五律','七绝','七律'].includes(p.genre)) : f1.filter(p=>p.genre===genre);
    render(theme.split('与')[0]+' · '+genre, f);
    scrollToContent();
}}

function render(title, poems) {{
    const c = document.getElementById('content');
    if(poems.length===0){{ c.innerHTML='<p style="text-align:center;color:#888;margin-top:60px;">该分类下暂无诗词。</p>'; return; }}
    let h = '<h3 style="margin-bottom:15px;color:#2e7d32;">'+title+'（共'+poems.length+'首）</h3>';
    poems.forEach(p=>{{
        h += '<div class="poem-card">';
        h += '<div class="poem-title">'+p.title+'</div>';
        h += '<div class="poem-author">冰雪</div>';
        if(p.date) h += '<div class="poem-date">'+p.date+'</div>';
        h += '<div class="poem-body">'+p.body+'</div>';
        const imgCount = p.images ? p.images.length : 0;
        if(imgCount > 0){{
            const isSingle = imgCount === 1;
            // 图片区在诗词正文下方
            h += '<div class="poem-img-float' + (isSingle ? ' single-img' : '') + '" id="imgs-'+p.id+'" style="display:none;">';
            p.images.forEach((img,idx)=>{{ h += '<img src="'+img+'" loading="lazy" onerror="this.style.display=\\'none\\'" alt="配图'+(idx+1)+'" onclick="window.open(this.src)">'; }});
            h += '</div>';
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\''+p.id+'\\')">🖼️ 查看配图（'+imgCount+'张）</button>';
        }}
        h += '</div>';
    }});
    c.innerHTML = h;
    c.scrollTop = 0;
}}

function toggleImgs(btn, poemId) {{
    const container = document.getElementById('imgs-'+poemId);
    if(container) {{
        const isOpen = container.style.display === 'block';
        if(isOpen) {{
            container.style.display = 'none';
            const count = container.querySelectorAll('img').length;
            btn.textContent = '🖼️ 查看配图（'+count+'张）';
        }} else {{
            container.style.display = 'block';
            btn.textContent = '🖼️ 收起配图';
        }}
    }}
}}

function showTodayPoems() {{
    const today = new Date();
    const month = String(today.getMonth()+1).padStart(2,'0');
    const day = String(today.getDate()).padStart(2,'0');
    const weekDays = ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'];
    const weekDay = weekDays[today.getDay()];
    const matched = POEMS.filter(p => {{ if(!p.date) return false; const parts = p.date.split('.'); return parts[1] === month && parts[2] === day; }});
    const c = document.getElementById('content');
    if(matched.length === 0) {{ c.innerHTML = '<p style="text-align:center;color:#888;margin-top:60px;">今日暂无历史诗词，请从体裁或内容菜单中选择浏览。</p>'; return; }}
    let h = '<div class="history-intro"><p>'+today.getFullYear()+'年'+month+'月'+day+'日 '+weekDay+' · 请欣赏</p></div>';
    h += '<h3 style="margin-bottom:15px;color:#2e7d32;">历史上的今天（共'+matched.length+'首）</h3>';
    matched.forEach(p=>{{
        h += '<div class="poem-card">';
        h += '<div class="poem-title">'+p.title+'</div>';
        h += '<div class="poem-author">冰雪</div>';
        if(p.date) h += '<div class="poem-date">'+p.date+'</div>';
        h += '<div class="poem-body">'+p.body+'</div>';
        const imgCount = p.images ? p.images.length : 0;
        if(imgCount > 0){{
            h += '<div class="poem-img-float open" id="imgs-'+p.id+'" style="display:block;">';
            p.images.forEach((img,idx)=>{{ h += '<img src="'+img+'" loading="lazy" onerror="this.style.display=\\'none\\'" alt="配图'+(idx+1)+'" onclick="window.open(this.src)">'; }});
            h += '</div>';
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\''+p.id+'\\')">🖼️ 收起配图（'+imgCount+'张）</button>';
        }}
        h += '</div>';
    }});
    c.innerHTML = h;
    c.scrollTop = 0;
}}

function openReport() {{ document.getElementById('reportText').textContent = REPORT_TEXT; document.getElementById('reportModal').style.display='block'; }}
function closeReport() {{ document.getElementById('reportModal').style.display='none'; }}
function openSearch() {{ document.getElementById('searchModal').style.display='block'; }}
function closeSearch() {{ document.getElementById('searchModal').style.display='none'; }}

function doSearch() {{
    const gStr = document.getElementById('searchGenre').value.trim();
    const sStr = document.getElementById('searchStart').value.trim();
    const eStr = document.getElementById('searchEnd').value.trim();
    const kStr = document.getElementById('searchKeywords').value.trim();
    let r = POEMS;
    if(gStr){{ const gs = gStr.split(/\\s+/); r = r.filter(p=>gs.includes(p.genre)); }}
    let sm=null, em=null;
    if(sStr){{ const ps=sStr.split(/\\s+/); if(ps.length===2) sm=[parseInt(ps[0]),parseInt(ps[1])]; }}
    if(eStr){{ const pe=eStr.split(/\\s+/); if(pe.length===2) em=[parseInt(pe[0]),parseInt(pe[1])]; }}
    if(sm||em){{ r = r.filter(p=>{{ if(!p.date) return false; const pts=p.date.split('.'); const m=parseInt(pts[1]),d=parseInt(pts[2]); if(sm&&(m<sm[0]||(m===sm[0]&&d<sm[1]))) return false; if(em&&(m>em[0]||(m===em[0]&&d>em[1]))) return false; return true; }}); }}
    if(kStr){{ const ks = kStr.split(/\\s+/); r = r.filter(p => ks.some(k => (p.title + ' ' + p.body).includes(k))); }}
    closeSearch();
    render('综合检索结果', r);
    scrollToContent();
}}

function openVideoModal(type) {{
    const modal = document.getElementById('videoModal');
    const title = document.getElementById('videoModalTitle');
    const list = document.getElementById('videoList');
    const player = document.getElementById('videoPlayer');
    let videos = [];
    if (type === 'recite') {{ videos = RECITE_VIDEOS; title.textContent = '🎤 诗词朗诵'; }}
    else {{ videos = FITNESS_VIDEOS; title.textContent = '💪 健身视频'; }}
    player.innerHTML = '<p>👈 请从左侧列表选择视频播放</p>';
    if (videos.length === 0) {{ list.innerHTML = '<p style="color:#888; padding:10px;">暂无视频</p>'; }}
    else {{
        let html = '';
        videos.forEach((v, idx) => {{ html += '<div class="video-item" id="vid-item-'+idx+'" onclick="playVideo(\\'' + v.path + '\\', \\'' + v.name + '\\', '+idx+')"><span class="video-name">' + (idx+1) + '. ' + v.name + '</span></div>'; }});
        list.innerHTML = html;
    }}
    modal.style.display = 'block';
}}

function playVideo(path, name, idx) {{
    document.querySelectorAll('.video-item').forEach(el => el.classList.remove('active'));
    const item = document.getElementById('vid-item-'+idx);
    if(item) item.classList.add('active');
    document.getElementById('videoPlayer').innerHTML = '<video controls autoplay style="width:100%; height:100%; border-radius:4px;"><source src="' + path + '" type="video/mp4">您的浏览器不支持视频播放。</video>';
}}

function closeVideoModal() {{ document.getElementById('videoModal').style.display = 'none'; document.getElementById('videoPlayer').innerHTML = '<p>👈 请从左侧列表选择视频播放</p>'; }}

function openGuestbook() {{ document.getElementById('guestbookModal').style.display = 'block'; loadGuestbook(); }}
function closeGuestbook() {{ document.getElementById('guestbookModal').style.display = 'none'; }}

function loadGuestbook() {{
    const msgs = JSON.parse(localStorage.getItem('ice_guestbook') || '[]');
    const container = document.getElementById('guestbookMessages');
    if(msgs.length === 0) {{ container.innerHTML = '<p style="color:#888;text-align:center;padding:16px;">暂无留言，欢迎留下您的足迹！</p>'; }}
    else {{
        let html = '';
        msgs.slice(-20).reverse().forEach(m => {{ html += '<div class="guestbook-msg"><span class="msg-author">'+m.name+'</span><span class="msg-time">'+m.time+'</span><div class="msg-text">'+m.msg+'</div></div>'; }});
        container.innerHTML = html;
    }}
}}

function submitGuestbook() {{
    const name = document.getElementById('guestName').value.trim();
    const msg = document.getElementById('guestMsg').value.trim();
    if(!name || !msg) {{ alert('请填写昵称和留言内容。'); return; }}
    const msgs = JSON.parse(localStorage.getItem('ice_guestbook') || '[]');
    const now = new Date();
    msgs.push({{ name: name, msg: msg, time: now.getFullYear()+'-'+(now.getMonth()+1)+'-'+now.getDate()+' '+now.getHours()+':'+String(now.getMinutes()).padStart(2,'0') }});
    localStorage.setItem('ice_guestbook', JSON.stringify(msgs));
    document.getElementById('guestName').value = '';
    document.getElementById('guestMsg').value = '';
    loadGuestbook();
}}

function initDrag() {{
    const modal = document.getElementById('searchModalContent');
    const header = document.getElementById('searchModalHeader');
    let isDragging = false, startX, startY, initialLeft, initialTop;
    header.onmousedown = function(e) {{
        isDragging = true; startX = e.clientX; startY = e.clientY;
        const rect = modal.getBoundingClientRect();
        initialLeft = rect.left; initialTop = rect.top;
        modal.style.transition = 'none'; e.preventDefault();
    }};
    document.onmousemove = function(e) {{ if(!isDragging) return; modal.style.left = (initialLeft + e.clientX - startX) + 'px'; modal.style.top = (initialTop + e.clientY - startY) + 'px'; }};
    document.onmouseup = function() {{ isDragging = false; modal.style.transition = ''; }};
}}

window.onclick = function(e){{ if(e.target.classList.contains('modal')) e.target.style.display='none'; }};
window.onload = init;
</script>
</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n{'=' * 60}")
    print(f"🎉 网站生成完毕！")
    print(f"📄 文件：{os.path.abspath(OUTPUT_HTML)}")
    print(f"{'=' * 60}")
    os.system("pause")

if __name__ == '__main__':
    main()