#!/usr/bin/env python3
"""
测试报告汇总脚本
功能：
1. 解析所有分片的 JUnit XML 报告
2. 统计测试结果
3. 生成汇总报告
"""

import argparse
import glob
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='Generate test summary report')
    parser.add_argument('--report-dir', type=str, required=True,
                        help='Directory containing test reports')
    parser.add_argument('--output-dir', type=str, default='summary',
                        help='Output directory for summary')
    return parser.parse_args()


def parse_junit_xml(xml_file: str) -> dict:
    """解析 JUnit XML 报告"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 统计
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        duration = 0.0

        # 查找所有测试套件
        for testsuite in root.iter('testsuite'):
            tests = int(testsuite.get('tests', 0))
            failures = int(testsuite.get('failures', 0))
            skips = int(testsuite.get('skipped', 0))
            errs = int(testsuite.get('errors', 0))
            time = float(testsuite.get('time', 0))

            total += tests
            failed += failures
            skipped += skips
            errors += errs
            duration += time

        passed = total - failed - skipped - errors

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors,
            'duration': duration
        }
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return None


def main():
    args = parse_args()

    report_dir = Path(args.report_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("Test Report Summary Generator")
    print(f"{'='*60}")
    print(f"Report directory: {report_dir}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

    # 查找所有 XML 报告
    xml_files = list(report_dir.glob('junit_shard_*.xml'))
    print(f"Found {len(xml_files)} XML report files")

    if not xml_files:
        print("No XML reports found")
        return 1

    # 解析所有报告
    all_results = []
    total_stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': 0,
        'duration': 0.0
    }

    for xml_file in xml_files:
        result = parse_junit_xml(str(xml_file))
        if result:
            shard_name = xml_file.stem.replace('junit_', '')
            result['shard'] = shard_name
            all_results.append(result)

            for key in total_stats:
                if key in result:
                    total_stats[key] += result[key]

    # 输出统计
    print(f"\n{'='*60}")
    print("Test Results Summary")
    print(f"{'='*60}")
    print(f"Total tests: {total_stats['total']}")
    print(f"Passed: {total_stats['passed']}")
    print(f"Failed: {total_stats['failed']}")
    print(f"Skipped: {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")
    print(f"Duration: {total_stats['duration']:.2f}s")
    print(f"{'='*60}\n")

    # 计算通过率
    if total_stats['total'] > 0:
        pass_rate = (total_stats['passed'] / total_stats['total']) * 100
        print(f"Pass rate: {pass_rate:.2f}%")

    # 保存汇总 JSON
    summary = {
        'timestamp': datetime.now().isoformat(),
        'shards': len(all_results),
        'results': all_results,
        'total': total_stats
    }

    summary_file = output_dir / 'test_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_file}")

    # 生成 Markdown 报告
    md_file = output_dir / 'test_summary.md'
    with open(md_file, 'w') as f:
        f.write("# PyTorch NPU Test Summary\n\n")
        f.write(f"**Generated at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Overall Statistics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total tests | {total_stats['total']} |\n")
        f.write(f"| Passed | {total_stats['passed']} |\n")
        f.write(f"| Failed | {total_stats['failed']} |\n")
        f.write(f"| Skipped | {total_stats['skipped']} |\n")
        f.write(f"| Errors | {total_stats['errors']} |\n")
        f.write(f"| Duration | {total_stats['duration']:.2f}s |\n")

        if total_stats['total'] > 0:
            f.write(f"| Pass rate | {pass_rate:.2f}% |\n")

        f.write("\n## Shard Details\n\n")
        f.write("| Shard | Tests | Passed | Failed | Skipped | Duration |\n")
        f.write("|-------|-------|--------|--------|---------|----------|\n")
        for r in sorted(all_results, key=lambda x: x.get('shard', '')):
            f.write(f"| {r['shard']} | {r['total']} | {r['passed']} | {r['failed']} | {r['skipped']} | {r['duration']:.2f}s |\n")

    print(f"Markdown report saved to {md_file}")

    return 0


if __name__ == '__main__':
    exit(main())