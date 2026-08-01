#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一视频播放器 · 最终完善版（顶部状态集中显示）
修复项：
1. 播放编号信息（第X号）移至顶部信息栏，与总数并排显示
2. 底部状态栏仅保留次要提示
"""
import os
import json
import boto3

# ===== R2 配置（完全沿用主脚本） =====
R2_BASE = 'https://pub-1f89bdd823e748d3b468bb1566f0c2a5.r2.dev'
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL', '')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'poem-audio-cache')

OUTPUT_FILE = 'player_test.html'

# ===== 扫描 R2 视频目录 =====
def scan_r2_directory(prefix):
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

# ===== 生成测试 HTML =====
def generate_test_html(fitness_files, video_files):
    fitness_urls = [f"{R2_BASE}/fitness/{f}" for f in fitness_files]
    video_urls = [f"{R2_BASE}/videos/{f}" for f in video_files]
    
    fitness_json = json.dumps(fitness_urls, ensure_ascii=False)
    video_json = json.dumps(video_urls, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统一视频播放器 · 最终版</title>
    <style>
        body {{ font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
        .player-container {{ background: #ffffff; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.12); width: 90%; max-width: 720px; padding: 20px 24px 24px 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .header h2 {{ margin: 0; color: #2c3e50; font-size: 1.2rem; }}
        .header .close-btn {{ background: none; border: none; font-size: 1.6rem; color: #999; cursor: pointer; }}
        
        /* ★★★ 信息栏优化：总数与当前播放编号并排显示 ★★★ */
        .info-bar {{ background: #eef2f7; border-radius: 8px; padding: 8px 14px; font-size: 0.9rem; color: #555; margin-bottom: 14px; text-align: center; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 6px; }}
        .info-bar .sep {{ color: #ccc; margin: 0 4px; }}
        .info-bar .current-highlight {{ color: #2c7be5; font-weight: bold; }}

        .mode-area {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; align-items: center; }}
        .mode-btn {{ padding: 6px 14px; border: none; border-radius: 20px; background: #e8ecf1; color: #333; cursor: pointer; font-size: 0.85rem; transition: 0.2s; }}
        .mode-btn:hover {{ background: #d0d7e0; }}
        .mode-btn.active {{ background: #2c7be5; color: #fff; }}
        .mode-btn.active:hover {{ background: #1a5bbf; }}
        .mode-area .custom-group {{ display: flex; gap: 6px; align-items: center; flex: 1; min-width: 180px; }}
        .mode-area .custom-group input {{ flex: 1; padding: 6px 10px; border: 1px solid #d0d7e0; border-radius: 20px; outline: none; font-size: 0.85rem; }}
        .mode-area .custom-group input:focus {{ border-color: #2c7be5; }}
        .video-wrapper {{ background: #000; border-radius: 8px; overflow: hidden; margin-bottom: 12px; }}
        .video-wrapper video {{ width: 100%; display: block; max-height: 400px; }}
        .video-wrapper .placeholder {{ color: #888; text-align: center; padding: 60px 0; background: #1a1a2e; }}
        .ctrl-bar {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 8px; }}
        .ctrl-bar button {{ padding: 6px 18px; border: none; border-radius: 6px; background: #f0f2f5; color: #333; cursor: pointer; }}
        .ctrl-bar .play-btn {{ background: #2c7be5; color: #fff; min-width: 70px; }}
        .ctrl-bar .stop-btn {{ background: #e74c3c; color: #fff; }}
        .ctrl-bar .full-btn {{ background: #27ae60; color: #fff; }}
        .status-msg {{ text-align: center; font-size: 0.8rem; color: #888; margin-top: 6px; min-height: 20px; }}
        #sourceSelect {{ padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; font-size: 0.85rem; }}
    </style>
</head>
<body>
<div class="player-container">
    <div class="header">
        <h2>🎬 统一视频播放器</h2>
        <button class="close-btn" onclick="closePlayer()">✕</button>
    </div>
    
    <!-- ★★★ 信息栏重构：总数和当前播放编号紧挨着 ★★★ -->
    <div class="info-bar" id="infoBar">
        📂 当前数据源：<select id="sourceSelect" onchange="switchSource()">
            <option value="fitness">💪 老来健身</option>
            <option value="video">👴👧 爷孙诗语</option>
        </select>
        <span class="sep">|</span>
        🔍 共 <span id="totalCount">0</span> 个视频 <span style="color:#999;">(编号 1 ~ <span id="maxNum">0</span>)</span>
        <span class="sep">|</span>
        <span id="currentInfo" class="current-highlight">📌 当前：无</span>
    </div>

    <div class="mode-area">
        <button id="btnSeq" class="mode-btn" onclick="playSequential()">▶ 顺序播放</button>
        <button id="btnRand3" class="mode-btn" onclick="playRandom(3)">🎲 随机3段</button>
        <button id="btnRand5" class="mode-btn" onclick="playRandom(5)">🎲 随机5段</button>
        <button id="btnRand8" class="mode-btn" onclick="playRandom(8)">🎲 随机8段</button>
        <div class="custom-group">
            <input type="text" id="customInput" placeholder="范围: 1-5 或 列表: 2 4 7">
            <button id="btnCustom" class="mode-btn" onclick="playCustom()">指定播放</button>
        </div>
    </div>
    <div class="video-wrapper">
        <video id="videoPlayer" controls></video>
        <div class="placeholder" id="placeholder">👆 选择模式开始播放</div>
    </div>
    <div class="ctrl-bar">
        <button class="play-btn" id="playPauseBtn" onclick="togglePlayPause()">⏸ 暂停</button>
        <button class="stop-btn" onclick="stopVideo()">⏹ 停止</button>
        <button class="full-btn" onclick="toggleFullscreen()">⛶ 全屏</button>
        <button onclick="restoreSmall()">☐ 小屏</button>
    </div>
    <div class="status-msg" id="statusMsg">等待操作...</div>
</div>

<script>
    // ===== 真实数据源 =====
    const DATA_SOURCES = {{ 'fitness': {fitness_json}, 'video': {video_json} }};

    let currentSource = 'fitness';
    let videoList = [];
    let totalVideos = 0;
    let playlist = [];
    let currentIndex = 0;
    let isPlaying = false;
    let videoElement = document.getElementById('videoPlayer');
    let placeholder = document.getElementById('placeholder');
    let playPauseBtn = document.getElementById('playPauseBtn');
    let statusMsg = document.getElementById('statusMsg');
    let currentInfo = document.getElementById('currentInfo');
    let customInput = document.getElementById('customInput');

    // ===== 更新顶部当前播放信息 =====
    function updateCurrentInfo(text) {{
        if (currentInfo) currentInfo.innerHTML = text;
    }}

    // ===== 按钮高亮互斥 =====
    function setActiveButton(btnId) {{
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        if (btnId) document.getElementById(btnId).classList.add('active');
    }}

    function clearCustomInput() {{
        customInput.value = '';
    }}

    // ===== 切换数据源 =====
    function switchSource() {{
        const sel = document.getElementById('sourceSelect');
        currentSource = sel.value;
        clearCustomInput();
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        initPlayer();
    }}

    function initPlayer() {{
        videoList = DATA_SOURCES[currentSource].slice();
        totalVideos = videoList.length;
        document.getElementById('totalCount').textContent = totalVideos;
        document.getElementById('maxNum').textContent = totalVideos;
        updateCurrentInfo('📌 当前：无');
        statusMsg.textContent = `✅ 已加载 ${{currentSource}}，共 ${{totalVideos}} 个视频`;
        stopVideo();
    }}

    // ===== 播放核心 =====
    function playList(indices) {{
        if (indices.length === 0) {{ statusMsg.textContent = '⚠️ 没有可播放的视频'; return; }}
        stopVideo();
        playlist = indices.slice();
        currentIndex = 0;
        isPlaying = true;
        playPauseBtn.textContent = '⏸ 暂停';
        statusMsg.textContent = `▶ 开始播放 ${{playlist.length}} 个视频`;
        playCurrent();
    }}

    function playCurrent() {{
        if (!isPlaying || currentIndex >= playlist.length) {{
            isPlaying = false;
            playPauseBtn.textContent = '▶ 播放';
            statusMsg.textContent = '✅ 全部播放完毕';
            placeholder.style.display = 'block';
            videoElement.style.display = 'none';
            updateCurrentInfo('📌 当前：播放完毕');
            clearCustomInput();
            return;
        }}
        const idx = playlist[currentIndex];
        const url = videoList[idx];
        if (!url) {{ currentIndex++; playCurrent(); return; }}
        placeholder.style.display = 'none';
        videoElement.style.display = 'block';
        videoElement.src = url;
        videoElement.play();
        // ★★★ 核心修改：顶部显示当前编号 ★★★
        updateCurrentInfo(`📌 当前：第 ${{idx+1}} 号， ${{currentIndex+1}}/${{playlist.length}}`);
        statusMsg.textContent = `▶ 正在播放第 ${{idx+1}} 号`;
        videoElement.onended = function() {{ currentIndex++; playCurrent(); }};
        videoElement.onerror = function() {{ statusMsg.textContent = `⚠️ 第 ${{idx+1}} 号加载失败，跳过`; currentIndex++; playCurrent(); }};
    }}

    // ===== 各播放模式 =====
    function playSequential() {{
        setActiveButton('btnSeq');
        clearCustomInput();
        let indices = Array.from({{length: totalVideos}}, (_, i) => i);
        playList(indices);
    }}

    function playRandom(count) {{
        let btnId = count===3 ? 'btnRand3' : count===5 ? 'btnRand5' : 'btnRand8';
        setActiveButton(btnId);
        clearCustomInput();
        if (totalVideos === 0) {{ statusMsg.textContent = '⚠️ 暂无视频'; return; }}
        let shuffled = Array.from({{length: totalVideos}}, (_, i) => i);
        for (let i = shuffled.length - 1; i > 0; i--) {{
            let j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }}
        let indices = shuffled.slice(0, Math.min(count, totalVideos));
        playList(indices);
    }}

    function playCustom() {{
        setActiveButton('btnCustom');
        const input = customInput.value.trim();
        if (!input) {{ statusMsg.textContent = '⚠️ 请输入编号或范围'; return; }}
        let indices = [];
        if (input.includes('-')) {{
            let parts = input.split('-');
            let start = parseInt(parts[0]);
            let end = parseInt(parts[1]);
            if (isNaN(start) || isNaN(end) || start < 1 || end > totalVideos || start > end) {{
                statusMsg.textContent = `⚠️ 请输入有效范围 (1 ~ ${{totalVideos}})`; return;
            }}
            for (let i = start - 1; i < end; i++) indices.push(i);
        }} else {{
            let nums = input.split(/\\s+/);
            for (let n of nums) {{
                let idx = parseInt(n) - 1;
                if (!isNaN(idx) && idx >= 0 && idx < totalVideos) indices.push(idx);
            }}
            if (indices.length === 0) {{ statusMsg.textContent = `⚠️ 未识别到有效编号`; return; }}
        }}
        playList(indices);
    }}

    // ===== 控制按钮 =====
    function togglePlayPause() {{
        if (!isPlaying || videoElement.paused === undefined) {{ playSequential(); return; }}
        if (videoElement.paused) {{ videoElement.play(); playPauseBtn.textContent = '⏸ 暂停'; }} 
        else {{ videoElement.pause(); playPauseBtn.textContent = '▶ 播放'; }}
    }}

    function stopVideo() {{
        isPlaying = false;
        videoElement.pause();
        videoElement.currentTime = 0;
        videoElement.src = '';
        videoElement.style.display = 'none';
        placeholder.style.display = 'block';
        playPauseBtn.textContent = '▶ 播放';
        statusMsg.textContent = '⏹ 已停止';
        updateCurrentInfo('📌 当前：已停止');
        playlist = [];
    }}

    function toggleFullscreen() {{
        if (videoElement.requestFullscreen) videoElement.requestFullscreen();
        else if (videoElement.webkitRequestFullscreen) videoElement.webkitRequestFullscreen();
    }}

    function restoreSmall() {{
        if (document.fullscreenElement) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
    }}

    function closePlayer() {{
        stopVideo();
        document.querySelector('.player-container').style.display = 'none';
        alert('播放器已关闭（测试完毕）');
    }}

    window.onload = function() {{
        initPlayer();
        videoElement.style.display = 'none';
        placeholder.style.display = 'block';
    }};
</script>
</body>
</html>'''

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 测试页面已生成：{OUTPUT_FILE}")

# ===== 主程序 =====
def main():
    print("=" * 50)
    print("   统一视频播放器 · 最终版（信息集中显示）")
    print("=" * 50)
    print("📡 正在连接 R2 并扫描真实数据源...")
    fitness_files = scan_r2_directory('fitness/')
    video_files = scan_r2_directory('videos/')
    print("📄 正在生成测试页面...")
    generate_test_html(fitness_files, video_files)
    print("\n🎉 测试页面生成完成！")
    print("👉 请双击打开 player_test.html 进行测试")
    print("   ✅ 总数与当前编号在顶部并排显示，一目了然")
    print("   ✅ 按钮互斥高亮、输入框自动清零")
    print("   ✅ 底部状态栏仅保留次要提示")
    print("=" * 50)
    input("按回车退出...")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")