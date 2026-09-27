#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词解析朗诵脚本（指定编号版）
- 只处理您输入的指定编号
- 不使用进度文件
- 强制重新生成并覆盖R2上已有文件
"""

import os
import re
import requests
import boto3
import time

# ========== 配置 ==========
TXT_FILE = '冰雪诗词_规范格式.txt'
MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')
MINIMAX_API_URL = 'https://api.minimax.chat/v1/chat/completions'
MINIMAX_TTS_URL = 'https://api.minimax.chat/v1/t2a_v2'

R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL', '')
R2_PUBLIC_URL = os.environ.get('R2_PUBLIC_URL', '')
R2_BUCKET_NAME = 'poem-audio-cache'

SLEEP_SECONDS = 2       # 每首间隔秒数
API_RETRY = 3           # API重试次数
# ==========================


def parse_poems(filepath):
    """解析 TXT 诗词库"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    blocks = re.split(r'\n-{5,}\n', text)
    poems = {}
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.search(r'诗词(\d+)', block)
        if not match:
            continue
        pid = match.group(1)
        lines = block.split('\n')
        date = ''
        for line in lines:
            m = re.search(r'(\d{4}\.\d{2}\.\d{2})', line)
            if m:
                date = m.group(1)
                break
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
        body_lines = []
        found_author = False
        found_date = False
        for i, line in enumerate(lines):
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
        poems[pid] = {'id': pid, 'title': title, 'date': date, 'body': body}
    return poems


def get_r2_image_urls(poem_id):
    """从 R2 获取图片公开链接"""
    images = []
    try:
        s3 = boto3.client(
            's3', endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        prefix = f'images/{poem_id}/'
        resp = s3.list_objects_v2(Bucket=R2_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                key = obj['Key']
                if key.lower().endswith(('.jpg', '.jpeg', '.png')):
                    images.append(f"{R2_PUBLIC_URL}/{key}")
        def sort_key(url):
            m = re.search(r'(\d+)\.\w+$', url)
            return int(m.group(1)) if m else 0
        images.sort(key=sort_key)
    except Exception as e:
        print(f"     ⚠️ 获取图片失败：{e}")
    return images


def minimax_analysis(poem, image_urls):
    """生成图文赏析（带重试）"""
    system_prompt = (
        "你是专业识图分析专家，使用MiniMax M3解读图像。"
        "执行以下不可违反规则："
        "1.全文仅使用标准简体中文输出，全程禁止任何英文单词、英文句子、拼音、中英混排；"
        "2.禁止出现任何英文术语、缩写、英文字母描述，所有画面元素、物体、色彩、布局全部用中文表达；"
        "3.禁止输出内部推理草稿、英文思考过程，不附带双语对照、不做中英翻译；"
        "4.即使图片内存在英文文字，仅用中文转述文字含义，不直接摘抄英文原文；"
        "5.输出结构通顺连贯，分点、段落全部纯中文，一旦出现英文视为违规。"
        "你的任务：完整、细致解读图片全部内容，并结合诗词生成精炼赏析。"
    )

    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }

    used_urls = image_urls[:6]

    if used_urls:
        user_text = (
            f"请结合以下诗词，写一段<250字的精炼赏析。\n\n"
            f"【标题】{poem['title']}\n"
            f"【创作日期】{poem['date']}\n"
            f"【作者】冰雪\n"
            f"【正文】\n{poem['body']}\n\n"
            f"你是资深古诗词鉴赏专家，文风温润流畅，赏析贴合原作意境。"
            f"配有 1 至多张配图时：不单独罗列画面，将画中景物、氛围轻柔融入诗文解读，诗画意境浑然一体，杜绝强行拼接画面描述；多张图画择核心意象简略融合，不堆砌画面细节。全文≤250 字。"
            f"统一约束：全程纯中文，解读通俗雅致，逻辑连贯，总文字严格控制在二百五十字以内，不超字数上限。"
            f"必要时与时间或季节或地域特征结合，或结合当时国内形势，或国际局势。全程只用简体中文，禁止出现任何英文。"
        )
        user_content = [{"type": "text", "text": user_text}]
        for url in used_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})
    else:
        user_text = (
            f"请结合以下诗词，写一段<200字的精炼赏析。\n\n"
            f"【标题】{poem['title']}\n"
            f"【创作日期】{poem['date']}\n"
            f"【作者】冰雪\n"
            f"【正文】\n{poem['body']}\n\n"
            f"无配图时：仅解读诗词，梳理意象、情感与主旨，全文≤200 字，行文自然不生硬。"
            f"统一约束：全程纯中文，解读通俗雅致，逻辑连贯，总文字严格控制在二百字以内。"
            f"全程只用简体中文，禁止出现任何英文。"
        )
        user_content = [{"type": "text", "text": user_text}]

    payload = {
        "model": "minimax-m3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "thinking": {"type": "disabled"}
    }

    for attempt in range(API_RETRY):
        try:
            resp = requests.post(MINIMAX_API_URL, json=payload, headers=headers, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    if content and content.strip():
                        return content
            else:
                print(f"     ⚠️ 赏析API状态码 {resp.status_code}，第{attempt+1}次重试...")
        except Exception as e:
            print(f"     ⚠️ 赏析API异常：{e}，第{attempt+1}次重试...")
        if attempt < API_RETRY - 1:
            time.sleep(5)

    return ''


def generate_tts_audio(text, voice):
    """生成朗诵音频（带重试）"""
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": "speech-2.8-hd", "text": text, "stream": False,
        "voice_setting": {"voice_id": voice, "speed": 0.85, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1}
    }
    for attempt in range(API_RETRY):
        try:
            resp = requests.post(MINIMAX_TTS_URL, json=payload, headers=headers, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                hex_audio = data.get('data', {}).get('audio', '')
                if hex_audio:
                    return bytes.fromhex(hex_audio)
            else:
                print(f"     ⚠️ TTS状态码 {resp.status_code}，第{attempt+1}次重试...")
        except Exception as e:
            print(f"     ⚠️ TTS异常：{e}，第{attempt+1}次重试...")
        if attempt < API_RETRY - 1:
            time.sleep(5)

    return None


def upload_to_r2(key, data, content_type):
    """上传到 R2（带重试）"""
    for attempt in range(API_RETRY):
        try:
            s3 = boto3.client(
                's3', endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name='auto'
            )
            s3.put_object(Bucket=R2_BUCKET_NAME, Key=key, Body=data, ContentType=content_type)
            return True
        except Exception as e:
            print(f"     ⚠️ R2上传失败：{e}，第{attempt+1}次重试...")
            if attempt < API_RETRY - 1:
                time.sleep(3)
    return False


def process_poem(p, image_urls, voice):
    """处理单首诗词：赏析 → 朗诵 → 存储"""
    # 1. 生成赏析
    analysis = minimax_analysis(p, image_urls)
    if not analysis:
        print(f"     ❌ 赏析生成失败")
        return False

    # 2. 构建朗诵文本
    title_for_tts = p['title'].replace('·', '。')
    date_str = p['date']
    if date_str and re.match(r'\d{4}\.\d{2}\.\d{2}', date_str):
        parts = date_str.split('.')
        formatted_date = f"创作于{int(parts[0])}年{int(parts[1])}月{int(parts[2])}日"
    else:
        formatted_date = ""

    if formatted_date:
        poem_text = f"{title_for_tts}。作者，冰雪。{formatted_date}。{p['body']}"
    else:
        poem_text = f"{title_for_tts}。作者，冰雪。{p['body']}"

    # 3. 生成朗诵
    poem_audio = generate_tts_audio(poem_text, voice)
    analysis_audio = generate_tts_audio(analysis, voice)

    if not poem_audio:
        print(f"     ❌ 正文朗诵生成失败")
        return False
    if not analysis_audio:
        print(f"     ❌ 赏析朗诵生成失败")
        return False

    # 4. 上传（三个都成功才算完成）
    ok1 = upload_to_r2(f'recite/{p["id"]}_poem.mp3', poem_audio, 'audio/mp3')
    ok2 = upload_to_r2(f'recite/{p["id"]}_analysis.mp3', analysis_audio, 'audio/mp3')
    ok3 = upload_to_r2(f'recite/{p["id"]}_analysis.txt',
                       analysis.encode('utf-8'), 'text/plain; charset=utf-8')

    if not (ok1 and ok2 and ok3):
        print(f"     ❌ R2上传不完整")
        return False

    return True


def main():
    print("=" * 60)
    print("  诗词解析朗诵脚本（指定编号版）")
    print("=" * 60)

    # 检查环境
    errors = []
    if not MINIMAX_API_KEY:
        errors.append("MINIMAX_API_KEY")
    if not R2_ACCESS_KEY_ID:
        errors.append("R2_ACCESS_KEY_ID")
    if not R2_PUBLIC_URL:
        errors.append("R2_PUBLIC_URL")
    if errors:
        print(f"\n⚠️ 缺少环境变量: {', '.join(errors)}")
        input("按回车退出...")
        return

    # 加载诗词库
    print("📖 加载诗词库...")
    poems = parse_poems(TXT_FILE)
    total = len(poems)
    print(f"✅ 共 {total} 首")

    # 输入指定编号
    print("\n请输入要处理的诗词编号（多个用逗号分隔）：")
    print("例如：493,1507,1806")
    user_input = input("编号：").strip()
    if not user_input:
        print("❌ 未输入编号")
        input("按回车退出...")
        return

    # 解析编号
    target_ids = []
    for x in re.split(r'[,，\s]+', user_input):
        x = x.strip()
        if x.isdigit():
            target_ids.append(x)

    if not target_ids:
        print("❌ 没有有效的编号")
        input("按回车退出...")
        return

    # 检查编号是否存在
    valid_ids = []
    for pid in target_ids:
        if pid in poems:
            valid_ids.append(pid)
        else:
            print(f"   ⚠️ 编号 {pid} 在诗词库中不存在，跳过")

    if not valid_ids:
        print("❌ 没有可处理的编号")
        input("按回车退出...")
        return

    print(f"\n✅ 将处理 {len(valid_ids)} 首：{', '.join(valid_ids)}")

    voices = ['male-qn-qingse', 'female-shaonv', 'presenter_male', 'presenter_female']

    success = 0
    failed = 0
    start_time = time.time()

    for i, pid in enumerate(valid_ids, 1):
        p = poems[pid]
        image_urls = get_r2_image_urls(pid)
        voice = voices[int(pid) % 4]

        print(f"\n[{i}/{len(valid_ids)}] 诗词 {pid}：{p['title']}")
        print(f"   📷 图片：{len(image_urls)} 张 | 🎤 {voice}")

        if process_poem(p, image_urls, voice):
            success += 1
            print(f"   ✅ 完成")
        else:
            failed += 1
            print(f"   ❌ 失败")

        time.sleep(SLEEP_SECONDS)

    # 统计
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ 本次完成：{success} 首")
    print(f"❌ 失败：{failed} 首")
    print(f"⏱ 用时：{elapsed:.0f} 秒（约 {elapsed/60:.1f} 分钟）")
    print(f"{'='*60}")
    input("按回车退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")