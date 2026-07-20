#!/usr/bin/env python3
"""
check_duplicate.py - 基于失败指纹判断是否已有同根因报告。

指纹 = SHA256(归一化的失败 job 名 + 关键错误行)
扫描 reports/ 目录中所有报告的 frontmatter fingerprint 字段，判断是否已存在。

用法：
    python3 check_duplicate.py --failures <failures.json> --reports-dir reports [--json]
"""

import hashlib
import json
import re
import sys
from pathlib import Path


def normalize_error_line(line: str) -> str:
    s = re.sub(r"\d{4}-\d{2}-\d{2}T[\d:.Z]+", "", line)
    s = re.sub(r"/tmp/\S+", "", s)
    s = re.sub(r"/home/runner/\S+", "", s)
    s = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", s)
    s = re.sub(r"\b\d{5,}\b", "NUM", s)
    s = s.strip()
    return s


def compute_fingerprint(failures_path: str) -> str:
    data = json.loads(Path(failures_path).read_text(encoding="utf-8"))
    failures = data.get("failures", [])
    if not failures:
        return ""
    parts = []
    for f in failures:
        job_name = f.get("job_name", "")
        errors = f.get("errors", [])
        error_lines = []
        for e in errors[:3]:
            line = e.get("error_line", "")
            error_lines.append(normalize_error_line(line))
        parts.append(f"{job_name}|{'||'.join(error_lines)}")
    raw = "\n".join(sorted(parts))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


def find_duplicate_fingerprint(fingerprint: str, reports_dir: Path) -> str | None:
    if not reports_dir.exists():
        return None
    for report_file in sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        content = report_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        existing_fp = fm.get("fingerprint", "")
        if existing_fp and existing_fp == fingerprint:
            return report_file.name
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="基于失败指纹去重检查")
    parser.add_argument("--failures", required=True, help="failures.json 路径")
    parser.add_argument("--reports-dir", default="reports", help="报告目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    fingerprint = compute_fingerprint(args.failures)
    if not fingerprint:
        msg = "无法计算指纹（failures.json 无失败信息）"
        if args.json:
            print(json.dumps({"duplicate": False, "reason": msg, "fingerprint": ""}))
        else:
            print(msg, file=sys.stderr)
        sys.exit(0)

    print(f"指纹: {fingerprint[:16]}...", file=sys.stderr)

    reports_dir = Path(args.reports_dir)
    existing = find_duplicate_fingerprint(fingerprint, reports_dir)

    if existing:
        msg = f"发现同根因报告: {existing}"
        print(msg, file=sys.stderr)
        if args.json:
            print(json.dumps({
                "duplicate": True,
                "fingerprint": fingerprint,
                "existing_report": existing,
            }, ensure_ascii=False, indent=2))
        else:
            print(existing)
    else:
        print("无同根因报告，可继续分析", file=sys.stderr)
        if args.json:
            print(json.dumps({
                "duplicate": False,
                "fingerprint": fingerprint,
            }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
