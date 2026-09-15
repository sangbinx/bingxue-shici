#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双模型优选结果对照分析
对比 DeepSeek 与 MiniMax 的诗词优选排名
"""

import json

DEEPSEEK_FILE = 'poem_rankings.json'
MINIMAX_FILE = 'poem_rankings_minimax.json'
OUTPUT_CONSENSUS = 'poem_rankings_consensus.json'
OUTPUT_REPORT = 'ranking_compare_report.txt'


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("  双模型优选结果对照分析")
    print("=" * 60)

    ds = load_json(DEEPSEEK_FILE)
    mm = load_json(MINIMAX_FILE)

    all_groups = sorted(set(ds.keys()) | set(mm.keys()))

    consensus = {}
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("双模型优选对照报告")
    report_lines.append("=" * 70)
    report_lines.append("")

    total_ds = 0
    total_mm = 0
    total_consensus = 0

    for group in all_groups:
        ds_list = ds.get(group, [])
        mm_list = mm.get(group, [])
        ds_set = set(ds_list)
        mm_set = set(mm_list)

        both = [pid for pid in ds_list if pid in mm_set]
        only_ds = [pid for pid in ds_list if pid not in mm_set]
        only_mm = [pid for pid in mm_list if pid not in ds_set]

        consensus[group] = both

        total_ds += len(ds_list)
        total_mm += len(mm_list)
        total_consensus += len(both)

        report_lines.append(f"【{group}】")
        report_lines.append(f"  DeepSeek 选中 {len(ds_list)} 首，MiniMax 选中 {len(mm_list)} 首")
        report_lines.append(f"  两者共识：{len(both)} 首")
        report_lines.append(f"  仅 DeepSeek：{len(only_ds)} 首 → {', '.join(only_ds)}")
        report_lines.append(f"  仅 MiniMax：{len(only_mm)} 首 → {', '.join(only_mm)}")
        report_lines.append("")

    report_lines.append("=" * 70)
    report_lines.append("汇总统计")
    report_lines.append("=" * 70)
    report_lines.append(f"DeepSeek 总入选：{total_ds} 首")
    report_lines.append(f"MiniMax 总入选：{total_mm} 首")
    report_lines.append(f"双模型共识：{total_consensus} 首")

    with open(OUTPUT_CONSENSUS, 'w', encoding='utf-8') as f:
        json.dump(consensus, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n📊 汇总统计：")
    print(f"  DeepSeek 总入选：{total_ds} 首")
    print(f"  MiniMax 总入选：{total_mm} 首")
    print(f"  双模型共识：{total_consensus} 首")
    print(f"\n✅ 共识榜单已保存到：{OUTPUT_CONSENSUS}")
    print(f"✅ 详细对照报告已保存到：{OUTPUT_REPORT}")

    input("\n按回车退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")