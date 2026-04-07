#!/usr/bin/env python3
"""
NPU 测试分片执行脚本
功能：
1. 加载 disabled_testcases.json 禁用测试列表
2. 发现测试文件并分片
3. 执行 pytest 并生成 JUnit XML 报告
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set


def parse_args():
    parser = argparse.ArgumentParser(description='Run PyTorch NPU tests for a shard')
    parser.add_argument('--shard', type=int, required=True,
                        help='Shard number (1-indexed)')
    parser.add_argument('--num-shards', type=int, required=True,
                        help='Total number of shards')
    parser.add_argument('--test-dir', type=str, required=True,
                        help='Path to PyTorch test directory')
    parser.add_argument('--disabled-testcases', type=str,
                        help='Path to disabled_testcases.json')
    parser.add_argument('--report-dir', type=str, default='test-reports',
                        help='Directory for test reports')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout per test in seconds')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    return parser.parse_args()


def load_disabled_testcases(json_file: str) -> Set[str]:
    """加载 disabled_testcases.json 中的禁用测试用例"""
    disabled = set()
    if json_file and os.path.exists(json_file):
        with open(json_file) as f:
            data = json.load(f)
            # JSON 格式: {"test_name": ["reason", ["issues"]], ...}
            disabled = set(data.keys())
            print(f"Loaded {len(disabled)} disabled test cases from {json_file}")
    return disabled


def discover_test_files(test_dir: str) -> List[str]:
    """发现所有 test_*.py 文件"""
    test_path = Path(test_dir)
    test_files = []

    # 查找所有 test_*.py 文件（排除某些特殊目录）
    exclude_dirs = {'distributions', 'custom_ops', 'jit'}

    for test_file in test_path.rglob('test_*.py'):
        rel_path = test_file.relative_to(test_path)
        # 检查是否在排除目录中
        if any(part in exclude_dirs for part in rel_path.parts):
            continue
        test_files.append(str(test_file))

    return sorted(test_files)


def shard_tests(tests: List[str], shard: int, num_shards: int) -> List[str]:
    """将测试文件均匀分片"""
    if num_shards <= 1:
        return tests

    total = len(tests)
    base_size = total // num_shards
    remainder = total % num_shards

    start = 0
    for i in range(1, shard):
        start += base_size + (1 if i <= remainder else 0)

    current_size = base_size + (1 if shard <= remainder else 0)
    return tests[start:start + current_size]


def run_pytest(
    test_files: List[str],
    test_dir: str,
    report_dir: str,
    shard: int,
    timeout: int,
    verbose: bool
) -> int:
    """执行 pytest"""
    os.makedirs(report_dir, exist_ok=True)

    xml_report = os.path.join(report_dir, f'junit_shard_{shard}.xml')
    log_file = os.path.join(report_dir, f'test_shard_{shard}.log')

    # 构建 pytest 命令
    cmd = [
        sys.executable, '-m', 'pytest',
        '-v' if verbose else '-q',
        f'--junit-xml={xml_report}',
        '--tb=short',
        f'--timeout={timeout}',
        '-p', 'no:xdist',  # 禁用 xdist（单进程）
        '--durations=50',
        '-x',  # 首次失败即停止（可选）
    ]

    cmd.extend(test_files)

    print(f"\n{'='*60}")
    print(f"Running shard {shard}: {len(test_files)} test files")
    print(f"{'='*60}\n")

    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(test_dir).parent)
    env['PYTORCH_TEST_NPU'] = '1'

    with open(log_file, 'w') as log:
        log.write(f"Test execution started at {datetime.now()}\n")
        log.write(f"Test files: {len(test_files)}\n\n")
        log.flush()

        result = subprocess.run(
            cmd,
            cwd=test_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=7200  # 整体超时 2 小时
        )

        log.write(result.stdout)

    print(result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout)
    return result.returncode


def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print("PyTorch NPU Test Shard Runner")
    print(f"{'='*60}")
    print(f"Shard: {args.shard}/{args.num_shards}")
    print(f"Test directory: {args.test_dir}")
    print(f"Disabled testcases: {args.disabled_testcases}")
    print(f"{'='*60}\n")

    # Step 1: 加载禁用测试用例
    disabled = load_disabled_testcases(args.disabled_testcases)

    # Step 2: 发现测试文件
    all_test_files = discover_test_files(args.test_dir)
    print(f"Discovered {len(all_test_files)} test files")

    # Step 3: 分片
    sharded_tests = shard_tests(all_test_files, args.shard, args.num_shards)
    print(f"Shard {args.shard} contains {len(sharded_tests)} test files")

    if not sharded_tests:
        print("No tests to run for this shard")
        return 0

    # Step 4: 保存分片信息
    info = {
        'shard': args.shard,
        'num_shards': args.num_shards,
        'total_files': len(all_test_files),
        'shard_files': len(sharded_tests),
        'disabled_count': len(disabled),
        'timestamp': datetime.now().isoformat()
    }
    info_file = os.path.join(args.report_dir, f'shard_{args.shard}_info.json')
    os.makedirs(args.report_dir, exist_ok=True)
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)

    # Step 5: 执行测试
    return run_pytest(
        sharded_tests,
        args.test_dir,
        args.report_dir,
        args.shard,
        args.timeout,
        args.verbose
    )


if __name__ == '__main__':
    sys.exit(main())