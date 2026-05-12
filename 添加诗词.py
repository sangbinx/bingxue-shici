import os
import re

# ---------- 配置 ----------
NEW_POEM_FILE = '待添加诗词.txt'
MAIN_POEM_FILE = '冰雪诗词_规范格式.txt'
IMAGE_DIR = '冰雪诗词_全部图片'
# -------------------------

def main():
    print("=" * 60)
    print("   冰雪诗词 - 新诗整合工具 (结构修正版)")
    print("=" * 60)

    # 1. 检查文件
    if not os.path.exists(NEW_POEM_FILE):
        print(f"❌ 找不到文件 '{NEW_POEM_FILE}'")
        os.system("pause")
        return

    with open(NEW_POEM_FILE, 'r', encoding='utf-8') as f:
        new_content = f.read().strip()

    if not new_content:
        print("❌ 文件为空。")
        os.system("pause")
        return

    # 2. 用“四位数字序列号”作为分隔符，拆分每首诗词
    # 这会匹配每一行开头的四位数字（紧跟着换行或字符串开始）
    blocks = re.split(r'\n(?=\d{4}\n)', new_content)
    
    new_poems = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        if len(lines) < 5:  # 至少需要：序列号、标题、空行、冰雪、日期
            continue

        # ---- 提取字段 ----
        idx = 0
        seq_num = lines[idx].strip()
        if not re.match(r'^\d{4}$', seq_num):
            continue
        idx += 1

        # 标题行：体裁 + 空格 + 题目
        title_line = lines[idx].strip()
        idx += 1
        
        # 跳过标题和作者之间的空行（可能有多行，但一般是1行）
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        # 作者行：应为“冰雪”
        if idx >= len(lines) or lines[idx].strip() != '冰雪':
            continue
        author = lines[idx].strip()
        idx += 1

        # 日期行：年月日用空格分隔，如“2025 11 02”
        if idx >= len(lines):
            continue
        date_line = lines[idx].strip()
        # 将空格替换为点号，形成标准日期格式
        date_str = date_line.replace(' ', '.')
        idx += 1

        # 剩余部分为正文和图片行
        body_lines = []
        imgs = []
        # 跳过日期后的空行（如果有）
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        for i in range(idx, len(lines)):
            line_str = lines[i].strip()
            if line_str.startswith('图片') and '：' in line_str:
                imgs.append(line_str)
            else:
                body_lines.append(line_str)

        # 处理标题：体裁 + 空格 + 题目 -> 体裁·题目
        # 标题行可能包含多个空格，我们取第一个空格作为分隔
        title_parts = title_line.split(' ', 1)
        if len(title_parts) == 2:
            genre = title_parts[0].strip()
            topic = title_parts[1].strip()
            formatted_title = f"{genre}·{topic}"
        else:
            formatted_title = title_line  # 如果格式不符，保持原样

        body = '\n'.join(body_lines).strip()

        new_poems.append({
            'seq': seq_num,
            'title': formatted_title,
            'date': date_str,
            'body': body,
            'imgs': imgs
        })

    if not new_poems:
        print("❌ 未能解析到有效的新诗词。请检查格式是否符合：")
        print("   2048")
        print("   七律 题目")
        print("   (空行)")
        print("   冰雪")
        print("   2025 11 02")
        print("   正文...")
        print("   (空行)")
        print("   图片1")
        os.system("pause")
        return

    print(f"\n📖 共解析到 {len(new_poems)} 首新诗词：")
    for p in new_poems:
        print(f"   【{p['seq']}】 {p['title']}（{p['date']}）")

    # 3. 追加到规范诗词库
    print(f"\n📝 正在追加到诗词库 '{MAIN_POEM_FILE}' ...")
    with open(MAIN_POEM_FILE, 'a', encoding='utf-8') as f:
        for p in new_poems:
            f.write("\n")
            f.write(f"【诗词 {p['seq']}】\n")
            f.write(f"微博ID：{p['seq']}\n\n")
            f.write(f"{p['title']}\n\n")
            f.write(f"冰雪\n")
            f.write(f"{p['date']}\n\n")
            f.write(f"{p['body']}\n\n")
            if p['imgs']:
                for img_line in p['imgs']:
                    img_desc = img_line.split('：')[0]
                    img_num = img_desc.replace('图片', '')
                    new_img_line = f"图片{img_num}：{p['seq']}-{img_num}"
                    f.write(f"{new_img_line}\n")
            else:
                f.write("(无配图)\n")
            f.write("----------------------------------------\n")

    print("   ✅ 追加完成")

    # 4. 创建图片文件夹
    print(f"\n📁 正在创建图片文件夹 ...")
    for p in new_poems:
        safe_title = p['title'].replace('/', '_').replace('\\', '_').replace(':', '：').replace('*', 'x').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
        folder_name = f"{p['seq']} - {safe_title}"
        folder_path = os.path.join(IMAGE_DIR, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"   ✅ 创建文件夹: {folder_name}")
        else:
            print(f"   ⚠️ 文件夹已存在: {folder_name}")

    # 5. 清空待添加文件
    with open(NEW_POEM_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    print(f"\n📄 已清空 '{NEW_POEM_FILE}'，准备下次使用。")

    print(f"\n{'=' * 60}")
    print(f"🎉 新诗整合完毕！共添加 {len(new_poems)} 首")
    print(f"   请运行生成网站脚本，更新网页内容。")
    print(f"{'=' * 60}")
    os.system("pause")


if __name__ == '__main__':
    main()