import requests

# ========== 配置 ==========
API_KEY = "sk-6e1f46c6b59341cfbbc6d8378b4ca087"
# =========================

def ai_create_poem(genre, theme, yun=""):
    """调用 DeepSeek API 创作诗词"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 根据体裁和用韵构建指令
    yun_instruction = ""
    if yun:
        yun_instruction = f"请使用{yun}。"

    system_prompt = f"你是一位精通古典诗词的诗人，擅长五绝、五律、七绝、七律及各类词牌。创作必须严格符合格律要求。{yun_instruction}"

    user_prompt = f"请写一首关于「{theme}」的{genre}。"

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 400
    }

    print(f"\n⏳ 正在为您创作一首关于「{theme}」的{genre}...\n")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        poem = result["choices"][0]["message"]["content"]
        return poem
    except requests.exceptions.Timeout:
        return "❌ 请求超时，请检查网络后重试。"
    except Exception as e:
        return f"❌ 发生错误：{e}"


def main():
    print("=" * 50)
    print("   🌸 冰雪诗词 · AI 创作助手 🌸")
    print("=" * 50)
    print("  欢迎使用！请按提示输入您的创作需求。\n")

    # 第一步：选择体裁
    print("【第一步】请选择诗词体裁：")
    print("  1. 五绝    2. 五律    3. 七绝    4. 七律")
    print("  5. 浣溪沙  6. 鹧鸪天  7. 蝶恋花  8. 其他词牌")
    print("  （直接输入体裁名称或数字编号均可）")

    genre_map = {
        "1": "五绝", "2": "五律", "3": "七绝", "4": "七律",
        "5": "浣溪沙", "6": "鹧鸪天", "7": "蝶恋花", "8": "词牌"
    }

    genre_input = input("\n👉 请选择：").strip()

    if genre_input in genre_map:
        if genre_input == "8":
            genre = input("  请输入词牌名（如：满江红）：").strip()
            if not genre:
                genre = "浣溪沙"  # 默认
        else:
            genre = genre_map[genre_input]
    else:
        # 用户直接输入了体裁名称
        genre = genre_input if genre_input else "七绝"

    # 第二步：输入主题或内容
    print(f"\n【第二步】您要写的{genre}，是关于什么主题的？")
    print("  可以是一个词（如：秋天、思乡），也可以是一段话（如：夕阳下的湖边垂柳）")

    theme = input("👉 请输入：").strip()
    if not theme:
        theme = "人生感悟"

    # 第三步：选择用韵（可选）
    print(f"\n【第三步】请选择用韵（可选，直接回车跳过）：")
    print("  1. 平水韵    2. 中华新韵    3. 不指定")

    yun_map = {"1": "平水韵", "2": "中华新韵", "3": ""}
    yun_input = input("👉 请选择：").strip()
    yun = yun_map.get(yun_input, "")

    # 第四步：调用API生成诗词
    poem = ai_create_poem(genre, theme, yun)

    # 第五步：展示结果
    print("\n" + "=" * 50)
    print("   📜 创作成果")
    print("=" * 50)
    print(f"\n{poem}\n")
    print("=" * 50)

    # 是否继续？
    again = input("\n🔄 还想再写一首吗？(y/n)：").strip().lower()
    if again == 'y' or again == 'yes':
        print("\n" * 2)
        main()
    else:
        print("\n🌸 感谢使用冰雪诗词AI创作助手，祝您诗意长存！\n")

    input("\n按回车键退出...")


if __name__ == "__main__":
    main()