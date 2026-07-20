#!/usr/bin/env python3
"""
scan_failures.py - 扫描 Ascend/pytorch 的 pytorch_ci_trigger.yml 失败运行。

查找最近 N 小时内 conclusion=failure 的运行，跳过已有报告的，
只返回最新 1 个未分析的失败运行。

用法：
    python3 scan_failures.py [--hours 12] [--reports-dir reports] [--max 1] [--json]
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = "Ascend/pytorch"
WORKFLOW_FILE = "pytorch_ci_trigger.yml"


def gh_api(endpoint: str, jq: str | None = None) -> list | dict | str | int | None:
    cmd = ["gh", "api", endpoint]
    if jq:
        cmd += ["--jq", jq]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        if not r.stdout.strip():
            return []
        return json.loads(r.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"gh api 调用失败: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return []


def get_workflow_id() -> str | None:
    result = gh_api(
        f"repos/{REPO}/actions/workflows",
        jq=".workflows[] | select(.path | endswith(\"{}\")) | .id".format(WORKFLOW_FILE),
    )
    if isinstance(result, list) and result:
        return str(result[0])
    if isinstance(result, (int, str)):
        return str(result)
    return None


def list_failed_runs(workflow_id: str, hours: int) -> list[dict]:
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - hours * 3600))
    result = gh_api(
        f"repos/{REPO}/actions/workflows/{workflow_id}/runs"
        f"?per_page=30&status=failure&created=>={since}",
        jq="[.workflow_runs[] | {id,run_name,name,conclusion,created_at,head_branch,event,html_url}]",
    )
    if not isinstance(result, list):
        return []
    runs = result
    runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return runs


def get_existing_reported_ids(reports_dir: Path) -> set[str]:
    ids = set()
    if not reports_dir.exists():
        return ids
    for f in reports_dir.glob("*.md"):
        stem = f.stem
        if stem.isdigit():
            ids.add(stem)
    return ids


def get_run_name(run_id: str) -> str:
    info = gh_api(f"repos/{REPO}/actions/runs/{run_id}", jq="{run_name,name}")
    if isinstance(info, dict):
        return info.get("run_name") or info.get("name") or f"Run {run_id}"
    return f"Run {run_id}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="扫描 pytorch_ci_trigger.yml 失败运行")
    parser.add_argument("--hours", type=int, default=12, help="扫描最近 N 小时（默认 12）")
    parser.add_argument("--reports-dir", type=str, default="reports", help="报告目录（默认 reports）")
    parser.add_argument("--max", type=int, default=1, help="最多返回几个（默认 1）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    reported_ids = get_existing_reported_ids(reports_dir)

    workflow_id = get_workflow_id()
    if not workflow_id:
        msg = f"未找到 workflow {WORKFLOW_FILE}"
        if args.json:
            print(json.dumps({"error": msg, "failures": []}))
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    print(f"Workflow ID: {workflow_id}", file=sys.stderr)
    print(f"扫描最近 {args.hours} 小时的失败运行...", file=sys.stderr)

    failed_runs = list_failed_runs(workflow_id, args.hours)
    print(f"找到 {len(failed_runs)} 个失败运行", file=sys.stderr)

    unanalyzed = []
    for run in failed_runs:
        run_id = str(run["id"])
        if run_id in reported_ids:
            print(f"  跳过 {run_id}（已有报告）", file=sys.stderr)
            continue
        run["run_name"] = run.get("run_name") or get_run_name(run_id)
        unanalyzed.append(run)
        if len(unanalyzed) >= args.max:
            break

    if not unanalyzed:
        msg = "无新的失败运行需要分析"
        if args.json:
            print(json.dumps({"message": msg, "failures": []}))
        else:
            print(msg, file=sys.stderr)
        return

    print(f"待分析: {len(unanalyzed)} 个", file=sys.stderr)
    for r in unanalyzed:
        print(f"  - {r['id']} {r.get('run_name', '')} ({r.get('created_at', '')})", file=sys.stderr)

    if args.json:
        print(json.dumps({"failures": unanalyzed}, ensure_ascii=False, indent=2))
    else:
        for r in unanalyzed:
            print(r["id"])


if __name__ == "__main__":
    main()
