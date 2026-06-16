import os
import re
import json
from datetime import datetime

# ---------- 配置 ----------
POEM_FILE = '冰雪诗词_规范格式.txt'
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
    {'name': '微信公众号', 'type': 'qrcode', 'img': 'gzh_qr.jpg'},
    {'name': '抖音视频', 'type': 'qrcode', 'img': 'douyin_qr.jpg'},
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
        poem_id = ''
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
                id_match = re.search(r'诗词(\d+)', stripped)
                if id_match:
                    poem_id = id_match.group(1)
            if author_found and body_started:
                if stripped and not stripped.startswith('图片') and stripped != '(无配图)':
                    body_lines.append(stripped)
            if author_found and re.match(r'^\d{4}\.\d{2}\.\d{2}$', stripped):
                body_started = True
        body = '\n'.join(body_lines)
        full_text = title_line + ' ' + body
        if not poem_id and weibo_id:
            poem_id = weibo_id
        poems.append({
            'id': weibo_id,
            'poemId': poem_id,
            'title': title_line,
            'genre': genre,
            'body': body,
            'date': date_str,
            'themes': classify_themes(full_text),
            'images': []
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
    print("   正在生成冰雪诗词数字图书馆（手机版修复+访客留言底色）")
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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
<title>冰雪诗词 · 数字图书馆</title>
<!-- 百度统计代码开始 -->
<script>
var _hmt = _hmt || [];
(function() {{
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?a78c6d40062f7f473f651d5f5670fe85";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
}})();
</script>
<!-- 百度统计代码结束 -->
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
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
.panel-title {{ text-align: center; font-weight: bold; flex-shrink: 0; cursor: pointer; user-select: none; }}
.left-menu, .right-menu {{ flex: 1; overflow-y: auto; padding: 0; }}
.center-buttons {{ flex: 1; display: flex; flex-direction: column; gap: 5px; align-items: center; padding: 8px; overflow-y: auto; }}
.menu-item {{ margin-bottom: 1px; }}
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
.button-group {{ margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
.poem-comment-area {{ margin-top: 12px; padding-top: 8px; border-top: 1px dashed #e0d5c8; display: none; }}
.poem-comment-area.active {{ display: block; }}
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
.footer {{ background: #1b5e20; color: #c8e6c9; text-align: center; padding: 10px; font-size: 0.8em; letter-spacing: 1px; flex-shrink: 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 20px; }}
.footer .counter {{ font-size: 0.9em; }}
.footer .qrcode-container img {{ width: 80px; height: 80px; border-radius: 4px; }}
/* AI写诗模态框样式（紧凑布局，四韵律） */
#aiPoemModal .guestbook-modal-content {{
    background: #fce4e4;
    border-radius: 16px;
    padding: 20px 24px;
    width: 50%;
    max-width: 550px;
    max-height: 85vh;
    overflow-y: auto;
    border: 1px solid #f0d0d0;
}}
#aiPoemModal .modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8c8c8;
}}
#aiPoemModal .modal-header h3 {{
    font-size: 1.1rem;
    font-weight: normal;
    color: #a33;
    margin: 0;
}}
#aiPoemModal .modal-header .modal-close {{
    font-size: 1.4rem;
    cursor: pointer;
    color: #c66;
    line-height: 1;
}}
#aiPoemModal .modal-header .modal-close:hover {{
    color: #a33;
}}
#aiPoemModal .compact-row {{
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
}}
#aiPoemModal .compact-row .label {{
    width: 60px;
    flex-shrink: 0;
    font-weight: bold;
    font-size: 0.9rem;
    color: #a33;
}}
#aiPoemModal .compact-row .control {{
    flex: 1;
}}
#aiPoemModal .compact-row select,
#aiPoemModal .compact-row input {{
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #e0c0c0;
    border-radius: 8px;
    font-size: 0.9rem;
    background: #fffef9;
}}
#aiPoemModal .two-cols {{
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
}}
#aiPoemModal .two-cols .compact-row {{
    flex: 1;
    margin-bottom: 0;
}}
#aiPoemModal .ci-pai-group {{
    margin-bottom: 16px;
}}
#aiPoemModal .prompt-section {{
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 8px;
}}
#aiPoemModal .prompt-label {{
    width: 60px;
    flex-shrink: 0;
    padding-top: 8px;
    font-weight: bold;
    font-size: 0.9rem;
    color: #a33;
}}
#aiPoemModal .prompt-textarea {{
    flex: 1;
}}
#aiPoemModal .prompt-textarea textarea {{
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #e0c0c0;
    border-radius: 8px;
    font-size: 0.9rem;
    resize: vertical;
    height: 110px;
    background: #fffef9;
}}
#aiPoemModal .button-row {{
    margin-top: 4px;
    margin-bottom: 20px;
    padding-left: 60px;
}}
#aiPoemModal .generate-btn {{
    background-color: #a33;
    color: white;
    border: none;
    padding: 8px 20px;
    border-radius: 30px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.2s;
}}
#aiPoemModal .generate-btn:hover {{
    background-color: #722;
}}
#aiPoemModal .ai-poem-result {{
    background: #fff8f0;
    border-radius: 12px;
    padding: 14px;
    margin-top: 8px;
    border: 1px solid #e8d0d0;
    font-size: 0.9rem;
    line-height: 1.65;
    white-space: pre-wrap;
    max-height: 260px;
    overflow-y: auto;
    display: none;
}}
#aiPoemModal .ai-poem-result.show {{
    display: block;
}}
#aiPoemModal .copy-btn {{
    background: #c96;
    color: #fff;
    border: none;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin-top: 10px;
    cursor: pointer;
}}
/* 访客留言窗口底色 */
#guestbookModal .guestbook-modal-content {{
    background: #fef9e7;
}}
/* 评论区专家优化样式 */
.tk-preview {{ display: none !important; }}
.tk-submit-action-icon,
.OwO,
.OwO-logo,
[class*="OwO"],
.tk-upload-btn,
[class*="upload"] {{ display: none !important; }}
/* 手机版自定义编辑框样式 */
.custom-edit-modal {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
}}
.custom-edit-content {{
    background: #fffef9;
    border-radius: 16px;
    padding: 20px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}}
.custom-edit-content textarea {{
    width: 100%;
    height: 200px;
    padding: 12px;
    font-size: 1rem;
    line-height: 1.6;
    font-family: "楷体", KaiTi, serif;
    border: 1px solid #d0c0a0;
    border-radius: 8px;
    resize: vertical;
}}
.custom-edit-content .btn-group {{
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 16px;
}}
.custom-edit-content button {{
    padding: 8px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
}}
.custom-edit-content .save-btn {{
    background: #4caf50;
    color: white;
}}
.custom-edit-content .cancel-btn {{
    background: #ccc;
    color: #333;
}}
/* 手机版适配 */
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
    .video-modal-content {{ width: 95%; height: 90vh; padding: 10px; }}
    .video-body {{ flex-direction: column; }}
    .video-list-side {{ width: 100%; border-right: none; border-bottom: 1px solid #e0d5c1; padding-right: 0; padding-bottom: 6px; max-height: 130px; }}
    .video-player-area {{ min-height: 250px; }}
    .guestbook-modal-content, .report-modal-content {{ width: 95%; min-width: auto; padding: 14px; margin: 15px auto; }}
    .history-intro p {{ font-size: 0.85em; }}
    .footer {{ font-size: 0.7em; padding: 8px; gap: 10px; }}
    .footer .qrcode-container img {{ width: 60px; height: 60px; }}
    .back-to-top {{ bottom: 20px; right: 20px; width: 38px; height: 38px; font-size: 1em; }}
    /* AI写诗手机版 */
    #aiPoemModal .guestbook-modal-content {{
        width: 95% !important;
        max-width: 95% !important;
    }}
    #aiPoemModal .compact-row .label {{
        width: 55px;
        font-size: 0.85rem;
    }}
    #aiPoemModal .prompt-label {{
        width: 55px;
        font-size: 0.85rem;
    }}
    #aiPoemModal .button-row {{
        padding-left: 55px;
    }}
    #aiPoemModal .two-cols {{
        flex-direction: column;
        gap: 12px;
    }}
    /* 手机版编辑框更大 */
    .custom-edit-content textarea {{
        height: 280px;
        font-size: 1rem;
    }}
}}
@media screen and (max-width: 480px) {{
    .header h1 {{ font-size: 1.1em; letter-spacing: 2px; }}
    .center-buttons button {{ font-size: 0.72em; padding: 6px 8px; }}
    .poem-body {{ font-size: 0.9em; }}
    #aiPoemModal .compact-row .label {{
        width: 50px;
        font-size: 0.8rem;
    }}
    #aiPoemModal .prompt-label {{
        width: 50px;
        font-size: 0.8rem;
    }}
    #aiPoemModal .button-row {{
        padding-left: 50px;
    }}
    #aiPoemModal .generate-btn {{
        padding: 6px 16px;
        font-size: 0.85rem;
    }}
    .custom-edit-content textarea {{
        height: 320px;
    }}
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
    <button onclick="showUsageGuide()">使用说明</button>
    <button onclick="openSearch()">三重检索</button>
    <button onclick="showQRCode('诗词朗诵', 'gzh_qr.jpg')">诗词朗诵</button>
    <button onclick="openAiPoem()">AI写诗</button>
    <button onclick="showQRCode('健身视频', 'douyin_qr.jpg')">健身视频</button>
    <button onclick="openGuestbook()">访客留言</button>
    <button onclick="showTodayPoems()">今日诗词</button>
    <button onclick="exportEdits()">导出修改</button>
    <div class="links-wrapper">
      <button onclick="toggleLinks()">相关链接</button>
      <div class="links-submenu" id="linksSubmenu"></div>
    </div>
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

<div class="footer">
  <span>冰雪诗词数字图书馆 © 2026 | 共收录 {len(poems)} 首诗词</span>
  <span class="counter">累计访问：<span id="busuanzi_value_site_pv">加载中</span> 次</span>
  <span class="counter">今日访客：<span id="todayVisitorCount">加载中</span> 人</span>
  <div class="qrcode-container" title="扫码访问冰雪诗词">
    <img src="qrcode.jpg" alt="网站二维码" onerror="this.parentElement.innerHTML='<span style=color:#a0c0a0;font-size:0.7em;>📷二维码</span>'">
  </div>
</div>

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
<div id="twikoo-global"></div>
</div>
</div>

<!-- AI写诗模态框（紧凑布局，四韵律） -->
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
    <button id="copyPoemBtn" class="copy-btn" style="display: none;">复制诗词</button>
  </div>
</div>
</div>
</div>

<script async src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script>
<script src="https://unpkg.com/twikoo@1.6.40/dist/twikoo.all.min.js"></script>
<script>
const POEMS = {poems_json};
const REPORT_TEXT = {report_escaped};
const GENRES = ['五绝', '五律', '七绝', '七律', '词牌诗词'];
const THEMES = ['家国情怀与时代歌咏','山水田园与闲居雅趣','亲情友情与人间至爱','四时风光与节气流转','羁旅思乡与行吟纪游','感怀人生与自省述志','咏物寄意与比兴抒怀','怀古咏史与读文有感','节日庆典与民俗风情','唱和应酬与赠友之作'];
const FRIENDLY_LINKS = {links_json};

// AI写诗调用地址（固定，不再需要手动修改）
const AI_POEM_WORKER_URL = 'https://poem.bingxue2026.com';

// ========== 本地编辑管理 ==========
let editedPoems = JSON.parse(localStorage.getItem('editedPoems') || '{{}}');
const EDIT_PASSWORD = "bingxue2026";

// ========== 今日访客独立计数 ==========
function initDailyVisitor() {{
    const today = new Date().toDateString();
    const lastVisitDate = localStorage.getItem('lastVisitDate');
    let todayCount = parseInt(localStorage.getItem('todayVisitorCount') || '0');
    if (lastVisitDate !== today) {{
        todayCount = 0;
        localStorage.setItem('lastVisitDate', today);
        localStorage.setItem('todayVisitorCount', '0');
    }}
    if (!sessionStorage.getItem('todayVisited')) {{
        todayCount++;
        localStorage.setItem('todayVisitorCount', todayCount);
        sessionStorage.setItem('todayVisited', 'true');
    }}
    const todayElem = document.getElementById('todayVisitorCount');
    if(todayElem) todayElem.innerText = localStorage.getItem('todayVisitorCount') || '0';
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
    if (window.scrollY > 300) btn.style.display = 'block';
    else btn.style.display = 'none';
}});

// ========== 全局关闭其他区域菜单 ==========
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
const originalOpenSearch = window.openSearch;
const originalShowQRCode = window.showQRCode;
const originalToggleLinks = window.toggleLinks;
const originalOpenGuestbook = window.openGuestbook;
const originalShowTodayPoems = window.showTodayPoems;
const originalExportEdits = window.exportEdits;
window.openSearch = function() {{ beforeCenterAction(); if(originalOpenSearch) originalOpenSearch(); }};
window.showQRCode = function(title, imgFile) {{ beforeCenterAction(); if(originalShowQRCode) originalShowQRCode(title, imgFile); }};
window.toggleLinks = function() {{ beforeCenterAction(); if(originalToggleLinks) originalToggleLinks(); }};
window.openGuestbook = function() {{ beforeCenterAction(); if(originalOpenGuestbook) originalOpenGuestbook(); }};
window.showTodayPoems = function() {{ beforeCenterAction(); if(originalShowTodayPoems) originalShowTodayPoems(); }};
window.exportEdits = function() {{ beforeCenterAction(); if(originalExportEdits) originalExportEdits(); }};

// ========== 使用说明功能 ==========
function showUsageGuide() {{
    beforeCenterAction();
    const container = document.getElementById('content');
    container.innerHTML = '<div style="text-align:center; padding:40px;">📖 正在加载使用说明...</div>';
    fetch('userguide.txt')
        .then(response => {{
            if (!response.ok) throw new Error('文件未找到');
            return response.text();
        }})
        .then(text => {{
            const htmlText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\n/g, '<br>');
            container.innerHTML = `
                <div style="background:#fffef9; border-radius:12px; padding:20px;">
                    <h2 style="color:#2e7d32;">📖 使用说明</h2>
                    <div style="line-height:1.8; margin-top:15px;">${{htmlText}}</div>
                    <button onclick="showTodayPoems()" style="margin-top:20px; padding:8px 20px; background:#4caf50; color:#fff; border:none; border-radius:4px; cursor:pointer;">← 返回诗词</button>
                </div>
            `;
        }})
        .catch(() => {{
            container.innerHTML = `
                <div style="background:#fffef9; border-radius:12px; padding:20px;">
                    <h2 style="color:#2e7d32;">📖 使用说明</h2>
                    <p>使用说明文件（userguide.txt）尚未上传。</p>
                    <p>请在网站根目录放置 userguide.txt 文件。</p>
                    <button onclick="showTodayPoems()" style="margin-top:20px; padding:8px 20px; background:#4caf50; color:#fff; border:none; border-radius:4px; cursor:pointer;">← 返回诗词</button>
                </div>
            `;
        }});
    scrollToContent();
}}

// ========== 菜单互斥函数 ==========
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
function closeLeftMenuPanel() {{
    const leftMenu = document.getElementById('leftSidebar');
    if (leftMenu) leftMenu.classList.remove('open');
    closeAllLeftSubmenus();
}}
function closeRightMenuPanel() {{
    const rightMenu = document.getElementById('rightSidebar');
    if (rightMenu) rightMenu.classList.remove('open');
    closeAllRightSubmenus();
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
            closeRightMenuPanel();
            const linksSub = document.getElementById('linksSubmenu');
            if(linksSub) linksSub.classList.remove('open');
            clearAllActive();
        }});
    }}
    if (rightTitle && rightMenu) {{
        rightTitle.addEventListener('click', function() {{
            rightMenu.classList.toggle('open');
            closeLeftMenuPanel();
            const linksSub = document.getElementById('linksSubmenu');
            if(linksSub) linksSub.classList.remove('open');
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
        html += '<div class="submenu" id="submenu-genre-' + g.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '') + '">';
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
        html += '<div class="submenu" id="submenu-theme-' + th.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '') + '">';
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
    const targetId = 'submenu-genre-' + genre.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '');
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
    const targetId = 'submenu-theme-' + theme.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '');
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

// 自定义编辑框（手机版专用，尺寸更大）
function showCustomEditDialog(id, currentBody) {{
    return new Promise((resolve) => {{
        // 移除已有的弹窗
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
    }});
}}

function editPoem(id) {{
    let pwd = prompt("请输入编辑密码：");
    if (pwd !== EDIT_PASSWORD) {{
        if (pwd !== null) alert("密码错误，无法编辑。");
        return;
    }}
    let currentBody = document.getElementById('body-' + id).innerText;
    // 手机端使用自定义大尺寸编辑框，电脑端仍使用 prompt（但为了一致性，也使用自定义对话框）
    showCustomEditDialog(id, currentBody).then(newBody => {{
        if (newBody !== null && newBody !== currentBody) {{
            editedPoems[id] = newBody;
            localStorage.setItem('editedPoems', JSON.stringify(editedPoems));
            document.getElementById('body-' + id).innerHTML = newBody.replace(/\\n/g, '<br>');
            alert("修改已保存（本地）。");
        }}
    }});
}}

function exportEdits() {{
    let pwd = prompt("请输入导出密码：");
    if (pwd !== EDIT_PASSWORD) {{
        if (pwd !== null) alert("密码错误，无法导出。");
        return;
    }}
    if (Object.keys(editedPoems).length === 0) {{
        alert('暂无修改记录。');
        return;
    }}
    let lines = [];
    for (let id in editedPoems) {{
        lines.push(id + '|||' + editedPoems[id]);
    }}
    const output = lines.join('\\n');
    navigator.clipboard.writeText(output).then(() => {{
        alert('✅ 已复制 ' + Object.keys(editedPoems).length + ' 条修改记录到剪贴板！\\n\\n请运行 sync_poems.py 脚本，粘贴记录完成同步。');
    }}).catch(() => {{
        alert('📤 请复制以下内容：\\n\\n' + output + '\\n\\n然后运行 sync_poems.py 脚本，粘贴记录完成同步。');
    }});
}}

// ========== AI写诗功能 ==========
function openAiPoem() {{
    beforeCenterAction();
    document.getElementById('aiPoemModal').style.display = 'block';
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

// 绑定 AI 写诗按钮事件
document.addEventListener('DOMContentLoaded', function() {{
    const genBtn = document.getElementById('generatePoemBtn');
    if (genBtn) genBtn.addEventListener('click', generatePoem);
    const copyBtn = document.getElementById('copyPoemBtn');
    if (copyBtn) copyBtn.addEventListener('click', copyPoem);
}});

// ========== 每首诗词独立评论加载 ==========
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

function render(title, poems) {{
    const c = document.getElementById('content');
    if(poems.length===0){{ c.innerHTML='<p style="text-align:center;color:#888;margin-top:60px;">该分类下暂无诗词。</p>'; return; }}
    let h = '<h3 style="margin-bottom:15px;color:#2e7d32;">'+title+'（共'+poems.length+'首）</h3>';
    poems.forEach(p=>{{
        const pid = p.poemId || p.id;
        h += '<div class="poem-card" style="overflow: auto;">';
        const imgCount = p.images ? p.images.length : 0;
        if(imgCount > 0){{
            const isSingle = imgCount === 1;
            h += '<div class="poem-img-float' + (isSingle ? ' single-img' : '') + '" id="imgs-'+p.id+'" style="display:block;">';
            p.images.forEach((img,idx)=>{{ h += '<img src="'+img+'" loading="lazy" onerror="this.style.display=\\'none\\'" alt="配图'+(idx+1)+'" onclick="window.open(this.src)">'; }});
            h += '</div>';
        }}
        h += '<div class="poem-title">'+p.title+'</div>';
        h += '<div class="poem-author">冰雪</div>';
        if(p.date) h += '<div class="poem-date">'+p.date+'</div>';
        let displayBody = editedPoems[p.id] || p.body;
        h += '<div class="poem-body" id="body-'+p.id+'">'+displayBody.replace(/\\n/g, '<br>')+'</div>';
        if(imgCount > 0){{
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\''+p.id+'\\')">查看配图('+imgCount+')</button>';
        }}
        h += '<div class="button-group">';
        h += '<button class="edit-btn" onclick="editPoem(\\''+p.id+'\\')">编辑</button>';
        h += '<button class="comment-btn" onclick="togglePoemComment(\\''+pid+'\\')">留言</button>';
        h += '</div>';
        h += '<div id="poem-comment-'+pid+'" class="poem-comment-area">';
        h += '<div id="twikoo-poem-'+pid+'"></div>';
        h += '</div>';
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
            btn.textContent = '查看配图('+count+')';
        }} else {{
            container.style.display = 'block';
            btn.textContent = '收起配图('+container.querySelectorAll('img').length+')';
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
    if(matched.length === 0) {{ c.innerHTML = '<p style="text-align:center;color:#888;margin-top:60px;">今日暂无历史诗词。</p>'; return; }}
    let h = '<div class="history-intro"><p>'+today.getFullYear()+'年'+month+'月'+day+'日 '+weekDay+' · 请欣赏</p></div>';
    h += '<h3 style="margin-bottom:15px;color:#2e7d32;">历史上的今天（共'+matched.length+'首）</h3>';
    matched.forEach(p=>{{
        const pid = p.poemId || p.id;
        h += '<div class="poem-card">';
        const imgCount = p.images ? p.images.length : 0;
        if(imgCount > 0){{
            h += '<div class="poem-img-float open" id="imgs-'+p.id+'" style="display:block;">';
            p.images.forEach((img,idx)=>{{ h += '<img src="'+img+'" loading="lazy" onerror="this.style.display=\\'none\\'" alt="配图'+(idx+1)+'" onclick="window.open(this.src)">'; }});
            h += '</div>';
        }}
        h += '<div class="poem-title">'+p.title+'</div>';
        h += '<div class="poem-author">冰雪</div>';
        if(p.date) h += '<div class="poem-date">'+p.date+'</div>';
        let displayBody = editedPoems[p.id] || p.body;
        h += '<div class="poem-body" id="body-'+p.id+'">'+displayBody.replace(/\\n/g, '<br>')+'</div>';
        if(imgCount > 0){{
            h += '<button class="img-toggle-btn" onclick="toggleImgs(this,\\''+p.id+'\\')">收起配图('+imgCount+')</button>';
        }}
        h += '<div class="button-group">';
        h += '<button class="edit-btn" onclick="editPoem(\\''+p.id+'\\')">编辑</button>';
        h += '<button class="comment-btn" onclick="togglePoemComment(\\''+pid+'\\')">留言</button>';
        h += '</div>';
        h += '<div id="poem-comment-'+pid+'" class="poem-comment-area">';
        h += '<div id="twikoo-poem-'+pid+'"></div>';
        h += '</div>';
        h += '</div>';
    }});
    c.innerHTML = h;
    c.scrollTop = 0;
}}

// ========== 全局留言板（访客留言） ==========
let globalTwikooInited = false;
function openGuestbook() {{
    beforeCenterAction();
    const modal = document.getElementById('guestbookModal');
    modal.style.display = 'block';
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
function closeGuestbook() {{ document.getElementById('guestbookModal').style.display='none'; }}
function openReport() {{ document.getElementById('reportText').textContent = REPORT_TEXT; document.getElementById('reportModal').style.display='block'; }}
function closeReport() {{ document.getElementById('reportModal').style.display='none'; }}
function openSearch() {{ beforeCenterAction(); document.getElementById('searchModal').style.display='block'; }}
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

function initDrag() {{
    const modal = document.getElementById('searchModalContent');
    const header = document.getElementById('searchModalHeader');
    if(!modal || !header) return;
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

function init() {{
    initDailyVisitor();
    buildLeftSidebar();
    buildRightSidebar();
    buildLinksSubmenu();
    initDrag();
    initMobileMenuToggle();
    initDesktopPanelToggle();
    showTodayPoems();
}}

window.onclick = function(e){{ if(e.target.classList.contains('modal')) e.target.style.display='none'; }};
window.onload = init;
</script>

<!-- ==================== Twikoo 评论区专家优化代码 ==================== -->
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
<!-- ==================== 优化结束 ==================== -->

</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n{'=' * 60}")
    print(f"🎉 网站生成完毕！")
    print(f"📄 文件：{os.path.abspath(OUTPUT_HTML)}")
    print(f"{'=' * 60}")
    print("✅ 本次修改完成：")
    print("   1. AI写诗地址固定为 https://poem.bingxue2026.com")
    print("   2. 访客留言窗口添加浅米色底色 (#fef9e7)")
    print("   3. 修复手机版导出修改按钮（密码验证正常）")
    print("   4. 修复手机版编辑按钮，使用大尺寸自定义编辑框（高度200px以上）")
    print("   5. 其他功能完全保持原样")
    os.system("pause")

if __name__ == '__main__':
    main()