import re
import os
import shutil

POEM_FILE = '冰雪诗词_规范格式.txt'
BACKUP_FILE = '冰雪诗词_规范格式_备份.txt'

def parse_and_replace(filepath, edits):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('----------------------------------------')
    new_blocks = []

    for block in blocks:
        if not block.strip():
            new_blocks.append(block)
            continue

        m_id = re.search(r'微博ID：\s*(\d+)', block)
        poem_id = m_id.group(1) if m_id else None

        if poem_id and poem_id in edits:
            new_body = edits[poem_id]
            lines = block.split('\n')
            new_lines = []
            body_started = False
            body_replaced = False

            for line in lines:
                stripped = line.strip()
                if re.match(r'^\d{4}\.\d{2}\.\d{2}$', stripped):
                    body_started = True
                    new_lines.append(line)
                    continue
                if body_started and not body_replaced:
                    if stripped and not stripped.startswith('图片') and stripped != '(无配图)':
                        new_lines.append(new_body)
                        body_replaced = True
                        continue
                    elif stripped.startswith('图片') or stripped == '(无配图)':
                        new_lines.append(line)
                        continue
                if body_replaced:
                    if stripped.startswith('图片') or stripped == '(无配图)' or not stripped:
                        new_lines.append(line)
                    continue
                new_lines.append(line)

            block = '\n'.join(new_lines)

        new_blocks.append(block)

    return '----------------------------------------'.join(new_blocks)


def main():
    print("=" * 50)
    print("  诗词库批量同步工具")
    print("=" * 50)
    print()
    print("请将从网页「导出修改」获取的内容粘贴到下方，输入空行结束：")
    print()

    edits = {}
    while True:
        line = input("> ").strip()
        if not line:
            break
        if '|||' in line:
            parts = line.split('|||', 1)
            if len(parts) == 2:
                edits[parts[0]] = parts[1]
                print(f"  ✅ 已记录 ID {parts[0]} 的修改")

    if not edits:
        print("❌ 未输入任何修改记录，退出。")
        input("\n按回车键退出...")
        return

    print(f"\n📊 共 {len(edits)} 条修改记录")
    confirm = input("确认同步到诗词库？(y/n)：").strip().lower()
    if confirm != 'y':
        print("已取消。")
        input("\n按回车键退出...")
        return

    if not os.path.exists(BACKUP_FILE):
        shutil.copy2(POEM_FILE, BACKUP_FILE)
        print(f"📄 已备份原文件到：{BACKUP_FILE}")

    new_content = parse_and_replace(POEM_FILE, edits)

    with open(POEM_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ 同步完成！{len(edits)} 首诗词已更新。")
    print(f"📄 原文件备份：{BACKUP_FILE}")
    print()
    print("💡 提示：同步完成后，请重新运行网站生成脚本以更新网页。")

    input("\n按回车键退出...")


if __name__ == '__main__':
    main()