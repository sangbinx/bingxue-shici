#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双模型优选合并 - 生成最终榜单（修正版）
精品：共识优先 + 1.3倍系数交替补足（每组最低5首）
优秀：两模型并集排除精品
"""

import json
import math

DEEPSEEK_FILE = 'poem_rankings.json'
MINIMAX_FILE = 'poem_rankings_minimax.json'
OUTPUT_FILE = 'poem_rankings_final.json'
TOTAL_POEMS = 2042
PREMIUM_RATIO = 1.3
MIN_PREMIUM = 5


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_group(ds_list, mm_list):
    """
    对单个分组进行合并，返回 (premium, excellent)
    premium: 共识优先 + 1.3倍系数交替补足
    excellent: 双方并集排除 premium
    """
    ds_set = set(ds_list)
    mm_set = set(mm_list)

    # 1. 共识：两边都有的，按 DS 顺序
    consensus = [pid for pid in ds_list if pid in mm_set]

    # 2. 各自独有
    only_ds = [pid for pid in ds_list if pid not in mm_set]
    only_mm = [pid for pid in mm_list if pid not in ds_set]

    # 3. 并集大小
    union_count = len(ds_set | mm_set)

    # 4. 精品目标数 = max(共识数 × 1.3, 5)，且不超过并集
    premium_target = max(math.ceil(len(consensus) * PREMIUM_RATIO), MIN_PREMIUM)
    premium_target = min(premium_target, union_count)

    # 5. 共识已够：直接截取
    if len(consensus) >= premium_target:
        premium = consensus[:premium_target]
    else:
        # 6. 交替补足
        premium = consensus[:]
        i_ds = 0
        i_mm = 0
        turn = 0  # 0=DS, 1=MM
        while len(premium) < premium_target:
            if turn == 0:
                if i_ds < len(only_ds):
                    premium.append(only_ds[i_ds])
                    i_ds += 1
                elif i_mm < len(only_mm):
                    premium.append(only_mm[i_mm])
                    i_mm += 1
                else:
                    break
                turn = 1
            else:
                if i_mm < len(only_mm):
                    premium.append(only_mm[i_mm])
                    i_mm += 1
                elif i_ds < len(only_ds):
                    premium.append(only_ds[i_ds])
                    i_ds += 1
                else:
                    break
                turn = 0

    # 7. 优秀：双方并集排除精品
    premium_set = set(premium)
    excellent = []
    for pid in ds_list:
        if pid not in premium_set and pid not in excellent:
            excellent.append(pid)
    for pid in mm_list:
        if pid not in premium_set and pid not in excellent:
            excellent.append(pid)

    return premium, excellent


def main():
    print("=" * 60)
    print("  双模型优选合并 - 生成最终榜单（修正版）")
    print("=" * 60)

    ds = load_json(DEEPSEEK_FILE)
    mm = load_json(MINIMAX_FILE)

    all_groups = sorted(set(ds.keys()) | set(mm.keys()))

    final = {}
    total_premium = 0
    total_excellent = 0

    print("\n📊 分组处理：")
    for group in all_groups:
        ds_list = ds.get(group, [])
        mm_list = mm.get(group, [])
        premium, excellent = build_group(ds_list, mm_list)
        final[group] = {
            'premium': premium,
            'excellent': excellent
        }
        total_premium += len(premium)
        total_excellent += len(excellent)
        print(f"  {group}: 精品 {len(premium)} 首，优秀 {len(excellent)} 首")

    total_selected = total_premium + total_excellent
    percentage = round(total_selected / TOTAL_POEMS * 100, 1)

    statistics = {
        'total_poems': TOTAL_POEMS,
        'premium_count': total_premium,
        'excellent_count': total_excellent,
        'total_selected': total_selected,
        'percentage': f'{percentage}%'
    }

    output = {'_statistics': statistics}
    output.update(final)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📈 汇总统计")
    print("=" * 60)
    print(f"  全站诗词总数：{TOTAL_POEMS} 首")
    print(f"  精品榜单：{total_premium} 首")
    print(f"  优秀榜单：{total_excellent} 首")
    print(f"  合计入选：{total_selected} 首（约占 {percentage}%）")
    print(f"\n✅ 结果已保存到：{OUTPUT_FILE}")
    input("\n按回车退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")