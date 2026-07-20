#!/usr/bin/env python3
"""
notify_feishu.py - 通过飞书 webhook 发送 CI 分析报告通知。

用法：
    python3 notify_feishu.py --report <报告路径> [--webhook <url>]
    python3 notify_feishu.py --report reports/29713196943.md

环境变量：
    FEISHU_WEBHOOK - 飞书机器人 webhook URL
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone


def parse_frontmatter(content: str) -> dict:
    fm = {}
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def extract_summary(content: str) -> str:
    m = re.search(r"##\s*失败概览\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if m:
        lines = m.group(1).strip().splitlines()
        return "\n".join(lines[:10])
    m = re.search(r"##\s*详细分析\s*\n(.*?)(?=\n##\s*失败\s*2|\Z)", content, re.DOTALL)
    if m:
        return m.group(1).strip()[:500]
    return "详见报告文件"


def send_feishu(webhook: str, title: str, content: str, report_url: str | None = None) -> bool:
    elements = [
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": content},
        }
    ]
    if report_url:
        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看报告"},
                "url": report_url,
                "type": "primary",
            }],
        })

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "red",
            },
            "elements": elements,
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code", 0) == 0 or result.get("StatusCode", 0) == 0:
                print("飞书通知发送成功", file=sys.stderr)
                return True
            else:
                print(f"飞书通知发送失败: {result}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"飞书通知发送异常: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="发送飞书 CI 通知")
    parser.add_argument("--report", required=True, help="报告文件路径")
    parser.add_argument("--webhook", default=os.environ.get("FEISHU_WEBHOOK", ""), help="飞书 webhook URL")
    parser.add_argument("--repo-url", default="", help="报告所在仓库的 URL（用于生成报告链接）")
    args = parser.parse_args()

    if not args.webhook:
        print("错误：未设置飞书 webhook（--webhook 或 FEISHU_WEBHOOK 环境变量）", file=sys.stderr)
        sys.exit(1)

    from pathlib import Path
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"错误：报告文件不存在: {report_path}", file=sys.stderr)
        sys.exit(1)

    content = report_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    run_id = fm.get("run_id", report_path.stem)
    run_name = fm.get("run_name", f"Run {run_id}")
    run_url = fm.get("run_url", f"https://github.com/Ascend/pytorch/actions/runs/{run_id}")

    summary = extract_summary(content)

    report_url = None
    if args.repo_url:
        report_url = f"{args.repo_url.rstrip('/')}/blob/main/reports/{report_path.name}"

    title = f"Ascend/pytorch CI 失败: {run_name}"
    msg_content = (
        f"**Run ID**: {run_id}\n"
        f"**运行链接**: [{run_url}]({run_url})\n\n"
        f"**失败概览**:\n{summary}"
    )

    success = send_feishu(args.webhook, title, msg_content, report_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
