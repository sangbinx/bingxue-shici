import os
import subprocess

# ---------- 配置区 ----------
INPUT_RECITE = r"朗诵"
INPUT_FITNESS = r"健身"
OUTPUT_RECITE = r"诗词朗诵视频"
OUTPUT_FITNESS = r"健身锻炼视频"
# -------------------------

def convert_videos_ffmpeg(input_folder, output_folder):
    if not os.path.exists(input_folder):
        print(f"[跳过] 文件夹不存在: {input_folder}")
        return

    print(f"\n========== 开始处理: {input_folder} ==========")
    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']

    for file_name in os.listdir(input_folder):
        if not any(file_name.lower().endswith(ext) for ext in video_exts):
            continue

        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)

        if os.path.exists(output_path):
            print(f"[跳过] {file_name} 已存在")
            continue

        print(f"[转换] {file_name} ...")
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"  ✅ 完成 → {output_folder}/{file_name}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    print(f"========== {input_folder} 处理完毕 ==========\n")

def main():
    print("=" * 60)
    print("   冰雪诗词 - 视频自动转换工具 (FFmpeg版)")
    print("=" * 60)

    convert_videos_ffmpeg(INPUT_RECITE, OUTPUT_RECITE)
    convert_videos_ffmpeg(INPUT_FITNESS, OUTPUT_FITNESS)

    print("\n🎉 全部转换任务完成！")
    os.system("pause")

if __name__ == "__main__":
    main()