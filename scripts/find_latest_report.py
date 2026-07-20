#!/usr/bin/env python3
"""
find_latest_report.py - 查找最新的 AI 分析报告，供 issue-create workflow 使用。

用法：
    python3 find_latest_report.py [--reports-dir reports] [--report-file <指定文件>] [--json]

无报告时输出空并 exit 0。
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    fm = {}
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip()
            if val.startswith("["):
                continue
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fm[key.strip()] = val
    return fm


def main():
    parser = argparse.ArgumentParser(description="查找最新 AI 分析报告")
    parser.add_argument("--reports-dir", default="reports", help="报告目录")
    parser.add_argument("--report-file", default="", help="指定报告文件名（可选）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)

    if args.report_file:
        report_path = Path(args.report_file)
        if not report_path.is_absolute():
            report_path = reports_dir / args.report_file
        if not report_path.exists():
            msg = f"指定的报告不存在: {report_path}"
            if args.json:
                print(json.dumps({"error": msg, "report": None}))
            else:
                print(msg, file=sys.stderr)
            sys.exit(0)
        reports = [report_path]
    else:
        if not reports_dir.exists():
            msg = "无报告"
            if args.json:
                print(json.dumps({"message": msg, "report": None}))
            else:
                print(msg, file=sys.stderr)
            sys.exit(0)
        reports = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not reports:
            msg = "无报告"
            if args.json:
                print(json.dumps({"message": msg, "report": None}))
            else:
                print(msg, file=sys.stderr)
            sys.exit(0)

    report_path = reports[0]
    content = report_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    run_id = fm.get("run_id", "")
    if not run_id:
        m = re.match(r"^(\d+)-", report_path.stem)
        run_id = m.group(1) if m else report_path.stem
    run_name = fm.get("run_name", f"Run {run_id}")

    pr_match = re.search(r"PR #(\d+)", run_name)
    pr_number = pr_match.group(1) if pr_match else ""

    result = {
        "report_path": str(report_path),
        "report_file": report_path.name,
        "run_id": run_id,
        "run_name": run_name,
        "pr_number": pr_number,
        "has_report": True,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(report_path)
        print(f"run_id: {run_id}", file=sys.stderr)
        print(f"run_name: {run_name}", file=sys.stderr)
        if pr_number:
            print(f"pr_number: {pr_number}", file=sys.stderr)


if __name__ == "__main__":
    main()
